# Limits (v0.1.0)

- The web version cannot fetch news: Google News and most publisher feeds do
  not allow web pages to read them. Use the desktop app or an AI assistant.
- Desktop briefs have no Lead Analysis, because that needs an AI. Google News
  gives no summary, so those stories show their headline only; publisher feeds
  usually include one or two sentences.
- Google News links open through a Google redirect page.
- The desktop app's schedule runs only while the computer is on. The GitHub
  copy needs no computer, but GitHub may delay or drop scheduled runs at busy
  times, and its history cache is removed after 7 days without a run.
- Checked 2026-10-23 from a home connection: Google News answered every search
  and 11 of 12 publisher feeds answered. UNVERIFIED until the first GitHub run:
  whether Google News answers GitHub's servers the same way, sending mail from
  GitHub's servers, and the notification email GitHub sends for the brief issue.
- Some sites refuse scripted requests (CISA's feed returned HTTP 403). The
  source health report lists any such feed by name.
- On a Mac, Python from python.org cannot check web certificates until you run
  Install Certificates.command in its Applications folder; the app says so.
- AI assistants can still make mistakes. The prompt demands links from a live
  search and the app checks ages, labels, links and duplicates, but read the
  source before you act on a story.
- UNVERIFIED: how the newsletter looks in every mail program (tested in
  Chromium only), and installation on real iPad and Android devices.
- The no-repeat history keeps the newest 20,000 links and headlines, and
  compares near-duplicate headlines against the newest 3,000.
