"""Country rings projected through the show camera, plus screen-space shapes."""

from __future__ import annotations

import math

import numpy as np
import skia
from scipy.ndimage import binary_closing, binary_dilation, gaussian_filter

from jt.draw import _ring_paths
from jt.show.basemap import view_for
from jt.show.truesize import km_ring, shift_vertices, shoelace


def fill_ring_list(canvas, rings, cam, rgb, alpha: int, stroke=None, stroke_w: float = 2.2,
                  shadow: float = 0.0, w: int = 1080, h: int = 1920):
    view = view_for(cam, w, h)
    path = skia.Path()
    path.setFillType(skia.PathFillType.kEvenOdd)
    for ring in rings:
        for piece in _ring_paths(np.asarray(ring, np.float64), view):
            if len(piece) < 3:
                continue
            path.moveTo(piece[0][0], piece[0][1])
            for x, y in piece[1:]:
                path.lineTo(x, y)
            path.close()
    if path.countPoints() < 3:
        return
    if shadow > 0.2:
        shade = skia.Paint(AntiAlias=True)
        shade.setColor(skia.ColorSetARGB(int(70 * min(1.0, shadow)), 0, 0, 0))
        canvas.save()
        canvas.translate(5.0 * shadow, 8.0 * shadow)
        canvas.drawPath(path, shade)
        canvas.restore()
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(int(alpha), rgb[0], rgb[1], rgb[2]))
    canvas.drawPath(path, paint)
    if stroke is not None and alpha > 8:
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=stroke_w)
        pen.setColor(skia.ColorSetARGB(255, stroke[0], stroke[1], stroke[2]))
        canvas.drawPath(path, pen)


def fill_iso(canvas, earth, cam, iso: str, rgb, alpha: int, stroke=None, stroke_w: float = 2.2,
             dlon: float = 0.0, dlat: float = 0.0, shadow: float = 0.0, w: int = 1080, h: int = 1920):
    rings = earth.rings.get(iso) or []
    if not rings:
        return
    view = view_for(cam, w, h)
    path = skia.Path()
    path.setFillType(skia.PathFillType.kEvenOdd)
    for ring in rings:
        moved = ring if dlon == 0.0 and dlat == 0.0 else shift_vertices(ring, dlon, dlat)
        for piece in _ring_paths(moved, view):
            if len(piece) < 3:
                continue
            path.moveTo(piece[0][0], piece[0][1])
            for x, y in piece[1:]:
                path.lineTo(x, y)
            path.close()
    if path.countPoints() < 3:
        return
    if shadow > 0.2:
        shade = skia.Paint(AntiAlias=True)
        shade.setColor(skia.ColorSetARGB(int(70 * min(1.0, shadow)), 0, 0, 0))
        canvas.save()
        canvas.translate(5.0 * shadow, 8.0 * shadow)
        canvas.drawPath(path, shade)
        canvas.restore()
    paint = skia.Paint(AntiAlias=True)
    paint.setColor(skia.ColorSetARGB(int(alpha), rgb[0], rgb[1], rgb[2]))
    canvas.drawPath(path, paint)
    if stroke is not None and alpha > 8:
        pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=stroke_w)
        pen.setColor(skia.ColorSetARGB(255, stroke[0], stroke[1], stroke[2]))
        canvas.drawPath(path, pen)


def _path_of(earth, cam, isos, w, h):
    view = view_for(cam, w, h)
    path = skia.Path()
    path.setFillType(skia.PathFillType.kWinding)
    n = 0
    for iso in isos:
        for ring in earth.rings.get(iso) or []:
            for piece in _ring_paths(ring, view):
                if len(piece) < 3:
                    continue
                path.moveTo(piece[0][0], piece[0][1])
                for x, y in piece[1:]:
                    path.lineTo(x, y)
                path.close()
                n += 1
    return path, n


def fill_union(canvas, earth, cam, isos, rgb, alpha: int, outline: int = 6, w: int = 1080, h: int = 1920):
    """One bright fill and a thick white outer coast. Internal borders stay out."""
    path, n = _path_of(earth, cam, isos, w, h)
    if n == 0:
        return
    info = skia.ImageInfo.MakeN32Premul(w, h)
    surf = skia.Surface.MakeRaster(info)
    mc = surf.getCanvas()
    mc.clear(skia.Color4f(0, 0, 0, 0))
    solid = skia.Paint(AntiAlias=True)
    solid.setColor(skia.ColorSetARGB(255, 255, 255, 255))
    mc.drawPath(path, solid)
    mask = surf.makeImageSnapshot().toarray()[:, :, 3] > 48
    closed = binary_closing(mask, iterations=3)
    edge = binary_dilation(closed, iterations=max(3, int(outline))) & ~closed
    edge_a = np.clip(gaussian_filter(edge.astype(np.float32), 0.6), 0, 1)
    fill_a = np.clip(gaussian_filter(closed.astype(np.float32), 0.7), 0, 1)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 0] = 255
    img[..., 1] = 255
    img[..., 2] = 255
    img[..., 3] = (edge_a * 255).astype(np.uint8)
    canvas.drawImage(skia.Image.fromarray(img), 0, 0)
    color = np.zeros((h, w, 4), np.uint8)
    color[..., 0] = rgb[0]
    color[..., 1] = rgb[1]
    color[..., 2] = rgb[2]
    color[..., 3] = (fill_a * alpha).astype(np.uint8)
    canvas.drawImage(skia.Image.fromarray(color), 0, 0)


def fill_many(canvas, earth, cam, isos, rgb, alpha: int, stroke=None, w: int = 1080, h: int = 1920):
    for iso in isos:
        fill_iso(canvas, earth, cam, iso, rgb, alpha, stroke=stroke, stroke_w=1.6, w=w, h=h)


def project_lonlat(cam, lon: float, lat: float, w: int, h: int):
    from jt.project import project_one
    view = view_for(cam, w, h)
    return project_one(lon, lat, view)


class Shape:
    """A country's coastline in local kilometres, scaled to an official area."""

    def __init__(self, polys: list[np.ndarray], area_m2: float):
        self.polys = polys
        self.area_m2 = float(area_m2)
        cx = 0.0
        cy = 0.0
        weight = 0.0
        for poly in polys:
            a = shoelace(poly)
            cx += float(poly[:, 0].mean()) * a
            cy += float(poly[:, 1].mean()) * a
            weight += a
        self.cx = cx / weight if weight else 0.0
        self.cy = cy / weight if weight else 0.0

    def draw(self, canvas, ox: float, oy: float, px_per_m: float, rgb, alpha: int,
             pop: float = 1.0, shadow: float = 1.0, stroke=(255, 255, 255), stroke_w: float = 5.0,
             rot: float = 0.0, under: bool = False):
        if pop <= 0.02 or not self.polys:
            return
        if alpha <= 0 and stroke is None:
            return
        s = px_per_m * pop
        turn = math.radians(rot)
        c, sn = math.cos(turn), math.sin(turn)
        path = skia.Path()
        path.setFillType(skia.PathFillType.kEvenOdd)
        for poly in self.polys:
            dx = (poly[:, 0] - self.cx) * s
            dy = -((poly[:, 1] - self.cy) * s)
            xs = ox + c * dx - sn * dy
            ys = oy + sn * dx + c * dy
            path.moveTo(float(xs[0]), float(ys[0]))
            for x, y in zip(xs[1:], ys[1:]):
                path.lineTo(float(x), float(y))
            path.close()
        blend = skia.BlendMode.kDstOver if under else skia.BlendMode.kSrcOver
        if shadow > 0 and not under:
            shade = skia.Paint(AntiAlias=True)
            shade.setColor(skia.ColorSetARGB(int(80 * shadow), 0, 0, 0))
            canvas.save()
            canvas.translate(6 * shadow, 9 * shadow)
            canvas.drawPath(path, shade)
            canvas.restore()
        paint = skia.Paint(AntiAlias=True)
        paint.setBlendMode(blend)
        paint.setColor(skia.ColorSetARGB(int(alpha), rgb[0], rgb[1], rgb[2]))
        canvas.drawPath(path, paint)
        if stroke is not None:
            pen = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=stroke_w)
            pen.setBlendMode(blend)
            pen.setColor(skia.ColorSetARGB(255, stroke[0], stroke[1], stroke[2]))
            canvas.drawPath(path, pen)


def _keep(ring, maxn=220) -> np.ndarray:
    if len(ring) <= maxn:
        return np.asarray(ring, np.float64)
    step = int(np.ceil(len(ring) / maxn))
    out = np.asarray(ring[::step], np.float64)
    if not np.allclose(out[0], out[-1]):
        out = np.vstack([out, out[:1]])
    return out


def shape_from(earth, iso: str, lon0: float, lat0: float, official_km2: float, pred=None) -> Shape:
    polys = []
    for ring in earth.rings.get(iso) or []:
        if pred is not None and not pred(ring):
            continue
        if len(ring) < 4:
            continue
        polys.append(km_ring(_keep(ring), lon0, lat0))
    measured = sum(shoelace(p) for p in polys)
    target = official_km2 * 1e6
    if measured > 1.0 and polys:
        scale = (target / measured) ** 0.5
        polys = [p * scale for p in polys]
    return Shape(polys, target)


def group_shape(earth, isos, lon0: float, lat0: float, official_km2: float) -> Shape:
    polys = []
    for iso in isos:
        for ring in earth.rings.get(iso) or []:
            if len(ring) < 8:
                continue
            # Drop far-flung specks that blow the silhouette apart.
            if abs(float(ring[:, 0].mean()) - lon0) > 45 or abs(float(ring[:, 1].mean()) - lat0) > 28:
                continue
            polys.append(km_ring(_keep(ring, 140), lon0, lat0))
    measured = sum(shoelace(p) for p in polys)
    target = official_km2 * 1e6
    if measured > 1.0 and polys:
        scale = (target / measured) ** 0.5
        polys = [p * scale for p in polys]
    return Shape(polys, target)
