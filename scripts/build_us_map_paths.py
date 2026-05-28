"""Build contiguous-US SVG paths from state GeoJSON (run to refresh report_us_region_map.py)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, box, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
GEOJSON = ROOT / "data" / "us-states-110m.json"
OUT_PY = ROOT / "report_us_region_map.py"

# report_regions uses abbreviations
REGION_ABBR: dict[str, set[str]] = {
    "Southwest": {"AZ", "NM", "NV", "UT", "CO", "OK", "TX"},
    "Southeast": {
        "FL", "GA", "AL", "MS", "LA", "SC", "NC", "TN", "KY", "VA", "AR", "WV",
    },
    "West": {"CA", "OR", "WA", "ID", "MT", "WY"},
    "Northeast": {
        "NY", "NJ", "PA", "MA", "CT", "RI", "NH", "VT", "ME", "MD", "DE", "DC",
    },
    "Midwest": {
        "IL", "IN", "OH", "MI", "WI", "MN", "IA", "MO", "ND", "SD", "NE", "KS",
    },
}

NAME_TO_ABBR = {
    "Alabama": "AL",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

CONUS_BOX = box(-125, 24.5, -66, 49.5)
CANVAS_W, CANVAS_H = 1000, 520
PAD = 10


def load_states() -> gpd.GeoDataFrame:
    gj = json.loads(GEOJSON.read_text(encoding="utf-8"))
    rows = []
    for feat in gj["features"]:
        name = feat["properties"]["name"]
        if name in ("Alaska", "Hawaii"):
            continue
        abbr = NAME_TO_ABBR.get(name)
        if not abbr:
            continue
        rows.append(
            {"name": name, "abbr": abbr, "geometry": shape(feat["geometry"])}
        )
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


def project_bounds(bounds: tuple[float, float, float, float]) -> tuple:
    minx, miny, maxx, maxy = bounds

    def tx(x: float) -> float:
        return PAD + (x - minx) / (maxx - minx) * (CANVAS_W - 2 * PAD)

    def ty(y: float) -> float:
        return PAD + (maxy - y) / (maxy - miny) * (CANVAS_H - 2 * PAD)

    return tx, ty


def path_from_geom(geom, tx, ty, simplify: float = 0.22) -> str:
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda p: p.area)
    if geom.geom_type != "Polygon":
        return ""
    line = LineString(geom.exterior.coords).simplify(simplify, preserve_topology=True)
    coords = list(line.coords)
    if len(coords) < 3:
        return ""
    parts = [f"M {tx(coords[0][0]):.1f} {ty(coords[0][1]):.1f}"]
    for x, y in coords[1:]:
        parts.append(f"L {tx(x):.1f} {ty(y):.1f}")
    parts.append("Z")
    return " ".join(parts)


def wrap_path(s: str, indent: int = 4) -> str:
    """Python literal for SVG path (single quoted string)."""
    return repr(s)


def main() -> None:
    states = load_states()
    conus = unary_union(states.geometry).intersection(CONUS_BOX)
    if conus.geom_type == "MultiPolygon":
        conus = max(conus.geoms, key=lambda p: p.area)

    tx, ty = project_bounds(conus.bounds)
    outline = path_from_geom(conus, tx, ty, simplify=0.18)

    region_paths: dict[str, str] = {}
    region_pins: dict[str, tuple[float, float]] = {}
    for region, abbrs in REGION_ABBR.items():
        polys = states[states["abbr"].isin(abbrs)].geometry
        if polys.empty:
            continue
        merged = unary_union(polys.tolist()).intersection(CONUS_BOX)
        region_paths[region] = path_from_geom(merged, tx, ty, simplify=0.25)
        c = merged.centroid
        region_pins[region] = (round(tx(c.x), 1), round(ty(c.y), 1))

    # State union already includes Great Lakes bays; no overlay cut-out needed.
    lakes = ""
    view_box = f"0 0 {CANVAS_W} {CANVAS_H}"

    pins_pct = {
        region: (
            round(left / CANVAS_W * 100, 1),
            round(top / CANVAS_H * 100, 1),
        )
        for region, (left, top) in region_pins.items()
    }

    tail = OUT_PY.read_text(encoding="utf-8").split("def _fill_for_index", 1)[1]
    header = [
        '"""Sketch-style US regional map for enrollment geography (HTML + inline SVG)."""',
        "from __future__ import annotations",
        "",
        "from report_demographics import index_vs_baseline",
        "",
        "# Contiguous US from state GeoJSON (PublicaMundi us-states).",
        "# Regenerate: uvx --with geopandas --with shapely python scripts/build_us_map_paths.py",
        f"MAP_VIEW_BOX = {view_box!r}",
        f"US_OUTLINE = {wrap_path(outline)}",
        f"US_GREAT_LAKES = {lakes!r}",
        "",
        "REGION_PATHS: dict[str, str] = {",
    ]
    for region in ["West", "Midwest", "Southwest", "Southeast", "Northeast"]:
        d = region_paths.get(region, "")
        header.append(f"    {region!r}: {wrap_path(d)},")
    header.append("}")
    header.append("")
    header.append("REGION_PIN: dict[str, tuple[float, float]] = {")
    for region in ["West", "Midwest", "Southwest", "Southeast", "Northeast"]:
        lx, ty_ = pins_pct[region]
        header.append(f"    {region!r}: ({lx}, {ty_}),")
    header.append("}")
    header.append("")
    OUT_PY.write_text("\n".join(header) + "\n\ndef _fill_for_index" + tail, encoding="utf-8")
    print(f"Wrote {OUT_PY}")
    print("Regions:", {k: len(v) for k, v in region_paths.items()})
    print("Pins:", pins_pct)


if __name__ == "__main__":
    main()
