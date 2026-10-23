# Categories

A category is one desk in the newsletter. The quickest way to add one: on
question 2 of the setup, or on step 2 (Categories), type the topic in your own
words in **Type what you want to follow**, with other names for it after
commas (`electric cars, EVs, charging stations`). Ready-made categories that
match appear as you type; press one to add it, or press **Add** to make the
words your own category. Each category has:

| Setting | What it does | Example |
|---|---|---|
| Name | The desk title in the newsletter | Network Security and Zero Trust |
| Searches | News searches, one per line; use OR between choices and quotes around phrases | `"zero trust" (network OR security)` |
| Must mention | One line per group, terms separated by commas. A story must mention at least one term from every line | Line 1: `zero trust, CISA, firewall, VPN` |
| Leave out | Stories that mention any of these are dropped | `webinar, sponsored content` |
| Publisher feeds | RSS or Atom links the desktop app also reads | `https://www.bleepingcomputer.com/feed/` |
| Stories | How many stories this desk shows (default: the setting for all) | 3 |
| Skip list articles | Drops "top 10" and "best of" pieces | on |

## Matching rules

- Matching is by whole word: `cyber` does not match `cybernetic`.
- Short all-capital terms (2 to 6 letters, such as `AI`, `CVE`, `TSP`) match only
  in capitals, so `AI` never matches "said" and `IT` never matches "it".
- Terms with punctuation work: `401(k)`, `S&P 500`, `zero-day`.
- `{location}` in a name or search becomes your town. In a must-mention line,
  `{local_terms}` stands for your town plus the nearby towns you listed.

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

22 categories in six groups, and five starter packs. The full list with every
search and term is in [prompt/category-library.md](../prompt/category-library.md),
built from `app/data/library.js`. To propose a new library category, open an
issue with the "New category" form.
