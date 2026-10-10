import random
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Follow, Friendship, Game, Group, Player, Profile, name_hue

User = get_user_model()
RANKS = [(0, "Fresh Face"), (10, "Associate"), (30, "Capo"), (60, "Underboss"), (100, "Godfather")]

def prof(u):
    return Profile.objects.get_or_create(user=u, defaults={"hue": name_hue(u.username)})[0]

def record(u):
    rs = u.results.all()
    played = rs.exclude(role_name="MC")
    n, w = played.count(), played.filter(won=True).count()
    xp = n + 2 * w
    cur = [r for r in RANKS if r[0] <= xp][-1]
    nxt = next((r for r in RANKS if r[0] > xp), None)
    return {"played": n, "wins": w, "losses": played.filter(won=False).count(), "rate": int(w * 100 / n) if n else 0,
            "hosted": rs.filter(role_name="MC").count(), "xp": xp, "rank": cur[1], "next": nxt, "need": nxt[0] - xp if nxt else 0,
            "pct": int((xp - cur[0]) * 100 / (nxt[0] - cur[0])) if nxt else 100,
            "by": [(f, played.filter(faction=f).count(), played.filter(faction=f, won=True).count())
                   for f in ("Mafia", "Citizen", "Neutral")]}

def fstatus(me, other):
    f = Friendship.objects.filter(Q(from_user=me, to_user=other) | Q(from_user=other, to_user=me)).first()
    if not f:
        return "none", None
    if f.accepted:
        return "friends", f
    return ("sent" if f.from_user_id == me.id else "received"), f

def friends_of(u):
    fs = Friendship.objects.filter(accepted=True).filter(Q(from_user=u) | Q(to_user=u)).select_related("from_user", "to_user")
    return [f.to_user if f.from_user_id == u.id else f.from_user for f in fs]

@login_required
def profile(request, username):
    u = get_object_or_404(User, username=username)
    me = request.user
    ctx = {"u": u, "p": prof(u), "rec": record(u), "recent": u.results.select_related("group")[:10], "is_me": u == me,
           "followers": u.followers_rel.count(), "following": u.following_rel.count(),
           "groups": u.game_groups.all(), "friends": friends_of(u)}
    if u == me:
        ctx["incoming"] = Friendship.objects.filter(to_user=me, accepted=False).select_related("from_user")
    else:
        ctx["i_follow"] = Follow.objects.filter(follower=me, following=u).exists()
        ctx["fs"] = fstatus(me, u)[0]
    return render(request, "game/profile.html", ctx)

class ProfileForm(forms.Form):
    username = forms.RegexField(r"^[\w.@+-]+$", max_length=30, error_messages={"invalid": "Letters, numbers and . @ + - _ only."})
    bio = forms.CharField(max_length=200, required=False, widget=forms.Textarea(attrs={"rows": 3}), label="About you")
    emoji = forms.CharField(max_length=8, required=False, label="Your emoji (optional)")
    hue = forms.IntegerField(min_value=0, max_value=359, label="Avatar color",
                             widget=forms.NumberInput(attrs={"type": "range", "min": 0, "max": 359}))
    def __init__(self, *a, user=None, **kw):
        super().__init__(*a, **kw)
        self.user = user
    def clean_username(self):
        n = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=n).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Somebody already has that name.")
        return n

@login_required
def profile_edit(request):
    p = prof(request.user)
    init = {"username": request.user.username, "bio": p.bio, "emoji": p.emoji, "hue": p.hue}
    form = ProfileForm(request.POST or None, initial=init, user=request.user)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        request.user.username = d["username"]
        request.user.save()
        p.bio, p.emoji, p.hue = d["bio"], d["emoji"].strip(), d["hue"]
        p.save()
        messages.success(request, "Profile saved.")
        return redirect("profile", username=request.user.username)
    return render(request, "game/profile_edit.html", {"form": form, "p": p})

@login_required
@require_POST
def follow(request, username):
    u = get_object_or_404(User, username=username)
    if u != request.user:
        obj, made = Follow.objects.get_or_create(follower=request.user, following=u)
        if not made:
            obj.delete()
    return redirect("profile", username=username)

@login_required
@require_POST
def friend(request, username):
    u = get_object_or_404(User, username=username)
    a, (st, f) = request.POST.get("a"), fstatus(request.user, u)
    if u != request.user:
        if a == "add" and st == "none":
            Friendship.objects.create(from_user=request.user, to_user=u)
        elif a == "accept" and st == "received":
            f.accepted = True
            f.save()
        elif a in ("decline", "cancel", "remove") and f:
            f.delete()
    return redirect(request.POST.get("back") or "profile", **({} if request.POST.get("back") else {"username": username}))

@login_required
def people(request):
    q = request.GET.get("q", "").strip()
    found = User.objects.filter(username__icontains=q).order_by("username")[:30] if q else []
    top = User.objects.annotate(w=Count("results", filter=Q(results__won=True))).filter(w__gt=0).order_by("-w", "username")[:10]
    return render(request, "game/people.html", {"q": q, "found": found, "top": top})

# ---------- groups ----------
def member_group(request, pk):
    g = get_object_or_404(Group, pk=pk)
    return g if g.members.filter(pk=request.user.pk).exists() else None

@login_required
def groups(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()[:60]
        if not name:
            messages.error(request, "Give the group a name first.")
            return redirect("groups")
        g = Group.objects.create(name=name, description=request.POST.get("description", "").strip()[:140], owner=request.user)
        g.members.add(request.user)
        return redirect("group", pk=g.pk)
    return render(request, "game/groups.html", {"mine": request.user.game_groups.all()})

@login_required
@require_POST
def group_join(request):
    g = Group.objects.filter(code=request.POST.get("code", "").strip().upper()).first()
    if not g:
        messages.error(request, "No group with that code.")
        return redirect("groups")
    g.members.add(request.user)
    return redirect("group", pk=g.pk)

@login_required
def group(request, pk):
    g = member_group(request, pk)
    if not g:
        messages.error(request, "That group is for members only. Ask for its invite code.")
        return redirect("groups")
    return render(request, "game/group.html", {"g": g, "members": g.members.all(), "open": g.games.filter(phase="lobby"),
                  "history": g.games.filter(phase="over").order_by("-id")[:8], "is_owner": g.owner_id == request.user.pk})

@login_required
@require_POST
def group_leave(request, pk):
    g = member_group(request, pk)
    if g:
        g.members.remove(request.user)
        rest = g.members.first()
        if not rest:
            g.delete()
        elif g.owner_id == request.user.pk:
            g.owner = rest
            g.save()
    return redirect("groups")

@login_required
@require_POST
def group_delete(request, pk):
    g = get_object_or_404(Group, pk=pk, owner=request.user)
    g.delete()
    messages.success(request, "Group deleted.")
    return redirect("groups")

def seat(request, game, mc=False):
    name, n = request.user.username[:40], 1
    while game.players.filter(name__iexact=name).exists():
        n += 1
        name = f"{request.user.username[:36]}{n}"
    p = Player.objects.create(game=game, name=name, is_mc=mc, user=request.user)
    request.session[f"p_{game.code}"] = p.id
    return p

@login_required
@require_POST
def group_host(request, pk):
    g = member_group(request, pk)
    if not g:
        return redirect("groups")
    game = Game.objects.create(group=g)
    seat(request, game, mc=True)
    return redirect("room", code=game.code)

@login_required
@require_POST
def group_sit(request, pk, code):
    g = member_group(request, pk)
    game = g.games.filter(code=code, phase="lobby").first() if g else None
    if not game:
        messages.error(request, "That table isn't open anymore.")
        return redirect("groups")
    if not game.players.filter(user=request.user).exists():
        seat(request, game)
    return redirect("room", code=game.code)
