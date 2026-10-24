# Daily Brief

Your morning news on one page, free. Open the web address, answer a short
setup interview (what you follow, which categories, your town, how fresh, how
many stories), and the page collects that day's news itself: fresh, on-topic
stories in every category you chose, with publisher photos, a forecast for your
town, and nothing you have already seen.

Your choices stay in your own browser, so each person who opens the address
gets their own brief. Come back any day and press **Get today's brief**, or let
the page collect by itself the first time you open it each day. There is no
account, no sign-up and no key. Every source is free: the GDELT news index and
publisher feeds for the news, and Open-Meteo for the forecast.

![A brief, shown as a page](docs/images/07-brief-page.png)

## 1. Open the app

### [jbrady0850.github.io/daily-brief-sitrep](https://jbrady0850.github.io/daily-brief-sitrep/)

Open the link on a computer, tablet or phone. Answer the eight questions, press
**Save and get my brief**, and the brief appears as a page a minute later. On a
phone, **Share**, **Add to Home Screen** keeps it one tap away; in Chrome or
Edge on a computer, the install button in the address bar does the same.

![Setup interview](docs/images/01-setup.png)

## 2. Pick from 67 categories, or type your own

The library has 11 groups: top news, weather, sports, technology, money and
business, science and health, entertainment and culture, life and home, your
area, government and defense, and career and education. Ten packs start you
off (for example **Headlines and weather** or **Sports fan**), and **Type what
you want to follow** turns any topic in your own words into a category.

| Group | Categories |
|---|---|
| Top news | U.S. headlines, world news, politics and policy, business headlines, good news |
| Weather | Severe weather across the country, forecasts and seasonal outlook, climate and environment, weather and safety in your town |
| Sports | Sports headlines, NFL, college football, NBA, college basketball, MLB, NHL, soccer, golf, motorsports, tennis, fantasy sports |
| Technology | Technology headlines, gadgets and reviews, cybersecurity, networks, cloud, enterprise AI, AI tools, open source |
| Money and business | Personal finance, retirement planning, markets and the economy, housing, small business, crypto, energy and gas prices |
| Science and health | Space, science and discovery, health and wellness, health and science |
| Entertainment and culture | Movies, television and streaming, music, books, video games, arts and culture |
| Life and home | Travel, food and dining, cars and electric vehicles, home and garden, pets, parenting and family, outdoors, faith, inspiring stories |
| Your area | Local community, local government, local sports, things to do |
| Government and defense | Military and veterans, defense AI, the federal workforce, pay, retirement and government technology |
| Career and education | Career growth and skills, schools and education |

![Category tiles](docs/images/03-category-tiles.png)

## Set up once, then read it every day

The app has two modes, so you always know where you are.

| Mode | What you see |
|---|---|
| Setting up | Eight questions, each with a sensible default, including your town for the forecast. Nothing is collected until you press **Save and build my brief** on the last question. |
| Your brief | Once saved, the app says **Setup complete**, builds today's brief while it shows each stage, and from then on opens on **Today's brief**. |

After setup the tabs are:

| Tab | What you do there |
|---|---|
| Today's brief | See whether today's brief is ready, build it, open it full screen, download it or copy it |
| Your choices | Your saved answers, with a Change link for each one. Changes take effect only when you press **Save changes**; **Cancel changes** keeps the old ones. **Fine-tune categories** edits searches and filters. |
| Every day | Keep the page handy, turn on the once-a-day automatic build, or set up a GitHub copy |
| AI assistants | Copy the prompt for Claude, ChatGPT, Gemini or Grok, and paste the assistant's brief |

![Your saved choices](docs/images/06-your-choices.png)

## How stories are picked

1. Each category runs its searches. A story stays only if it mentions at least
   one term from every "must mention" line and none of the "leave out" terms.
   Social media posts and paperwork notices are dropped.
2. **NEWS** is published inside your window (24 hours by default). When a
   category is short, **OLDER** stories fill in, stamped with their true age.
   Undated official pages appear last, labelled **REFERENCE**.
3. Nothing you have already seen comes back: not the same link, not the same
   headline, and not the same story from a second outlet. A story appears in
   one category only.
4. A category is never padded. If nothing new turned up, it says so.

[docs/CATEGORIES.md](docs/CATEGORIES.md) explains how to write a category.
[docs/ROADMAP.md](docs/ROADMAP.md) reviews the whole process, the lessons behind
every rule, and the ranked list of improvements.

## Other ways to use it

| Way | What it gives you |
|---|---|
| An AI assistant (Claude, ChatGPT, Gemini, Grok) | The same interview, a brief written from a live web search, and a Lead Analysis. Paste its reply on the Today tab. See [docs/AI-ASSISTANTS.md](docs/AI-ASSISTANTS.md). |
| A GitHub copy (optional) | GitHub's servers collect the brief from Google News each morning and post it as an issue in your private copy, with no browser open. See [docs/GITHUB-CLOUD.md](docs/GITHUB-CLOUD.md). |
| The desktop app | The same app on your own computer, reading Google News and every publisher feed: install Python 3.9 or newer from python.org, download this project (**Code**, **Download ZIP**), and double-click `Start-Windows.bat`, `Start-Mac.command` or `start-linux.sh`. On a Mac, the first time, right-click `Start-Mac.command` and choose **Open**, and run **Install Certificates.command** from the Python folder in Applications. |

Email sending was removed in version 0.2.0. The brief is a web page you open,
download or copy; see [CHANGELOG.md](CHANGELOG.md).

## Where the news comes from

| Order | Source | When |
|---|---|---|
| 1 | Publisher feeds that allow web pages (The New York Times, Fox News, CNBC, ESPN, CBS Sports, Wired, NASA, Dark Reading, Industry Dive trade sites and others) | Every brief |
| 2 | The backup collection: a file this project's GitHub workflow rebuilds every four hours from Google News and every library feed, published beside the app; recent stories from the last run stay, so a bad run cannot empty a category | When a category is still short |
| 3 | The GDELT news index | Only for what is still short, mostly categories about your town and topics you typed |

**Your town.** The town question keeps your town, its state and the nearby
towns or county that count as local; picking your town for the forecast fills in
the state and county. Town searches ask for your town or any of those nearby
places, because a small town's news often names only its county. Town news is the hardest to find from a web page, so the
question also takes your local TV station's or paper's news feed, with a
**Check** button that says whether this page can read it. If the news search
does not answer on a given day, a town category says "Not checked today"
instead of "No new items".

A category may also name **on-topic feeds**, such as a tennis feed for the
tennis category; their stories count as on topic without a must-mention word.
See [docs/CATEGORIES.md](docs/CATEGORIES.md).

## Privacy

No account of ours and no tracking. Settings and the no-repeat history stay in
your browser. The page reads the publisher feeds your categories list and the
backup collection on its own site, sends the searches of categories still short
to the GDELT news index, and, when the forecast is on,
sends your town's rounded map position to Open-Meteo. Story photos load from
the publishers' own sites. See [docs/PRIVACY.md](docs/PRIVACY.md) and
[docs/LIMITS.md](docs/LIMITS.md).

## For developers

```
python -m dailybrief --help        # every command
python -m dailybrief run --config daily-brief-settings.json --out output   # one run, nothing posted
python -m dailybrief sample        # render the sample brief page to output/
python tools/icons_source.py       # rebuild app/data/icons.js
python -m pytest -q                # the tests
```

Standard library only. The browser engine (`app/js/engine.js`,
`app/js/newsletter.js`) and the Python engine (`dailybrief/`) are twins, and the
parity tests require identical results. The browser collector
(`app/js/collect.js`) and the Python collector (`dailybrief/collect.py`) share
the forecast code and the brief format. See [CONTRIBUTING.md](CONTRIBUTING.md).

| Folder | What is in it |
|---|---|
| `app/` | The app: plain HTML, CSS and JavaScript, no build step, with the icon set and sample artwork |
| `dailybrief/` | Python collector, page renderer, issue delivery, schedule gate, desktop app, command line |
| `.github/workflows/` | The optional daily run, the tests, and the Pages publish |
| `prompt/` | The AI prompt (full and compact) and the category library |
| `examples/` | An invented sample brief and its settings |
| `tools/` | The source of the icon set |
| `docs/` | Guides, the roadmap and screenshots |
| `tests/` | Engine, parity, collector, cloud, server, command line and browser tests |

## Licence

MIT. See [LICENSE](LICENSE). The icons and artwork were drawn for this project
and are under the same licence.
