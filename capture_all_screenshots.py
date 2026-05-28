"""
Capture desktop + mobile landing-page screenshots (full-page scroll capture).

Usage:
  uvx --with playwright --with pillow python capture_all_screenshots.py
  uvx --with playwright --with pillow python capture_all_screenshots.py --samples
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
from pathlib import Path

from PIL import Image
from playwright.async_api import Frame, Page, async_playwright

from report_html_sections import (
    GRADUATE_TOTAL_ID,
    LEVEL_DETAIL_URLS,
    LEVEL_DETAIL_LABELS,
    UNDERGRAD_TOTAL_ID,
)
from report_periods import SAMPLE_DETAIL_PROGRAM_IDS

PROGRAMS_WITH_URLS = [
    ("001Do00000ScUyCIAV", "AA in Business", "https://www.uagc.edu/online-degrees/associate/business"),
    ("001Do00000ScUzUIAV", "AA in Early Childhood Education", "https://www.uagc.edu/online-degrees/associate/early-childhood-education"),
    ("001Do00000ScUyvIAF", "AA in Military Studies", "https://www.uagc.edu/online-degrees/associate/military-studies"),
    ("001Do00000ScUyDIAV", "AA in Organizational Management", "https://www.uagc.edu/online-degrees/associate/organizational-management"),
    ("001Do00000ScUyPIAV", "BA in Accounting", "https://www.uagc.edu/online-degrees/bachelors/accounting"),
    ("001Do00000ScUzGIAV", "BA in Applied Behavioral Science", "https://www.uagc.edu/online-degrees/bachelors/applied-behavioral-science"),
    ("001Do00000ScUyQIAV", "BA in Business Administration", "https://www.uagc.edu/online-degrees/bachelors/business-administration"),
    ("001Do00000ScUyEIAV", "BA in Business Economics", "https://www.uagc.edu/online-degrees/bachelors/business-economics"),
    ("001Do00000ScUzHIAV", "BA in Business Information Systems", "https://www.uagc.edu/online-degrees/bachelors/business-information-systems"),
    ("001Do00000ScUyRIAV", "BA in Business Leadership", "https://www.uagc.edu/online-degrees/bachelors/business-leadership"),
    ("001Do00000ScUzdIAF", "BA in Child Development", "https://www.uagc.edu/online-degrees/bachelors/child-development"),
    ("001Do00000ScUysIAF", "BA in Communication Studies", "https://www.uagc.edu/online-degrees/bachelors/communication-studies"),
    ("001Do00000ScUzeIAF", "BA in Early Childhood Development with Differentiated Instruction", "https://www.uagc.edu/online-degrees/bachelors/early-childhood-development-differentiated-instruction"),
    ("001Do00000ScUzfIAF", "BA in Early Childhood Education", "https://www.uagc.edu/online-degrees/bachelors/early-childhood-education"),
    ("001Do00000ScUzgIAF", "BA in Early Childhood Education Administration", "https://www.uagc.edu/online-degrees/bachelors/early-childhood-education-administration"),
    ("001Do00000ScUzhIAF", "BA in Education Studies", "https://www.uagc.edu/online-degrees/bachelors/education-studies"),
    ("001Do00000ScUySIAV", "BA in Finance", "https://www.uagc.edu/online-degrees/bachelors/finance"),
    ("001Do00000ScUzEIAV", "BA in Health & Human Services", "https://www.uagc.edu/online-degrees/bachelors/health-human-services"),
    ("001Do00000ScUyeIAF", "BA in Health and Wellness", "https://www.uagc.edu/online-degrees/bachelors/health-and-wellness"),
    ("001Do00000ScUybIAF", "BA in Health Care Administration", "https://www.uagc.edu/online-degrees/bachelors/health-care-administration"),
    ("001Do00000ScUz6IAF", "BA in Homeland Security and Emergency Management", "https://www.uagc.edu/online-degrees/bachelors/homeland-security-emergency-management"),
    ("001Do00000ScUyXIAV", "BA in Human Resources Management", "https://www.uagc.edu/online-degrees/bachelors/human-resources-management"),
    ("001Do00000ScUzZIAV", "BA in Instructional Design", "https://www.uagc.edu/online-degrees/bachelors/instructional-design"),
    ("001Do00000ScUyqIAF", "BA in Liberal Arts", "https://www.uagc.edu/online-degrees/bachelors/liberal-arts"),
    ("001Do00000ScUyTIAV", "BA in Marketing", "https://www.uagc.edu/online-degrees/bachelors/marketing"),
    ("001Do00000ScUyUIAV", "BA in Operations Management & Analysis", "https://www.uagc.edu/online-degrees/bachelors/operations-management-analysis"),
    ("001Do00000ScUyVIAV", "BA in Organizational Management", "https://www.uagc.edu/online-degrees/bachelors/organizational-management"),
    ("001Do00000ScUyWIAV", "BA in Project Management", "https://www.uagc.edu/online-degrees/bachelors/project-management"),
    ("001Do00000ScUzFIAV", "BA in Psychology", "https://www.uagc.edu/online-degrees/bachelors/psychology"),
    ("001Do00000ScUz7IAF", "BA in Social and Criminal Justice", "https://www.uagc.edu/online-degrees/bachelors/criminal-justice"),
    ("001Do00000ScUyzIAF", "BA in Social Science", "https://www.uagc.edu/online-degrees/bachelors/social-science"),
    ("001Do00000ScUzCIAV", "BA in Sociology", "https://www.uagc.edu/online-degrees/bachelors/sociology"),
    ("001Do00000ScUyNIAV", "BA in Supply Chain Management", "https://www.uagc.edu/online-degrees/bachelors/supply-chain-management"),
    ("001Do00000ScUzIIAV", "BS in Computer Software Technology", "https://www.uagc.edu/online-degrees/bachelors/computer-software-technology"),
    ("001Do00000ScUzJIAV", "BS in Cyber & Data Security Technology", "https://www.uagc.edu/online-degrees/bachelors/cyber-data-security-technology"),
    ("001Do00000ScUyaIAF", "BS in Health Information Management", "https://www.uagc.edu/online-degrees/bachelors/health-information-management"),
    ("001Do00000ScUzKIAV", "BS in Information Technology", "https://www.uagc.edu/online-degrees/bachelors/information-technology"),
    ("001Do00000ScUymIAF", "BS in Nursing", "https://www.uagc.edu/online-degrees/bachelors/nursing"),
    ("001Vr00000YtotRIAR", "DPS in Organizational Leadership", "https://www.uagc.edu/online-degrees/doctoral/organizational-leadership"),
    ("001Do00000ScUzbIAF", "MA in Early Childhood Education Leadership", "https://www.uagc.edu/online-degrees/masters/early-childhood-education-leadership"),
    ("001Do00000ScUzcIAF", "MA in Education", "https://www.uagc.edu/online-degrees/masters/education"),
    ("001Do00000ScUynIAF", "MA in Health Care Administration", "https://www.uagc.edu/online-degrees/masters/health-care-administration"),
    ("001Do00000ScUzAIAV", "MA in Human Services", "https://www.uagc.edu/online-degrees/masters/human-services"),
    ("001Do00000ScUy8IAF", "MA in Organizational Management", "https://www.uagc.edu/online-degrees/masters/organizational-management"),
    ("001Do00000ScUz9IAF", "MA in Psychology", "https://www.uagc.edu/online-degrees/masters/psychology"),
    ("001Do00000ScUzSIAV", "MA in Special Education", "https://www.uagc.edu/online-degrees/masters/special-education"),
    ("001Do00000ScUzTIAV", "MA in Teaching and Learning with Technology", "https://www.uagc.edu/online-degrees/masters/teaching-and-learning-with-technology"),
    ("001Do00000ScUyZIAV", "Master of Accountancy", "https://www.uagc.edu/online-degrees/masters/accounting"),
    ("001Do00000ScUy9IAF", "Master of Business Administration", "https://www.uagc.edu/online-degrees/masters/business-administration"),
    ("001Do00000ScUyAIAV", "Master of Human Resource Management", "https://www.uagc.edu/online-degrees/masters/human-resources-management"),
    ("001Do00000ScUzMIAV", "Master of Information Systems Management", "https://www.uagc.edu/online-degrees/masters/information-systems-management"),
    ("001Do00000ScUylIAF", "Master of Public Health", "https://www.uagc.edu/online-degrees/masters/public-health"),
    ("001Vr00000t9K7vIAE", "MPS in Leadership", "https://www.uagc.edu/online-degrees/masters/leadership"),
    ("001Do00000ScUz8IAF", "MS in Criminal Justice", "https://www.uagc.edu/online-degrees/masters/criminal-justice"),
    ("001Do00000ScUyBIAV", "MS in Finance", "https://www.uagc.edu/online-degrees/masters/finance"),
    ("001Do00000ScUykIAF", "MS in Health Informatics and Analytics", "https://www.uagc.edu/online-degrees/masters/health-informatics-analytics"),
    ("001Do00000ScUzQIAV", "MS in Instructional Design and Technology", "https://www.uagc.edu/online-degrees/masters/instructional-design-technology"),
    ("001Do00000ScUzNIAV", "MS in Technology Management", "https://www.uagc.edu/online-degrees/masters/technology-management"),
    ("001Do00000ScUzOIAV", "Post Baccalaureate Teaching Certificate", "https://www.uagc.edu/online-degrees/certificates/post-baccalaureate-teaching"),
    ("001Do00000YZZzVIAX", "Undecided - Bachelors", "https://www.uagc.edu/online-degrees/bachelors"),
    ("001Do00000YZZxZIAX", "Undecided - Business", "https://www.uagc.edu/online-degrees/business"),
    ("001Do00000YZZxjIAH", "Undecided - Criminal Justice", "https://www.uagc.edu/online-degrees/criminal-justice"),
    ("001Do00000YZZyXIAX", "Undecided - Education", "https://www.uagc.edu/online-degrees/education"),
    ("001Do00000YZZyYIAX", "Undecided - Health Care", "https://www.uagc.edu/online-degrees/health-care"),
    ("001Do00000YZZymIAH", "Undecided - Information Technology", "https://www.uagc.edu/online-degrees/information-technology"),
    ("001Do00000YZZz6IAH", "Undecided - Liberal Arts", "https://www.uagc.edu/online-degrees/liberal-arts"),
    ("001Do00000YZZz7IAH", "Undecided - Masters", "https://www.uagc.edu/online-degrees/masters"),
    ("001Do00000YZZzGIAX", "Undecided - Social & Behavioral Science", "https://www.uagc.edu/online-degrees/social-behavioral-science"),
    ("001Do00000YZZzHIAX", "Undecided - Undecided", "https://www.uagc.edu/online-degrees"),
]

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "screenshots"

LEVEL_LANDING_CAPTURES = [
    (UNDERGRAD_TOTAL_ID, LEVEL_DETAIL_LABELS[UNDERGRAD_TOTAL_ID], LEVEL_DETAIL_URLS[UNDERGRAD_TOTAL_ID]),
    (GRADUATE_TOTAL_ID, LEVEL_DETAIL_LABELS[GRADUATE_TOTAL_ID], LEVEL_DETAIL_URLS[GRADUATE_TOTAL_ID]),
]

DESKTOP_SIZE = (1440, 900)
MOBILE_SIZE = (390, 844)
VIEWPORT_PAGES = 2
SCROLL_OVERLAP = 0.08
MAX_FULL_PAGE_HEIGHT = 16000  # cap stitched height for very long pages

CAREER_IFRAME_SELECTORS = (
    'iframe[src*="lightcast"]',
    'iframe[src*="Lightcast"]',
    'iframe[src*="emsicdn"]',
    'iframe[src*="emsi"]',
    'iframe[src*="career"]',
    'iframe[title*="Career"]',
    'iframe[title*="career"]',
    'iframe[id*="career"]',
    'iframe[name*="career"]',
)

FRAME_CONTENT_PROBES = (
    "Earnings Potential",
    "Projected Outlook",
    "Job Openings",
    "Hard Skills",
    "Lightcast",
    "POWERED BY",
    "Medical and Health",
)


def page_filenames(device: str, pid: str) -> list[str]:
    base = f"{device}_{pid}"
    return [f"{base}.png", f"{base}_page2.png"]


async def lazy_scroll_page(page: Page) -> None:
    """Scroll the full document to trigger lazy-loaded sections and iframes."""
    await page.evaluate(
        """async () => {
            const delay = (ms) => new Promise((r) => setTimeout(r, ms));
            const step = Math.max(350, Math.floor(window.innerHeight * 0.65));
            const maxY = document.documentElement.scrollHeight;
            for (let y = 0; y <= maxY; y += step) {
                window.scrollTo(0, y);
                await delay(250);
            }
            window.scrollTo(0, document.documentElement.scrollHeight);
            await delay(400);
            window.scrollTo(0, 0);
            await delay(300);
        }"""
    )


async def career_section_scroll_y(page: Page) -> int | None:
    """Y offset to frame the Careers / Lightcast embed in the viewport."""
    y = await page.evaluate(
        """() => {
            const pick = (el) => {
                if (!el) return null;
                const top = el.getBoundingClientRect().top + window.scrollY;
                return Math.max(0, Math.round(top - 72));
            };
            const heading = Array.from(document.querySelectorAll('h2, h3, h4'))
                .find((el) => /careers related/i.test(el.textContent || ''));
            if (heading) return pick(heading);
            const iframe = document.querySelector(
                'iframe[src*="lightcast"], iframe[src*="emsicdn"], iframe[src*="career"]'
            );
            return pick(iframe);
        }"""
    )
    return int(y) if y is not None else None


async def _wait_for_frame_content(frame: Frame) -> bool:
    await frame.wait_for_load_state("domcontentloaded", timeout=25000)
    try:
        await frame.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    for probe in FRAME_CONTENT_PROBES:
        try:
            await frame.get_by_text(probe, exact=False).first.wait_for(
                state="visible",
                timeout=12000,
            )
            return True
        except Exception:
            continue
    return False


async def wait_for_career_embeds(page: Page) -> bool:
    """Scroll to the Lightcast careers iframe and wait until content paints."""
    heading = page.get_by_text("Careers Related", exact=False).first
    try:
        if await heading.count() > 0:
            await heading.scroll_into_view_if_needed(timeout=15000)
            await page.wait_for_timeout(600)
    except Exception:
        pass

    for sel in CAREER_IFRAME_SELECTORS:
        loc = page.locator(sel).first
        try:
            if await loc.count() == 0:
                continue
            await loc.scroll_into_view_if_needed(timeout=15000)
            await loc.wait_for(state="attached", timeout=15000)
            box = await loc.bounding_box()
            if not box or box.get("height", 0) < 40:
                await page.wait_for_timeout(1500)
            frame = loc.content_frame()
            if frame is not None:
                if await _wait_for_frame_content(frame):
                    await page.wait_for_timeout(2000)
                    return True
            await page.wait_for_timeout(2500)
            return True
        except Exception:
            continue
    return False


async def dismiss_overlays(page: Page) -> None:
    """Close cookie/consent banners when present."""
    selectors = [
        'button:has-text("Accept")',
        'button:has-text("Accept All")',
        'button:has-text("I Agree")',
        'button:has-text("Got it")',
        '[aria-label="Close"]',
        'button.onetrust-close-btn-handler',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=800):
                await loc.click(timeout=2000)
                await page.wait_for_timeout(400)
        except Exception:
            pass


async def capture_landing_screenshots(
    page: Page,
    device: str,
    pid: str,
    width: int,
    height: int,
) -> dict[str, str | None]:
    """Viewport hero/mid slices plus one full-page scroll capture."""
    await page.set_viewport_size({"width": width, "height": height})
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)
    await dismiss_overlays(page)
    await lazy_scroll_page(page)
    await wait_for_career_embeds(page)
    career_y = await career_section_scroll_y(page)

    names = page_filenames(device, pid)
    out: dict[str, str | None] = {"page1": None, "page2": None, "full": None}
    scroll_step = int(height * (1 - SCROLL_OVERLAP))

    for i in range(VIEWPORT_PAGES):
        if i == 0:
            y = 0
        elif i == 1 and career_y is not None:
            y = career_y
            await wait_for_career_embeds(page)
        else:
            y = i * scroll_step
        await page.evaluate(f"window.scrollTo(0, {y})")
        await page.wait_for_timeout(900 if i == 1 else 600)
        png = await page.screenshot(full_page=False, type="png")
        im = Image.open(io.BytesIO(png)).convert("RGB")
        path = OUTPUT_DIR / names[i]
        im.save(path, optimize=True)
        out["page1" if i == 0 else "page2"] = names[i]

    await lazy_scroll_page(page)
    await wait_for_career_embeds(page)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(400)
    doc_height = await page.evaluate(
        "() => Math.max("
        "document.body.scrollHeight, document.documentElement.scrollHeight)"
    )
    capture_height = min(int(doc_height), MAX_FULL_PAGE_HEIGHT)
    png = await page.screenshot(full_page=True, type="png")
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.height > capture_height:
        im = im.crop((0, 0, im.width, capture_height))
    full_name = f"{device}_{pid}_full.png"
    im.save(OUTPUT_DIR / full_name, optimize=True)
    out["full"] = full_name
    return out


async def capture_all(programs: list[tuple[str, str, str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        desktop_page = await browser.new_page()
        mobile_page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
            viewport={"width": MOBILE_SIZE[0], "height": MOBILE_SIZE[1]},
            is_mobile=True,
            has_touch=True,
        )

        dw, dh = DESKTOP_SIZE
        print(f"=== DESKTOP ({len(programs)} programs, hero/mid + full-page) ===")
        for i, (pid, name, url) in enumerate(programs):
            print(f"  [{i+1}/{len(programs)}] {name}...", end=" ")
            try:
                await desktop_page.goto(url, wait_until="load", timeout=90000)
                await desktop_page.wait_for_timeout(2500)
                pages = await capture_landing_screenshots(
                    desktop_page, "desktop", pid, dw, dh
                )
                results.setdefault(pid, {})["desktop"] = pages
                print("OK")
            except Exception as exc:
                print(f"ERROR: {exc}")
                results.setdefault(pid, {})["desktop"] = None

        mw, mh = MOBILE_SIZE
        print(f"\n=== MOBILE ({len(programs)} programs) ===")
        for i, (pid, name, url) in enumerate(programs):
            print(f"  [{i+1}/{len(programs)}] {name}...", end=" ")
            try:
                await mobile_page.goto(url, wait_until="load", timeout=90000)
                await mobile_page.wait_for_timeout(2500)
                pages = await capture_landing_screenshots(
                    mobile_page, "mobile", pid, mw, mh
                )
                results.setdefault(pid, {})["mobile"] = pages
                print("OK")
            except Exception as exc:
                print(f"ERROR: {exc}")
                results.setdefault(pid, {})["mobile"] = None

        await browser.close()

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    success = sum(
        1 for v in results.values() if (v.get("desktop") or {}).get("page1")
    )
    print(f"\nDone! {success}/{len(programs)} desktop captures.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture UAGC program landing pages")
    parser.add_argument(
        "--samples",
        action="store_true",
        help="Only capture SAMPLE_DETAIL_PROGRAM_IDS (detail report pages)",
    )
    args = parser.parse_args()
    programs = PROGRAMS_WITH_URLS
    if args.samples:
        programs = [t for t in PROGRAMS_WITH_URLS if t[0] in SAMPLE_DETAIL_PROGRAM_IDS]
        programs = LEVEL_LANDING_CAPTURES + programs
        print(f"Sample-only mode: {len(programs)} programs (incl. level totals)")
    else:
        programs = LEVEL_LANDING_CAPTURES + list(PROGRAMS_WITH_URLS)
    asyncio.run(capture_all(programs))


if __name__ == "__main__":
    main()
