"""
RB250 dash panel - 2 mm plate with the screen window.
Run:  python make_panel.py   ->  rb250_dash_panel.stl, preview PNG, 1:1 PDF template
All sizes in mm. Y = 0 at the top of the round end, measured downwards.
"""
import os
import numpy as np
import trimesh
from shapely.geometry import Polygon, box
from shapely.affinity import scale

HERE = os.path.dirname(os.path.abspath(__file__))

THICK = 4.0
HEIGHT = 130.0
# (depth from top, full width) taken from the template
STATIONS = [(5, 80), (18, 119), (37, 130), (62, 135), (100, 142), (HEIGHT, 150)]
GAP_TOP = 111.0     # gap between the legs starts here
GAP_W = 90.0        # gap width (legs are 30 mm each: 150 - 2*30)
GAP_R = 12.0        # rounded U corners
# Newhaven NHD-3.5-HDMI-HR-RSXP viewing area 72.48 x 55.38 (+ small clearance)
WIN_W, WIN_H, WIN_R = 73.0, 56.0, 1.0
WIN_TOP = 18.0      # top of the window on the 119 mm line
# two push-button holes below the screen (12 mm panel-mount buttons)
BTN_D = 12.0
BTN_Y = 92.0        # centre depth from top (window ends at 74, gap starts at 111)
BTN_X = 30.0        # +/- from centre: SELECT left, NEXT right
# raised lettering
TEXT_RAISE = 0.8    # mm above the plate
LABEL_H = 4.5       # NEXT / SELECT letter height, under each hole
BADGE_H = 6.5       # RB250 badge letter height, between the buttons
FONTS = os.path.join(HERE, "..", "assets", "fonts")


def catmull(pts, n=24):
    pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = (np.array(p) for p in pts[i - 1:i + 3])
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-2]))
    return [tuple(p) for p in out]


def outline():
    # one smooth curve: crown across the top (y=0 centre, y=5 at 80 mm wide) into the sides
    crown = [(-20, 1.25), (0, 0), (20, 1.25)]  # mirrored point keeps the top centre flat
    side = catmull(crown + [(w / 2, y) for y, w in STATIONS])
    right = [p for p in side if p[0] >= 0]
    right[0] = (0.0, 0.0)
    leg_in = GAP_W / 2
    # bottom of right leg, up the inner edge, round corner, across the gap top (to centre)
    right += [(leg_in, HEIGHT), (leg_in, GAP_TOP + GAP_R)]
    for a in np.linspace(0, np.pi / 2, 12)[1:]:
        right.append((leg_in - GAP_R + GAP_R * np.cos(a), GAP_TOP + GAP_R - GAP_R * np.sin(a)))
    right.append((0, GAP_TOP))
    poly = Polygon([(x, -y) for x, y in right] + [(x, -y) for x, y in
                                                  [(-px, py) for px, py in reversed(right)]])
    return poly.buffer(0)


def window():
    w = box(-WIN_W / 2 + WIN_R, -(WIN_TOP + WIN_H) + WIN_R, WIN_W / 2 - WIN_R, -WIN_TOP - WIN_R)
    return w.buffer(WIN_R, resolution=8)


def buttons():
    from shapely.geometry import Point
    return [Point(x, -BTN_Y).buffer(BTN_D / 2, resolution=32) for x in (-BTN_X, BTN_X)]


def text_shape(msg, height, font, cx, cy):
    """Text as a shapely shape, centred at (cx, cy) in plate coords (cy negative = down)."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from shapely.affinity import translate
    from shapely.geometry import MultiPolygon
    tp = TextPath((0, 0), msg, size=10, prop=FontProperties(fname=os.path.join(FONTS, font)))
    shape = None
    for ring in tp.to_polygons():
        if len(ring) < 3:
            continue
        p = Polygon(ring).buffer(0)
        shape = p if shape is None else shape.symmetric_difference(p)  # holes in R, B, 0
    minx, miny, maxx, maxy = shape.bounds
    k = height / (maxy - miny)
    shape = scale(shape, k, k, origin=(0, 0))
    minx, miny, maxx, maxy = shape.bounds
    shape = translate(shape, cx - (minx + maxx) / 2, cy - (miny + maxy) / 2)
    return shape if isinstance(shape, (Polygon, MultiPolygon)) else shape.buffer(0)


def lettering():
    label_y = -(BTN_Y + BTN_D / 2 + 2.5 + LABEL_H / 2)
    return [
        text_shape("SELECT", LABEL_H, "ChakraPetch-Bold.ttf", -BTN_X, label_y),
        text_shape("NEXT", LABEL_H, "ChakraPetch-Bold.ttf", BTN_X, label_y),
        text_shape("RB250", BADGE_H, "ChakraPetch-Bold.ttf", 0, -BTN_Y),
    ]


def build():
    plate = outline().difference(window())
    for b in buttons():
        plate = plate.difference(b)
    mesh = trimesh.creation.extrude_polygon(plate, THICK)
    assert mesh.is_watertight
    parts = [mesh]
    for t in lettering():
        assert plate.contains(t), "lettering runs off the panel"
        polys = list(t.geoms) if hasattr(t, "geoms") else [t]
        for p in polys:
            m = trimesh.creation.extrude_polygon(p, TEXT_RAISE + 0.1)
            assert m.is_watertight
            m.apply_translation((0, 0, THICK - 0.1))  # tiny overlap so slicers merge it
            parts.append(m)
    mesh = trimesh.util.concatenate(parts)
    stl = os.path.join(HERE, "rb250_dash_panel.stl")
    mesh.export(stl)
    b = plate.bounds
    print(f"STL: {stl}")
    print(f"size {b[2]-b[0]:.1f} x {b[3]-b[1]:.1f} x {THICK} mm (+{TEXT_RAISE} lettering)")
    return plate


def drawings(plate):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def draw(ax, dims=True):
        x, y = plate.exterior.xy
        ax.fill(x, y, color="#9aa3ad")
        ax.plot(x, y, color="k", lw=0.8)
        for hole in plate.interiors:
            hx, hy = hole.xy
            ax.fill(hx, hy, color="white")
            ax.plot(hx, hy, color="k", lw=0.8)
        if dims:
            for yy, w in STATIONS[:-1]:
                ax.annotate("", (-w / 2, -yy), (w / 2, -yy),
                            arrowprops=dict(arrowstyle="<->", lw=0.5, color="#b00"))
                ax.text(w / 2 + 2, -yy, f"{w:.0f}", va="center", fontsize=6, color="#b00")
            ax.text(0, -(WIN_TOP + WIN_H / 2), f"SCREEN\n{WIN_W:.0f} x {WIN_H:.0f}",
                    ha="center", va="center", fontsize=7)
            ax.text(0, -(GAP_TOP + 10), f"gap {GAP_W:.0f}", ha="center", fontsize=6)
            ax.text(-BTN_X - BTN_D, -BTN_Y, f"{BTN_D:.0f} mm", ha="right", va="center", fontsize=5)
            ax.text(-75, -(HEIGHT + 6), f"total {HEIGHT:.0f} high, 150 wide at the legs, "
                    f"{THICK:.0f} mm thick", fontsize=6)
        for t in lettering():
            for p in (list(t.geoms) if hasattr(t, "geoms") else [t]):
                lx, ly = p.exterior.xy
                ax.fill(lx, ly, color="#3b4148")
                for hole in p.interiors:
                    hx, hy = hole.xy
                    ax.fill(hx, hy, color="#9aa3ad")
        ax.set_aspect("equal")
        ax.axis("off")

    fig, ax = plt.subplots(figsize=(6, 6))
    draw(ax)
    fig.savefig(os.path.join(HERE, "rb250_dash_panel_preview.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)

    # 1:1 printable template on A4 (print at 100% / "actual size")
    fig = plt.figure(figsize=(210 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-105, 105)
    ax.set_ylim(-250, 47)
    draw(ax, dims=True)
    ax.set_aspect("equal")
    ax.plot([-80, -30], [-215, -215], color="k", lw=1)
    ax.text(-55, -220, "this line must measure 50 mm", ha="center", fontsize=7)
    ax.text(0, 38, "RB250 dash panel - 1:1 template (print at 100%, A4)", ha="center", fontsize=9)
    fig.savefig(os.path.join(HERE, "rb250_dash_panel_template_A4.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    drawings(build())
