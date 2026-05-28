"""US state → region mapping for concise enrollment geography."""
from __future__ import annotations

STATE_NAME_TO_ABBR: dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}

REGION_ORDER = ["Southwest", "Southeast", "West", "Northeast", "Midwest", "Other"]

REGION_STATES: dict[str, frozenset[str]] = {
    "Southwest": frozenset({"AZ", "NM", "NV", "UT", "CO", "OK", "TX"}),
    "Southeast": frozenset({
        "FL", "GA", "AL", "MS", "LA", "SC", "NC", "TN", "KY", "VA", "AR", "WV",
    }),
    "West": frozenset({"CA", "OR", "WA", "ID", "MT", "WY", "AK", "HI"}),
    "Northeast": frozenset({
        "NY", "NJ", "PA", "MA", "CT", "RI", "NH", "VT", "ME", "MD", "DE", "DC",
    }),
    "Midwest": frozenset({
        "IL", "IN", "OH", "MI", "WI", "MN", "IA", "MO", "ND", "SD", "NE", "KS",
    }),
}


def normalize_state(raw: str | None) -> str | None:
    if not raw:
        return None
    s = str(raw).strip()
    if len(s) == 2:
        return s.upper()
    return STATE_NAME_TO_ABBR.get(s.lower())


def state_to_region(state: str | None) -> str:
    abbr = normalize_state(state)
    if not abbr:
        return "Other"
    for region, states in REGION_STATES.items():
        if abbr in states:
            return region
    return "Other"


def region_distribution(
    rows: list[dict], min_pct: float = 5.0
) -> dict[str, float]:
    from collections import Counter

    n = len(rows)
    if n == 0:
        return {}
    c = Counter(state_to_region(r.get("state")) for r in rows if r.get("state"))
    out: dict[str, float] = {}
    for region in REGION_ORDER:
        count = c.get(region, 0)
        if count:
            pct = round(count / n * 100, 1)
            if pct >= min_pct or region != "Other":
                out[region] = pct
    return out
