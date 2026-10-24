# Limits (v0.4.0)

- The web page reads only the sources that allow web pages to read them: the
  GDELT news index, and publisher feeds such as ESPN, CBS Sports, NASA, The New
  York Times, Fox News, CNBC and Wired. Google News and most other feeds do not
  allow it; the desktop app and the GitHub copy read those instead. A feed that
  refuses shows as "not readable from a web page" under Sources and filters.
- The page reads, in order: the publisher feeds, then the backup collection,
  then the GDELT news index, and only for what is still short. The backup
  collection is a file this project's GitHub workflow rebuilds every four hours
  (at 23 minutes past the hour, in UTC) from Google News and every library
  feed, including feeds web pages cannot read. It covers the 62 library
  categories that do not depend on your town. It is up to four hours old, and
  in a public repository GitHub stops scheduled workflows after 60 days with no
  new commits; the page then falls back to the news index.
- The GDELT index turns requests away when it is busy or when one connection
  asks too often (HTTP 503 and 429, seen on 2026-10-23; after a day of heavy
  testing it refused one home connection for hours). The town categories and
  categories you type yourself depend on it.
  It asks one search at a time, waits six seconds between searches (twelve
  after a refusal), retries a refused search once, and after three refused
  searches in a row uses the feeds alone for the rest of the run. A live run
  of seven categories on 2026-10-23 took about three minutes and kept 28
  stories, 17 with photos; one category came back empty.
- GDELT and Google News give a headline only, so those stories show no summary.
  GDELT usually gives the story's share photo; feeds add a summary and often a
  photo. Photos load from the publishers' sites, and one that fails to load
  leaves an empty frame.
- Briefs collected without an AI have no Lead Analysis.
- Google News links open through a Google redirect page.
- Choices and the no-repeat history live in one browser. Clearing site data, a
  private window, or another device starts fresh; move with the settings file.
- The once-a-day collection runs only when you open the page. For a brief with
  no browser open, set up the optional GitHub copy; GitHub may delay or drop
  scheduled runs at busy times, and its history cache is removed after 7 days
  without a run.
- The forecast covers four days from Open-Meteo, for non-commercial use under
  its terms (fewer than 10,000 calls a day; this page makes one per brief).
- Checked 2026-10-23 from a browser on the published page: GDELT, Open-Meteo,
  and feeds from ESPN, CBS Sports, NASA, The New York Times, Fox News, CNBC,
  MarketWatch, Wired and K-12 Dive answered; Google News, BBC, NPR, Reuters-style
  wire feeds and most WordPress sites refused. Google News answered every search
  from a home connection and from GitHub's servers.
- On a Mac, Python from python.org cannot check web certificates until you run
  Install Certificates.command in its Applications folder; the app says so.
- AI assistants can still make mistakes. The prompt demands links from a live
  search and the app checks ages, labels, links and duplicates, but read the
  source before you act on a story.
- UNVERIFIED: installation on real iPad and Android devices, and the
  notification email GitHub sends for a brief issue.
- The no-repeat history keeps the newest 20,000 links and headlines, and
  compares near-duplicate headlines against the newest 3,000.
