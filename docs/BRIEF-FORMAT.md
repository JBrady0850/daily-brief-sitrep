# File formats

## Brief (`daily-brief/v1`)

Written by the desktop app (`run`), by an AI assistant in JSON mode, or by hand.
Checked by `python -m dailybrief check`.

| Field | Meaning |
|---|---|
| `schema` | `daily-brief/v1` |
| `source` | `desktop`, `ai` or `sample` |
| `model` | Optional: the assistant and model that wrote it |
| `title`, `date` | Newsletter title and edition date (YYYY-MM-DD) |
| `generated_at` | When it was made, UTC, `2026-10-23T11:00:00Z` |
| `window_hours`, `backfill_max_hours`, `items_per_category` | The limits it was built with |
| `total` | Number of stories; must match the stories present |
| `withheld`, `ledger_applied` | Stories left out as already sent, and whether the history was used |
| `analysis` | Optional: `top_three` (list), `connection`, `watch` (list), `action` |
| `categories` | List of `{id, name, color?, tag?, signal?, so_what?, items}` |

Each item: `title`, `url` (http or https), `source`, `published` (UTC time, or
null for REFERENCE), `recency` (`news`, `backfill` or `reference`), `summary`,
optional `age_hours` and `starter`.

## Settings (`version: 1`)

See section 7 of `prompt/daily-brief-prompt.md`, `examples/sample-settings.json`,
and `python -m dailybrief validate your-settings.json`.

## History (`ledger.json`)

`urls` and `titles` map a normalized link or headline to the date it was sent;
`recent` holds the newest 3,000 headlines for near-duplicate checks;
`sent_dates` lists the days a brief went out.
