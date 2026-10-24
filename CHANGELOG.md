# Changelog

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
