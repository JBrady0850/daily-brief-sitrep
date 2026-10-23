# File formats

## Brief (`daily-brief/v1`)

Written by the web page (`source: web`), the desktop app or the GitHub copy
(`run`, `source: desktop`), by an AI assistant in JSON mode, or by hand.
Checked by `python -m dailybrief check`.

| Field | Meaning |
|---|---|
| `schema` | `daily-brief/v1` |
| `source` | `web`, `desktop`, `ai` or `sample` |
| `model` | Optional: the assistant and model that wrote it |
| `title`, `date` | Page title and edition date (YYYY-MM-DD) |
| `generated_at` | When it was made, UTC, `2026-10-23T11:00:00Z` |
| `window_hours`, `backfill_max_hours`, `items_per_category` | The limits it was built with |
| `total` | Number of stories; must match the stories present |
| `withheld`, `ledger_applied` | Stories left out as already sent, and whether the history was used |
| `analysis` | Optional: `top_three` (list), `connection`, `watch` (list), `action` |
| `weather` | Optional forecast: `place`, `units` (`fahrenheit` or `celsius`), `fetched_at`, `current` (`{temp, code}` or null), and `days`, a list of up to four `{date, code, hi, lo, rain}`. `code` is a WMO weather code as Open-Meteo gives it; `rain` is the chance of rain in percent |
| `categories` | List of `{id, name, color?, icon?, tag?, signal?, so_what?, items}`; `icon` names an icon in `app/data/icons.js` |

Each item: `title`, `url` (http or https), `source`, `published` (UTC time, or
null for REFERENCE), `recency` (`news`, `backfill` or `reference`), `summary`,
optional `age_hours`, `starter` and `image`. `image` is an https link to the
story's photo; anything else is ignored with a warning, so the page never loads
a picture over plain http.

## Settings (`version: 1`)

See section 7 of `prompt/daily-brief-prompt.md`, `examples/sample-settings.json`,
and `python -m dailybrief validate your-settings.json`.

## History (`ledger.json`)

`urls` and `titles` map a normalized link or headline to the date it was sent;
`recent` holds the newest 3,000 headlines for near-duplicate checks;
`sent_dates` lists the days a brief went out.
