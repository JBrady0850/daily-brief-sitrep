# Optional: run it on GitHub each morning

The web address does everything on its own: it remembers your choices and
collects the news in your browser when you open it. This guide is for people
who also want a brief waiting each morning with no browser open. Your own copy
of this project collects the news on GitHub's servers and posts it as an issue
in your copy. It uses free services only:

| Part | Service | Key or password? |
|---|---|---|
| News | Google News RSS searches and publisher RSS feeds | None |
| Forecast | Open-Meteo, when your settings turn the forecast on | None |
| Running it | GitHub Actions, on a schedule | None (GitHub gives every run its own token) |
| No-repeat history | The GitHub Actions cache in your copy | None |
| Delivery | A GitHub issue in your copy; GitHub notifies you by email or in its app, following your notification settings | None |

No AI service, search API or paid service is involved, and no secret is stored.
Email sending was removed in version 0.2.0.

## Set it up (about ten minutes)

1. **Make your settings.** Open the app, answer the setup questions, and on
   question 7 open **Only if you also run a GitHub copy** to pick the delivery
   time and your time zone.
2. **Make your own private copy.** On the project's GitHub page choose
   **Use this template**, **Create a new repository**, choose **Private**, and
   create it. Keep it private: in a public repository anyone can read your
   settings and the run logs, and anyone who can read it can reach the history
   cache through a pull request.
3. **Add your settings.** In the app, **Settings**, choose **Download settings
   file**. In your copy choose **Add file**, **Upload files**, drop in
   `daily-brief-settings.json`, and commit. Upload it again whenever you change
   something in the app.
4. **Check your notifications.** Nothing to add to the copy. On github.com,
   **Settings**, **Notifications**, make sure you are notified about issues you
   participate in; the brief mentions you, which counts as participating.
5. **Set the time.** GitHub schedules in UTC and cannot follow a time zone, so
   the workflow runs twice, an hour apart, and sends on the first run at or
   after your delivery time. Step 4 of the app (Every day) shows the two `cron:` lines for
   your time and zone. In your copy open
   `.github/workflows/daily-brief.yml`, choose **Edit**, replace the two lines
   under `schedule:`, and commit.
6. **Test it.** Open **Actions**, choose **Daily brief**, then **Run workflow**.
   The run summary lists the subject, the story counts, any source problems,
   and the issue it opened.

## How a morning run decides

| Situation | What happens |
|---|---|
| Before your delivery time | Skips; the next run sends |
| At or after your delivery time | Sends |
| Already sent today | Skips |
| The last scheduled run of the day, still before your time | Sends early and warns, because no later run is coming (your cron lines do not match your time zone) |
| More than three hours late | Sends, with a warning (GitHub delayed the run) |
| You press **Run workflow** | Sends now, even if today's brief already went out |

The history (what you have already been sent) is saved to the Actions cache
after every run. GitHub removes a cache that nobody has used for 7 days, so a
copy that stops running for a week starts its history again.

## Costs and limits

- GitHub Actions is free for public repositories. A private repository uses the
  included minutes of your GitHub plan; each run takes about a minute, and two
  runs a day use about three minutes.
- GitHub may delay scheduled runs at busy times, mostly at the top of the hour,
  and may drop some. The default lines run at quarter past, and suit 06:15 in
  US Eastern time; the app gives the lines for your own time.
- In a public repository GitHub turns scheduled workflows off after 60 days with
  no activity. Turn it back on from **Actions**, **Daily brief**,
  **Enable workflow**.
- Checked 2026-10-23 against GitHub's documentation (events that trigger
  workflows, disabling and enabling workflows, dependency caching, and Actions
  billing). The first real run on GitHub's servers, the same day, collected 25
  stories from Google News and opened the brief issue in 26 seconds. Still
  UNVERIFIED: the notification email GitHub sends for a brief issue.
- Checked 2026-10-23 from a home connection with the same code: Google News
  answered every search, a Federal IT pack run kept 44 stories and a Technology
  pack run kept 35, and 11 of 12 publisher feeds answered. CISA's advisory feed
  refused scripted requests (HTTP 403) and was removed from the library; its
  advisories still arrive through the Google News searches.

## Optional

- **Keep the brief files.** Add an Actions variable `BRIEF_KEEP_FILES` set to
  `true` to save each brief (the page, text and JSON) as a run artifact for
  7 days. Leave it off in a public copy.
