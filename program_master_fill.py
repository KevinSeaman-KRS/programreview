"""Ensure every MASTER_PROGRAM_IDS row exists in report data (zero-filled if no BQ volume)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Keep in sync with pull_full_data.py until consolidated into one module.
MASTER_PROGRAM_IDS: list[str] = [
    "001Do00000ScUyCIAV", "001Do00000ScUzUIAV", "001Do00000ScUyvIAF",
    "001Do00000ScUyDIAV", "001Do00000ScUyPIAV", "001Do00000ScUzGIAV",
    "001Do00000ScUyQIAV", "001Do00000ScUyEIAV", "001Do00000ScUzHIAV",
    "001Do00000ScUyRIAV", "001Do00000ScUzdIAF", "001Do00000ScUysIAF",
    "001Do00000ScUzeIAF", "001Do00000ScUzfIAF", "001Do00000ScUzgIAF",
    "001Do00000ScUzhIAF", "001Do00000ScUySIAV", "001Do00000ScUzEIAV",
    "001Do00000ScUyeIAF", "001Do00000ScUybIAF", "001Do00000ScUz6IAF",
    "001Do00000ScUyXIAV", "001Do00000ScUzZIAV", "001Do00000ScUyqIAF",
    "001Do00000ScUyTIAV", "001Do00000ScUyUIAV", "001Do00000ScUyVIAV",
    "001Do00000ScUyWIAV", "001Do00000ScUzFIAV", "001Do00000ScUz7IAF",
    "001Do00000ScUyzIAF", "001Do00000ScUzCIAV", "001Do00000ScUyNIAV",
    "001Do00000ScUzIIAV", "001Do00000ScUzJIAV", "001Do00000ScUyaIAF",
    "001Do00000ScUzKIAV", "001Do00000ScUymIAF", "001Vr00000YtotRIAR",
    "001Do00000ScUzbIAF", "001Do00000ScUzcIAF", "001Do00000ScUynIAF",
    "001Do00000ScUzAIAV", "001Do00000ScUy8IAF", "001Do00000ScUz9IAF",
    "001Do00000ScUzSIAV", "001Do00000ScUzTIAV", "001Do00000ScUyZIAV",
    "001Do00000ScUy9IAF", "001Do00000ScUyAIAV", "001Do00000ScUzMIAV",
    "001Do00000ScUylIAF", "001Vr00000t9K7vIAE", "001Do00000ScUz8IAF",
    "001Do00000ScUyBIAV", "001Do00000ScUykIAF", "001Do00000ScUzQIAV",
    "001Do00000ScUzNIAV", "001Do00000ScUzOIAV", "001Do00000YZZzVIAX",
    "001Do00000YZZxZIAX", "001Do00000YZZxjIAH", "001Do00000YZZyXIAX",
    "001Do00000YZZyYIAX", "001Do00000YZZymIAH", "001Do00000YZZz6IAH",
    "001Do00000YZZz7IAH", "001Do00000YZZzGIAX", "001Do00000YZZzHIAX",
]

# Programs where vs-prior shows NEW (launch or prior volume not meaningful).
MATRIX_NEW_PROGRAM_IDS: frozenset[str] = frozenset({
    "001Vr00000YtotRIAR",  # DPS
    "001Vr00000t9K7vIAE",  # MPS
    "001Do00000ScUyEIAV",  # BA in Business Economics
    "001Do00000ScUyeIAF",  # BA in Health and Wellness
})


def apply_matrix_new_flags(programs: list[dict[str, Any]]) -> None:
    for p in programs:
        p["matrix_flag_new"] = p.get("program_id") in MATRIX_NEW_PROGRAM_IDS


def _load_bridge(bridge_path: Path) -> dict[str, dict[str, Any]]:
    if not bridge_path.exists():
        return {}
    data = json.loads(bridge_path.read_text(encoding="utf-8"))
    return {p["program_id"]: p for p in data.get("programs", [])}


def zero_fill_program_row(bridge: dict[str, Any], program_id: str) -> dict[str, Any]:
    name = (
        bridge.get("lead_program_name")
        or bridge.get("full_program_name")
        or program_id
    )
    return {
        "program_id": program_id,
        "program_name": name,
        "degree_level": bridge.get("degree_level") or "Graduate",
        "degree_type": bridge.get("degree_type") or "",
        "leads": 0,
        "apps_started": 0,
        "apps_submitted": 0,
        "decisions": 0,
        "new_enrollments": 0,
        "pct_navigational": None,
        "py_leads": 0,
        "py_apps_started": 0,
        "py_apps_submitted": 0,
        "py_decisions": 0,
        "py_new_enrollments": 0,
        "matrix_flag_new": False,
    }


def fill_missing_master_programs(
    programs: list[dict[str, Any]],
    bridge_path: Path,
    master_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Append zero-metric rows for master IDs missing from BigQuery pull."""
    master = master_ids or MASTER_PROGRAM_IDS
    present = {p["program_id"] for p in programs}
    bridge_by_id = _load_bridge(bridge_path)
    out = list(programs)
    for pid in master:
        if pid in present:
            continue
        bridge = bridge_by_id.get(pid)
        if not bridge:
            continue
        out.append(zero_fill_program_row(bridge, pid))
    return out
