"""Constants for the Göttinger Müllkalender integration."""
from __future__ import annotations

DOMAIN = "goettingen_muellkalender"

CONF_STREET = "street"
CONF_HOUSE_NUMBER = "house_number"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_NAME = "Müllkalender Göttingen"
DEFAULT_SCAN_INTERVAL_HOURS = 12

# GEB publishes a personal iCalendar export per street/house number at
# https://abfuhr.geb-goettingen.de/<year>/forward.php?str=<street>+&nr=<house_number>&year=<year>
# Discovered from a live example (Lindenweg 15) since GEB has no public
# API docs; the URL pattern moves the year into the path each year.
FORWARD_URL_TEMPLATE = "https://abfuhr.geb-goettingen.de/{year}/forward.php"

# How far back/forward to look when expanding calendar events.
LOOKBACK_DAYS = 1
LOOKAHEAD_DAYS = 400

# Number of upcoming dates to expose as an attribute per waste type.
MAX_UPCOMING_DATES = 5

FALLBACK_ICON = "mdi:trash-can-outline"

# Keyword based mapping of GEB calendar event summaries to waste types.
# Extend this list if the GEB calendar exposes additional categories
# (e.g. "Schadstoffmobil" dates for a different street) whose summary
# text isn't recognized correctly.
CATEGORY_DEFINITIONS: list[dict[str, object]] = [
    {
        "slug": "restmuell",
        "name": "Restmüll",
        "icon": "mdi:trash-can",
        "keywords": ("restmüll", "restabfall", "restmuell"),
    },
    {
        "slug": "biomuell",
        "name": "Biomüll",
        "icon": "mdi:leaf",
        "keywords": ("biomüll", "bioabfall", "biotonne", "biomuell"),
    },
    {
        "slug": "papier",
        "name": "Papiertonne",
        "icon": "mdi:file-document-outline",
        "keywords": ("papier", "altpapier"),
    },
    {
        "slug": "gelber_sack",
        "name": "Gelber Sack / Wertstoff",
        "icon": "mdi:recycle",
        "keywords": ("gelber sack", "gelben sack", "gelbe tonne", "wertstoff", "verpackung", "sack"),
    },
    {
        "slug": "sperrmuell",
        "name": "Sperrmüll",
        "icon": "mdi:sofa",
        "keywords": ("sperrmüll", "sperrgut", "sperrmuell"),
    },
    {
        "slug": "gruenschnitt",
        "name": "Grün-/Strauchschnitt",
        "icon": "mdi:tree",
        "keywords": (
            "grünschnitt",
            "strauchschnitt",
            "grünabfall",
            "gartenabfall",
            "baumschnitt",
        ),
    },
    {
        "slug": "schadstoff",
        "name": "Schadstoffmobil",
        "icon": "mdi:biohazard",
        "keywords": ("schadstoff",),
    },
    {
        "slug": "weihnachtsbaum",
        "name": "Weihnachtsbaum",
        "icon": "mdi:pine-tree",
        "keywords": ("weihnachtsbaum", "christbaum"),
    },
]
