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
    """Split into 4 frames and fit them into 512x128.

    All four frames share ONE crop window (the union of their content boxes)
    and ONE scale, so the character keeps a constant size and position — only
    legs/tail animate. (Per-frame trimming made fluffy tails change the box
    each frame, which scaled the body differently and looked like flicker.)
    """
    w, h = src.size
    fw = w // FRAMES
    cols = [src.crop((i * fw, 0, (w if i == FRAMES - 1 else (i + 1) * fw), h))
            for i in range(FRAMES)]

    boxes = [b for b in (c.getbbox() for c in cols) if b]
    if not boxes:
        return src.resize((CELL * FRAMES, CELL), Image.LANCZOS)
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)

    cw, ch = x1 - x0, y1 - y0
    avail = CELL - 2 * MARGIN
    scale = min(avail / cw, avail / ch)
    nw, nh = max(1, round(cw * scale)), max(1, round(ch * scale))
    x_in_cell = (CELL - nw) // 2
    y_in_cell = CELL - MARGIN - nh               # bottom-align (feet on ground)

    out = Image.new("RGBA", (CELL * FRAMES, CELL), (0, 0, 0, 0))
    for i, col in enumerate(cols):
        frame = col.crop((x0, y0, x1, y1)).resize((nw, nh), Image.LANCZOS)
        out.alpha_composite(frame, (i * CELL + x_in_cell, y_in_cell))
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
