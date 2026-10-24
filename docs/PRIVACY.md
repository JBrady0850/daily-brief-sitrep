# Privacy

- No account, no analytics, no server of ours.
- The web page keeps your settings, the no-repeat history and the last brief in
  this browser's local storage. **Settings, Erase everything** removes them.
- When it collects a brief, the web page reads the publisher feeds your
  categories list and the backup collection, a file on this site's own address
  that holds no information about you (reading it sends nothing). Only for
  categories still short does it send their searches to the GDELT news index
  (api.gdeltproject.org). When the forecast is on, it sends your town's map position,
  rounded to about a kilometre, to Open-Meteo, and the town search sends the
  name you type. Requests carry no cookies and no referrer.
- Local news feed links you add on the town question stay in this browser; the
  page reads those feeds directly, like any other feed.
- Story photos load from the publishers' own sites when you view the brief,
  without a referrer. Downloaded pages load them the same way when opened.
- The desktop app keeps its copy in a `.daily-brief` folder in your home folder
  (or the folder named by `DAILY_BRIEF_HOME`): `config.json` (settings for
  scheduled runs), `ledger.json` (the no-repeat history) and `briefs/`. If an
  older version left `smtp.json` there, it holds a mail password and nothing
  reads it any more: delete it. The app reminds you when it starts.
- The desktop app sends your category searches to Google News and fetches the
  feeds you list. It listens only on 127.0.0.1, answers only requests addressed
  to this computer, and requires a key that changes every time it starts, so
  another web site cannot use it.
- An optional GitHub copy holds your settings file and runs with GitHub's own
  token; no secret is stored. Keep it private: in a public repository anyone
  can read the settings, the run logs, and (through a pull request) the history
  cache. The brief is posted as an issue in your copy, so in a private copy
  only you can see it.
- The settings hold what you tell the interview: categories, optional town and
  forecast place, and optional goals and watch list. Leave out anything you
  would not paste into an AI chat. The AI prompt and the settings file never
  include an email address, even from settings made by version 0.1.0.
- The settings checker warns if the reader part of your settings (role, town,
  goals and watch list) holds an email address or phone number, and
  `python -m dailybrief scan` checks files before you publish them.
