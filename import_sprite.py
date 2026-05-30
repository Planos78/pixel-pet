"""Conform a generated sprite image into sprite_sheet/<name>.png.

    python3.11 import_sprite.py <name> <image_path> [--keep-bg]

Steps:
  1. flood-fill the white background to transparent from the image edges
     (interior whites like eye highlights are preserved)
  2. resize to exactly 512x128 (4 frames of 128x128)
  3. save to sprite_sheet/<name>.png

<name> is the creature key used in pet.py's PETS list, e.g.
    cat  persian  corgi  pikachu  totoro
(or any new name you add there).

    python3.11 import_sprite.py pikachu ~/Downloads/pikachu_sheet.png
"""

import os
import sys
from collections import deque

from PIL import Image


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
    if "--keep-bg" not in flags:
        img = remove_white_bg(img)
    img = img.resize((512, 128), Image.LANCZOS)

    out = os.path.join(out_dir, name + ".png")
    img.save(out)
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
