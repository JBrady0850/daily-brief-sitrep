# Changelog

## 0.7.0 (2026-10-24)

Put your categories in order.

- Setup has a new third question, **Put them in order**. It lists the
  categories you picked with buttons to move each one up, down or to the top.
  The brief shows the categories in that order, most important first, and a
  story that fits two categories goes to the one higher on the list. The
  buttons work with touch, mouse and keyboard, keep the page where it is, keep
  the focus on the moved category and announce its new place.
- **Your choices** has an **Order** row with its own Change link.
- Setup now has nine questions. Change links find their question by name, so
  a new question never sends a link to the wrong page.

## 0.6.3 (2026-10-24)

- Choices saved before 0.2.0 no longer show "delivery.channels lists email"
  under "Worth a look" on every review. The retired email channel and email
  settings are dropped quietly when the choices load, when a backup is
  restored and when a settings file is checked, in the web page, the desktop
  app and the GitHub copy. Any other unknown channel is still an error.

## 0.6.2 (2026-10-24)

"Not checked today" only when nothing could check the desk.

- A desk whose news searches failed now counts as checked when the backup
  collection covers its category, because GitHub searched it (Google News and
  its feeds) within the last four hours. Such a desk says "No new items",
  meaning nothing new that you have not already been sent, instead of "Not
  checked today". On 2026-10-24 the Federal Workforce and Federal Pay desks
  said "Not checked today" on a second brief of the day, while the backup
  held their stories, already shown in the first brief.
- Federal Workforce Actions and Federal Pay, Leave and Benefits read more
  federal news feeds on GitHub (FedWeek, FedSmith, Federal News Network). In a
  check on 2026-10-24 they offered up to 4 more on-topic stories for workforce
  actions and up to 9 for pay and benefits from the last four days.

## 0.6.1 (2026-10-24)

A tab left open across a release no longer builds the brief with the old code.

- Before every brief, and when the page comes back into view, the page asks the
  site which version it serves. When the site's version is newer, the page
  reloads once and then builds the brief, so a phone tab opened before a
  release still gets the new sources (such as 0.6.0's local station news). It
  never reloads twice for the same version.
- The status line names the version that built the brief when it is older than
  the page ("Built by version 0.5.1; check again to use 0.6.1").

## 0.6.0 (2026-10-24)

Town news comes from GitHub alone.

- **Local news by state.** The Pages workflow now reads the news feeds of
  about 400 local TV stations every four hours (their sites do not let web
  pages read them) and publishes one file per state beside the app, with the
  newest 30 stories per station from the last four days. Every state and DC
  has at least one station. A station that does not answer keeps its recent
  stories from the file already on the site.
- The page reads only the file for your state (from the State or region
  answer) and keeps the stories that name your town or a nearby place. Your
  town is never sent anywhere. GDELT is asked only for what is still short.
- The station list, `dailybrief/local_stations.json`, comes from the station
  groups' own published lists (Gray, Nexstar with TEGNA, Scripps, Hearst) plus
  stations from other groups; `tools/stations_source.py` rebuilds it and keeps
  only stations whose feed answers with recent stories.
- A town desk whose local stations answered is "checked", even on a day the
  news search refuses; only a desk with no answering source says "Not checked
  today".
- The town categories' topic words are stricter now that they see every local
  story: Local Government no longer counts a story just for saying "county" or
  "city", and crime stories stay out of Local Government, Local Sports, Things
  to Do and Weather and Safety.
- The news search stops starting searches after 90 seconds, so a slow news
  index cannot hold a brief for minutes (a live test on 2026-10-24 waited six
  and a half minutes on it before this change).
- The desktop app and the GitHub copy read the same stations directly for town
  categories. Both stay optional: the web page needs neither.

## 0.5.1 (2026-10-24)

The backup collection survives a run that Google News turns away.

- On 2026-10-24 Google News answered every search from GitHub's servers with
  "Service Unavailable", and the backup run ran out of time after 36 of 62
  categories. Now three refused searches in a row end the searching for that
  run, and every category still reads its feeds: a test run with Google
  refusing finished in 36 seconds with stories for 59 of 62 categories.
- Stories from the file already on the site stay when they are still within
  four days and on topic, so one bad run cannot empty a category. The new
  `build-cache --previous` option names that file; the Pages workflow
  downloads it from the site first.
- The desktop app and the GitHub copy stop asking Google News after three
  refused searches in a row, too, and read the feeds for the rest of the run
  (the web page already does this with its news index).
- Town searches now ask for your town **or** the nearby places you listed (up
  to four names), instead of the town alone. The nearby places already counted
  as local; now they are searched too. A small town's news often names only its
  county: in a test for one small city on 2026-10-24, Google News found 11
  stories for the five town categories this way, against 3 for the town name
  alone.

## 0.5.0 (2026-10-24)

Town categories no longer depend on the news search alone.

- The town question adds **State or region** and fills it, with the county, when
  you pick your town for the forecast. The county joins the nearby places that
  count as local.
- **Your local news feed**: paste up to five feed links (a local TV station or
  paper). Every town category reads them, and their stories still have to name
  your town or a nearby place. A **Check** button reads each feed and says how
  many stories name your area, or that the site does not let web pages read it.
- The desktop app and the GitHub copy add your state to town searches on Google
  News. A `{region}` placeholder is available to any category.
- A desk whose searches all failed now says **Not checked today** (on the card,
  in the summary and in the plain text) instead of "No new items".
- Your choices shows your area with its state, the nearby places and your local
  feeds.

## 0.4.0 (2026-10-24)

A busy news index no longer empties a brief.

- **Backup collection.** The project's GitHub workflow now rebuilds a file of
  stories for every library category every four hours, from Google News and
  every library feed (including feeds web pages cannot read), and publishes it
  beside the app. The page reads it after the publisher feeds and before the
  GDELT news index, so GDELT is asked only for what is still short: mostly the
  categories about your town and topics you typed. Reading the file sends
  nothing about you anywhere. `python -m dailybrief build-cache` builds it.
- **On-topic feeds.** A category can list feeds about its topic and nothing
  else (a tennis feed for tennis). Their stories count as on topic without a
  must-mention word; the leave-out words and every other filter still apply.
  Both engines and both collectors support it, and the category editor has a
  box for it.
- **More feeds a web page can read.** A live check of all 67 categories with
  GDELT switched off found 16 empty; 31 categories gained feeds verified
  readable from the published page (more New York Times and Fox News sections,
  CNBC sections, ESPN fantasy and tennis, Dark Reading, the GitHub blog and ten
  Industry Dive trade sites), 16 of them as on-topic feeds.
- The building panel shows a Backup collection stage, and Sources and filters
  counts the stories it gave.

## 0.3.0 (2026-10-23)

Setting up and reading the brief are now clearly separate.

- Before setup is saved, the app shows only the setup questions, AI
  assistants, Settings and Help. Nothing is collected until **Save and build
  my brief** on the last question. A **See a sample brief** button shows what
  the result looks like.
- Saving shows **Setup complete**, then a **Building today's brief** panel that
  names each stage (your choices, publisher feeds, news search, your page)
  before the brief appears.
- After setup the app opens on **Today's brief**, with a line that says whether
  today's brief is ready, being built, or not built yet.
- The Setup tab becomes **Your choices**: the saved answers, each with a
  Change link. Changes apply only on **Save changes**; **Cancel changes**
  keeps the saved ones, and a reminder shows on other pages while changes are
  unsaved. If the choices change after today's brief was built, the page
  offers to rebuild it.
- The numbered tabs and the Next and Back bar between pages are gone.
- Ticking a category no longer jumps to the top of the page: the tile changes
  in place. Packs, typed topics and other changes on a page keep the scroll
  position, the open groups and the focused box.
- A brief pasted from an AI assistant before setup shows on the AI assistants
  tab.

## 0.2.1 (2026-10-23)

- More categories read publisher feeds that allow web pages (The New York
  Times, Fox News, Wired, CNBC, ESPN and CBS Sports), so most categories fill
  even when the GDELT news search is busy. Only the five categories about
  your own town (local news, local government, local sports, things to do,
  and weather and safety in your town) still depend on the search.
- Each feed address is read once per run and shared by every category that
  lists it.
- The test workflow stops a stalled job after 20 minutes.

## 0.2.0 (2026-10-23)

The web address is now the whole app: it collects the news itself, remembers
your choices in your own browser, and shows the brief as a full web page.

- Collects in the browser, free and with no key: the GDELT news search, the
  publisher feeds that allow web pages to read them, and an Open-Meteo forecast
  for your town. Requests to GDELT are spaced out and retried once.
- The brief is a web page, not an email: category icons, story photos from the
  publishers' own feeds and share images, a forecast panel, and header artwork.
- The category library grows from 22 to 67 categories in 11 groups, adding
  weather, sports (NFL, college football, NBA, college basketball, MLB, NHL,
  soccer, golf, motorsports, tennis, fantasy), top news, entertainment, science
  and space, and life and home, plus five new packs.
- Email sending is removed everywhere (SMTP, mail settings, the `send` command,
  the `.eml` draft). Settings from 0.1.0 that list email still load, with a
  warning. If you saved mail settings, delete `smtp.json` from your data folder.
- `run --mark-read` keeps a scheduled run on your own computer free of repeats.
- Tests no longer fail in a copy that set its own delivery time.
- The app declares its own install identity (`/daily-brief-sitrep/`), so it
  never shares one with another app installed from the same github.io site.

## 0.1.0 (2026-10-23)

First public version.

- Runs entirely on GitHub, free: `.github/workflows/daily-brief.yml` collects
  the news from Google News RSS and publisher feeds, builds the newsletter, and
  delivers it as a GitHub issue (no password) or by email through your own mail
  account, twice-daily UTC runs with a delivery-time gate for daylight saving
  time, and the no-repeat history in the Actions cache. No keys or paid services.
- Web app (GitHub Pages, home screen, or opened from disk): an eight-question
  setup interview, a category editor with a 22-category library and five starter
  packs, your own categories in plain words, newsletter preview, email draft
  (.eml), copy for email, settings file, backup and restore.
- Desktop app (`Start-Windows.bat`, `Start-Mac.command`, `start-linux.sh`):
  live news from Google News RSS and publisher feeds, the permanent no-repeat
  history, SMTP sending, a source health report, and scheduled runs with
  `python -m dailybrief run --send`.
- AI prompt for Claude, ChatGPT, Gemini and Grok: interview, run, update and
  JSON modes, Lead Analysis, SEEN HISTORY, and a compact version for
  size-limited instruction boxes.
- Newsletter theme: masthead, optional countdown with milestones, stat tiles,
  freshness bar, Lead Analysis, colour-coded category cards and freshness pills.
- Browser and Python engines tested against each other for identical results.
- Checked on live feeds and by an adversarial review before release: em dashes
  in feed headlines, a stricter career desk, a refused government feed removed,
  "Mark as read" no longer cancels the scheduled email, safer backup restore
  and mail settings, a once-a-day guard on "Email it now", unreadable dates left
  out, a faster no-repeat check, neutral examples, and prompt fixes for JSON
  mode, dates and settings order. See docs/ROADMAP.md, section 2.
