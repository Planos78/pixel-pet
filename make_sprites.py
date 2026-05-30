"""Generate placeholder pixel-art sprite sheets for Pixel Pet.

Draws a cute black cat at a low resolution (crisp pixel look) and upscales
with NEAREST so the result reads as hard-edged pixel art. Produces two
512x128 PNG sheets (4 frames of 128x128 each) on a transparent background:

    sprite_sheet/walk_sprite.png   walk cycle, cat facing left
    sprite_sheet/sit_sprite.png    sitting loop with a blink

Swap these out for real ChatGPT/Canva/Photoroom sprites any time — the app
loads whatever PNGs sit in sprite_sheet/ as long as they are 4 frames wide.

    python3.11 make_sprites.py
"""

import os
from PIL import Image, ImageDraw

GRID = 32          # low-res draw grid
SCALE = 4          # GRID * SCALE -> 128 px per frame
FRAME = GRID * SCALE
FRAMES = 4

# Palette (matches the PDF spec)
BODY = (26, 26, 26, 255)      # #1A1A1A jet black
OUTLINE = (10, 10, 10, 255)   # #0A0A0A near-black
EYE = (170, 255, 0, 255)      # #AAFF00 yellow-green
HILITE = (255, 255, 255, 255)
NOSE = (255, 153, 153, 255)   # #FF9999 pink
CLEAR = (0, 0, 0, 0)


def _canvas():
    return Image.new("RGBA", (GRID, GRID), CLEAR)


def draw_walk(frame):
    """Cat facing left, walking. Legs alternate, tail sways."""
    img = _canvas()
    d = ImageDraw.Draw(img)
    legs_up = frame in (0, 2)

    # body + head
    d.ellipse([13, 12, 28, 24], fill=BODY, outline=OUTLINE)
    d.ellipse([3, 8, 16, 21], fill=BODY, outline=OUTLINE)
    # ears
    d.polygon([(4, 9), (7, 3), (10, 10)], fill=BODY, outline=OUTLINE)
    d.polygon([(10, 9), (13, 3), (15, 10)], fill=BODY, outline=OUTLINE)
    # tail (sways between frames)
    tail_y = 9 if frame % 2 == 0 else 14
    d.line([(27, 18), (30, tail_y)], fill=BODY, width=2)
    # legs (front pair + back pair alternate)
    front = 24 if legs_up else 27
    back = 27 if legs_up else 24
    d.rectangle([15, 22, 16, front], fill=BODY)
    d.rectangle([18, 22, 19, back], fill=BODY)
    d.rectangle([22, 22, 23, front], fill=BODY)
    d.rectangle([25, 22, 26, back], fill=BODY)
    # face (eye + highlight + nose), facing left
    d.rectangle([6, 12, 8, 14], fill=EYE)
    img.putpixel((7, 12), HILITE)
    img.putpixel((4, 15), NOSE)
    return img


def draw_sit(frame):
    """Cat sitting upright, facing left. Body fixed, eyes blink / ears twitch."""
    img = _canvas()
    d = ImageDraw.Draw(img)

    # haunches + chest
    d.ellipse([11, 14, 25, 29], fill=BODY, outline=OUTLINE)
    d.ellipse([9, 16, 18, 28], fill=BODY, outline=OUTLINE)
    # head
    d.ellipse([6, 5, 18, 17], fill=BODY, outline=OUTLINE)
    # ears (right ear twitches down on frame 1)
    d.polygon([(6, 6), (9, 1), (12, 7)], fill=BODY, outline=OUTLINE)
    ear_tip = 3 if frame == 1 else 1
    d.polygon([(12, 6), (15, ear_tip), (17, 7)], fill=BODY, outline=OUTLINE)
    # front legs tucked
    d.rectangle([10, 25, 12, 29], fill=BODY)
    d.rectangle([15, 25, 17, 29], fill=BODY)
    # tail curled at base
    d.line([(24, 27), (28, 24), (27, 20)], fill=BODY, width=2)
    # eyes (blink closed on frame 2)
    if frame == 2:
        d.line([(8, 11), (11, 11)], fill=EYE)
    else:
        d.rectangle([8, 10, 10, 12], fill=EYE)
        img.putpixel((9, 10), HILITE)
    img.putpixel((7, 13), NOSE)
    return img


def build_sheet(draw_fn, path):
    sheet = Image.new("RGBA", (FRAME * FRAMES, FRAME), CLEAR)
    for i in range(FRAMES):
        frame = draw_fn(i).resize((FRAME, FRAME), Image.NEAREST)
        sheet.paste(frame, (i * FRAME, 0))
    sheet.save(path)
    print("wrote", path, sheet.size)


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite_sheet")
    os.makedirs(out, exist_ok=True)
    build_sheet(draw_walk, os.path.join(out, "walk_sprite.png"))
    build_sheet(draw_sit, os.path.join(out, "sit_sprite.png"))


if __name__ == "__main__":
    main()
