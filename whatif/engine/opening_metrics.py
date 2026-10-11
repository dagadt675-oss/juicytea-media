"""Opening-frame measurements shared by the render metric and its tests.

Image y is 0 at the top and 1 at the bottom, matching the zenith reference.
Widths are fractions of frame width. The deck slope is degrees from horizontal
in pixel space (0 would lie across the frame, 90 would run straight down).

Zenith numbers were measured on refs/zenith_opening.jpg (540×960):

- portal outer width where the legs meet the deck, cables excluded: 0.180
- portal height from that row to the top beam: 0.375 of the frame
- deck width at the near bank (image y 0.58): 0.222
- deck width on the lower deck (image y 0.78): 0.300
- deck centerline angle: 56.9°
- deck asphalt, median of the roadway: sRGB (33, 44, 66)
- foreground tree canopies: 0.055 of the frame (the 5–6% band)
"""

from __future__ import annotations

IDX_DECK = 2
IDX_CANOPY = 3
IDX_PORTAL = 11

BANK_Y = 0.58
BOTTOM_Y = 0.78

ZENITH = {
    "portal_outer_width": 0.180,
    "portal_height": 0.375,
    "deck_width_bank": 0.222,
    "deck_width_bottom": 0.300,
    "deck_slope_deg": 56.9,
    "deck_rgb": (33.0, 44.0, 66.0),
    "tree_canopy": 0.055,
}

# Relative error for the bridge numbers. Trees use the 5–6% band instead.
TOLERANCE = 0.05
TREE_BAND = (0.05, 0.06)


def rel_error(got, target):
    if target == 0:
        return 0.0 if got == 0 else 1.0
    return abs(got - target) / abs(target)


def _spans(mask_row, gap):
    import numpy as np

    xs = np.flatnonzero(mask_row)
    if len(xs) == 0:
        return []
    spans = []
    start = prev = int(xs[0])
    for x in xs[1:]:
        x = int(x)
        if x <= prev + gap:
            prev = x
        else:
            spans.append((start, prev))
            start = prev = x
    spans.append((start, prev))
    return spans


def deck_edges(deck, y0=0.54, y1=0.96, gap_frac=0.025):
    """(y, left, right, clipped) for each row of the deck mask.

    `clipped` is true when the run touches the right border, so the right
    edge is the frame and not the deck.
    """
    import numpy as np

    height, width = deck.shape
    gap = max(2, int(round(gap_frac * width)))
    rows = []
    y_start = max(0, int(y0 * height))
    y_stop = min(height, int(y1 * height))
    for y in range(y_start, y_stop):
        spans = [span for span in _spans(deck[y], gap) if span[1] - span[0] > 0.04 * width]
        if not spans:
            continue
        # The bridge is the run that reaches furthest right.
        left, right = max(spans, key=lambda span: span[1])
        if left < 0.40 * width:
            continue
        # A run that ends in the last percent of the frame is cut off by the border.
        clipped = right >= width - max(3, int(0.012 * width))
        rows.append((y / height, left / width, (right + 1) / width, clipped))
    return rows


def _center_fit(edges):
    import numpy as np

    # Only the straight run. Past y≈0.74 the near end is cut by the frame
    # and then by the end of the slab, which bends the centerline.
    open_rows = [
        row
        for row in edges
        if (not row[3]) and 0.54 <= row[0] <= 0.74 and 0.02 < row[1] and row[2] < 0.985
    ]
    if len(open_rows) < 4:
        return None
    ys = np.array([row[0] for row in open_rows])
    cxs = np.array([(row[1] + row[2]) * 0.5 for row in open_rows])
    slope, intercept = np.polyfit(ys, cxs, 1)
    return slope, intercept


def deck_width_at(edges, y_frac, window=0.012):
    """Full deck width at image y, extrapolated when the right edge is clipped."""
    near = [row for row in edges if abs(row[0] - y_frac) <= window]
    open_near = [row for row in near if not row[3]]
    if open_near:
        return sum(row[2] - row[1] for row in open_near) / len(open_near)
    if not near:
        return None
    fit = _center_fit(edges)
    if fit is None:
        return None
    slope, intercept = fit
    center = slope * y_frac + intercept
    left = sum(row[1] for row in near) / len(near)
    return max(0.0, 2.0 * (center - left))


def deck_slope_deg(edges, y0=0.56, y1=0.76):
    """Angle of the deck centerline from horizontal, in pixel space."""
    import math

    import numpy as np

    open_rows = [
        row
        for row in edges
        if (not row[3]) and y0 <= row[0] <= min(y1, 0.74) and row[2] < 0.985
    ]
    if len(open_rows) < 4:
        return None
    # Fit pixel x of the center against pixel y. The frame is 9:16, so a
    # fraction of width and a fraction of height are not the same length.
    ys = np.array([row[0] * 1920.0 for row in open_rows])
    xs = np.array([(row[1] + row[2]) * 0.5 * 1080.0 for row in open_rows])
    dx_dy, _intercept = np.polyfit(ys, xs, 1)
    return math.degrees(math.atan2(1.0, dx_dy))


def portal_at_deck(portal, deck):
    """Outer leg width and height where the portal meets the deck.

    Returns (outer_width, height, contact_y, top_y) as frame fractions.
    """
    import numpy as np

    height, width = portal.shape
    portal_rows = np.flatnonzero(portal.any(axis=1))
    if len(portal_rows) == 0:
        return None
    top = float(portal_rows[0]) / height
    hits = []
    for y in range(height):
        pxs = np.flatnonzero(portal[y])
        dxs = np.flatnonzero(deck[y])
        if len(pxs) < 2 or len(dxs) < 4:
            continue
        deck_center = 0.5 * (int(dxs[0]) + int(dxs[-1]))
        if int(pxs[0]) < deck_center < int(pxs[-1]):
            hits.append((y, (int(pxs[-1]) - int(pxs[0]) + 1) / width))
    if not hits:
        return None
    # The near face of the tower is the lower half of the overlap.
    lower = hits[len(hits) // 2 :]
    outer = float(np.median([item[1] for item in lower]))
    contact = float(np.median([item[0] for item in lower])) / height
    return outer, contact - top, contact, top


def canopy_sizes(mask, min_pixels=12):
    """(center_x, center_y, width) for each canopy component."""
    import numpy as np
    from collections import deque

    height, width = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    found = []
    ys, xs = np.where(mask)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if seen[y0, x0]:
            continue
        queue = deque([(y0, x0)])
        seen[y0, x0] = True
        count = 0
        minx = maxx = x0
        miny = maxy = y0
        while queue:
            y, x = queue.popleft()
            count += 1
            minx = min(minx, x)
            maxx = max(maxx, x)
            miny = min(miny, y)
            maxy = max(maxy, y)
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    if ny < 0 or nx < 0 or ny >= height or nx >= width:
                        continue
                    if seen[ny, nx] or not mask[ny, nx]:
                        continue
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        if count < min_pixels:
            continue
        found.append(
            (
                (minx + maxx) * 0.5 / width,
                (miny + maxy) * 0.5 / height,
                (maxx - minx + 1) / width,
            )
        )
    return found


def foreground_canopy(sizes):
    """Median width of the near park trees, the ones the reference shows at 5–6%."""
    import numpy as np

    near = [size for cx, cy, size in sizes if 0.62 <= cy <= 0.84 and 0.0 <= cx <= 0.55]
    if not near:
        near = [size for _cx, _cy, size in sizes]
    if not near:
        return None
    return float(np.median(near))


def deck_rgb(image, deck, y0=0.57, y1=0.72):
    """Median sRGB of the deck roadway, ignoring lane paint."""
    import numpy as np

    height, width = deck.shape[:2]
    y_a = int(y0 * height)
    y_b = max(y_a + 1, int(y1 * height))
    region = deck[y_a:y_b]
    pixels = image[y_a:y_b][region]
    if len(pixels) == 0:
        return None
    luma = pixels.astype(np.float32).mean(axis=1)
    dark = pixels[luma < 110]
    if len(dark) < 20:
        dark = pixels
    return tuple(float(v) for v in np.median(dark, axis=0))


def color_error(got, target):
    if got is None:
        return None
    return sum(abs(a - b) for a, b in zip(got, target)) / (3.0 * 255.0)


def score(metrics):
    """List of (name, got, target, error, ok). `error` is relative, or absolute for color."""
    rows = []

    def add(name, got, target, error, ok):
        rows.append(
            {
                "name": name,
                "got": got,
                "target": target,
                "error": error,
                "ok": ok,
            }
        )

    checks = (
        ("portal_outer_width", ZENITH["portal_outer_width"]),
        ("portal_height", ZENITH["portal_height"]),
        ("deck_width_bank", ZENITH["deck_width_bank"]),
        ("deck_width_bottom", ZENITH["deck_width_bottom"]),
        ("deck_slope_deg", ZENITH["deck_slope_deg"]),
    )
    for name, target in checks:
        got = metrics.get(name)
        if got is None:
            add(name, None, target, None, False)
            continue
        err = rel_error(got, target)
        add(name, got, target, err, bool(err <= TOLERANCE))
    got_rgb = metrics.get("deck_rgb")
    err = color_error(got_rgb, ZENITH["deck_rgb"])
    add("deck_rgb", got_rgb, ZENITH["deck_rgb"], err, bool(err is not None and err <= TOLERANCE))
    canopy = metrics.get("tree_canopy")
    lo, hi = TREE_BAND
    add(
        "tree_canopy",
        canopy,
        ZENITH["tree_canopy"],
        None if canopy is None else rel_error(canopy, ZENITH["tree_canopy"]),
        bool(canopy is not None and lo <= canopy <= hi),
    )
    return rows


def measure_masks(index, image):
    """index: int array, image: uint8 RGB. Both are top-left origin."""
    import numpy as np

    portal = index == IDX_PORTAL
    deck = index == IDX_DECK
    canopy = index == IDX_CANOPY
    edges = deck_edges(deck)
    portal_stats = portal_at_deck(portal, deck)
    sizes = canopy_sizes(canopy)
    metrics = {
        "deck_width_bank": deck_width_at(edges, BANK_Y),
        "deck_width_bottom": deck_width_at(edges, BOTTOM_Y),
        "deck_slope_deg": deck_slope_deg(edges),
        "deck_rgb": deck_rgb(image, deck) if image is not None else None,
        "tree_canopy": foreground_canopy(sizes),
        "tree_count": len(sizes),
        "portal_outer_width": None if portal_stats is None else portal_stats[0],
        "portal_height": None if portal_stats is None else portal_stats[1],
        "portal_contact_y": None if portal_stats is None else portal_stats[2],
        "portal_top_y": None if portal_stats is None else portal_stats[3],
    }
    metrics["rows"] = score(metrics)
    metrics["passed"] = all(row["ok"] for row in metrics["rows"])
    return metrics
