"""Conform a generated sprite image into sprite_sheet/<name>.png.

    python3.11 import_sprite.py <name> <image_path> [--keep-bg]

The AI usually returns a wide image (e.g. ~1792x896) of 4 frames. Naively
resizing that to 512x128 squashes tall characters. Instead this:
  1. flood-fills the white background to transparent from the edges
     (interior whites like belly/eye highlights are preserved)
  2. splits the image into 4 equal columns (the 4 frames)
  3. trims each frame to its content, scales it to fit a 128x128 cell while
     PRESERVING aspect ratio, and bottom-aligns it (feet on the ground)
  4. assembles a clean 512x128 sheet -> sprite_sheet/<name>.png

<name> is the creature key in pet.py's PETS list:
    cat  persian  corgi  pikachu  totoro   (or any new name you add)

    python3.11 import_sprite.py totoro ~/Downloads/totoro.png
"""

import os
import sys
from collections import deque

from PIL import Image

FRAMES = 4
CELL = 128
MARGIN = 6          # transparent padding inside each cell (px)


def remove_white_bg(img, thresh=236):
    """Flood-fill near-white from the borders to transparent. Connected
    background only — interior white pixels (highlights) stay opaque."""
    w, h = img.size
    px = img.load()

    def is_white(p):
        return p[0] >= thresh and p[1] >= thresh and p[2] >= thresh

    seen = bytearray(w * h)
    dq = deque()
    for x in range(w):
        dq.append((x, 0))
        dq.append((x, h - 1))
    for y in range(h):
        dq.append((0, y))
        dq.append((w - 1, y))

    while dq:
        x, y = dq.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]:
            continue
        seen[y * w + x] = 1
        p = px[x, y]
        if is_white(p):
            px[x, y] = (p[0], p[1], p[2], 0)
            dq.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return img


def conform(src):
    """Split into 4 frames, trim + aspect-fit + bottom-align each into a cell."""
    w, h = src.size
    fw = w // FRAMES
    out = Image.new("RGBA", (CELL * FRAMES, CELL), (0, 0, 0, 0))
    for i in range(FRAMES):
        x0 = i * fw
        x1 = w if i == FRAMES - 1 else (i + 1) * fw
        col = src.crop((x0, 0, x1, h))
        bbox = col.getbbox()
        if bbox:
            col = col.crop(bbox)
        cw, ch = col.size
        avail = CELL - 2 * MARGIN
        scale = min(avail / cw, avail / ch)
        nw, nh = max(1, round(cw * scale)), max(1, round(ch * scale))
        col = col.resize((nw, nh), Image.LANCZOS)
        x = i * CELL + (CELL - nw) // 2          # center horizontally
        y = CELL - MARGIN - nh                   # bottom-align (feet on ground)
        out.alpha_composite(col, (x, y))
    return out


def main():
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        sys.exit(1)

    name, path = args
    path = os.path.expanduser(path)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite_sheet")
    os.makedirs(out_dir, exist_ok=True)

    img = Image.open(path).convert("RGBA")
    if "--keep-bg" in flags:
        sheet = img.resize((CELL * FRAMES, CELL), Image.LANCZOS)
    else:
        sheet = conform(remove_white_bg(img))

    out = os.path.join(out_dir, name + ".png")
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
