# Email

## From your GitHub copy

Add the mail settings as repository secrets in your private copy (**Settings**,
**Secrets and variables**, **Actions**): `SMTP_HOST`, `SMTP_USER`,
`SMTP_PASSWORD`, `MAIL_TO`, and optionally `SMTP_PORT`, `SMTP_SECURITY`,
`MAIL_FROM`. The values below for Gmail apply. If you would rather not store a
mail password anywhere, choose the GitHub issue channel instead: GitHub posts
the brief in your copy and emails it to you. See [GITHUB-CLOUD.md](GITHUB-CLOUD.md).

## From the desktop app

On step 4 (Email), fill in **Mail settings** and press **Save mail settings**,
then **Send a test (the sample)**. The settings, including the password, are
saved in `smtp.json` in your data folder (`.daily-brief` in your home folder)
and never shown again. On a Mac or Linux the file is readable only by your
account from the moment it is created; on Windows it sits in your own user
folder. Change the server, port, security or account and the app asks for the
password again, so a saved password never goes to a server it was not typed for.

### Gmail or Google Workspace

| Setting | Value |
|---|---|
| SMTP server | smtp.gmail.com |
| Port and security | 587 with STARTTLS (or 465 with SSL) |
| Account name | your full Gmail address |
| App password | a 16-character app password, not your normal password |

To make an app password, turn on 2-Step Verification in your Google Account,
then open Security, App passwords, and create one. Google does not offer app
passwords on some work or school accounts, on accounts with Advanced Protection,
or when 2-Step Verification uses only security keys. Google's help page:
<https://support.google.com/accounts/answer/185833>. Checked 2026-10-23.

### Any other provider

Use the SMTP server, port and app password your provider documents.

### Environment variables

The command line and scheduled runs also read these, and they win over the
saved settings: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
`SMTP_SECURITY` (`starttls`, `ssl` or `none`), `MAIL_FROM`, `MAIL_TO` (commas).

## Without the desktop app

- **Download email draft** saves an `.eml` file. Outlook opens it as a draft
  ready to send. Other mail programs open it as a message you can forward.
- **Copy for email** copies the formatted newsletter. Paste it into a new
  message in Gmail, Outlook or Apple Mail.

## A brief written by an AI assistant

Ask the assistant for JSON, save the reply's JSON as `brief.json`, then:

```
python -m dailybrief check brief.json
python -m dailybrief send brief.json            # or --dry-run to write the files only
```

The same day is not sent twice unless you add `--force`, and every sent story
joins the no-repeat history.
