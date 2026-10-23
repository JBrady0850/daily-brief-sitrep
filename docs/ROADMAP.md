# Process review and roadmap

This page reviews how the Daily Brief works, what earlier versions of the same
pipeline got wrong, and the improvements and expansions that would make the
public project better. Items are ranked by value to a reader, then by effort.

## 1. How a brief is made

| Stage | What happens | Where |
|---|---|---|
| Collect | At the web address: a GDELT news search for each category, the publisher feeds that allow web pages, and an Open-Meteo forecast. On a computer or GitHub: Google News RSS searches, every listed feed and the same forecast | `app/js/collect.js` in the browser; `dailybrief/collect.py` in the desktop app and the GitHub copy; or an AI assistant's web search |
| Filter | Keep a story only if it mentions a term from every "must mention" group and no "leave out" term; drop social media, paperwork notices and, if asked, list articles | `selectBrief` / `select_brief` |
| Date | NEWS inside the freshness window; OLDER (labelled, true age) only when a category is short; undated REFERENCE pages only when allowed and still short | `classify` |
| No repeats | Leave out anything already sent (link, headline, or the same story from another outlet) and anything already used in another category | `ledgerHas`, `nearDup` |
| Rank and fill | Freshest and most on-topic first, up to the category quota; never pad | `score` |
| Analyze | Lead Analysis (top three, connection, watch list, action), AI path only | The prompt, section 4 |
| Check | Counts, links, ages, labels, duplicates, em dashes | `checkBrief` / `check_brief` |
| Render | A self-contained web page (category icons, story photos, forecast panel, header artwork), plain text and a title line | `app/js/newsletter.js`, `dailybrief/render.py`, `app/data/icons.js` |
| Show | The page inside the app, full screen in a new tab, as a download, or copied | The app |
| Routine | Choices saved in the browser; an optional once-a-day collection when the page opens; an optional GitHub copy that posts an issue | `app/js/app.js`, `.github/workflows/daily-brief.yml`, `dailybrief/github_issue.py` |
| Schedule (GitHub copy) | Two UTC runs an hour apart; the first at or after the delivery time in your time zone posts | `.github/workflows/daily-brief.yml`, `dailybrief/schedule.py` |
| Record | The no-repeat history updates after the web page shows a brief, after a posted issue, or on "Mark as read" | `ledgerAdd` |

## 2. Lessons carried into v0.1.0

The Daily Brief began as a private daily script. Its history recorded these
failures; each one shaped a rule in this version.

| What went wrong | Why | What v0.1.0 does |
|---|---|---|
| The same stories came back three days running | Nothing remembered what had been sent, and the window had been widened to a week | A permanent no-repeat history (link, headline and near-duplicate headline), a 24-hour default window, and a rule never to widen the window to fill a category |
| Week-old stories filled thin categories | The window was widened to cure empty categories | Older stories appear only when a category is short, labelled OLDER with their true age, up to a separate limit |
| The order never changed day to day | Every fresh story scored the same | Score falls continuously with age |
| Off-topic stories ("AI" matched "said", "RIF" matched "tariff") | Plain substring matching | Whole-word matching; short all-capital terms match only in capitals; every "must mention" group must match |
| Paperwork notices passed every filter | They are full of the right keywords | A paperwork filter on headlines |
| Social media posts and video pages crept in | Search returns them | An avoided-sites list, editable in the settings |
| Undated pages vanished without trace | Items with no date were silently dropped | A REFERENCE label for undated authoritative pages, and a "left out" count per reason |
| One launch sent the email twice | No guard against two runs | A run lock and a once-per-day send guard |
| Test runs used up tomorrow's stories | Dry runs wrote to the history | Only a confirmed send or "Mark as read" writes to the history |
| Summaries repeated the headline | Google News descriptions are the headline plus the outlet | Such summaries are dropped; the story shows its headline only |
| Models ignored "no em dashes" | Style rules in prompts are followed unevenly | The checker rejects em dashes in a brief before it is shown or sent |
| A dead feed went unnoticed for weeks | Failures were not reported | A per-source health report with every run |
| Stated counts drifted from reality | Documents and generated files were edited by hand | Generated files are rebuilt and checked in CI; the browser and desktop engines are tested against each other |

Before release, a live run on real feeds and an adversarial review found more,
and each is now fixed and covered by a test:

| What went wrong | Why | What v0.1.0 does |
|---|---|---|
| A real headline with an em dash failed the brief check | Feeds use em dashes; nothing removed them | Em dashes in feed text become hyphens; the run refuses to send a brief that fails its check |
| Election stories filled the career desk | "Certification" also means certifying an election | Career stories must also mention work or technology, and election terms are left out |
| A government feed answered every scripted request with HTTP 403 | The site blocks automated readers | The feed left the library; the health report names any feed that refuses |
| "Mark as read" cancelled that day's scheduled email | Marking recorded the day as sent | Marking remembers the stories only; a real send records the day |
| A crafted backup could run script in the app, and a changed mail server could receive the saved password | Restored settings were not checked; two numbers reached the page unescaped; the password outlived its server | Restores are checked like imports, every value is escaped, the copy fallback never puts HTML in the page, and a new server needs the password again |
| Stories with an unreadable date became undated reference pages | Only a missing date and a readable one were told apart | An unreadable date leaves the story out; more date formats are read |
| A full history made each run slow | Every story re-read 3,000 old headlines | The history is indexed once per run |

## 3. Improvement and expansion items

Effort: S (a day), M (a few days), L (a week or more). Status: Planned, Idea, or
Needs a decision.

| ID | Item | Why it matters | Effort | Status |
|---|---|---|---|---|
| R22 | Collect at the web address | The page gathers the news itself from free sources that allow browsers (GDELT, open feeds, Open-Meteo), so the address alone is the app | M | Done in 0.2.0 |
| R23 | The brief as a web page | Icons, publisher photos, a forecast panel and header artwork instead of an email layout | M | Done in 0.2.0 |
| R24 | A bigger library | 67 categories in 11 groups, including weather, sports, entertainment and life at home | M | Done in 0.2.0 |
| R25 | A second browser-readable news index | A fallback when GDELT is busy (candidates: the Hacker News search for technology, Wikipedia's current events) | M | Idea |
| R1 | Cloud schedule with GitHub Actions in your own private copy | A brief with no computer left on | M | Done in 0.1.0 |
| R19 | Save settings to your GitHub copy from the app | Skip the download and upload step with a fine-grained token kept in the browser | M | Idea |
| R20 | Run now button in the app | Start the workflow from the app (workflow dispatch) | S | Idea |
| R21 | First-run report from the cloud | After the first GitHub run, confirm Google News and the issue notification work from GitHub's servers (Google News and the issue passed on 2026-10-23; the notification email remains) | S | Planned |
| R2 | Bring your own AI key in the app (Anthropic, OpenAI, Google, xAI) | Lead Analysis on desktop briefs, and live news in the web version through the provider's web search | M | Planned |
| R3 | One-click scheduling in the desktop app | Removes the Task Scheduler or crontab step | S | Planned |
| R4 | Source health over time | Catch a dead feed the day it dies, from the history of runs | S | Planned |
| R5 | Outlet count as an importance signal | A story many outlets cover ranks higher, instead of being thrown away as a duplicate | S | Planned |
| R6 | Feed relay template for the web version | A small worker you deploy yourself lets the web page read Google News and every feed | M | Needs a decision |
| R8 | Dark mode for the brief page | Readable at night | S | Idea |
| R9 | Article summaries for desktop briefs | Read the article page for one or two sentences when the feed has none | M | Idea |
| R10 | Several readers, several briefs | One copy serves a family or a team, each with their own categories and recipients | M | Idea |
| R11 | Weekly digest mode | Seven-day window, top stories only, for slow-moving categories | S | Idea |
| R12 | Category pack contributions | An issue form and CI checks so readers can share packs | S | Idea |
| R13 | Prompt regression runs | Each month, run the prompt in each assistant and score the JSON with `python -m dailybrief check` | M | Idea |
| R14 | Region and language presets | Google News editions outside the US in the interview | S | Idea |
| R15 | Your briefs as an RSS feed or archive page | Read past briefs in a feed reader | M | Idea |
| R16 | Chat delivery (Slack, Teams, Discord webhooks) | A second delivery path beside the issue | S | Idea |
| R17 | Thumbs up or down on a story | Tune categories from what you actually read | L | Idea |
| R18 | Audio brief | Listen on the drive | L | Idea |

### R1. Cloud schedule with GitHub Actions (done in 0.1.0)

`.github/workflows/daily-brief.yml` runs twice a day in your private copy, and
`dailybrief/schedule.py` sends on the first run at or after your delivery time,
which handles daylight saving time without a time zone in cron. The history
lives in the Actions cache, and delivery is a GitHub issue (no password).
Email delivery was removed in 0.2.0. See [GITHUB-CLOUD.md](GITHUB-CLOUD.md). The
first real run (2026-10-23) collected 25 stories from Google News on GitHub's
servers and opened the brief issue. Still UNVERIFIED: the notification email
for the issue (R21).

### R2. Bring your own AI key

An optional key, kept in the browser, adds the Lead Analysis to desktop briefs
and lets the web version ask the provider's web search for the stories. The
layer must fail safe: if the key is missing, wrong or out of credit, the brief
goes out without the analysis. Acceptance: the same checker passes on the AI
output; a revoked key leaves the brief identical to a run without a key.

### R3. One-click scheduling

A button in the desktop app that shows the exact scheduled task it will create
(time, command, folder), asks for confirmation, and creates it. Acceptance: the
task appears in Task Scheduler or crontab and runs the next morning.

### R4. Source health over time

Keep a small per-source record (last success, last failure, items) across runs
and flag a source that fails twice in a row. Acceptance: a feed that returns 404
on two runs appears in the health report as a repeating failure with its first
failure date.

### R5. Outlet count

Count how many outlets carried a story before duplicates are collapsed, and add
a small bonus to its score. Acceptance: of two equally fresh stories, the one
three outlets carried ranks first.

### R6. Feed relay

A short worker script, deployed by the reader to their own free account, that
fetches only Google News RSS and the reader's feeds and adds the header browsers
need. The hosted app would use it when a relay address is set in Settings. This
needs a decision because it puts a server, however small, in the path.

## 4. Release checklist

1. `python -m pytest -q` (all tests, including the browser tests).
2. `python -m dailybrief build-assets --check`.
3. `python -m dailybrief scan . --terms <your private word list>`, kept outside
   the repository.
4. Bump `VERSION` in `app/js/engine.js`, `dailybrief/engine.py` and `app/sw.js`,
   and add a CHANGELOG entry.
5. In a fork or a new home for the project, change the app link at the top of
   the README, turn on **Settings, Template repository** so readers can use
   **Use this template**, and turn on Pages (Source: GitHub Actions).
