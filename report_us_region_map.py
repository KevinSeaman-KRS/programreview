"""Sketch-style US regional map for enrollment geography (HTML + inline SVG)."""
from __future__ import annotations

from report_demographics import index_vs_baseline

# Contiguous US from state GeoJSON (PublicaMundi us-states).
# Regenerate: uvx --with geopandas --with shapely python scripts/build_us_map_paths.py
MAP_VIEW_BOX = '0 0 1000 520'
US_OUTLINE = 'M 519.2 417.2 L 514.9 415.6 L 516.1 423.7 L 507.8 432.8 L 497.6 438.2 L 486.1 436.3 L 490.5 441.6 L 484.2 442.3 L 471.6 463.8 L 476.7 492.1 L 471.5 494.2 L 443.5 480.8 L 438.3 461.4 L 405.4 414.5 L 389.7 412.1 L 373.7 430.4 L 352.9 416.9 L 346.3 397.7 L 321.1 373.8 L 290.1 372.6 L 290.1 382.0 L 241.4 382.0 L 177.9 358.1 L 179.5 353.5 L 138.7 357.2 L 132.8 341.5 L 114.2 326.1 L 81.9 317.8 L 79.2 304.4 L 57.7 279.3 L 59.6 269.3 L 48.9 260.2 L 49.1 241.5 L 47.4 246.0 L 40.0 244.0 L 26.5 224.9 L 24.5 206.8 L 15.9 198.0 L 20.9 173.7 L 12.6 144.9 L 19.1 124.9 L 22.9 77.4 L 29.7 74.3 L 20.9 73.0 L 23.8 68.7 L 11.4 40.8 L 11.9 30.7 L 42.4 36.7 L 48.8 52.6 L 52.0 37.9 L 43.1 17.9 L 511.7 17.9 L 515.1 10.2 L 521.3 23.8 L 548.5 25.7 L 572.6 37.7 L 585.0 33.6 L 605.7 38.3 L 586.7 46.2 L 565.0 65.2 L 585.0 60.0 L 584.1 64.2 L 592.1 68.0 L 630.1 49.7 L 633.9 51.2 L 625.7 63.5 L 634.8 61.0 L 645.7 69.7 L 683.0 64.1 L 683.6 69.8 L 698.9 68.8 L 701.2 79.1 L 709.9 80.0 L 689.9 78.6 L 689.1 82.8 L 675.5 77.7 L 653.8 82.6 L 636.2 101.3 L 632.4 109.3 L 649.6 95.8 L 634.6 136.4 L 635.9 155.9 L 642.9 169.5 L 656.6 164.4 L 663.6 147.4 L 658.2 129.3 L 662.8 106.7 L 673.7 97.7 L 675.2 105.5 L 682.1 88.4 L 688.9 84.5 L 712.6 97.4 L 712.4 114.0 L 702.6 127.7 L 719.4 119.5 L 724.1 124.0 L 726.2 149.5 L 721.5 148.7 L 710.3 167.7 L 726.9 174.9 L 783.4 150.7 L 788.4 146.0 L 784.7 136.2 L 820.6 136.0 L 832.9 130.7 L 831.6 116.9 L 856.8 100.0 L 913.2 100.1 L 927.7 91.3 L 938.8 65.4 L 951.9 49.6 L 957.4 55.5 L 968.7 51.8 L 976.2 57.7 L 976.1 86.4 L 981.9 87.9 L 981.4 94.5 L 990.0 104.4 L 965.8 115.8 L 956.0 112.1 L 951.3 122.5 L 934.4 127.6 L 921.9 156.6 L 938.6 168.9 L 916.4 173.0 L 915.9 167.8 L 913.6 175.1 L 876.7 183.0 L 903.1 182.9 L 867.6 190.1 L 869.1 208.3 L 857.3 224.1 L 843.5 211.2 L 853.0 235.3 L 837.3 262.7 L 842.4 245.6 L 831.3 234.3 L 837.3 212.5 L 827.4 228.7 L 830.7 243.4 L 815.7 232.5 L 815.1 237.5 L 832.9 246.9 L 832.2 263.5 L 825.5 263.8 L 837.0 266.8 L 841.0 282.7 L 825.4 287.1 L 840.6 287.1 L 840.7 294.4 L 828.7 300.0 L 832.1 307.6 L 828.5 313.4 L 816.3 314.5 L 803.4 330.2 L 787.0 334.5 L 779.9 347.5 L 753.9 367.6 L 745.2 386.1 L 747.6 413.8 L 768.4 475.5 L 766.5 497.2 L 760.5 508.4 L 750.7 510.0 L 746.0 495.6 L 740.4 495.1 L 734.0 473.8 L 730.8 476.3 L 723.2 462.3 L 728.4 454.0 L 722.8 457.1 L 720.5 453.0 L 724.1 432.3 L 700.6 407.3 L 678.8 415.6 L 668.4 404.6 L 639.0 404.4 L 633.0 395.3 L 630.8 402.9 L 618.8 401.0 L 602.3 408.5 L 611.3 411.9 L 604.3 419.5 L 616.1 426.4 L 613.4 429.9 L 601.7 420.2 L 597.4 426.9 L 585.6 428.3 L 567.1 412.8 L 560.0 419.0 L 544.4 414.1 L 519.2 417.2 Z'
US_GREAT_LAKES = ''

REGION_PATHS: dict[str, str] = {
    'West': 'M 111.7 242.5 L 181.0 306.4 L 189.4 320.7 L 179.4 339.2 L 182.8 352.7 L 138.7 357.2 L 132.8 341.5 L 114.2 326.1 L 81.9 317.8 L 79.2 304.4 L 57.7 279.3 L 59.6 269.3 L 48.9 260.2 L 49.1 241.5 L 40.0 244.0 L 26.5 224.9 L 24.5 206.8 L 15.0 194.3 L 20.9 173.7 L 12.6 144.9 L 22.9 77.4 L 29.7 74.3 L 20.9 73.0 L 11.9 30.7 L 42.4 36.7 L 48.8 52.6 L 52.0 37.9 L 43.1 17.9 L 360.7 17.9 L 360.6 182.7 L 241.9 182.8 L 241.9 162.1 L 89.9 162.3 L 89.9 224.0 L 111.7 242.5 Z',
    'Midwest': 'M 610.0 273.0 L 603.8 285.8 L 592.8 285.8 L 596.6 275.6 L 520.8 275.5 L 520.8 265.2 L 394.7 265.3 L 394.6 182.7 L 360.6 182.7 L 360.7 17.9 L 511.7 17.9 L 515.1 10.2 L 521.3 23.8 L 605.7 38.3 L 565.0 65.2 L 585.0 60.0 L 592.1 68.0 L 630.1 49.7 L 625.7 63.5 L 655.3 70.7 L 683.0 64.1 L 708.2 77.8 L 647.2 86.7 L 632.4 109.3 L 649.6 95.8 L 634.6 136.4 L 635.9 155.9 L 642.9 169.5 L 656.6 164.4 L 663.6 147.4 L 658.2 129.3 L 662.8 106.7 L 673.7 97.7 L 675.2 105.5 L 685.1 84.7 L 697.4 87.2 L 712.6 97.4 L 712.4 114.0 L 702.6 127.7 L 722.3 121.1 L 728.0 142.1 L 710.3 167.7 L 726.9 174.9 L 760.2 162.6 L 754.9 209.3 L 734.4 223.4 L 729.4 235.4 L 687.2 221.9 L 666.4 245.4 L 634.3 246.8 L 610.0 273.0 Z',
    'Southwest': 'M 528.2 335.4 L 530.6 368.4 L 539.1 385.7 L 534.0 415.9 L 518.7 413.8 L 507.8 432.8 L 486.1 436.3 L 490.5 441.6 L 471.2 466.5 L 476.7 492.1 L 460.0 490.7 L 443.5 480.8 L 438.3 461.4 L 405.4 414.5 L 389.7 412.1 L 373.7 430.4 L 352.9 416.9 L 346.3 397.7 L 321.1 373.8 L 241.4 382.0 L 177.9 358.1 L 189.4 320.7 L 89.9 224.0 L 89.9 162.3 L 241.9 162.1 L 241.9 182.8 L 394.6 182.7 L 394.7 265.3 L 520.8 265.2 L 523.1 334.5 L 528.2 335.4 Z',
    'Southeast': 'M 747.6 413.8 L 768.4 475.5 L 763.8 504.6 L 750.7 510.0 L 723.2 462.3 L 728.4 454.0 L 720.5 453.0 L 724.1 432.3 L 700.6 407.3 L 678.8 415.6 L 668.4 404.6 L 639.0 404.4 L 633.0 395.3 L 630.8 402.9 L 602.3 408.5 L 611.3 411.9 L 604.3 419.5 L 613.4 429.9 L 601.7 420.2 L 585.6 428.3 L 567.1 412.8 L 560.0 419.0 L 534.0 415.9 L 539.1 385.7 L 530.6 368.4 L 530.6 336.3 L 523.1 334.5 L 520.8 275.5 L 596.6 275.6 L 592.8 285.8 L 603.8 285.8 L 615.7 260.8 L 623.8 263.7 L 634.3 246.8 L 666.4 245.4 L 687.2 221.9 L 729.4 235.4 L 734.4 223.4 L 754.9 209.3 L 760.2 190.2 L 760.2 209.1 L 777.8 209.1 L 777.6 219.7 L 805.7 211.6 L 819.2 228.3 L 815.1 237.5 L 832.9 246.9 L 832.2 263.5 L 825.5 263.8 L 837.0 266.8 L 841.0 282.7 L 825.4 287.1 L 841.7 292.1 L 828.7 300.0 L 828.5 313.4 L 790.7 331.1 L 753.9 367.6 L 745.2 386.1 L 747.6 413.8 Z',
    'Northeast': 'M 842.4 245.6 L 831.3 234.3 L 837.3 212.5 L 827.4 228.7 L 830.7 243.4 L 816.4 237.2 L 819.2 228.3 L 805.7 211.6 L 777.6 219.7 L 777.8 209.1 L 760.2 209.1 L 760.2 162.6 L 788.4 146.0 L 784.7 136.2 L 832.9 130.7 L 831.6 116.9 L 856.8 100.0 L 913.2 100.1 L 927.7 91.3 L 951.9 49.6 L 976.2 57.7 L 976.1 86.4 L 990.0 104.4 L 965.8 115.8 L 956.0 112.1 L 951.3 122.5 L 934.4 127.6 L 921.9 156.6 L 938.6 168.9 L 916.4 173.0 L 915.9 167.8 L 913.6 175.1 L 876.7 183.0 L 903.1 182.9 L 867.6 190.1 L 869.1 208.3 L 857.3 224.1 L 843.5 211.2 L 853.0 235.3 L 842.4 245.6 Z',
}

REGION_PIN: dict[str, tuple[float, float]] = {
    'West': (17.4, 25.2),
    'Midwest': (53.2, 28.6),
    'Southwest': (32.6, 57.4),
    'Southeast': (68.2, 62.9),
    'Northeast': (86.6, 29.0),
}


def _fill_for_index(idx: int, min_idx: int, max_idx: int) -> str:
    """UAGC blue ramp — darker fill for higher index vs degree-level baseline (100)."""
    if max_idx <= min_idx:
        t = 0.5
    else:
        t = (idx - min_idx) / (max_idx - min_idx)
    t = max(0.0, min(1.0, t)) ** 0.85
    r0, g0, b0 = 235, 240, 246
    r1, g1, b1 = 12, 35, 75
    r = int(r0 + (r1 - r0) * t)
    g = int(g0 + (g1 - g0) * t)
    b = int(b0 + (b1 - b0) * t)
    return f"rgb({r},{g},{b})"


def render_us_region_map_html(
    regions: dict[str, float],
    base_regions: dict[str, float],
    *,
    compact: bool = False,
) -> str:
    if not regions:
        return ""

    region_index: dict[str, int] = {}
    for region, pct in regions.items():
        idx = index_vs_baseline(pct, base_regions.get(region))
        if idx is not None:
            region_index[region] = idx
    idx_vals = list(region_index.values())
    min_idx = min(idx_vals) if idx_vals else 100
    max_idx = max(idx_vals) if idx_vals else 100

    sorted_regions = sorted(regions.items(), key=lambda x: -x[1])

    paths_html: list[str] = []
    for region in REGION_PATHS:
        d = REGION_PATHS[region]
        pct = regions.get(region)
        idx = region_index.get(region)
        if pct is not None and idx is not None:
            fill = _fill_for_index(idx, min_idx, max_idx)
            cls = "us-map-region us-map-region--active"
            title = f"{region}: {pct:.1f}% (index {idx})"
        else:
            fill = "#f1f5f9"
            cls = "us-map-region us-map-region--muted"
            title = region
        paths_html.append(
            f'<path class="{cls}" d="{d}" fill="{fill}" '
            f'data-region="{region}" role="img" aria-label="{title}">'
            f"<title>{title}</title></path>"
        )

    pins_html: list[str] = []
    for region, pct in sorted_regions:
        pos = REGION_PIN.get(region)
        if not pos:
            continue
        left, top = pos
        idx = index_vs_baseline(pct, base_regions.get(region))
        idx_html = (
            f'<span class="idx-badge">index {idx}</span>' if idx else ""
        )
        pins_html.append(
            f'<div class="us-map-pin" style="left:{left}%;top:{top}%" '
            f'data-region="{region}">'
            f'<span class="us-map-pin-name">{region}</span>'
            f'<span class="us-map-pin-pct">{pct:.1f}%</span>'
            f"{idx_html}</div>"
        )

    stage_cls = "us-map-stage us-map-stage--compact" if compact else "us-map-stage"
    return (
        f'<div class="{stage_cls}" role="group" aria-label="US enrollment by region">'
        f'<svg class="us-map-sketch" viewBox="{MAP_VIEW_BOX}" '
        'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" '
        'aria-hidden="true">'
        f'<path class="us-map-outline" d="{US_OUTLINE}" fill="#f4f4f3" '
        'stroke="#98A4AE" stroke-width="1.5" stroke-linejoin="round"/>'
        + (
            f'<path class="us-map-lakes" d="{US_GREAT_LAKES}" fill="#f4f4f3" '
            'stroke="#D0D0CE" stroke-width="1"/>'
            if US_GREAT_LAKES
            else ""
        )
        + "".join(paths_html)
        + "</svg>"
        + "".join(pins_html)
        + "</div>"
    )
