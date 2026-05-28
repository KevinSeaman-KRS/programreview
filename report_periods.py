"""Shared reporting windows (America/New_York inquiry / matric dates)."""

PRIMARY_START = "2025-10-01"
PRIMARY_END = "2026-04-01"  # exclusive — through March 2026
PRIOR_START = "2025-04-01"
PRIOR_END = "2025-10-01"  # exclusive — April–September 2025

PRIMARY_LABEL = "Oct 2025 – Mar 2026"
PRIOR_LABEL = "Apr – Sep 2025"

# Enrolled-student profile (SRM matriculations) — 12 months for stable composition %
DEMOGRAPHICS_MATRIC_START = "2025-04-01"
DEMOGRAPHICS_MATRIC_END = "2026-04-01"  # exclusive — through March 2026
DEMOGRAPHICS_MATRIC_LABEL = "Apr 2025 – Mar 2026"

NAVIGATIONAL_SEGMENTS = frozenset({"Brand - Search", "Organic"})

# Detail-page monthly chart + table (14 months)
MONTHLY_DETAIL_START = "2025-04-01"
MONTHLY_DETAIL_END = "2026-06-01"  # exclusive — through May 2026
MONTHLY_DETAIL_LABEL = "Apr 2025 – May 2026"

MONTHLY_DETAIL_MONTHS: list[str] = [
    "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
    "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03",
    "2026-04", "2026-05",
]

# Legacy sample set (capture_all_screenshots.py --samples); report includes all enrolling programs
SAMPLE_DETAIL_PROGRAM_IDS: frozenset[str] = frozenset({
    "001Do00000ScUyQIAV",  # BA in Business Administration
    "001Do00000ScUy9IAF",  # Master of Business Administration
    "001Do00000ScUzFIAV",  # BA in Psychology
    "001Do00000ScUybIAF",  # BA in Health Care Administration
    "001Do00000ScUz7IAF",  # BA in Social and Criminal Justice
    "001Do00000ScUz6IAF",  # BA in Homeland Security and Emergency Management
})

SAMPLE_DETAIL_LABELS: dict[str, str] = {
    "001Do00000ScUyQIAV": "BA in Business Administration",
    "001Do00000ScUy9IAF": "Master of Business Administration",
    "001Do00000ScUzFIAV": "BA in Psychology",
    "001Do00000ScUybIAF": "BA in Health Care Administration",
    "001Do00000ScUz7IAF": "BA in Social and Criminal Justice",
    "001Do00000ScUz6IAF": "BA in Homeland Security and Emergency Management",
}
