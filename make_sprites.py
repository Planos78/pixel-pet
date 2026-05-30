"""Generate pixel-art sprite sheets for every Pixel Pet creature.

Each creature is drawn on a 64x64 logical grid (crisp shapes), then upscaled
x2 with NEAREST so the result is hard-edged pixel art. Every sheet is
512x128 — four 128x128 frames side by side.

Walkers face left; their 4 frames are a leg/tail cycle (feet rest near the
bottom of the frame so they stand on the dock line). Flyers face left; their
4 frames are a wing/bob cycle centered in the frame.

    python3.11 make_sprites.py

Output -> sprite_sheet/<name>.png  (cat, persian, corgi, pikachu, totoro)
Swap any PNG for a real ChatGPT/Canva sheet any time (white bg auto-removed).
"""

import os
from PIL import Image, ImageDraw

S = 64                 # logical grid
SCALE = 2              # -> 128 px per frame
FRAME = S * SCALE
N = 4
CLEAR = (0, 0, 0, 0)


# ---- small drawing helpers -------------------------------------------------
def canvas():
    return Image.new("RGBA", (S, S), CLEAR)


def ell(d, box, fill, outline=None):
    d.ellipse(box, fill=fill, outline=outline)


def poly(d, pts, fill, outline=None):
    d.polygon(pts, fill=fill, outline=outline)


def px(img, x, y, c):
    if 0 <= x < S and 0 <= y < S:
        img.putpixel((x, y), c)


def eye(img, d, cx, cy, white, iris, pupil=(8, 8, 8, 255), w=4, h=5):
    """An almond eye facing left, with iris, slit pupil and a highlight."""
    d.ellipse([cx - w, cy - h // 2, cx + w, cy + h // 2], fill=white)
    d.ellipse([cx - 2, cy - h // 2 + 1, cx + 2, cy + h // 2 - 1], fill=iris)
    d.line([(cx, cy - h // 2 + 1), (cx, cy + h // 2 - 1)], fill=pupil)
    px(img, cx - 1, cy - 1, (255, 255, 255, 255))


# ===========================================================================
# Black cat — walk, facing left
# ===========================================================================
C_BASE = (32, 32, 34, 255)
C_SHAD = (18, 18, 20, 255)
C_HI = (52, 52, 56, 255)
C_OUT = (10, 10, 12, 255)
C_PINK = (255, 150, 165, 255)


def draw_cat(f):
    img = canvas()
    d = ImageDraw.Draw(img)
    up = f in (0, 2)
    fa, fb = (58, 54) if up else (54, 58)   # alternating foot heights

    # tail (curves up from rear-right, sways)
    ty = 26 if f % 2 == 0 else 22
    d.line([(50, 42), (57, 36), (56, ty)], fill=C_BASE, width=3)
    # legs (front pair near head, back pair near rear) + little paws
    for lx, ly in ((20, fa), (27, fb), (40, fb), (46, fa)):
        d.line([(lx, 46), (lx, ly)], fill=C_BASE, width=3)
        d.ellipse([lx - 2, ly - 1, lx + 2, ly + 2], fill=C_BASE)
    # body
    ell(d, [18, 32, 52, 50], C_BASE, C_OUT)
    ell(d, [22, 40, 50, 51], C_SHAD)           # belly shadow
    ell(d, [22, 31, 46, 40], C_HI)             # back highlight
    # head
    ell(d, [4, 24, 28, 46], C_BASE, C_OUT)
    ell(d, [8, 26, 24, 36], C_HI)
    # ears with pink inner
    poly(d, [(6, 26), (9, 16), (15, 26)], C_BASE, C_OUT)
    poly(d, [(16, 26), (21, 17), (25, 27)], C_BASE, C_OUT)
    poly(d, [(9, 24), (10, 20), (13, 25)], C_PINK)
    poly(d, [(18, 25), (20, 21), (22, 26)], C_PINK)
    # face: eye, nose, whiskers
    eye(img, d, 12, 33, (240, 255, 235, 255), (150, 220, 30, 255), w=4, h=6)
    poly(d, [(4, 35), (8, 34), (6, 37)], C_PINK)        # nose
    for wy in (35, 37, 39):
        d.line([(2, wy), (9, wy - 1)], fill=(210, 210, 210, 150))
    return img


# ===========================================================================
# White Persian cat — walk, facing left, pink eyes, very fluffy
# ===========================================================================
P_BASE = (248, 248, 250, 255)
P_SHAD = (214, 216, 226, 255)
P_OUT = (196, 198, 210, 255)
P_PINK = (255, 130, 170, 255)
P_NOSE = (255, 160, 185, 255)


def _fluff(d, box, fill, outline, bumps=10):
    """A fluffy blob: ellipse with a scalloped pixel edge."""
    ell(d, box, fill, outline)


def draw_persian(f):
    img = canvas()
    d = ImageDraw.Draw(img)
    up = f in (0, 2)
    fa, fb = (59, 56) if up else (56, 59)

    # fluffy tail (big plume, sways)
    ty = 24 if f % 2 == 0 else 20
    ell(d, [48, 30, 60, 46], P_BASE, P_OUT)
    ell(d, [50, ty, 60, 36], P_BASE, P_OUT)
    # legs (short, fluffy)
    for lx, ly in ((22, fa), (29, fb), (40, fb), (46, fa)):
        d.line([(lx, 48), (lx, ly)], fill=P_BASE, width=4)
        ell(d, [lx - 2, ly - 1, lx + 3, ly + 2], fill=P_BASE)
    # body (round, fluffy)
    _fluff(d, [16, 30, 52, 52], P_BASE, P_OUT)
    ell(d, [22, 42, 48, 52], P_SHAD)
    # head (big, round, flat face)
    _fluff(d, [2, 22, 30, 48], P_BASE, P_OUT)
    # ears (small, tucked in fluff)
    poly(d, [(7, 24), (9, 17), (14, 25)], P_BASE, P_OUT)
    poly(d, [(18, 25), (23, 18), (26, 26)], P_BASE, P_OUT)
    poly(d, [(9, 23), (10, 20), (12, 24)], P_PINK)
    # cheek fluff
    ell(d, [1, 33, 12, 46], P_BASE, P_OUT)
    ell(d, [20, 33, 31, 46], P_BASE, P_OUT)
    # pink eyes (two, flat face faces left so both slightly visible)
    eye(img, d, 11, 33, (255, 235, 242, 255), (255, 120, 165, 255),
        pupil=(180, 40, 90, 255), w=4, h=6)
    eye(img, d, 20, 34, (255, 235, 242, 255), (255, 120, 165, 255),
        pupil=(180, 40, 90, 255), w=3, h=5)
    # tiny pink nose + mouth
    poly(d, [(13, 38), (17, 38), (15, 41)], P_NOSE)
    d.line([(15, 41), (12, 43)], fill=P_OUT)
    d.line([(15, 41), (18, 43)], fill=P_OUT)
    return img


# ===========================================================================
# Corgi — walk, facing left, tan + white, big ears
# ===========================================================================
G_TAN = (228, 158, 80, 255)
G_TAN_S = (196, 126, 56, 255)
G_WHITE = (250, 248, 244, 255)
G_OUT = (120, 78, 36, 255)
G_NOSE = (40, 30, 28, 255)


def draw_corgi(f):
    img = canvas()
    d = ImageDraw.Draw(img)
    up = f in (0, 2)
    fa, fb = (61, 58) if up else (58, 61)

    # stubby tail (wags)
    ty = 30 if f % 2 == 0 else 26
    ell(d, [52, ty, 60, 40], G_TAN, G_OUT)
    # short legs (white socks)
    for lx, ly, fwd in ((20, fa, True), (27, fb, True), (42, fb, False), (48, fa, False)):
        d.line([(lx, 50), (lx, ly)], fill=G_TAN, width=4)
        d.rectangle([lx - 2, ly - 3, lx + 2, ly], fill=G_WHITE)
    # long low body
    ell(d, [16, 34, 54, 54], G_TAN, G_OUT)
    ell(d, [20, 46, 50, 55], G_WHITE)          # white chest/belly
    ell(d, [24, 33, 48, 42], G_TAN_S)          # back shade
    # head (fox-like)
    ell(d, [2, 26, 26, 48], G_TAN, G_OUT)
    # big upright ears
    poly(d, [(4, 28), (6, 12), (16, 28)], G_TAN, G_OUT)
    poly(d, [(16, 28), (24, 13), (27, 30)], G_TAN, G_OUT)
    poly(d, [(7, 26), (8, 17), (13, 26)], (255, 210, 180, 255))
    poly(d, [(18, 27), (22, 18), (24, 28)], (255, 210, 180, 255))
    # white facial blaze + muzzle
    poly(d, [(8, 28), (12, 48), (16, 28)], G_WHITE)
    ell(d, [1, 38, 12, 48], G_WHITE)
    # eye + nose + mouth
    eye(img, d, 14, 34, (255, 255, 255, 255), (60, 40, 30, 255),
        pupil=(20, 14, 12, 255), w=3, h=5)
    ell(d, [2, 40, 7, 45], G_NOSE)             # black nose
    d.line([(4, 45), (4, 48)], fill=G_OUT)
    d.line([(4, 48), (8, 49)], fill=G_OUT)
    return img


# ===========================================================================
# Pikachu — walk, facing left
# ===========================================================================
K_YEL = (250, 208, 48, 255)
K_YEL_S = (224, 170, 24, 255)
K_OUT = (150, 100, 12, 255)
K_BROWN = (120, 78, 28, 255)
K_RED = (232, 54, 40, 255)


def draw_pikachu(f):
    img = canvas()
    d = ImageDraw.Draw(img)
    up = f in (0, 2)
    fa, fb = (61, 58) if up else (58, 61)

    # lightning-bolt tail (behind, right side)
    bolt_y = 18 if f % 2 == 0 else 22
    poly(d, [(52, 44), (60, 36), (55, 34), (61, bolt_y),
             (57, bolt_y + 6), (54, 40)], K_YEL, K_OUT)
    poly(d, [(52, 44), (58, 38), (54, 38)], K_BROWN)   # brown tail base
    # legs
    for lx, ly in ((22, fa), (30, fb), (40, fb), (47, fa)):
        d.line([(lx, 50), (lx, ly)], fill=K_YEL, width=4)
        ell(d, [lx - 2, ly - 2, lx + 2, ly + 1], fill=K_YEL_S)
    # chubby body
    ell(d, [16, 30, 52, 54], K_YEL, K_OUT)
    ell(d, [22, 44, 48, 55], K_YEL_S)          # belly shade
    # back stripes (brown)
    d.line([(26, 31), (44, 31)], fill=K_BROWN, width=2)
    d.line([(28, 35), (42, 35)], fill=K_BROWN, width=2)
    # head
    ell(d, [4, 22, 30, 46], K_YEL, K_OUT)
    # long ears with black tips
    poly(d, [(8, 24), (4, 4), (16, 22)], K_YEL, K_OUT)
    poly(d, [(18, 22), (26, 5), (28, 26)], K_YEL, K_OUT)
    poly(d, [(4, 4), (8, 6), (9, 12)], (40, 36, 38, 255))     # ear tips
    poly(d, [(26, 5), (24, 8), (23, 13)], (40, 36, 38, 255))
    # red cheek
    ell(d, [6, 36, 14, 43], K_RED)
    # eyes (round black with highlight) + nose + mouth
    eye(img, d, 13, 30, (255, 255, 255, 255), (24, 22, 24, 255),
        pupil=(10, 10, 10, 255), w=4, h=6)
    eye(img, d, 22, 31, (255, 255, 255, 255), (24, 22, 24, 255),
        pupil=(10, 10, 10, 255), w=3, h=5)
    px(img, 17, 36, (40, 30, 28, 255))         # nose
    d.line([(17, 37), (14, 39)], fill=K_OUT)
    d.line([(17, 37), (20, 39)], fill=K_OUT)
    return img


# ===========================================================================
# Totoro — fly, facing left, gentle bob + ear/arm flap
# ===========================================================================
T_BASE = (138, 146, 158, 255)
T_SHAD = (104, 112, 126, 255)
T_BELLY = (232, 230, 224, 255)
T_OUT = (70, 76, 88, 255)
T_DARK = (40, 44, 52, 255)


def draw_totoro(f):
    img = canvas()
    d = ImageDraw.Draw(img)
    bob = (0, -2, 0, 2)[f]                      # vertical bob
    arm = (0, -3, 0, 3)[f]                      # arm/ear flap
    o = bob

    # big teardrop body
    ell(d, [14, 8 + o, 52, 60 + o], T_BASE, T_OUT)
    ell(d, [18, 36 + o, 48, 58 + o], T_SHAD)    # lower shade
    # cream belly with gray chevrons
    ell(d, [20, 26 + o, 46, 58 + o], T_BELLY, T_OUT)
    for cy in (34, 40, 46):
        d.line([(28, cy + o), (33, cy - 3 + o), (38, cy + o)], fill=T_SHAD)
    # ears (pointy, flap)
    poly(d, [(22, 14 + o), (20, 1 + o + arm), (28, 13 + o)], T_BASE, T_OUT)
    poly(d, [(38, 13 + o), (46, 1 + o - arm), (44, 14 + o)], T_BASE, T_OUT)
    # arms out (flying)
    d.line([(15, 30 + o), (6, 30 + o - arm)], fill=T_BASE, width=5)
    d.line([(51, 30 + o), (60, 30 + o + arm)], fill=T_BASE, width=5)
    # big eyes close together + pupils + nose + whiskers
    eye(img, d, 27, 22 + o, (250, 250, 250, 255), (250, 250, 250, 255),
        pupil=(20, 20, 24, 255), w=5, h=8)
    eye(img, d, 38, 22 + o, (250, 250, 250, 255), (250, 250, 250, 255),
        pupil=(20, 20, 24, 255), w=5, h=8)
    ell(d, [30, 28 + o, 36, 33 + o], T_DARK)    # nose
    for wy in (29, 32, 35):
        d.line([(30, wy + o), (16, wy - 2 + o)], fill=(230, 230, 230, 140))
        d.line([(36, wy + o), (50, wy - 2 + o)], fill=(230, 230, 230, 140))
    return img


# ---- build sheets ----------------------------------------------------------
CREATURES = {
    "cat": draw_cat,
    "persian": draw_persian,
    "corgi": draw_corgi,
    "pikachu": draw_pikachu,
    "totoro": draw_totoro,
}


def build_sheet(draw_fn, path):
    sheet = Image.new("RGBA", (FRAME * N, FRAME), CLEAR)
    for i in range(N):
        frame = draw_fn(i).resize((FRAME, FRAME), Image.NEAREST)
        sheet.paste(frame, (i * FRAME, 0))
    sheet.save(path)
    print("wrote", os.path.basename(path), sheet.size)


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite_sheet")
    os.makedirs(out, exist_ok=True)
    for name, fn in CREATURES.items():
        build_sheet(fn, os.path.join(out, name + ".png"))


if __name__ == "__main__":
    main()
