"""Analyze Cursor usage-events CSV for active time estimates."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

GAP_MINUTES = 45
PADDING_MIN_PER_SESSION = 8

SETUP_CUTOFF_DATE = "2026-05-22"
REPORT_START_DATE = "2026-05-26"
SETUP_CALENDAR_DAYS = frozenset({"2026-05-21", "2026-05-22"})
REPORT_CALENDAR_DAYS = frozenset({"2026-05-26", "2026-05-27"})


def resolve_usage_csv(explicit: Path | None = None) -> Path | None:
    """Find Cursor usage-events export (project data/ or Downloads)."""
    candidates: list[Path] = []
    if explicit and explicit.exists():
        candidates.append(explicit)
    root = Path(__file__).resolve().parents[1]
    candidates.extend(
        [
            root / "data" / "cursor_usage_events.csv",
            root / "cursor_usage_events.csv",
            Path(r"c:\Users\kseaman\Downloads\usage-events-2026-05-27.csv"),
            Path.home() / "Downloads" / "usage-events-2026-05-27.csv",
        ]
    )
    for path in candidates:
        if path.exists():
            return path
    return None


def analyze_usage(csv_path: Path | None = None) -> dict | None:
    """Return token/time summary dict for methodology appendix."""
    path = resolve_usage_csv(csv_path)
    if not path:
        return None

    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ts = datetime.fromisoformat(r["Date"].replace("Z", "+00:00"))
            tokens = int(str(r["Total Tokens"]).replace(",", "") or 0)
            rows.append({"ts": ts, "tokens": tokens, "model": r.get("Model", "")})

    if not rows:
        return None

    rows.sort(key=lambda x: x["ts"])
    total_tokens = sum(r["tokens"] for r in rows)

    by_day: dict[str, dict] = defaultdict(
        lambda: {"events": 0, "tokens": 0, "first": None, "last": None}
    )
    for r in rows:
        d = r["ts"].date().isoformat()
        by_day[d]["events"] += 1
        by_day[d]["tokens"] += r["tokens"]
        if by_day[d]["first"] is None or r["ts"] < by_day[d]["first"]:
            by_day[d]["first"] = r["ts"]
        if by_day[d]["last"] is None or r["ts"] > by_day[d]["last"]:
            by_day[d]["last"] = r["ts"]

    gap = timedelta(minutes=GAP_MINUTES)
    sessions: list[dict] = []
    cur_start = cur_end = rows[0]["ts"]
    cur_events = 1
    cur_tokens = rows[0]["tokens"]
    for r in rows[1:]:
        if r["ts"] - cur_end > gap:
            sessions.append(
                {
                    "start": cur_start,
                    "end": cur_end,
                    "events": cur_events,
                    "tokens": cur_tokens,
                }
            )
            cur_start = cur_end = r["ts"]
            cur_events = 1
            cur_tokens = r["tokens"]
        else:
            cur_end = r["ts"]
            cur_events += 1
            cur_tokens += r["tokens"]
    sessions.append(
        {
            "start": cur_start,
            "end": cur_end,
            "events": cur_events,
            "tokens": cur_tokens,
        }
    )

    def session_hours(s: dict) -> float:
        return (s["end"] - s["start"]).total_seconds() / 3600 + PADDING_MIN_PER_SESSION / 60

    span_total = sum((s["end"] - s["start"]).total_seconds() for s in sessions) / 3600
    active_est = span_total + len(sessions) * (PADDING_MIN_PER_SESSION / 60)

    setup_sess = [s for s in sessions if s["start"].date().isoformat() <= SETUP_CUTOFF_DATE]
    report_sess = [s for s in sessions if s["start"].date().isoformat() >= REPORT_START_DATE]
    setup_h = sum(session_hours(s) for s in setup_sess)
    report_h = sum(session_hours(s) for s in report_sess)

    setup_tok = sum(by_day[d]["tokens"] for d in SETUP_CALENDAR_DAYS if d in by_day)
    report_tok = sum(by_day[d]["tokens"] for d in REPORT_CALENDAR_DAYS if d in by_day)
    other_tok = total_tokens - setup_tok - report_tok

    models: dict[str, int] = defaultdict(int)
    for r in rows:
        if r["model"]:
            models[r["model"]] += r["tokens"]

    return {
        "csv_file": path.name,
        "date_range": f"{rows[0]['ts'].date().isoformat()} – {rows[-1]['ts'].date().isoformat()}",
        "events": len(rows),
        "total_tokens": total_tokens,
        "sessions": len(sessions),
        "active_hours_est": round(active_est, 1),
        "session_span_hours": round(span_total, 1),
        "phases": [
            {
                "label": "Environment & initial build (through May 22)",
                "hours": round(setup_h, 1),
                "tokens": setup_tok,
                "sessions": len(setup_sess),
            },
            {
                "label": "Report refine & deploy (May 26–27)",
                "hours": round(report_h, 1),
                "tokens": report_tok,
                "sessions": len(report_sess),
            },
            {
                "label": "Other days in export (e.g. May 20)",
                "hours": round(max(0.0, active_est - setup_h - report_h), 1),
                "tokens": other_tok,
                "sessions": len(sessions) - len(setup_sess) - len(report_sess),
            },
        ],
        "models": sorted(models.items(), key=lambda x: -x[1])[:6],
        "methodology_note": (
            "Estimated active time = span between first and last agent event per session "
            f"(>{GAP_MINUTES} min gap starts a new session) plus {PADDING_MIN_PER_SESSION} minutes "
            "padding per session. Source: Cursor dashboard usage export (agent events)."
        ),
    }


def main() -> None:
    path = resolve_usage_csv()
    if not path:
        print("No usage CSV found.")
        return
    stats = analyze_usage(path)
    if not stats:
        print("No rows in usage CSV.")
        return
    print(f"File: {path}")
    print(f"Range: {stats['date_range']}")
    print(f"Events: {stats['events']:,}")
    print(f"Total tokens: {stats['total_tokens']:,}")
    print(f"Sessions: {stats['sessions']}")
    print(f"Estimated active time: {stats['active_hours_est']} h")
    for phase in stats["phases"]:
        pct = 100 * phase["tokens"] / stats["total_tokens"] if stats["total_tokens"] else 0
        print(
            f"  {phase['label']}: {phase['tokens']/1e6:.1f}M tok ({pct:.0f}%) "
            f"~ {phase['hours']}h ({phase['sessions']} sessions)"
        )


if __name__ == "__main__":
    main()
