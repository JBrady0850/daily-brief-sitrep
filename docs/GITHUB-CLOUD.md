# Run it on GitHub (free, no computer needed)

Your own copy of this project can collect the news, build the newsletter and
deliver it every morning on GitHub's servers. It uses free services only:

| Part | Service | Key or password? |
|---|---|---|
| News | Google News RSS searches and publisher RSS feeds | None |
| Running it | GitHub Actions, on a schedule | None (GitHub gives every run its own token) |
| No-repeat history | The GitHub Actions cache in your copy | None |
| Delivery, option 1 | A GitHub issue in your copy; GitHub emails it to you | None |
| Delivery, option 2 | Email through your own mail account | That account's app password, stored as a secret |

No AI service, search API or paid service is involved.

## Set it up (about ten minutes)

1. **Make your settings.** Open the app, answer the setup questions, and on
   question 7 pick the delivery time, your time zone and how it arrives
   (email, GitHub issue, or both).
2. **Make your own private copy.** On the project's GitHub page choose
   **Use this template**, **Create a new repository**, choose **Private**, and
   create it. Keep it private: in a public repository anyone can read your
   settings and the run logs, and anyone who can read it can reach the history
   cache through a pull request.
3. **Add your settings.** In the app, step 4 (Email), choose **Download the
   settings file**. In your copy choose **Add file**, **Upload files**, drop in
   `daily-brief-settings.json`, and commit. Upload it again whenever you change
   something in the app.
4. **Email only: add the mail secrets.** In your copy open **Settings**,
   **Secrets and variables**, **Actions**, **New repository secret**, and add:

   | Secret | Value |
   |---|---|
   | `SMTP_HOST` | Your provider's SMTP server, `smtp.gmail.com` for Gmail |
   | `SMTP_USER` | Your mail address |
   | `SMTP_PASSWORD` | An app password for that account ([docs/EMAIL.md](EMAIL.md)) |
   | `MAIL_TO` | Who gets the brief, commas between addresses |
   | `SMTP_PORT`, `SMTP_SECURITY`, `MAIL_FROM` | Optional: 587 and STARTTLS are the defaults |

   Secrets are never shown again, never printed in the logs, and are not given
   to runs started from forks.
5. **GitHub issue only:** nothing to add. Check that **Settings**,
   **Notifications** on github.com has email turned on for issues you
   participate in; the brief mentions you, which counts as participating.
6. **Set the time.** GitHub schedules in UTC and cannot follow a time zone, so
   the workflow runs twice, an hour apart, and sends on the first run at or
   after your delivery time. Step 4 of the app shows the two `cron:` lines for
   your time and zone. In your copy open
   `.github/workflows/daily-brief.yml`, choose **Edit**, replace the two lines
   under `schedule:`, and commit.
7. **Test it.** Open **Actions**, choose **Daily brief**, then **Run workflow**.
   The run summary lists the subject, the story counts, any source problems,
   and how the brief was delivered.

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
  UNVERIFIED: sending mail from GitHub's servers through your provider, and the
  email GitHub sends for a brief issue.
- Checked 2026-10-23 from a home connection with the same code: Google News
  answered every search, a Federal IT pack run kept 44 stories and a Technology
  pack run kept 35, and 11 of 12 publisher feeds answered. CISA's advisory feed
  refused scripted requests (HTTP 403) and was removed from the library; its
  advisories still arrive through the Google News searches.

## Optional

- **Keep the brief files.** Add an Actions variable `BRIEF_KEEP_FILES` set to
  `true` to save each brief (HTML, text, email file, JSON) as a run artifact for
  7 days. Leave it off in a public copy.
