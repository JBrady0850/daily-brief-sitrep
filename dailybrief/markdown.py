"""The brief as GitHub-flavored Markdown, for the GitHub issue channel and for
pasting anywhere that shows Markdown. Same order and labels as the newsletter."""
from __future__ import annotations

import re
from typing import Any

from . import engine as E
from .render import age_of, countdown_data, pretty_date, source_label, stats, subject_line, tag_of

_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]<>()#+!|~])")


_ZWSP = chr(0x200B)


def md(text: Any) -> str:
    """Escapes Markdown and HTML punctuation so feed text shows as plain text.
    An invisible space after each @ stops a headline from mentioning a GitHub user."""
    return _MD_SPECIAL.sub(r"\\\1", E.collapse(text)).replace("@", "@" + _ZWSP)


def _link(url: Any) -> str:
    u = str(url or "").strip()
    return u.replace("(", "%28").replace(")", "%29").replace(" ", "%20") if E.valid_url(u) else ""


def render_markdown(brief: dict, cfg: Any = None) -> str:
    n = E.normalize_config(cfg or {})
    s = stats(brief)
    win = brief.get("window_hours") or n["brief"]["window_hours"]
    title = E.collapse(brief.get("title")) or n["brief"]["title"]
    day = str(brief.get("date") or "")
    L = ["# " + md(title), "",
         "**" + md(pretty_date(day)) + "** | " + str(s["total"]) + " stories across " + str(s["cats"])
         + " categories | " + str(s["news"]) + " fresh in the last " + str(win) + " hours", ""]
    if brief.get("source") == "sample":
        L += ["> Sample brief: invented headlines that show the layout.", ""]
    cd = countdown_data(n, day)
    if cd:
        L.append("**" + md(cd["label"]) + ": " + str(cd["days"]) + " days** to " + md(pretty_date(cd["date"])))
        for m in cd["upcoming"]:
            L.append("- " + str(E.days_between(day, m["date"])) + " d, " + m["date"] + ": " + md(m["label"])
                     + (" (" + md(m["note"]) + ")" if m["note"] else ""))
        L.append("")
    a = brief.get("analysis")
    if isinstance(a, dict):
        top = [E.collapse(x) for x in (a.get("top_three") or []) if E.collapse(x)] if isinstance(a.get("top_three"), list) else []
        watch = a.get("watch") if isinstance(a.get("watch"), list) else ([a.get("watch")] if a.get("watch") else [])
        watch = [E.collapse(x) for x in watch if E.collapse(x)]
        if top or watch or E.collapse(a.get("connection")) or E.collapse(a.get("action")):
            L += ["## Lead analysis", ""]
            L += [str(i + 1) + ". " + md(t) for i, t in enumerate(top)]
            if E.collapse(a.get("connection")):
                L.append("\n**Connection:** " + md(a.get("connection")))
            if watch:
                L.append("\n**" + md(n["brief"]["watch_label"]) + ":**")
                L += ["- " + md(t) for t in watch]
            if E.collapse(a.get("action")):
                L.append("\n**Action:** " + md(a.get("action")))
            L += ["", "*Analysis is inference from the headlines below, not reporting.*", ""]
    for index, cat in enumerate(brief.get("categories") or []):
        items = cat.get("items") if isinstance(cat.get("items"), list) else []
        n_news = len([i for i in items if i.get("recency") == "news"])
        n_back = len([i for i in items if i.get("recency") == "backfill"])
        n_ref = len([i for i in items if i.get("recency") == "reference"])
        mix = str(n_news) + " fresh" + (", " + str(n_back) + " older" if n_back else "") + (", " + str(n_ref) + " reference" if n_ref else "")
        L += ["## [" + md(tag_of(cat, index)) + "] " + md(cat.get("name")) + " (" + mix + ")", ""]
        if E.collapse(cat.get("signal")):
            L.append("**Signal:** " + md(cat.get("signal")) + "  ")
        if E.collapse(cat.get("so_what")):
            L.append("**So what:** " + md(cat.get("so_what")))
        if not items:
            L.append("*No new items in the last " + str(win) + " hours that you have not already been sent.*")
        for it in items:
            age = age_of(it, brief)
            r = it.get("recency")
            label = "REFERENCE, undated" if r == "reference" else ("OLDER, " + E.humanize_age(age)) if r == "backfill" else ("NEWS, " + E.humanize_age(age))
            href = _link(it.get("url"))
            head = "[" + md(it.get("title")) + "](" + href + ")" if href else md(it.get("title"))
            src = md(it.get("source"))
            L.append("- **" + head + "** | " + (src + " | " if src else "") + "`" + label + "`")
            if E.collapse(it.get("summary")):
                L.append("  " + md(it.get("summary")))
        L.append("")
    L += ["---", "*" + md(subject_line(brief, n)) + ". Generated " + md(brief.get("generated_at") or "") + ", "
          + md(source_label(brief)) + ". Daily Brief " + E.VERSION + ".*"]
    return "\n".join(L) + "\n"
