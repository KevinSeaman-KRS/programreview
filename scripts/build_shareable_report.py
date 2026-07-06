"""
Build a self-contained HTML report by embedding screenshots as compressed JPEG.

Reads deploy/index.html, finds all <img src="screenshots/..."> references,
compresses the images, embeds them as base64 data URIs, and writes a single
shareable HTML file.

Usage:
    python scripts/build_shareable_report.py
    python scripts/build_shareable_report.py --max-width 800 --quality 70
    python scripts/build_shareable_report.py --include-full   # keep _full and _page2
"""
from __future__ import annotations

import argparse
import base64
import io
import logging
import re
from pathlib import Path

from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "deploy"
HTML_IN = DEPLOY / "index.html"
SCREENSHOT_DIR = DEPLOY / "screenshots"


def compress_image(path: Path, max_width: int, quality: int) -> tuple[str, int, int]:
    """Compress a PNG to JPEG, return (base64_data_uri, original_bytes, new_bytes)."""
    orig_size = path.stat().st_size
    img = Image.open(path)

    if img.mode in ("RGBA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if img.width > max_width:
        ratio = max_width / img.width
        new_h = int(img.height * ratio)
        img = img.resize((max_width, new_h), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    new_size = buf.tell()
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    data_uri = f"data:image/jpeg;base64,{b64}"
    return data_uri, orig_size, new_size


def should_include(filename: str, include_full: bool) -> bool:
    """Decide whether to embed this screenshot or remove the img tag."""
    if include_full:
        return True
    if "_full." in filename or "_page2." in filename:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Build shareable single-file report")
    parser.add_argument("--max-width", type=int, default=900)
    parser.add_argument("--quality", type=int, default=75)
    parser.add_argument("--include-full", action="store_true",
                        help="Include full-page and page2 screenshots (large)")
    parser.add_argument("--no-images", action="store_true",
                        help="Strip all screenshot img tags for a lightweight version")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path (default: deploy/program_report_shareable.html)")
    args = parser.parse_args()

    out_path = Path(args.output) if args.output else DEPLOY / "program_report_shareable.html"

    html = HTML_IN.read_text(encoding="utf-8")
    logger.info("Read %s (%.1f MB)", HTML_IN.name, len(html) / 1e6)

    img_pattern = re.compile(
        r'<img\s+[^>]*src="(screenshots/[^"]+)"[^>]*/?>',
        re.IGNORECASE,
    )
    matches = list(img_pattern.finditer(html))
    logger.info("Found %d screenshot references", len(matches))

    total_orig = 0
    total_new = 0
    embedded = 0
    skipped = 0
    removed = 0

    for match in reversed(matches):
        full_tag = match.group(0)
        src = match.group(1)

        if args.no_images:
            html = html[:match.start()] + "" + html[match.end():]
            removed += 1
            continue

        hero_match = re.search(r'data-hero="(screenshots/[^"]+)"', full_tag)
        if hero_match and not args.include_full:
            chosen_src = hero_match.group(1)
        else:
            chosen_src = src

        img_path = DEPLOY / chosen_src

        if not img_path.exists():
            fallback = DEPLOY / src
            if fallback.exists():
                img_path = fallback
                chosen_src = src
            else:
                logger.warning("  MISSING: %s", chosen_src)
                skipped += 1
                continue

        data_uri, orig, new = compress_image(img_path, args.max_width, args.quality)
        total_orig += orig
        total_new += new
        embedded += 1

        new_tag = re.sub(r'src="[^"]*"', f'src="{data_uri}"', full_tag)
        new_tag = re.sub(r'\s*data-hero="[^"]*"', '', new_tag)
        new_tag = re.sub(r'\s*data-mid="[^"]*"', '', new_tag)
        new_tag = re.sub(r'\s*data-full="[^"]*"', '', new_tag)
        new_tag = re.sub(r'\s*loading="lazy"', '', new_tag)
        html = html[:match.start()] + new_tag + html[match.end():]

        if embedded % 20 == 0:
            logger.info("  Processed %d / %d...", embedded, len(matches))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    final_size = out_path.stat().st_size

    logger.info("\n=== Summary ===")
    logger.info("  Screenshots embedded: %d", embedded)
    logger.info("  Screenshots skipped:  %d (missing)", skipped)
    logger.info("  Original image size:  %.1f MB", total_orig / 1e6)
    logger.info("  Compressed to:        %.1f MB (JPEG %d%%, max %dpx)", total_new / 1e6, args.quality, args.max_width)
    logger.info("  Final HTML size:      %.1f MB", final_size / 1e6)
    logger.info("  Wrote: %s", out_path)


if __name__ == "__main__":
    main()
