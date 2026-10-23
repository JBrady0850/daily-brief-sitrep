# Privacy

- No account, no analytics, no server of ours.
- The web version keeps your settings, recipients, history and last brief in
  this browser's local storage. **Settings, Erase everything** removes them.
- The desktop app keeps its copy in a `.daily-brief` folder in your home folder
  (or the folder named by `DAILY_BRIEF_HOME`): `config.json` (settings for
  scheduled runs), `ledger.json` (the no-repeat history), `smtp.json` (mail
  settings, owner-only where the system allows), and `briefs/`.
- Your GitHub copy holds your settings file and runs the brief with your
  secrets. Keep it private: in a public repository anyone can read the settings,
  the run logs, and (through a pull request) the history cache. Secrets are
  masked in logs and are not given to runs from forks. The issue channel posts
  the brief in your copy, so in a private copy only you can see it.
- The desktop app sends your category searches to Google News and fetches the
  feeds you list. Mail goes through the provider you set up. It listens only on
  127.0.0.1, answers only requests addressed to this computer, and requires a key
  that changes every time it starts, so another web site cannot use it.
- The AI prompt and the settings file never include your email address. The
  settings hold what you tell the interview: categories, optional town, and
  optional goals and watch list. Leave out anything you would not paste into an
  AI chat.
- The settings checker warns if the reader part of your settings (role, town,
  goals and watch list) holds an email address or phone number, and
  `python -m dailybrief scan` checks files before you publish them.
- A saved mail password is used only with the server, port and account it was
  typed for. Change any of those and the app asks for the password again.
