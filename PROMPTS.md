# Sprite generation prompts

Paste each prompt into **ChatGPT (image gen)** or **Gemini / Nano Banana**.
Each asks for a 512×128 strip of 4 frames so the app can use it directly.

## Workflow
1. Generate the image with a prompt below.
2. Download the PNG.
3. Conform it into the app (auto-removes the white background + resizes):
   ```bash
   cd ~/pixel-pet
   python3.11 import_sprite.py pikachu ~/Downloads/your_pikachu.png
   ```
   Use the matching name: `cat` `persian` `corgi` `pikachu` `totoro`.
4. Restart the app: `pkill -f pet.py; open dist/PixelPet.app`
   (or rebuild the .app: `python3.11 setup.py py2app`).

If the result still has a colored box behind it, re-export the source on a
**pure white #FFFFFF** background, or add `--keep-bg` and remove the bg in
Photoroom first. If the strip isn't 4 even frames, regenerate — the prompt
must produce exactly 4 frames side by side.

---

## Shared rules (every prompt already includes these)
- single PNG, exactly **512×128 px**, **4 frames side by side**, each 128×128
- no title, no border, no labels, no grid lines, no numbers
- pure flat **white #FFFFFF** background
- clean pixel art, bold dark outline, flat cel colors
- **hard pixel edges, no anti-aliasing, no gradients, no shadows, no glow**
- the character stays the **same size and vertical position** in every frame;
  **feet rest on the bottom edge**; only legs/tail/wings move between frames

---

## 🐈‍⬛ cat (walk, facing left)
```
Create a pixel art sprite sheet of a cute black cat walking, side view facing LEFT.
Output: single PNG, exactly 512x128 pixels, 4 frames side by side, each 128x128.
No title, no border, no labels, no grid lines. Background: pure flat white #FFFFFF.
Style: clean pixel art, bold near-black outline, flat colors, hard pixel edges,
no anti-aliasing, no gradients, no shadows.
Character: jet black body #1A1A1A, bright yellow-green almond eyes #AAFF00 with a
1px white highlight and a slit pupil, pink ear-insides and nose, thin whiskers,
a curved tail.
Animation: 4-frame walk cycle, legs alternate each frame; cat same size and
vertical position in every frame; feet on the bottom edge; only legs and tail move.
```

## 🐈 persian (white Persian cat, pink eyes, walk, facing left)
```
Create a pixel art sprite sheet of a fluffy WHITE Persian cat walking, side view
facing LEFT. Output: single PNG, exactly 512x128 pixels, 4 frames side by side,
each 128x128. No title, no border, no labels, no grid lines. Background: pure
flat white #FFFFFF (the cat is white, so give it a light gray outline so it is
visible on white).
Style: clean pixel art, light gray outline #C8C8D0, flat colors, hard pixel edges,
no anti-aliasing, no gradients, no shadows.
Character: fluffy white body with a flat round face, big pink eyes #FF7FB0 with a
white highlight, small pink nose, small ears, a very fluffy plume tail.
Animation: 4-frame walk cycle, legs alternate each frame; same size and vertical
position in every frame; feet on the bottom edge; only legs and tail move.
```

## 🐕 corgi (walk, facing left)
```
Create a pixel art sprite sheet of a Corgi dog walking, side view facing LEFT.
Output: single PNG, exactly 512x128 pixels, 4 frames side by side, each 128x128.
No title, no border, no labels, no grid lines. Background: pure flat white #FFFFFF.
Style: clean pixel art, bold brown outline, flat colors, hard pixel edges,
no anti-aliasing, no gradients, no shadows.
Character: orange-tan body #E89A50 with a white chest, white legs/paws and a white
facial blaze, big upright triangular ears, black nose, short stubby legs, a low
long body, a small fluffy tail.
Animation: 4-frame walk cycle, short legs alternate each frame; same size and
vertical position in every frame; feet on the bottom edge; only legs and tail move.
```

## ⚡ pikachu (walk, facing left)
```
Create a pixel art sprite sheet of Pikachu (Pokemon) walking on all fours,
side view facing LEFT. Output: single PNG, exactly 512x128 pixels, 4 frames side
by side, each 128x128. No title, no border, no labels, no grid lines.
Background: pure flat white #FFFFFF.
Style: clean pixel art, bold dark-brown outline, flat cel colors, hard pixel edges,
no anti-aliasing, no gradients, no shadows.
Character: bright yellow body #F8D030, two long ears with black tips, a red circle
cheek, small black eyes with a white highlight, two short brown stripes on the back,
a brown-based yellow lightning-bolt tail.
Animation: 4-frame walk cycle, legs alternate each frame; Pikachu same size and
vertical position in every frame; feet on the bottom edge; only legs and tail move.
```

## 🌳 totoro (walk, facing left)
```
Create a pixel art sprite sheet of Totoro (My Neighbor Totoro) WALKING,
side view facing LEFT. Output: single PNG, exactly 512x128 pixels, 4 frames
side by side, each 128x128. No title, no border, no labels, no grid lines.
Background: pure flat white #FFFFFF.
Style: clean pixel art, bold dark outline, flat colors, hard pixel edges,
no anti-aliasing, no gradients, no shadows.
Character: large round gray-blue body #8A929E, a cream-white belly with small
gray chevron (V) markings, two small pointed ears on top of the head, one round
black eye with a tiny white highlight, a small triangular nose, short whiskers,
short stubby legs with small feet.
Animation: 4-frame walk cycle, the stubby legs alternate each frame; Totoro
same size and vertical position in every frame; feet rest on the bottom edge;
body waddles slightly.
```

---

### Add a brand-new creature
1. Generate + `python3.11 import_sprite.py <newname> <image>`
2. Add an entry to the `PETS` list in `pet.py`:
   ```python
   {"name": "<newname>", "sheet": "<newname>.png", "kind": "walk",  # or "fly"
    "size": 88, "speed": 2.0, "anim": 6, "msgs": ["hi!", "..."]},
   ```
3. For a `.app`, also add `sprite_sheet/<newname>.png` to `DATA_FILES` in setup.py.
