# Mafia Night

A Django web app for playing the Mafia Game, built from the Mafia Game Constitution (modified version, March 22, 2025).

## Run it on your computer
```
python -m venv venv
venv\Scripts\activate            (Windows)   |   source venv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_game
python manage.py runserver
```
Open http://127.0.0.1:8000/. To let friends join on the same Wi-Fi, run `python manage.py runserver 0.0.0.0:8000` and share your computer's IP address.

Optional: `python manage.py createsuperuser` gives you a login for /admin/.

## Accounts and social login
Players sign up with a username or use Google, Facebook or GitHub. Set these before running, then add each provider's callback URL (for example `http://127.0.0.1:8000/accounts/github/login/callback/`) in its developer console:
`GOOGLE_ID, GOOGLE_SECRET, FACEBOOK_ID, FACEBOOK_SECRET, GITHUB_ID, GITHUB_SECRET`
The username signup works without any keys, and a provider's button only appears once its ID variable is set. Never put secrets in settings.py. On PythonAnywhere set them in the WSGI file with `os.environ[...]`, plus `DJANGO_DEBUG=0` and a long `SECRET_KEY`.

## How a round goes
1. The MC opens a room and shares the 4-letter code. Players join with a name.
2. The MC picks how many of each role to use and deals. The MC sits that round out and can hand the mic to someone else between rounds.
3. The MC moves between Night and Day, takes players out or brings them back, and narrates. Players peek at their role, vote by day, and follow the story feed.
4. The win check follows the constitution. Special wins (Cult Leader, Jackal) are declared by the MC.

The MC can add, edit, or delete roles and rules any time from the Roles and Rules pages. Remember Article V: everyone should agree before the game starts.

## Put it on GitHub (new repo)
1. On github.com click **New repository**. Name it (for example `mafia-night`), leave it empty (no README, no .gitignore), click **Create repository**.
2. In your project folder, the one that has `manage.py`:
```
git init
git add .
git commit -m "Mafia Night first version"
git branch -M main
git remote add origin https://github.com/<your-username>/mafia-night.git
git push -u origin main
```
`.gitignore` already keeps `venv/`, `db.sqlite3` and `__pycache__` out of the repo.

## Put it on PythonAnywhere (new account or new app)
1. Log in at pythonanywhere.com, open a **Bash** console from the Dashboard.
2. Make a virtual environment and clone the repo (use the newest Python 3 your account offers, Django 6 needs 3.12 or higher):
```
virtualenv --python=python3.13 mafiaenv
source mafiaenv/bin/activate
git clone https://github.com/<your-username>/mafia-night.git
cd mafia-night
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_game
```
3. **Web** tab > **Add a new web app** > Next > **Manual configuration** > pick the same Python version.
4. In the **Virtualenv** box enter `/home/<your-pa-username>/mafiaenv`.
5. Click the WSGI configuration file link, delete everything in it, and paste:
```python
import os
import sys

path = "/home/<your-pa-username>/mafia-night"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "mafia.settings"
os.environ["DJANGO_DEBUG"] = "0"
os.environ["SECRET_KEY"] = "put-a-long-random-string-here"

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
application = StaticFilesHandler(get_wsgi_application())
```
6. Save, then press the green **Reload** button. Your game lives at `https://<your-pa-username>.pythonanywhere.com/`.
7. For later updates: push from your computer, then in the PythonAnywhere Bash console run `cd ~/mafia-night && git pull`, `python manage.py migrate` if models changed, and Reload.

`ALLOWED_HOSTS` already accepts `.pythonanywhere.com`. If you use Google/Facebook/GitHub login, open `/admin/`, go to **Sites**, and change `example.com` to your PythonAnywhere address.

Authors: proposed by Jhon Grover Longsud, modified by Leeh Vann Joshua M. Lomocso.

## Keys and guests
Keys live in `.env` (copy `.env.example`), which is git-ignored. Real environment variables override it. Guests get a throwaway account from the login or signup page. Clean old ones in /admin when you like.
