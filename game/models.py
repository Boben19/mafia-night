import random, string
from django.conf import settings
from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Role(BaseModel):
    FACTIONS = [("Mafia", "Mafia"), ("Citizen", "Citizen"), ("Neutral", "Neutral")]
    name = models.CharField(max_length=60, unique=True)
    faction = models.CharField(max_length=10, choices=FACTIONS)
    ability = models.TextField()
    vote_weight = models.PositiveSmallIntegerField(default=1, help_text="How many votes this player's vote counts as")
    vote_immune = models.BooleanField(default=False, help_text="Cannot be voted out")
    def __str__(self):
        return self.name

class Rule(BaseModel):
    title = models.CharField(max_length=120)
    text = models.TextField()
    def __str__(self):
        return self.title

def make_code():
    while True:
        c = "".join(random.choices(string.ascii_uppercase, k=4))
        if not Game.objects.filter(code=c).exists():
            return c

class Game(BaseModel):
    code = models.CharField(max_length=4, unique=True, default=make_code)
    phase = models.CharField(max_length=10, default="lobby")  # lobby, night, day, over
    day = models.PositiveSmallIntegerField(default=0)
    winner = models.CharField(max_length=20, blank=True)
    group = models.ForeignKey("Group", null=True, blank=True, on_delete=models.SET_NULL, related_name="games")

    def check_winner(self):
        sides = [p.role.faction for p in self.players.filter(alive=True, is_mc=False, role__isnull=False).select_related("role")]
        if not sides:
            return ""
        if "Mafia" not in sides:
            return "Citizens"
        if "Citizen" not in sides and "Neutral" not in sides:
            return "Mafia"
        return ""

class Player(BaseModel):
    game = models.ForeignKey(Game, related_name="players", on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    is_mc = models.BooleanField(default=False)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    alive = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="seats")
    vote = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="votes_against")
    class Meta:
        ordering = ["-is_mc", "id"]
    def __str__(self):
        return self.name

class Story(BaseModel):
    game = models.ForeignKey(Game, related_name="story", on_delete=models.CASCADE)
    text = models.CharField(max_length=300)
    class Meta:
        ordering = ["-id"]


U = settings.AUTH_USER_MODEL

def name_hue(name):
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) % 360
    return h

class Profile(BaseModel):
    user = models.OneToOneField(U, on_delete=models.CASCADE, related_name="profile")
    bio = models.CharField(max_length=200, blank=True)
    emoji = models.CharField(max_length=8, blank=True)
    hue = models.PositiveSmallIntegerField(default=40)

class Follow(BaseModel):
    follower = models.ForeignKey(U, on_delete=models.CASCADE, related_name="following_rel")
    following = models.ForeignKey(U, on_delete=models.CASCADE, related_name="followers_rel")
    class Meta:
        unique_together = [("follower", "following")]

class Friendship(BaseModel):
    from_user = models.ForeignKey(U, on_delete=models.CASCADE, related_name="friend_sent")
    to_user = models.ForeignKey(U, on_delete=models.CASCADE, related_name="friend_received")
    accepted = models.BooleanField(default=False)
    class Meta:
        unique_together = [("from_user", "to_user")]

def make_group_code():
    while True:
        c = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Group.objects.filter(code=c).exists():
            return c

class Group(BaseModel):
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=140, blank=True)
    owner = models.ForeignKey(U, on_delete=models.CASCADE, related_name="owned_groups")
    members = models.ManyToManyField(U, related_name="game_groups", blank=True)
    code = models.CharField(max_length=6, unique=True, default=make_group_code)
    def __str__(self):
        return self.name

class MatchResult(BaseModel):
    user = models.ForeignKey(U, on_delete=models.CASCADE, related_name="results")
    game_code = models.CharField(max_length=4)
    role_name = models.CharField(max_length=60)   # "MC" when they hosted
    faction = models.CharField(max_length=10, blank=True)
    won = models.BooleanField(null=True)
    winner = models.CharField(max_length=20, blank=True)
    days = models.PositiveSmallIntegerField(default=0)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL, related_name="results")
    class Meta:
        ordering = ["-id"]
