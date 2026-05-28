"""
Marketing segment hierarchy (initial → rollup) for program report widgets and Sankey.

Source: business rollup keyed on mars_segment_legacy (= initial_marketing_segment).
BQ vw_lead_extract_details: mars_segment_legacy + marketing_segment_rollup.
"""
from __future__ import annotations

# mars_segment_legacy → marketing_rollup, segment_rollup, segment1
MARS_LEGACY_MAP: dict[str, dict[str, str]] = {
    "Agg - Tier 1": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Affiliate",
        "segment1": "Affiliate",
    },
    "Display - Facebook": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Display",
        "segment1": "Display",
    },
    "Display - Other": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Display",
        "segment1": "Display",
    },
    "B2B - TPA": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Display",
        "segment1": "Display",
    },
    "Display - Partner Display": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Affiliate - Search",
        "segment1": "Affiliate - Search",
    },
    "Search - Generic": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Non Brand - Search",
        "segment1": "Non-Brand Search",
    },
    "Unknown": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Display",
        "segment1": "Display",
    },
    "Search - Tradename": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Brand - Search",
        "segment1": "Brand - Search",
    },
    "Call In": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Organic",
        "segment1": "Organic B2C",
    },
    "Mil - Outreach": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Organic",
        "segment1": "Organic B2C",
    },
    "oap": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Organic",
        "segment1": "Organic B2C",
    },
    "Organic": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Organic",
        "segment1": "Organic B2C",
    },
    "Referral": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Organic",
        "segment1": "Organic B2C",
    },
    "EP - Events": {
        "marketing_rollup": "B2B",
        "segment_rollup": "Organic",
        "segment1": "Organic B2B",
    },
    "EP - Organic": {
        "marketing_rollup": "B2B",
        "segment_rollup": "Organic",
        "segment1": "Organic B2B",
    },
    "AP - Organic": {
        "marketing_rollup": "B2B",
        "segment_rollup": "Organic",
        "segment1": "Organic B2B",
    },
    "AP - Events": {
        "marketing_rollup": "B2B",
        "segment_rollup": "Organic",
        "segment1": "Organic B2B",
    },
    # Observed in BQ; not in reference sheet — treat as navigational organic B2C
    "Paid List - No Consent": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Organic",
        "segment1": "Organic B2C",
    },
}

# When mars_segment_legacy is null, infer from marketing_segment_rollup (BQ column)
SEGMENT_ROLLUP_FALLBACK: dict[str, dict[str, str]] = {
    "Affiliate": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Affiliate",
        "segment1": "Affiliate",
    },
    "Display": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Display",
        "segment1": "Display",
    },
    "Affiliate - Search": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Affiliate - Search",
        "segment1": "Affiliate - Search",
    },
    "Non Brand - Search": {
        "marketing_rollup": "Paid",
        "segment_rollup": "Non Brand - Search",
        "segment1": "Non-Brand Search",
    },
    "Brand - Search": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Brand - Search",
        "segment1": "Brand - Search",
    },
    "Organic": {
        "marketing_rollup": "Navigational",
        "segment_rollup": "Organic",
        "segment1": "Organic B2C",
    },
}

# initial_marketing_segment1 — Sankey inflow (more detail than Paid/Nav/B2B)
SEGMENT1_ORDER = [
    "Display",
    "Affiliate",
    "Affiliate - Search",
    "Non-Brand Search",
    "Brand - Search",
    "Organic B2C",
    "Organic B2B",
]

SEGMENT1_COLORS = {
    "Display": "#0076A8",
    "Affiliate": "#378DBD",
    "Affiliate - Search": "#81D3EB",
    "Non-Brand Search": "#0C234B",
    "Brand - Search": "#AB0520",
    "Organic B2C": "#98A4AE",
    "Organic B2B": "#0076A8",
}

MARKETING_ROLLUP_ORDER = ["Paid", "Navigational", "B2B"]

MARKETING_ROLLUP_COLORS = {
    "Paid": "#AB0520",
    "Navigational": "#0C234B",
    "B2B": "#0076A8",
}

# Sankey inflow uses initial_marketing_segment1 labels → rollup for widget strips.
SEGMENT1_TO_MARKETING_ROLLUP: dict[str, str] = {
    row["segment1"]: row["marketing_rollup"] for row in MARS_LEGACY_MAP.values()
}
for row in SEGMENT_ROLLUP_FALLBACK.values():
    SEGMENT1_TO_MARKETING_ROLLUP.setdefault(row["segment1"], row["marketing_rollup"])

SEGMENT_ROLLUP_ORDER = [
    "Organic",
    "Display",
    "Affiliate",
    "Affiliate - Search",
    "Non Brand - Search",
    "Brand - Search",
]

SEGMENT_ROLLUP_COLORS = {
    "Organic": "#98A4AE",
    "Display": "#0076A8",
    "Affiliate": "#378DBD",
    "Affiliate - Search": "#81D3EB",
    "Non Brand - Search": "#0C234B",
    "Brand - Search": "#AB0520",
}

# Paid marketing rollup → segment rollup breakdown (widget row 2)
PAID_SEGMENT_ROLLUP_ORDER = [
    "Display",
    "Affiliate",
    "Affiliate - Search",
    "Non Brand - Search",
]


def _lookup_row(
    mars_segment_legacy: str | None,
    marketing_segment_rollup: str | None,
) -> dict[str, str] | None:
    legacy = (mars_segment_legacy or "").strip()
    rollup = (marketing_segment_rollup or "").strip()
    if legacy and legacy in MARS_LEGACY_MAP:
        return MARS_LEGACY_MAP[legacy]
    if rollup and rollup in SEGMENT_ROLLUP_FALLBACK:
        return SEGMENT_ROLLUP_FALLBACK[rollup]
    return None


def resolve_segment1(
    mars_segment_legacy: str | None,
    marketing_segment_rollup: str | None,
) -> str | None:
    """Return initial_marketing_segment1 label for Sankey inflow."""
    row = _lookup_row(mars_segment_legacy, marketing_segment_rollup)
    return row["segment1"] if row else None


def resolve_marketing_levels(
    mars_segment_legacy: str | None,
    marketing_segment_rollup: str | None,
) -> tuple[str, str] | None:
    """Return (marketing_rollup, segment_rollup) or None if segment should be skipped."""
    row = _lookup_row(mars_segment_legacy, marketing_segment_rollup)
    if not row:
        return None
    return row["marketing_rollup"], row["segment_rollup"]


def navigational_legacy_sql_list() -> str:
    """Quoted literals for SQL IN (...) — Navigational mars_segment_legacy values."""
    vals = [
        k
        for k, v in MARS_LEGACY_MAP.items()
        if v["marketing_rollup"] == "Navigational"
    ]
    return ", ".join(f"'{v}'" for v in sorted(vals))
