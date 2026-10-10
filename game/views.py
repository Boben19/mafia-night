import random
import re, secrets
from django.contrib import messages
from django.contrib.auth import login as auth_login, get_user_model
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Game, Player, Role, Rule, Story

ROLE_FIELDS = ["name", "faction", "ability", "vote_weight", "vote_immune"]

def is_mc(request):
    ids = [v for k, v in request.session.items() if k.startswith("p_")]
    return Player.objects.filter(id__in=ids, is_mc=True).exists()

def me_in(request, g):
    return g.players.select_related("role").filter(id=request.session.get(f"p_{g.code}")).first()

def tally(g):
    w = {}
    for p in g.players.filter(is_mc=False, alive=True, vote__alive=True).exclude(vote=None).select_related("role"):
        w[p.vote_id] = w.get(p.vote_id, 0) + (p.role.vote_weight if p.role else 1)
    byid = {p.id: p for p in g.players.filter(id__in=w)}
    return sorted(((byid[i], n) for i, n in w.items()), key=lambda x: -x[1])

def signature(g):
    seats = "/".join(f"{p.id}:{int(p.alive)}:{p.vote_id or 0}:{int(p.is_mc)}" for p in g.players.all())
    return "|".join(str(x) for x in (g.phase, g.day, g.winner, g.story.count(), seats))

@login_required
def home(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()[:40]
        if not name:
            messages.error(request, "Tell us your name first.")
            return redirect("home")
        if "create" in request.POST:
            g = Game.objects.create()
            p = Player.objects.create(game=g, name=name, is_mc=True)
        else:
            g = Game.objects.filter(code=request.POST.get("code", "").strip().upper()).first()
            if g and g.players.filter(id=request.session.get(f"p_{g.code}")).exists():
                return redirect("room", code=g.code)
            if not g or g.phase != "lobby":
                messages.error(request, "No open room with that code. Double-check it with your MC.")
                return redirect("home")
            if g.players.filter(name__iexact=name).exists():
                messages.error(request, "Somebody already took that name, try another.")
                return redirect("home")
            p = Player.objects.create(game=g, name=name)
        request.session[f"p_{g.code}"] = p.id
        return redirect("room", code=g.code)
    return render(request, "game/home.html", {"role_count": Role.objects.count(), "rule_count": Rule.objects.count()})

def finish(g):
    w = g.check_winner()
    if w and g.phase != "over":
        g.winner, g.phase = w, "over"
        g.save()
        Story.objects.create(game=g, text=f"Game over. Winner: {w}!")

def mc_action(request, g, a):
    P = request.POST
    say = lambda t: Story.objects.create(game=g, text=t)
    players = g.players.filter(is_mc=False)
    if a == "deal" and g.phase == "lobby":
        pool = []
        for r in Role.objects.all():
            pool += [r] * int(P.get(f"n_{r.id}") or 0)
        n = players.count()
        if n < 4:
            messages.error(request, "You need at least 4 players besides yourself.")
            return
        if len(pool) > n:
            messages.error(request, f"You picked {len(pool)} roles but only {n} people are playing.")
            return
        citizen, _ = Role.objects.get_or_create(name="Citizen", defaults={"faction": "Citizen", "ability": "No special ability."})
        pool += [citizen] * (n - len(pool))
        random.shuffle(pool)
        for p, r in zip(players, pool):
            p.role, p.alive, p.vote = r, True, None
            p.save()
        g.story.all().delete()
        g.phase, g.day, g.winner = "night", 1, ""
        g.save()
        say("Roles are dealt. Night 1 begins, everybody close your eyes.")
    elif a in ("night", "day") and g.phase in ("night", "day"):
        players.update(vote=None)
        if a == "night":
            g.day += 1
        g.phase = a
        g.save()
        say(f"Night {g.day} falls. Eyes closed." if a == "night" else f"Day {g.day} breaks. Open your eyes and start talking.")
    elif a in ("kill", "revive") and g.phase in ("night", "day"):
        p = players.filter(id=P.get("pid")).first()
        if p:
            p.alive = a == "revive"
            p.save()
            say(f"{p.name} is back in the game." if a == "revive" else f"{p.name} has been taken out.")
            finish(g)
    elif a == "eliminate" and g.phase == "day":
        t = tally(g)
        if not t or (len(t) > 1 and t[0][1] == t[1][1]):
            say("The vote is tied, so nobody leaves the table.")
            return
        p = t[0][0]
        if p.role and p.role.vote_immune:
            say(f"{p.name} got the most votes, but can't be voted out.")
            return
        p.alive = False
        p.save()
        say(f"The town voted out {p.name}. They were the {p.role}.")
        if p.role and p.role.name == "Jester":
            g.winner, g.phase = "Jester", "over"
            g.save()
            say("The Jester got exactly what they wanted. Winner: Jester!")
        else:
            finish(g)
    elif a == "say" and P.get("text", "").strip():
        say(P["text"].strip()[:300])
    elif a == "winner" and P.get("text", "").strip():
        g.winner, g.phase = P["text"].strip()[:20], "over"
        g.save()
        say(f"Game over. Winner: {g.winner}!")
    elif a == "reset":
        players.update(role=None, alive=True, vote=None)
        g.story.all().delete()
        g.phase, g.day, g.winner = "lobby", 0, ""
        g.save()
    elif a == "pass_mc" and g.phase == "lobby":
        n = players.filter(id=P.get("pid")).first()
        if n:
            g.players.filter(is_mc=True).update(is_mc=False)
            n.is_mc = True
            n.save()

@login_required
def room(request, code):
    g = get_object_or_404(Game, code=code.upper())
    me = me_in(request, g)
    if not me:
        return redirect("home")
    if request.method == "POST":
        a = request.POST.get("a")
        if me.is_mc:
            mc_action(request, g, a)
        elif a == "vote" and g.phase == "day" and me.alive:
            me.vote = g.players.filter(id=request.POST.get("target") or 0, alive=True, is_mc=False).first()
            me.save()
        return redirect("room", code=g.code)
    players = list(g.players.select_related("role"))
    mafia = []
    if me.role and me.role.faction == "Mafia":
        mafia = [p for p in players if p != me and p.role and p.role.faction == "Mafia"]
    votes = tally(g)
    top = votes[0][1] if votes else 1
    bars = [(p, n, int(n * 100 / top)) for p, n in votes]
    return render(request, "game/room.html", {"g": g, "me": me, "players": players, "tally": votes, "bars": bars,
        "mafia": mafia, "roles": Role.objects.order_by("faction", "name"), "sig": signature(g)})

def ping(request, code):
    return HttpResponse(signature(get_object_or_404(Game, code=code.upper())))

# Roles and rules library: anyone can read, only the MC can change things
class MCOnly(UserPassesTestMixin):
    def test_func(self):
        return is_mc(self.request)
    def handle_no_permission(self):
        messages.error(self.request, "Only the MC can change roles and rules.")
        return redirect("home")

class Library:
    paginate_by = 8
    template_name = "game/library.html"
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            f = Q()
            for s in self.search_fields:
                f |= Q(**{s + "__icontains": q})
            qs = qs.filter(f)
        s = self.request.GET.get("sort_by")
        return qs.order_by(s if s in dict(self.sorts) else self.sorts[0][0])
    def get_context_data(self, **kw):
        c = super().get_context_data(**kw)
        c.update(title=self.title, add_url=self.urls[0], edit_url=self.urls[1], del_url=self.urls[2],
                 sorts=self.sorts, is_mc=is_mc(self.request))
        return c

class RoleList(Library, ListView):
    model, title = Role, "Role guide"
    search_fields = ["name", "ability"]
    sorts = [("name", "Name"), ("faction", "Faction")]
    urls = ("role-add", "role-edit", "role-delete")

class RuleList(Library, ListView):
    model, title = Rule, "House rules"
    search_fields = ["title", "text"]
    sorts = [("title", "Title"), ("-created_at", "Newest")]
    urls = ("rule-add", "rule-edit", "rule-delete")

class RoleCreate(MCOnly, CreateView):
    model, fields, title = Role, ROLE_FIELDS, "Add a role"
    template_name = "game/form.html"
    success_url = reverse_lazy("roles")

class RoleUpdate(MCOnly, UpdateView):
    model, fields, title = Role, ROLE_FIELDS, "Edit role"
    template_name = "game/form.html"
    success_url = reverse_lazy("roles")

class RoleDelete(MCOnly, DeleteView):
    model = Role
    template_name = "game/confirm.html"
    success_url = reverse_lazy("roles")

class RuleCreate(MCOnly, CreateView):
    model, fields, title = Rule, ["title", "text"], "Add a rule"
    template_name = "game/form.html"
    success_url = reverse_lazy("rules")

class RuleUpdate(MCOnly, UpdateView):
    model, fields, title = Rule, ["title", "text"], "Edit rule"
    template_name = "game/form.html"
    success_url = reverse_lazy("rules")

class RuleDelete(MCOnly, DeleteView):
    model = Rule
    template_name = "game/confirm.html"
    success_url = reverse_lazy("rules")


@require_POST
def guest_login(request):
    """Let someone in without an account. They get a throwaway user tied to this browser."""
    nick = re.sub(r"[^A-Za-z0-9 _-]", "", request.POST.get("name", "")).strip()[:20] or "Guest"
    User = get_user_model()
    while True:
        username = f"{nick.replace(' ', '_')}-{secrets.token_hex(2)}"
        if not User.objects.filter(username=username).exists():
            break
    user = User(username=username)
    user.set_unusable_password()
    user.save()
    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    nxt = request.POST.get("next", "")
    ok = nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()})
    return redirect(nxt if ok else "home")
