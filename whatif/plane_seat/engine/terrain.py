"""One continuous ground for the route.

Heights come from the SRTM tile N45E007 and from scanned displacement
maps. Blend edges follow the luminance of a coast photograph, so a
boundary wanders by hundreds of metres instead of cutting in a straight
line. No procedural noise.
"""

from __future__ import annotations

import gzip
import struct
from pathlib import Path

import bpy

TEX = Path("/workspace/assets/found/textures")
ROUTE_TEX = TEX / "route"
HGT_PATH = Path("/workspace/assets/found/terrain/N45E007.hgt.gz")
SCANS = Path("/workspace/assets/found/terrain/polyhaven")

ROUTE = 12000.0


def _smooth(a, b, x):
    if b <= a:
        return 0.0 if x < a else 1.0
    u = max(0.0, min(1.0, (x - a) / (b - a)))
    return u * u * (3.0 - 2.0 * u)


class _Image:
    """Greyscale sample of a scan. Pixels come from Blender, not PIL."""

    def __init__(self, path: Path):
        image = bpy.data.images.load(str(path), check_existing=True)
        self.w, self.h = int(image.size[0]), int(image.size[1])
        # Blender stores floats, bottom row first, RGBA.
        raw = image.pixels[:]
        self.px = raw[0::4]
        # A coarse copy keeps blend edges and dune bodies in the broad forms
        # of the scan. The full image stays on the shader for surface detail.
        n = 28
        bins = [0.0] * (n * n)
        counts = [0] * (n * n)
        for y in range(self.h):
            iy = min(n - 1, y * n // self.h)
            row = y * self.w
            for x in range(self.w):
                ix = min(n - 1, x * n // self.w)
                slot = iy * n + ix
                bins[slot] += self.px[row + x]
                counts[slot] += 1
        self.coarse = [bins[i] / counts[i] if counts[i] else 0.0 for i in range(n * n)]
        self.cn = n

    def sample_coarse(self, u, v):
        u = u % 1.0
        v = v % 1.0
        x = u * (self.cn - 1)
        y = v * (self.cn - 1)
        x0 = int(x)
        y0 = int(y)
        x1 = min(self.cn - 1, x0 + 1)
        y1 = min(self.cn - 1, y0 + 1)
        tx = x - x0
        ty = y - y0

        def at(ix, iy):
            return self.coarse[iy * self.cn + ix]

        return (
            at(x0, y0) * (1 - tx) * (1 - ty)
            + at(x1, y0) * tx * (1 - ty)
            + at(x0, y1) * (1 - tx) * ty
            + at(x1, y1) * tx * ty
        )

    def sample(self, u, v):
        u = u % 1.0
        v = v % 1.0
        x = u * (self.w - 1)
        y = v * (self.h - 1)
        x0 = int(x)
        y0 = int(y)
        x1 = min(self.w - 1, x0 + 1)
        y1 = min(self.h - 1, y0 + 1)
        tx = x - x0
        ty = y - y0

        def at(ix, iy):
            return self.px[iy * self.w + ix]

        return (
            at(x0, y0) * (1 - tx) * (1 - ty)
            + at(x1, y0) * tx * (1 - ty)
            + at(x0, y1) * (1 - tx) * ty
            + at(x1, y1) * tx * ty
        )


class _Hgt:
    def __init__(self, path: Path):
        raw = gzip.open(path, "rb").read()
        self.n = int(round((len(raw) / 2) ** 0.5))
        self.raw = raw
        self.x0, self.y0, self.win_x, self.win_y, self.lo, self.hi = self._window()
        print(
            "hgt window",
            self.x0,
            self.y0,
            "size",
            self.win_x,
            self.win_y,
            "metres",
            self.lo,
            self.hi,
        )

    def _at(self, x, y):
        x = max(0, min(self.n - 1, int(x)))
        y = max(0, min(self.n - 1, int(y)))
        h = struct.unpack_from(">h", self.raw, (y * self.n + x) * 2)[0]
        return h

    def _window(self):
        win_x, win_y = 200, 120
        best = None
        for y0 in range(120, self.n - win_y - 120, 30):
            for x0 in range(120, self.n - win_x - 120, 30):
                vals = []
                for y in range(y0, y0 + win_y, 6):
                    for x in range(x0, x0 + win_x, 6):
                        h = self._at(x, y)
                        if h > -1000:
                            vals.append(h)
                if len(vals) < 80:
                    continue
                vals.sort()
                lo = vals[len(vals) // 10]
                hi = vals[len(vals) * 9 // 10]
                relief = hi - lo
                if best is None or relief > best[0]:
                    best = (relief, x0, y0, lo, hi)
        _relief, x0, y0, lo, hi = best
        return x0, y0, win_x, win_y, lo, hi

    def sample(self, u, v):
        """u, v in 0..1 across the chosen window. Returns 0..1."""
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))
        x = self.x0 + u * (self.win_x - 1)
        y = self.y0 + v * (self.win_y - 1)
        x0 = int(x)
        y0 = int(y)
        tx = x - x0
        ty = y - y0
        h00 = self._at(x0, y0)
        h10 = self._at(x0 + 1, y0)
        h01 = self._at(x0, y0 + 1)
        h11 = self._at(x0 + 1, y0 + 1)
        for value in (h00, h10, h01, h11):
            if value < -1000:
                h00 = h10 = h01 = h11 = self.lo
                break
        h = (
            h00 * (1 - tx) * (1 - ty)
            + h10 * tx * (1 - ty)
            + h01 * (1 - tx) * ty
            + h11 * tx * ty
        )
        span = max(1.0, self.hi - self.lo)
        return max(0.0, min(1.0, (h - self.lo) / span))


def _link(obj):
    if not obj.users_collection:
        bpy.context.scene.collection.objects.link(obj)
    return obj


class Ground:
    def __init__(self):
        self.hgt = _Hgt(HGT_PATH)
        self.mask = _Image(ROUTE_TEX / "coast_land_rocks_01_diff_1k.jpg")
        self.dunes = _Image(ROUTE_TEX / "dirt_aerial_02_disp_1k.jpg")
        self.field = _Image(TEX / "forest_ground_04_disp_1k.jpg") if (TEX / "forest_ground_04_disp_1k.jpg").is_file() else self.dunes

    def _canon(self, x):
        """Fold onto the route so x and x±12000 describe the same ground."""
        return x % ROUTE

    def _wobble(self, x, y):
        # One photograph, sampled so a single tile is wider than a blend.
        # The dune scan has broad light and dark ridges. One tile is about
        # two kilometres, so a boundary follows those ridges for hundreds of metres.
        return (self.dunes.sample_coarse(x * 0.00028, y * 0.00024) - 0.5) * 2.0

    def weights(self, x, y):
        xx = self._canon(x)
        wob = self._wobble(xx, y)
        # Distance to the city that sits at both ends of the loop.
        dx = min(xx, ROUTE - xx)
        city = 1.0 - _smooth(750.0 + wob * 320.0, 1680.0 + wob * 320.0, dx)
        # Fields only on the way out of the opening city, before the range.
        forest = _smooth(1100.0 + wob * 360.0, 1900.0 + wob * 360.0, xx)
        forest *= 1.0 - _smooth(2500.0 + wob * 280.0, 3300.0 + wob * 280.0, xx)
        mountain_in = _smooth(2400.0 + wob * 480.0, 3200.0 + wob * 480.0, xx)
        mountain_out = 1.0 - _smooth(4000.0 + wob * 420.0, 4900.0 + wob * 420.0, xx)
        mountain = mountain_in * mountain_out * (1.0 - city)
        shore = 5400.0 + wob * 640.0
        shore2 = 7700.0 + wob * 560.0
        sea = _smooth(shore - 220.0, shore + 480.0, xx)
        sea *= 1.0 - _smooth(shore2 - 420.0, shore2 + 180.0, xx)
        sea *= 1.0 - city
        dune_in = _smooth(shore2 - 60.0, shore2 + 780.0, xx)
        dune_out = 1.0 - _smooth(9600.0 + wob * 280.0, 10800.0, xx)
        dunes = dune_in * dune_out * (1.0 - sea) * (1.0 - city)
        forest *= (1.0 - mountain) * (1.0 - sea) * (1.0 - dunes) * (1.0 - city)
        beach = 1.0 - _smooth(0.0, 520.0, abs(xx - shore))
        beach = max(beach, 1.0 - _smooth(0.0, 520.0, abs(xx - shore2)))
        beach *= 1.0 - sea * 0.65
        beach *= 1.0 - city
        return {
            "city": city,
            "forest": max(0.0, forest),
            "mountain": max(0.0, mountain),
            "sea": max(0.0, sea),
            "dunes": max(0.0, dunes),
            "beach": max(0.0, min(1.0, beach)),
            "xx": xx,
            "wob": wob,
        }

    def height(self, x, y):
        w = self.weights(x, y)
        xx = w["xx"]
        micro = (self.field.sample(xx * 0.008, y * 0.008) - 0.5) * 4.0
        u = (xx - 2100.0) / 3000.0
        v = (y + 2800.0) / 5600.0
        elev = self.hgt.sample(u, v) if 0.0 <= u <= 1.0 else 0.0
        # Real DEM shape, scaled so the cruise clears the ridges.
        mountain = elev * 380.0 * w["mountain"]
        broad = self.dunes.sample_coarse(xx * 0.0017, y * 0.0014)
        dune = max(0.0, (broad - 0.30) * 160.0) * w["dunes"]
        h = micro * (1.0 - w["mountain"]) * (1.0 - w["sea"]) + mountain + dune
        h = h * (1.0 - w["sea"]) + (-6.0) * w["sea"]
        return h, w


def _image_node(nt, path, noncolor=False):
    node = nt.nodes.new("ShaderNodeTexImage")
    image = bpy.data.images.load(str(path), check_existing=True)
    node.image = image
    node.interpolation = "Smart"
    if noncolor:
        try:
            image.colorspace_settings.name = "Non-Color"
        except TypeError:
            pass
    return node


def _mapping(nt, scale):
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    return mapping


def _ground_material():
    mat = bpy.data.materials.new("RouteGround")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(node for node in nt.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.86

    def tex(path, scale, noncolor=False):
        node = _image_node(nt, path, noncolor=noncolor)
        nt.links.new(_mapping(nt, scale).outputs["Vector"], node.inputs["Vector"])
        return node

    snow = tex(ROUTE_TEX / "snow_02_diff_1k.jpg", 0.012)
    forest = tex(TEX / "forest_ground_04_diff_1k.jpg", 0.018)
    rock = tex(TEX / "aerial_rocks_01_diff_1k.jpg", 0.01)
    sand = tex(ROUTE_TEX / "gravelly_sand_diff_1k.jpg", 0.02)
    red = tex(TEX / "red_sand_diff_1k.jpg", 0.025)
    broad = tex(ROUTE_TEX / "dirt_aerial_02_diff_1k.jpg", 0.0035)
    beach = tex(ROUTE_TEX / "coast_sand_01_diff_1k.jpg", 0.02)
    city = tex(TEX / "aerial_ground_rock_diff_1k.jpg", 0.014)
    land = tex(ROUTE_TEX / "coast_land_rocks_01_diff_1k.jpg", 0.008)
    snow_n = tex(ROUTE_TEX / "snow_02_nor_gl_1k.jpg", 0.012, noncolor=True)

    # Red sand breaks up the gravel colour. The mix factor is the scan itself.
    sand_mix = nt.nodes.new("ShaderNodeMixRGB")
    sand_mix.inputs["Fac"].default_value = 0.55
    nt.links.new(broad.outputs["Color"], sand_mix.inputs["Color1"])
    nt.links.new(sand.outputs["Color"], sand_mix.inputs["Color2"])
    red_mix = nt.nodes.new("ShaderNodeMixRGB")
    red_mix.inputs["Fac"].default_value = 0.35
    nt.links.new(sand_mix.outputs["Color"], red_mix.inputs["Color1"])
    nt.links.new(red.outputs["Color"], red_mix.inputs["Color2"])

    biome = nt.nodes.new("ShaderNodeVertexColor")
    biome.layer_name = "Biome"
    cover = nt.nodes.new("ShaderNodeVertexColor")
    cover.layer_name = "Cover"
    bsep = nt.nodes.new("ShaderNodeSeparateColor")
    csep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(biome.outputs["Color"], bsep.inputs["Color"])
    nt.links.new(cover.outputs["Color"], csep.inputs["Color"])

    def mix(color_a, color_b, fac):
        node = nt.nodes.new("ShaderNodeMixRGB")
        nt.links.new(fac, node.inputs["Fac"])
        if isinstance(color_a, tuple):
            node.inputs["Color1"].default_value = color_a
        else:
            nt.links.new(color_a, node.inputs["Color1"])
        nt.links.new(color_b, node.inputs["Color2"])
        return node.outputs["Color"]

    # Biome.R snow, G forest, B sand, A beach. Cover.R rock, G city, B foothill.
    color = mix(rock.outputs["Color"], snow.outputs["Color"], bsep.outputs["Red"])
    color = mix(color, forest.outputs["Color"], bsep.outputs["Green"])
    color = mix(color, red_mix.outputs["Color"], bsep.outputs["Blue"])
    color = mix(color, beach.outputs["Color"], biome.outputs["Alpha"])
    color = mix(color, city.outputs["Color"], csep.outputs["Green"])
    color = mix(color, land.outputs["Color"], csep.outputs["Blue"])
    nt.links.new(color, bsdf.inputs["Base Color"])

    normal = nt.nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = 0.35
    nt.links.new(snow_n.outputs["Color"], normal.inputs["Color"])
    nt.links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def build_route(track):
    """Mesh parented to the track. Returns a height(x, y) callable."""
    ground = Ground()
    x0, x1 = -1600.0, 13600.0
    y0, y1 = -2800.0, 2800.0
    nx, ny = 560, 150
    dx = (x1 - x0) / (nx - 1)
    dy = (y1 - y0) / (ny - 1)
    verts = []
    biome = []
    cover = []
    for j in range(ny):
        y = y0 + j * dy
        for i in range(nx):
            x = x0 + i * dx
            z, w = ground.height(x, y)
            verts.append((x, y, z))
            snow = w["mountain"] * _smooth(0.25, 0.62, z / 250.0)
            rock = w["mountain"] * (1.0 - snow)
            biome.append((snow, w["forest"], w["dunes"], min(1.0, w["beach"])))
            cover.append((rock, w["city"], w["mountain"] * (1.0 - snow) * 0.35, 1.0))
    faces = []
    for j in range(ny - 1):
        row = j * nx
        nxt = row + nx
        for i in range(nx - 1):
            faces.append((row + i, row + i + 1, nxt + i + 1, nxt + i))
    mesh = bpy.data.meshes.new("RouteMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = True
    try:
        mesh.shade_smooth()
    except (AttributeError, RuntimeError):
        pass
    layer_b = mesh.color_attributes.new("Biome", "FLOAT_COLOR", "POINT")
    layer_c = mesh.color_attributes.new("Cover", "FLOAT_COLOR", "POINT")
    for i, color in enumerate(biome):
        layer_b.data[i].color = color
    for i, color in enumerate(cover):
        layer_c.data[i].color = color
    mesh.materials.append(_ground_material())
    obj = bpy.data.objects.new("RouteGround", mesh)
    obj.parent = track
    _link(obj)
    print("route ground", len(verts), "verts")
    _build_water(track, ground, x0, x1, y0, y1, nx, ny, dx, dy)

    def height_at(x, y):
        return ground.height(x, y)[0]

    _place_cliffs(track, height_at)
    # A short profile so a seam shows up in the log before the render.
    profile = [round(height_at(x, 0.0), 1) for x in range(0, 12001, 800)]
    print("route profile", profile)
    return height_at


def _build_water(track, ground, x0, x1, y0, y1, nx, ny, dx, dy):
    """Water only where the coast is below sea level, so the shore is the terrain."""
    del x1, y1
    index = {}
    verts = []
    for j in range(ny):
        y = y0 + j * dy
        for i in range(nx):
            x = x0 + i * dx
            if ground.weights(x, y)["sea"] < 0.35:
                continue
            swell = (ground.dunes.sample_coarse(x * 0.00015, y * 0.00015) - 0.5) * 5.0
            index[(i, j)] = len(verts)
            verts.append((x, y, 0.35 + swell))
    faces = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            quad = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            if all(point in index for point in quad):
                faces.append(tuple(index[point] for point in quad))
    if len(faces) < 8:
        print("water skipped", len(faces))
        return
    mesh = bpy.data.meshes.new("SeaMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mat = bpy.data.materials.new("Sea")
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.03, 0.18, 0.26, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.04
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.9
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.4
    mesh.materials.append(mat)
    obj = bpy.data.objects.new("Sea", mesh)
    obj.parent = track
    _link(obj)
    print("sea faces", len(faces))
    _ocean_swell(track, mat)


def _ocean_swell(track, mat):
    """One Ocean-modifier tile in the middle of the sea. It does not repeat."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=1.0)
    obj = bpy.context.active_object
    obj.name = "Swell"
    obj.parent = track
    waves = obj.modifiers.new("Waves", "OCEAN")
    waves.geometry_mode = "GENERATE"
    waves.resolution = 16
    waves.spatial_size = 220
    waves.wave_scale = 3.2
    waves.choppiness = 1.1
    waves.wave_alignment = 0.18
    waves.wind_velocity = 16.0
    waves.repeat_x = 1
    waves.repeat_y = 1
    obj.scale = (6.0, 8.0, 5.0)
    obj.location = (6550.0, 0.0, 1.1)
    obj.data.materials.append(mat)


def _place_cliffs(track, height_at):
    """A few Poly Haven scans on the foothills. Not a tiled field."""
    seats = [
        ("mountainside/mountainside_2k.gltf", 2680.0, -600.0, 18.0, 0.4),
        ("mountainside/mountainside_2k.gltf", 3600.0, 900.0, 22.0, 1.2),
        ("rock_face_01/rock_face_01_2k.gltf", 3000.0, 200.0, 14.0, 0.2),
        ("rock_face_02/rock_face_02_2k.gltf", 4200.0, -400.0, 16.0, -0.6),
    ]
    for rel, x, y, scale, yaw in seats:
        path = SCANS / rel
        if not path.is_file():
            print("missing scan", path)
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(path))
        fresh = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
        if not fresh:
            continue
        src = fresh[0]
        zs = [vert.co.z for vert in src.data.vertices]
        base = min(zs) if zs else 0.0
        copy = src.copy()
        copy.data = src.data
        copy.parent = track
        copy.scale = (scale, scale, scale)
        copy.rotation_euler[2] = yaw
        copy.location = (x, y, height_at(x, y) - base * scale)
        _link(copy)
        src.hide_render = True
        print("cliff", rel, "height", round(max(zs) - base, 2))
