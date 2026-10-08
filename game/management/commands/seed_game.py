from django.core.management.base import BaseCommand
from game.models import Role, Rule

ROLES = [
 ("Mafia", "Mafia", "Can kill one player each night."),
 ("Host/Hostess", "Mafia", "Seduces (blocks) a player from speaking or voting. Seducing a Mafia member puts them in contact with you."),
 ("Witch", "Mafia", "Curses a player every night. If the cursed player can't find the Witch, they die."),
 ("Thief", "Mafia", "Steals another player's occupation and uses their abilities for a day. Stealing a Mafia role puts you in contact."),
 ("Spy", "Mafia", "Investigates one player's role each night. Investigating a Mafia member puts you in contact. Detectives can't detect the Spy."),
 ("Hitman", "Mafia", "From the second night, kills a player by correctly guessing their role. Guessing Mafia puts you in contact."),
 ("Big Boss", "Mafia", "Has one chance to convert a player's role to Citizen."),
 ("Citizen", "Citizen", "No special abilities."),
 ("Detective", "Citizen", "Investigates a player's role every night."),
 ("Doctor", "Citizen", "Heals or protects one player each night."),
 ("Sheriff", "Citizen", "Has one shot. Hit a Mafia member and you live; miss and you die."),
 ("Priest", "Citizen", "Can sacrifice themselves to revive another player the next day."),
 ("Guardian Angel", "Citizen", "Can protect one player after they die."),
 ("Mayor", "Citizen", "Their vote counts as two and they cannot be voted out."),
 ("Judge", "Citizen", "Can overrule a voting result once per game."),
 ("Magician", "Citizen", "Tricks a player into switching roles upon the Magician's death."),
 ("Ghoul", "Citizen", "Inherits the role of the first player killed."),
 ("Martyr", "Citizen", "If voted out, takes another player along. Each night picks a player; if that player is Mafia and tries to kill the Martyr, the Mafia member dies too."),
 ("Psychic", "Citizen", "Investigates and learns the role of a dead player."),
 ("Nurse", "Citizen", "Prescribes a player each night. Prescribing the Doctor puts you in contact. If the Doctor dies, the Nurse inherits the healing ability."),
 ("Reporter/Paparazzi", "Citizen", "One chance to stalk a player and learn their role."),
 ("Prophet", "Citizen", "If alive on the fourth day, can reveal a prophecy: is a player a Citizen or a Cultist?"),
 ("Jackal", "Neutral", "Kills one player each night. Wins by being the last one standing."),
 ("Jester", "Neutral", "Wins by getting voted out."),
 ("Cult Leader", "Neutral", "Converts one player to the cult each night. Wins by converting everyone left."),
]
RULES = [
 ("The goal", "Mafia eliminates every Citizen and opposing role. Citizens find and eliminate every Mafia member. Neutrals chase their own objectives."),
 ("Night and day", "At night, special roles act in secret. By day, everyone discusses, accuses, and votes someone out. The MC narrates and guides each phase."),
 ("Keep it secret", "Never reveal your role unless an ability or a vote reveals it."),
 ("Voting", "A majority vote is needed to eliminate someone. The Judge may overrule a result once per game."),
 ("Winning", "Mafia wins when all Citizens and Neutrals are gone. Citizens win when all Mafia are gone. Neutrals win when they meet their own condition."),
 ("Fair play", "No cheating, no talking about the game outside the designated discussions, and respect every player. Harassment is not tolerated."),
 ("The MC", "The MC runs the game, enforces the rules, and keeps it fun. The MC sits out the round they run."),
 ("Custom roles and rules", "New roles or rule changes are allowed, but all players must agree to them before the game starts."),
]

class Command(BaseCommand):
    help = "Load the roles and house rules from the Mafia constitution"
    def handle(self, *args, **kwargs):
        for n, f, t in ROLES:
            Role.objects.get_or_create(name=n, defaults={"faction": f, "ability": t,
                "vote_weight": 2 if n == "Mayor" else 1, "vote_immune": n == "Mayor"})
        for t, x in RULES:
            Rule.objects.get_or_create(title=t, defaults={"text": x})
        self.stdout.write(self.style.SUCCESS("Roles and rules loaded."))
