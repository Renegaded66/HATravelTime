#!/usr/bin/env python3
"""Generate the brand assets (icon/logo, light + dark) for the integration and the add-on.

Home Assistant >= 2026.3 serves brand images from ``custom_components/<domain>/brand/``.
Required file names: icon.png (256x256), icon@2x.png (512x512), logo.png (1024x256),
logo@2x.png (2048x512) and the ``dark_*`` variants. All with a transparent background.

Everything is drawn at 8x and downscaled with LANCZOS, which is why this script only needs
Pillow - no SVG rasterizer, no Inkscape.

Usage:  python3 scripts/generate_brand_assets.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_BRAND = ROOT / "custom_components" / "traveltimefree" / "brand"
ADDON_DIR = ROOT / "addon" / "traveltime"

SUPERSAMPLE = 8

BLUE = (26, 115, 232, 255)
DARK_BLUE = (11, 79, 168, 255)
LIGHT_BLUE = (138, 180, 248, 255)
INK = (31, 41, 55, 255)
DARK_INK = (240, 243, 248, 255)
TILE = (24, 35, 46, 255)

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise SystemExit("Keine passende Schrift gefunden")


def _bezier(p0, p1, p2, p3, steps: int = 240):
    points = []
    for index in range(steps + 1):
        t = index / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def _pin_points(center: tuple[float, float], radius: float, tip_scale: float = 2.05):
    """Return the polygon of a map pin (circle head + tapered tip)."""
    import math

    cx, cy = center
    distance = radius * tip_scale
    tip = (cx, cy + distance)
    angle = math.acos(radius / distance)  # angle between down vector and tangent point
    left = (cx - radius * math.sin(angle), cy + radius * math.cos(angle))
    right = (cx + radius * math.sin(angle), cy + radius * math.cos(angle))
    return [left, right, tip]


def _draw_glyph(size: int, route: tuple, marker: tuple, tile: tuple | None = None) -> Image.Image:
    """Draw the route glyph (start dot -> curved route -> destination pin)."""
    scale = size * SUPERSAMPLE
    image = Image.new("RGBA", (scale, scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if tile is not None:
        draw.rounded_rectangle(
            [(0, 0), (scale - 1, scale - 1)], radius=int(scale * 0.22), fill=tile
        )

    margin = scale * 0.16
    inner = scale - 2 * margin

    def point(x: float, y: float) -> tuple[float, float]:
        return (margin + x * inner, margin + y * inner)

    start = point(0.18, 0.80)
    end = point(0.74, 0.24)
    head_radius = inner * 0.125

    # Route: S-curve between the two markers.
    route_points = _bezier(
        start,
        point(0.18, 0.44),
        point(0.74, 0.60),
        end,
    )
    # Stamp overlapping dots instead of a polyline: the result is a perfectly smooth
    # round-capped stroke, independent of the point density of the curve.
    stroke_radius = inner * 0.050
    for x, y in route_points:
        draw.ellipse(
            [(x - stroke_radius, y - stroke_radius), (x + stroke_radius, y + stroke_radius)],
            fill=route,
        )

    # Start marker: filled dot with a small gap to the line end.
    start_radius = inner * 0.100
    draw.ellipse(
        [
            (start[0] - start_radius, start[1] - start_radius),
            (start[0] + start_radius, start[1] + start_radius),
        ],
        fill=marker,
    )

    # Destination marker: map pin with a hole.
    draw.polygon(_pin_points(end, head_radius), fill=marker)
    draw.ellipse(
        [(end[0] - head_radius, end[1] - head_radius), (end[0] + head_radius, end[1] + head_radius)],
        fill=marker,
    )
    hole = head_radius * 0.42
    draw.ellipse(
        [(end[0] - hole, end[1] - hole), (end[0] + hole, end[1] + hole)],
        fill=(0, 0, 0, 0),
    )

    return _square(image)


def _square(image: Image.Image, padding: float = 0.06) -> Image.Image:
    """Trim to the visible content and re-pad to a centred square."""
    bbox = image.getbbox()
    if bbox is None:
        return image
    cropped = image.crop(bbox)
    width, height = cropped.size
    side = max(width, height)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(cropped, ((side - width) // 2, (side - height) // 2))
    if padding:
        padded = int(side * (1 + padding * 2))
        result = Image.new("RGBA", (padded, padded), (0, 0, 0, 0))
        offset = (padded - side) // 2
        result.paste(canvas, (offset, offset))
        canvas = result
    return canvas


def icon(size: int, route: tuple, marker: tuple) -> Image.Image:
    return _draw_glyph(size, route, marker).resize((size, size), Image.Resampling.LANCZOS)


def tile_icon(size: int, route: tuple, marker: tuple) -> Image.Image:
    glyph = _draw_glyph(size, route, marker, tile=TILE).resize((size, size), Image.Resampling.LANCZOS)
    return glyph


def logo(width: int, route: tuple, marker: tuple, text_color: tuple) -> Image.Image:
    """Horizontal lockup (glyph + wordmark) on a canvas of exactly width x height.

    Nothing is resized after composing: stretching would distort glyph and letters.
    """
    height = width // 4
    glyph_side = int(height * 0.88)
    glyph = _draw_glyph(glyph_side, route, marker).resize(
        (glyph_side, glyph_side), Image.Resampling.LANCZOS
    )

    font = _font(int(height * 0.40))
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    box = probe.textbbox((0, 0), "Travel Time", font=font)
    text_width, text_height = box[2] - box[0], box[3] - box[1]

    gap = int(height * 0.10)
    total = glyph_side + gap + text_width
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    x0 = (width - total) // 2
    canvas.paste(glyph, (x0, (height - glyph_side) // 2), glyph)
    ImageDraw.Draw(canvas).text(
        (x0 + glyph_side + gap, (height - text_height) // 2 - box[1]),
        "Travel Time",
        font=font,
        fill=text_color,
    )
    return canvas


def main() -> None:
    INTEGRATION_BRAND.mkdir(parents=True, exist_ok=True)

    assets = {
        "icon.png": icon(256, BLUE, DARK_BLUE),
        "icon@2x.png": icon(512, BLUE, DARK_BLUE),
        "dark_icon.png": icon(256, LIGHT_BLUE, LIGHT_BLUE),
        "dark_icon@2x.png": icon(512, LIGHT_BLUE, LIGHT_BLUE),
        "logo.png": logo(1024, BLUE, DARK_BLUE, INK),
        "logo@2x.png": logo(2048, BLUE, DARK_BLUE, INK),
        "dark_logo.png": logo(1024, LIGHT_BLUE, LIGHT_BLUE, DARK_INK),
        "dark_logo@2x.png": logo(2048, LIGHT_BLUE, LIGHT_BLUE, DARK_INK),
    }
    for name, image in assets.items():
        target = INTEGRATION_BRAND / name
        image.save(target, "PNG", optimize=True)
        print(f"{target.relative_to(ROOT)}  {image.width}x{image.height}  {target.stat().st_size / 1024:.1f} kB")

    # Add-on store artwork: full bleed tile + 250x100 logo.
    addon_icon = tile_icon(256, (255, 255, 255, 255), LIGHT_BLUE)
    addon_icon.save(ADDON_DIR / "icon.png", "PNG", optimize=True)
    addon_logo = logo(1000, (255, 255, 255, 255), LIGHT_BLUE, DARK_INK)
    addon_logo.resize((250, 100), Image.Resampling.LANCZOS).save(ADDON_DIR / "logo.png", "PNG", optimize=True)
    print("addon/traveltime/icon.png 256x256")
    print("addon/traveltime/logo.png 250x100")


if __name__ == "__main__":
    main()
