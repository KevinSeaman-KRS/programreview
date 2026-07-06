"""Shared helpers for enrolled-student demographic profiles."""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable


def distribution_pct(rows: list[dict], field: str, top_n: int = 8, min_pct: float = 0.0) -> dict[str, float]:
    n = len(rows)
    if n == 0:
        return {}
    c = Counter(r[field] for r in rows if r.get(field) is not None)
    out: dict[str, float] = {}
    for key, count in c.most_common(top_n):
        pct = round(count / n * 100, 1)
        if pct >= min_pct:
            out[str(key)] = pct
    return out


CORE_LOB_VALUES = frozenset({"Core", "Core/Other"})
MIL_LOB_VALUES = frozenset({"Military"})
MILITARY_FUNDING_YES = frozenset({"Military Funding"})
TRANSFER_UNDERGRAD_ORDER = [
    "True Zero",
    "Not True Zero",
    "1 to 15 Credits",
    "16 to 30 Credits",
    "31 to 45 Credits",
    "46 to 60 Credits",
    "61+ Credits",
]


def core_student_rows(rows: list[dict]) -> list[dict]:
    return [
        r
        for r in rows
        if (r.get("lineofbusiness") or "").strip() in CORE_LOB_VALUES
    ]


def military_lob_rows(rows: list[dict]) -> list[dict]:
    return [
        r
        for r in rows
        if (r.get("lineofbusiness") or "").strip() in MIL_LOB_VALUES
    ]


def pell_pct_core(rows: list[dict]) -> float | None:
    """Pell share among Core LOB enrollments only."""
    core = core_student_rows(rows)
    if not core:
        return None
    return pct_from_dist(distribution_pct(core, "pell"), "Pell")


def military_funding_pct(rows: list[dict]) -> float | None:
    """Military funding share among Military LOB enrollments only."""
    mil = military_lob_rows(rows)
    if not mil:
        return None
    funded = sum(
        1
        for r in mil
        if (r.get("MilitaryFunding") or "").strip() in MILITARY_FUNDING_YES
    )
    return round(funded / len(mil) * 100, 1)


def profile_rows(
    rows: list[dict], label: str, *, graduate: bool = False
) -> dict[str, Any] | None:
    n = len(rows)
    if n == 0:
        return None

    ages = [r["age_at_matric"] for r in rows if r.get("age_at_matric") is not None]
    ages_sorted = sorted(ages)

    def age_pct(lo: int | None, hi: int | None) -> float | None:
        if not ages:
            return None
        if lo is None:
            ok = [a for a in ages if a < hi]
        elif hi is None:
            ok = [a for a in ages if a >= lo]
        else:
            ok = [a for a in ages if lo <= a < hi]
        return round(len(ok) / len(ages) * 100, 1)

    out: dict[str, Any] = {
        "label": label,
        "count": n,
        "gender": distribution_pct(rows, "gender"),
        "gender_by_lob": gender_by_lob(rows),
        "race": distribution_pct(rows, "race", top_n=8),
        "minority": distribution_pct(rows, "minority"),
        "maritalstatus": distribution_pct(rows, "maritalstatus"),
        "lineofbusiness": distribution_pct(rows, "lineofbusiness"),
        "top_states": distribution_pct(rows, "state", top_n=5, min_pct=3.0),
        "age_median": ages_sorted[len(ages_sorted) // 2] if ages_sorted else None,
        "age_mean": round(sum(ages) / len(ages), 1) if ages else None,
        "age_under25": age_pct(None, 25),
        "age_25to34": age_pct(25, 35),
        "age_35to44": age_pct(35, 45),
        "age_45plus": age_pct(45, None),
    }
    if not graduate:
        out["pell"] = distribution_pct(rows, "pell")
        out["transferstatus"] = distribution_pct(rows, "transferstatus")
        core_pell = pell_pct_core(rows)
        if core_pell is not None:
            out["pell_core_pct"] = core_pell
            out["pell_core_n"] = len(core_student_rows(rows))
    mil_rows = military_lob_rows(rows)
    mil_funding = military_funding_pct(rows)
    if mil_funding is not None:
        out["military_funding_pct"] = mil_funding
        out["military_lob_n"] = len(mil_rows)
    return out


def display_transfer_credits(dist: dict[str, float]) -> dict[str, float]:
    """Undergraduate transfer-credit bands; omit Master (graduate-only label)."""
    buckets: dict[str, float] = {}
    for label, pct in dist.items():
        if label == "Master":
            continue
        buckets[label] = buckets.get(label, 0) + pct
    ordered: dict[str, float] = {}
    for key in TRANSFER_UNDERGRAD_ORDER:
        if key in buckets:
            ordered[key] = buckets[key]
    for key, pct in buckets.items():
        if key not in ordered:
            ordered[key] = pct
    return _renormalize(ordered)


def index_vs_baseline(program_pct: float | None, baseline_pct: float | None) -> int | None:
    if program_pct is None or baseline_pct is None or baseline_pct == 0:
        return None
    return round(program_pct / baseline_pct * 100)


def pct_from_dist(dist: dict[str, float], key: str) -> float | None:
    return dist.get(key)


def _renormalize(buckets: dict[str, float]) -> dict[str, float]:
    total = sum(buckets.values())
    if total <= 0:
        return {}
    return {k: round(v / total * 100, 1) for k, v in buckets.items() if v > 0}


def display_gender(dist: dict[str, float]) -> dict[str, float]:
    """Male and female only; drop non-specified and re-scale to 100%."""
    return _renormalize({
        "Male": dist.get("Male", 0),
        "Female": dist.get("Female", 0),
    })


def display_race(dist: dict[str, float]) -> dict[str, float]:
    """Four buckets (short labels): Black, White, Hispanic, Other."""
    buckets = {
        "Black": 0.0,
        "White": 0.0,
        "Hispanic": 0.0,
        "Other": 0.0,
    }
    for label, pct in dist.items():
        if label == "Black or African American":
            buckets["Black"] += pct
        elif label == "White":
            buckets["White"] += pct
        elif label in ("Hispanics of Any Race", "Hispanic"):
            buckets["Hispanic"] += pct
        else:
            buckets["Other"] += pct
    return _renormalize(buckets)


LOB_DISPLAY_LABELS = {
    "Core/Other": "Core",
    "Core": "Core",
    "Full Tuition Grant": "B2B",
    "Military": "Military",
    "Tuition Benefit": "TB",
}

# LOB filters for cross-tab — maps display label to row-filter function
_LOB_FILTER_MAP: list[tuple[str, Any]] = [
    ("Core",     lambda r: (r.get("lineofbusiness") or "").strip() in {"Core", "Core/Other"}),
    ("Military", lambda r: (r.get("lineofbusiness") or "").strip() == "Military"),
    ("B2B",      lambda r: (r.get("lineofbusiness") or "").strip() == "Full Tuition Grant"),
    ("TB",       lambda r: (r.get("lineofbusiness") or "").strip() == "Tuition Benefit"),
]


def gender_by_lob(rows: list[dict], min_n: int = 10) -> dict[str, dict[str, float]]:
    """Female/Male % breakdown within each LOB. Only includes LOBs with >= min_n students."""
    result: dict[str, dict[str, float]] = {}
    for lob_label, filter_fn in _LOB_FILTER_MAP:
        subset = [r for r in rows if filter_fn(r)]
        if len(subset) >= min_n:
            result[lob_label] = display_gender(distribution_pct(subset, "gender"))
    return result


def display_lineofbusiness(dist: dict[str, float]) -> dict[str, float]:
    """Short LOB labels: Core, FTG, Military, TB."""
    buckets: dict[str, float] = {}
    for label, pct in dist.items():
        short = LOB_DISPLAY_LABELS.get(label, label)
        buckets[short] = buckets.get(short, 0) + pct
    return _renormalize(buckets)


def display_maritalstatus(dist: dict[str, float]) -> dict[str, float]:
    """Single, married, divorced only."""
    return _renormalize({
        "Single": dist.get("Single", 0),
        "Married": dist.get("Married", 0),
        "Divorced": dist.get("Divorced", 0),
    })


def index_delta_note(program_pct: float | None, baseline_pct: float | None) -> str:
    """Plain-language comparison vs same-level enrolled baseline."""
    if program_pct is None or baseline_pct is None:
        return ""
    diff = program_pct - baseline_pct
    if abs(diff) < 2:
        return "in line with"
    if diff > 0:
        return f"{diff:.0f} pts above"
    return f"{abs(diff):.0f} pts below"
