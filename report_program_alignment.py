"""Academic alignment (college / division / department) for program detail pages."""

from __future__ import annotations

import json
from collections import defaultdict
from html import escape as html_escape
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
ALIGNMENT_PATH = ROOT / "data" / "program_alignment.json"


def load_program_alignment(path: Path | None = None) -> dict | None:
    p = path or ALIGNMENT_PATH
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def resolve_alignment_by_program_id(
    programs: list[dict],
    alignment_data: dict | None,
) -> dict[str, dict]:
    if not alignment_data:
        return {}
    by_name = alignment_data.get("by_program_name") or {}
    by_apl = alignment_data.get("by_apl_program_id") or {}
    aliases = alignment_data.get("aliases") or {}
    out: dict[str, dict] = {}
    for prog in programs:
        pid = prog.get("program_id")
        if not pid:
            continue
        name = prog.get("program_name") or ""
        lookup_name = aliases.get(name, name)
        rec = by_name.get(lookup_name)
        if not rec:
            cvue = (prog.get("program_code_cvue") or "").strip().upper()
            if cvue:
                rec = by_apl.get(cvue)
        if rec:
            out[pid] = rec
    return out


def render_academic_alignment_section(rec: dict | None) -> str:
    if not rec or not rec.get("college"):
        return ""
    apl_prog = rec.get("apl_program_id")
    apl_college = rec.get("apl_college_id")
    apl_division = rec.get("apl_division_id")
    apl_dept = rec.get("apl_department_id")

    def row(label: str, value: str | None, code: str | None = None) -> str:
        if not value:
            return ""
        code_bit = ""
        if code:
            code_bit = f' <span class="alignment-code">({html_escape(code)})</span>'
        return (
            f"<dt>{html_escape(label)}</dt>"
            f"<dd>{html_escape(value)}{code_bit}</dd>"
        )

    rows = [
        row("College", rec.get("college"), apl_college),
        row("Division", rec.get("division"), apl_division),
        row("Department", rec.get("department"), apl_dept),
        row("Dean", rec.get("dean")),
        row("Associate dean", rec.get("associate_dean")),
        row("Department head", rec.get("department_head")),
    ]
    body = "".join(r for r in rows if r)
    if not body:
        return ""

    apl_line = ""
    if apl_prog:
        apl_line = (
            f'<p class="alignment-apl">APL program ID: '
            f"<code>{html_escape(apl_prog)}</code></p>"
        )

    return (
        '        <div class="card alignment-card">\n'
        "            <h4>Academic alignment</h4>\n"
        f"{apl_line}"
        f'            <dl class="alignment-dl">{body}</dl>\n'
        "        </div>\n\n"
    )


def _sort_key(text: str | None) -> str:
    return (text or "").casefold()


def build_leadership_tree(
    detail_programs: list[dict],
    alignment_by_pid: dict[str, dict],
) -> tuple[dict[str, dict[str, dict[str, list[dict]]]], list[dict]]:
    """
    Nest programs under dean → associate dean → department head.

    Returns (tree, unmapped_programs) for programs lacking alignment rows.
    """
    tree: dict[str, dict[str, dict[str, list[dict]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    unmapped: list[dict] = []
    for prog in detail_programs:
        rec = alignment_by_pid.get(prog.get("program_id", ""))
        if not rec:
            unmapped.append(prog)
            continue
        dean = rec.get("dean") or "—"
        ad = rec.get("associate_dean") or "—"
        dh = rec.get("department_head") or "—"
        tree[dean][ad][dh].append(prog)
    for dean in tree:
        for ad in tree[dean]:
            for dh in tree[dean][ad]:
                tree[dean][ad][dh].sort(
                    key=lambda p: _sort_key(p.get("program_name"))
                )
    return tree, unmapped


def render_organization_nav_tab(
    detail_programs: list[dict],
    alignment_by_pid: dict[str, dict],
    *,
    make_anchor: Callable[[str], str],
    level_detail_links: list[tuple[str, str]],
    undecided_label: str | None = None,
    section_links: list[tuple[str, str]] | None = None,
) -> str:
    """Summary tab: dean → associate dean → department head → program detail links."""
    tree, unmapped = build_leadership_tree(detail_programs, alignment_by_pid)
    if not tree and not unmapped:
        return (
            '<div id="tab-organization" class="tab-content">\n'
            '<p class="org-nav-empty">Academic alignment data not loaded. '
            "Run <code>scripts/build_program_alignment.py</code> first.</p>\n"
            "</div>\n"
        )

    h = '<div id="tab-organization" class="tab-content">\n'
    h += (
        '<p class="matrix-legend org-nav-intro">'
        "<strong>Dean → associate dean → department head → program.</strong> "
        "Expand or collapse sections; links jump to program detail pages below. "
        "Source: Program Alignment List workbook.</p>\n"
    )

    if level_detail_links or section_links or undecided_label:
        h += '<div class="org-nav-jumps">\n'
        if level_detail_links:
            h += '<span class="org-nav-jumps-label">Level rollups:</span> '
            h += " · ".join(
                f'<a href="#{html_escape(anchor)}">{html_escape(label)}</a>'
                for label, anchor in level_detail_links
            )
            h += "\n"
        if undecided_label:
            h += (
                f'<span class="org-nav-jumps-label"> · Placeholders:</span> '
                f'<a href="#{html_escape(make_anchor(undecided_label))}">'
                f"{html_escape(undecided_label)}</a>\n"
            )
        if section_links:
            h += '<span class="org-nav-jumps-label"> · Sections:</span> '
            h += " · ".join(
                f'<a href="#{html_escape(anchor)}">{html_escape(label)}</a>'
                for label, anchor in section_links
            )
            h += "\n"
        h += "</div>\n"

    h += '<div class="org-nav-tree">\n'
    for dean in sorted(tree.keys(), key=_sort_key):
        dean_count = sum(
            len(progs)
            for ad in tree[dean].values()
            for progs in ad.values()
        )
        h += (
            f'<details class="org-nav-dean" open>'
            f'<summary>{html_escape(dean)}'
            f' <span class="org-nav-count">({dean_count} programs)</span></summary>\n'
        )
        for ad in sorted(tree[dean].keys(), key=_sort_key):
            ad_count = sum(len(progs) for progs in tree[dean][ad].values())
            h += (
                f'<details class="org-nav-ad" open>'
                f'<summary>{html_escape(ad)}'
                f' <span class="org-nav-count">({ad_count})</span></summary>\n'
            )
            for dh in sorted(tree[dean][ad].keys(), key=_sort_key):
                progs = tree[dean][ad][dh]
                h += (
                    f'<div class="org-nav-dh-block">'
                    f'<div class="org-nav-dh">{html_escape(dh)}</div>\n'
                    '<ul class="org-nav-programs">\n'
                )
                for prog in progs:
                    name = prog.get("program_name") or ""
                    anchor = make_anchor(name)
                    h += (
                        f'<li><a href="#{html_escape(anchor)}">'
                        f"{html_escape(name)}</a></li>\n"
                    )
                h += "</ul></div>\n"
            h += "</details>\n"
        h += "</details>\n"
    h += "</div>\n"

    if unmapped:
        unmapped.sort(key=lambda p: _sort_key(p.get("program_name")))
        h += (
            '<details class="org-nav-unmapped">'
            f'<summary>Programs without alignment mapping '
            f"({len(unmapped)})</summary>\n"
            '<ul class="org-nav-programs">\n'
        )
        for prog in unmapped:
            name = prog.get("program_name") or ""
            anchor = make_anchor(name)
            h += (
                f'<li><a href="#{html_escape(anchor)}">'
                f"{html_escape(name)}</a></li>\n"
            )
        h += "</ul></details>\n"

    h += "</div>\n"
    return h
