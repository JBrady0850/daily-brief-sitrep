"""Source of the Daily Brief icon set, drawn for this project (24 by 24 grid,
round 1.8 strokes in the current colour). Run it to rebuild app/data/icons.js:

    python tools/icons_source.py

The weather icons carry their own colours; every other icon follows the text
colour. Keep each icon simple enough to read at 18 pixels.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dailybrief.jsdata import write_js_json  # noqa: E402

ICONS = {
    # general news
    "news": '<rect x="3" y="4" width="15" height="16" rx="2"/><path d="M18 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2H5"/><path d="M7 8h7M7 12h7M7 16h4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/>',
    "flag": '<path d="M5 21V4"/><path d="M5 4h12l-2.5 4L17 12H5"/>',
    "capitol": '<path d="M3 21h18M5 21v-7M9 21v-7M15 21v-7M19 21v-7M3 14h18M6 14a6 6 0 0 1 12 0M12 8V4M12 4h2"/>',
    "shield": '<path d="M12 3l8 3v5c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3M12 15v2"/>',
    "network": '<circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M12 7v5M12 12l-5.5 5.5M12 12l5.5 5.5"/>',
    "cloud": '<path d="M7 18a4 4 0 0 1-.6-8 6 6 0 0 1 11.4 1.5A3.5 3.5 0 0 1 17.5 18z"/>',
    "chip": '<rect x="7" y="7" width="10" height="10" rx="1.5"/><rect x="10" y="10" width="4" height="4"/><path d="M10 7V4M14 7V4M10 20v-3M14 20v-3M7 10H4M7 14H4M20 10h-3M20 14h-3"/>',
    "sparkle": '<path d="M11 3l1.8 5.2L18 10l-5.2 1.8L11 17l-1.8-5.2L4 10l5.2-1.8z"/><path d="M18.5 14.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/>',
    "code": '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
    "chart": '<path d="M4 4v16h16"/><path d="M7 15l4-4 3 3 5-6"/><path d="M15 8h4v4"/>',
    "coin": '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.6-1.5-3-1.5-1.7 0-3 .9-3 2s1.3 1.7 3 2 3 .9 3 2-1.3 2-3 2c-1.4 0-2.5-.5-3-1.5M12 6v2M12 16v2"/>',
    "house": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "hourglass": '<path d="M7 3h10M7 21h10"/><path d="M8 3v2.5a4 4 0 0 0 1.6 3.2L12 10.5l2.4-1.8A4 4 0 0 0 16 5.5V3"/><path d="M8 21v-2.5a4 4 0 0 1 1.6-3.2L12 13.5l2.4 1.8a4 4 0 0 1 1.6 3.2V21"/>',
    "graduation": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c3 2 9 2 12 0v-5M22 9v6"/>',
    "health": '<path d="M20.5 8.8c0 5-8.5 11-8.5 11S3.5 13.8 3.5 8.8A4.5 4.5 0 0 1 12 6.3a4.5 4.5 0 0 1 8.5 2.5z"/><path d="M6 12h3l1.5-2.5 2 5 1.5-2.5h4"/>',
    "flask": '<path d="M9 3h6M10 3v6L4.5 18.5A1.7 1.7 0 0 0 6 21h12a1.7 1.7 0 0 0 1.5-2.5L14 9V3"/><path d="M7 15h10"/>',
    "rocket": '<path d="M12 2c3 2 5 6 4.5 11L14.5 16h-5L7.5 13C7 8 9 4 12 2z"/><circle cx="12" cy="9" r="1.8"/><path d="M7.5 13L5 15.5l1 3.5 3.5-3M16.5 13l2.5 2.5-1 3.5-3.5-3M11 19l1 3 1-3"/>',
    "leaf": '<path d="M5 19c0-9 6-14 15-15-1 9-6 15-15 15z"/><path d="M5 19l8-8"/>',
    "plane": '<path d="M10.5 4.5a1.5 1.5 0 0 1 3 0V9l7 4v2l-7-2v4l2 1.5V20L12 19l-3.5 1v-1.5l2-1.5v-4l-7 2v-2l7-4z"/>',
    "car": '<path d="M3 17v-4l2.2-5.2A2 2 0 0 1 7 6.5h10a2 2 0 0 1 1.8 1.3L21 13v4h-2M5 17H3M15 17H9"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><path d="M4 13h16"/>',
    "food": '<path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10"/><path d="M17 21V3c-2.2 1.5-3 4-3 7v3h3"/>',
    "film": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
    "music": '<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
    "tv": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M8 21h8M12 18v3M8 2l4 4 4-4"/>',
    "book": '<path d="M4 19V5a2 2 0 0 1 2-2h14v14H6a2 2 0 0 0-2 2 2 2 0 0 0 2 2h14v-4"/>',
    "gamepad": '<path d="M7 8h10a4 4 0 0 1 3.9 4.8l-.8 3.7a2 2 0 0 1-3.5.8L14.5 15h-5l-2.1 2.3a2 2 0 0 1-3.5-.8l-.8-3.7A4 4 0 0 1 7 8z"/><path d="M8 10.5v3M6.5 12h3M15.5 11.5h.01M17.5 13h.01"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    # app status marks
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.8 2.8L16.2 9.6"/>',
    "pencil": '<path d="M4 20h4L19.2 8.8a2 2 0 0 0 0-2.8l-1.2-1.2a2 2 0 0 0-2.8 0L4 16z"/><path d="M13.5 6.5l4 4"/>',
    # ordering controls
    "up": '<path d="M12 19V5M6 11l6-6 6 6"/>',
    "down": '<path d="M12 5v14M6 13l6 6 6-6"/>',
    "top": '<path d="M5 4h14M12 20V9M6.5 14.5L12 9l5.5 5.5"/>',
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="M3.5 7l8.5 6.5L20.5 7"/>',
    "sunrise": '<path d="M3 18h18M6 18a6 6 0 0 1 12 0M12 4v4M4.6 9.6l2 1.5M19.4 9.6l-2 1.5M8 21h8"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "city": '<path d="M3 21h18M5 21V8l6-3v16M11 21V9h8v12M14 12h2M14 15h2M14 18h2M7.5 10h1M7.5 13h1M7.5 16h1"/>',
    "alert": '<path d="M12 3.5l9.5 16.5h-19z"/><path d="M12 10v4M12 17h.01"/>',
    "umbrella": '<path d="M3 12a9 9 0 0 1 18 0z"/><path d="M12 12v6.5a2 2 0 0 1-4 0M12 3v0"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4M8 14h2M14 14h2M8 17h2"/>',
    "people": '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9.5" r="2.2"/><path d="M3.5 20a5.5 5.5 0 0 1 11 0M15 15.6a4 4 0 0 1 6 3.4"/>',
    "paw": '<circle cx="6.5" cy="10.5" r="1.8"/><circle cx="10" cy="6.5" r="1.8"/><circle cx="14" cy="6.5" r="1.8"/><circle cx="17.5" cy="10.5" r="1.8"/><path d="M12 12c-3 0-5.5 3.5-5.5 5.5 0 1.5 1.2 2.5 2.7 2.5 1.2 0 1.8-.7 2.8-.7s1.6.7 2.8.7c1.5 0 2.7-1 2.7-2.5 0-2-2.5-5.5-5.5-5.5z"/>',
    "medal": '<path d="M8 3l4 6 4-6M6.5 3H10M14 3h3.5"/><circle cx="12" cy="15" r="6"/><path d="M12 12l.9 1.9 2.1.3-1.5 1.5.4 2.1-1.9-1-1.9 1 .4-2.1-1.5-1.5 2.1-.3z"/>',
    "crypto": '<path d="M12 2l8.5 5v10L12 22l-8.5-5V7z"/><path d="M10 8v8M10 8h3a2 2 0 0 1 0 4h-3 3.5a2 2 0 0 1 0 4H10M11 6.5V8M13 6.5V8M11 16v1.5M13 16v1.5"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.2A2 2 0 0 0 9.7 17h8.4a2 2 0 0 0 2-1.6L21.5 8H6"/>',
    "phone": '<rect x="6" y="2" width="12" height="20" rx="2.5"/><path d="M11 18h2"/>',
    "mountain": '<path d="M2 20l7-11 4 6 2.5-3.5L22 20z"/><path d="M7.2 11.8L9 13l1.5-1.5"/>',
    "megaphone": '<path d="M3 10v4a1 1 0 0 0 1 1h3l9 5V4L7 9H4a1 1 0 0 0-1 1z"/><path d="M7 15l1.5 5h2.5L10 15.8M19.5 9a4 4 0 0 1 0 6"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    # sports
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 21h8M9 17h6"/>',
    "football": '<path d="M5 19c-1.5-5 1-11 7-13.6 3-1.2 5.8-1.2 7-.4 1.5 5-1 11-7 13.6-3 1.2-5.8 1.2-7 .4z"/><path d="M9.5 14.5l5-5M10.5 11.5l2 2M12.5 9.5l2 2M8.5 13.5l2 2"/>',
    "basketball": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3v18M5.6 5.6c3.5 3.5 3.5 9.3 0 12.8M18.4 5.6c-3.5 3.5-3.5 9.3 0 12.8"/>',
    "baseball": '<circle cx="12" cy="12" r="9"/><path d="M8 4.2c1.8 2.1 2.6 4.8 2.2 7.8S8.4 17.6 6 19.2M16 4.8c-2.1 1.8-3 4.4-2.6 7.2s2 5.2 4.6 6.6"/>',
    "hockey": '<path d="M15 3l-4.8 12.4a2.5 2.5 0 0 1-2.3 1.6H3.5v2.5h5a4 4 0 0 0 3.7-2.5L17.8 3"/><ellipse cx="18.5" cy="19" rx="3" ry="1.5"/>',
    "soccer": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5l4 2.9-1.5 4.7h-5L8 10.4z"/><path d="M12 7.5V3M16 10.4l4.2-1.4M14.5 15.1l2.6 3.6M9.5 15.1l-2.6 3.6M8 10.4L3.8 9"/>',
    "golf": '<path d="M10 18V3l8 4-8 4"/><ellipse cx="10" cy="19.5" rx="6" ry="1.5"/>',
    "racing": '<path d="M5 21V4"/><path d="M5 4h14v10H5"/><path d="M5 9h14M12 4v10M8.5 4v5M15.5 9v5"/>',
    "tennis": '<circle cx="12" cy="12" r="9"/><path d="M5.5 5.8c3.3 3.4 3.3 9 0 12.4M18.5 5.8c-3.3 3.4-3.3 9 0 12.4"/>',
    "college": '<path d="M3 21h18M4 21V10l8-5 8 5v11"/><path d="M9 21v-6h6v6M12 5V2l3 1.5"/>',
}

# Weather icons carry their own colours, so they read the same on any page.
SUN = 'fill="#f2b632" stroke="#c98a0b"'
CLOUD = 'fill="#e8edf3" stroke="#6b7c93"'
DARK = 'fill="#aab6c6" stroke="#55657b"'
WEATHER = {
    "clear": '<circle cx="12" cy="12" r="5" ' + SUN + '/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6" stroke="#c98a0b"/>',
    "partly": '<circle cx="9" cy="9" r="4" ' + SUN + '/><path d="M9 2.5v1.4M2.5 9h1.4M4.4 4.4l1 1M13.6 4.4l-1 1" stroke="#c98a0b"/><path d="M8.5 20a3.5 3.5 0 0 1-.5-7 5 5 0 0 1 9.6 1.3A3 3 0 0 1 17.5 20z" ' + CLOUD + '/>',
    "cloudy": '<path d="M7 19a4 4 0 0 1-.6-8 6 6 0 0 1 11.4 1.5A3.5 3.5 0 0 1 17.5 19z" ' + CLOUD + '/>',
    "fog": '<path d="M7 14a4 4 0 0 1-.6-8 6 6 0 0 1 11.4 1.5A3.5 3.5 0 0 1 17.5 14z" ' + CLOUD + '/><path d="M4 17.5h16M6 20.5h12" stroke="#8a97a8"/>',
    "drizzle": '<path d="M7 15a4 4 0 0 1-.6-8 6 6 0 0 1 11.4 1.5A3.5 3.5 0 0 1 17.5 15z" ' + CLOUD + '/><path d="M8.5 18v1M12 18.5v1M15.5 18v1" stroke="#3a7bd5"/>',
    "rain": '<path d="M7 14a4 4 0 0 1-.6-8 6 6 0 0 1 11.4 1.5A3.5 3.5 0 0 1 17.5 14z" ' + DARK + '/><path d="M8 17l-1 3M12 17l-1 3M16 17l-1 3" stroke="#2b6cc4"/>',
    "snow": '<path d="M7 14a4 4 0 0 1-.6-8 6 6 0 0 1 11.4 1.5A3.5 3.5 0 0 1 17.5 14z" ' + CLOUD + '/><path d="M8 16.8v2.6M6.9 17.4l2.2 1.4M9.1 17.4l-2.2 1.4M12 19v2.6M10.9 19.6l2.2 1.4M13.1 19.6l-2.2 1.4M16 16.8v2.6M14.9 17.4l2.2 1.4M17.1 17.4l-2.2 1.4" stroke="#5b8fd6" stroke-width="1.3"/>',
    "storm": '<path d="M7 14a4 4 0 0 1-.6-8 6 6 0 0 1 11.4 1.5A3.5 3.5 0 0 1 17.5 14z" ' + DARK + '/><path d="M12.5 13l-2.5 4h3l-2 4.5" fill="none" stroke="#e0a400"/>',
}

# Line art for the page header and the setup screen.
ART = {
    "masthead": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 160" preserveAspectRatio="xMaxYMid slice" aria-hidden="true">'
        '<g fill="none" stroke="#ffffff" stroke-opacity=".10" stroke-width="1.2">'
        '<circle cx="470" cy="80" r="150"/><circle cx="470" cy="80" r="115"/><circle cx="470" cy="80" r="80"/><circle cx="470" cy="80" r="45"/>'
        '<path d="M320 80h300M470 -70v300M364 -26l212 212M364 186l212-212"/></g>'
        '<g fill="#e0b43a" fill-opacity=".9"><circle cx="470" cy="80" r="5"/><circle cx="532" cy="42" r="3"/><circle cx="405" cy="125" r="3"/>'
        '<circle cx="560" cy="118" r="2.5"/><circle cx="398" cy="38" r="2.5"/></g>'
        '<path d="M398 38L470 80 532 42M470 80l-65 45M470 80l90 38" stroke="#e0b43a" stroke-opacity=".55" stroke-width="1.2" fill="none"/></svg>'
    ),
    "hero": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200" role="img" aria-label="A morning newspaper in front of a rising sun">'
        '<defs><linearGradient id="dbsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe7b0"/><stop offset="1" stop-color="#fff7e6"/></linearGradient></defs>'
        '<rect x="0" y="0" width="320" height="200" rx="18" fill="url(#dbsky)"/>'
        '<circle cx="232" cy="118" r="54" fill="#f2b632"/><g stroke="#f2b632" stroke-width="5" stroke-linecap="round">'
        '<path d="M232 40v14M276 58l-9 10M188 58l9 10M300 112h-14M178 112h-14"/></g>'
        '<path d="M0 150c60-18 120-18 180 0s110 14 140 4v46H0z" fill="#0f2744"/>'
        '<path d="M0 170c70-14 130-10 190 4s100 10 130 2v24H0z" fill="#1d3a5f"/>'
        '<g transform="translate(40 38) rotate(-6)"><rect width="150" height="112" rx="8" fill="#ffffff" stroke="#0f2744" stroke-width="3"/>'
        '<rect x="14" y="14" width="122" height="16" rx="3" fill="#0f2744"/><rect x="14" y="38" width="56" height="40" rx="3" fill="#e0b43a"/>'
        '<g stroke="#9aa8ba" stroke-width="4" stroke-linecap="round"><path d="M80 42h56M80 54h56M80 66h40M14 90h122M14 101h100"/></g></g>'
        '</svg>'
    ),
}

WEATHER_CODES = {
    "clear": [0, 1], "partly": [2], "cloudy": [3], "fog": [45, 48],
    "drizzle": [51, 53, 55, 56, 57], "rain": [61, 63, 65, 66, 67, 80, 81, 82],
    "snow": [71, 73, 75, 77, 85, 86], "storm": [95, 96, 99],
}
WEATHER_WORDS = {
    "clear": "Clear", "partly": "Partly cloudy", "cloudy": "Cloudy", "fog": "Fog", "drizzle": "Drizzle",
    "rain": "Rain", "snow": "Snow", "storm": "Thunderstorms",
}

HEADER = """/* Daily Brief icons and artwork, drawn for this project and free to reuse under
   the project's MIT licence. Generated by tools/icons_source.py; edit there.
   Plain JSON after the equals sign, so the Python tools read the same file. */"""


def data() -> dict:
    return {"version": 1, "icons": ICONS, "weather": WEATHER, "art": ART,
            "weather_codes": WEATHER_CODES, "weather_words": WEATHER_WORDS}


def main() -> int:
    write_js_json(ROOT / "app" / "data" / "icons.js", "DB_ICONS", data(), HEADER)
    print("Wrote app/data/icons.js:", len(ICONS), "icons,", len(WEATHER), "weather icons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
