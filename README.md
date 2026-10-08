# Mafia Night

A Django web app for playing the Mafia Game, built from the Mafia Game Constitution (modified version, March 22, 2025).

## Run it
```
python -m venv mafiaenv
mafiaenv\Scripts\activate        (Windows)   |   source mafiaenv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
python manage.py makemigrations game
python manage.py migrate
python manage.py seed_game
python manage.py runserver
```
Open http://127.0.0.1:8000/. To let friends join on the same Wi-Fi, run `python manage.py runserver 0.0.0.0:8000` and share your computer's IP address.

## Accounts and social login
Players sign up with a username or use Google, Facebook or GitHub. Set these before running, then add each provider's callback URL (for example `http://127.0.0.1:8000/accounts/github/login/callback/`) in its developer console:
`GOOGLE_ID, GOOGLE_SECRET, FACEBOOK_ID, FACEBOOK_SECRET, GITHUB_ID, GITHUB_SECRET`
The username signup works without any keys.

## How a round goes
1. The MC opens a room and shares the 4-letter code. Players join with a name.
2. The MC picks how many of each role to use and deals. The MC sits that round out and can hand the mic to someone else between rounds.
3. The MC moves between Night and Day, takes players out or brings them back, and narrates. Players peek at their role, vote by day, and follow the story feed.
4. The win check follows the constitution. Special wins (Cult Leader, Jackal) are declared by the MC.

The MC can add, edit, or delete roles and rules any time from the Roles and Rules pages. Remember Article V: everyone should agree before the game starts.

## Deploying on PythonAnywhere
Same steps as the PSUSphere guide: push to GitHub, clone, install requirements.txt in a virtualenv, set ALLOWED_HOSTS (already allows .pythonanywhere.com), point the WSGI file at `mafia.settings`, and reload.

Authors: proposed by Jhon Grover Longsud, modified by Leeh Vann Joshua M. Lomocso.
