# Categories

A category is one desk on the brief page. The quickest way to add one: on
question 2 of the setup, or on step 2 (Categories), type the topic in your own
words in **Type what you want to follow**, with other names for it after
commas (`electric cars, EVs, charging stations`). Ready-made categories that
match appear as you type; press one to add it, or press **Add** to make the
words your own category. Each category has:

| Setting | What it does | Example |
|---|---|---|
| Name | The desk title on the page | Network Security and Zero Trust |
| Searches | News searches, one per line; use OR between choices and quotes around phrases | `"zero trust" (network OR security)` |
| Must mention | One line per group, terms separated by commas. A story must mention at least one term from every line | Line 1: `zero trust, CISA, firewall, VPN` |
| Leave out | Stories that mention any of these are dropped | `webinar, sponsored content` |
| On-topic feeds | Feeds about this topic and nothing else. Their stories count as on topic without a "must mention" term; the "leave out" terms and every other filter still apply | `https://rss.nytimes.com/services/xml/rss/nyt/Tennis.xml` |
| Publisher feeds | RSS or Atom links also read for this desk. The web page can read only feeds that allow web pages (see docs/LIMITS.md) | `https://www.espn.com/espn/rss/nfl/news` |
| Icon | The picture on the desk's heading, from `app/data/icons.js` | `football` |
| Stories | How many stories this desk shows (default: the setting for all) | 3 |
| Skip list articles | Drops "top 10" and "best of" pieces | on |

## Matching rules

- Matching is by whole word: `cyber` does not match `cybernetic`.
- Short all-capital terms (2 to 6 letters, such as `AI`, `CVE`, `TSP`) match only
  in capitals, so `AI` never matches "said" and `IT` never matches "it".
- Terms with punctuation work: `401(k)`, `S&P 500`, `zero-day`.
- `{location}` in a name or search becomes your town, and `{region}` your state
  or region. In a must-mention line, `{local_terms}` stands for your town plus
  the nearby towns and county you listed.
- In a search, a quoted `"{location}"` that is not inside a group searches your
  area: your town or any nearby place you listed, up to four names in all, for
  example `("Springfield" OR "Sangamon County") council`. Nearby names shorter
  than three letters are left out of searches (the news index refuses them).
  Inside a group it stays your town, because groups cannot nest.
- Town categories (those with `{location}`, `{local_terms}` or `needs_location`)
  also read the news of the local TV stations in your state (gathered on GitHub
  every four hours; see `dailybrief/local_stations.json`) and the local news
  feeds you add on the town question. Their stories still need to name your
  town or a nearby place, and the desk's topic words still apply.
- Things to Do (`local-events`) also reads the week's events from the nearest
  station calendar (see `app/data/calendars.js`): first those within 5 miles of
  the town, so its own events lead, then those within 20 miles.
  Events lead the desk, a day at a time, and carry an `event` with their start
  and place; the desk's excluded words still apply.

## Writing a good category

1. Start with two searches: one broad, one specific.
2. Add a must-mention line that names the subject itself, so a search result
   that only brushes the topic is left out.
3. For a subject that needs two things at once (AI and the military, say), use
   two must-mention lines.
4. Run a brief, open **Sources and filters** under the preview, and look at the
   "left out" counts. Many "off topic" means the searches are too broad; an
   empty desk means the must-mention terms are too narrow.

## The library

67 categories in 11 groups (top news, weather, sports, technology, money and
business, science and health, entertainment and culture, life and home, your
area, government and defense, career and education), and ten starter packs.
Every library category has an icon and a colour that passes the contrast check
for white text. The full list with every
search and term is in [prompt/category-library.md](../prompt/category-library.md),
built from `app/data/library.js`. To propose a new library category, open an
issue with the "New category" form.
