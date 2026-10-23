# AI assistants

The prompt in [prompt/](../prompt/) makes any assistant with web search run the
setup interview and write the brief. It refuses to write a brief without a web
search tool, so it cannot invent news from memory.

| File | Use |
|---|---|
| `daily-brief-prompt.md` | The full prompt, for project instructions or a first message |
| `daily-brief-prompt-compact.md` | Under 5,100 characters, for instruction boxes with a limit |
| `category-library.md` | Upload next to the prompt so the assistant can offer the library |
| `daily-brief-settings.json` | Your settings, from step 5 or Settings in the app |

Commands: START, RUN, UPDATE, JSON, SHOW SETTINGS, HELP.

## What was checked (2026-10-23)

| Assistant | Fact | Source |
|---|---|---|
| Claude | Web search is available on all plans | Anthropic announcement, May 2025 update |
| Claude | Projects are on all plans, free accounts up to five; the same help page lists project instructions under paid plans | support.claude.com article 10185728 |
| Claude | Scheduled tasks are on paid plans | support.claude.com article 13854387 |
| ChatGPT | Scheduled tasks live on the Scheduled page | help.openai.com article 10291617 |
| ChatGPT | GPT instructions are limited to 8,000 characters | OpenAI community forum (not an official help page) |
| ChatGPT | Scheduled tasks do not run inside GPTs | Third-party guide only: UNVERIFIED |
| Gemini | Gems hold custom instructions | support.google.com/gemini answer 15236405 |
| Gemini | Scheduled actions: up to 10 active, run within an hour of the set time, Google AI Pro, Ultra and some Workspace plans | Press reports of Google's launch notes |
| Gemini | Whether a scheduled action can use a Gem | UNVERIFIED |
| Grok | Projects with instructions and sources; Automations (formerly Tasks) for scheduled runs | Third-party guides only: UNVERIFIED |

Menus change. If a step does not match what you see, the assistant's own help
page is the authority.

## Size-limited instruction boxes

Use the compact prompt and upload the settings file as a knowledge file; the app's
"Copy the compact prompt" button points the assistant at that file. A scheduled
task usually cannot take files, so for a scheduled task use the compact prompt
with your settings built in (`python -m dailybrief prompt --compact --config your-settings.json`).
