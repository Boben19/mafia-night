import random, string
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
