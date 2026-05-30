# HANDOFF — Pixel Pet 🐈‍⬛

State of the project for picking up on another account / machine.
**Last updated: 2026-05-30**

---

## TL;DR
macOS desktop pet: pixel-art creatures walk along the bottom of the screen on
top of all windows. Working + on GitHub. 4 creatures so far. The one open item
is **making the walk animation smoother** (see Open items #1).

- Repo: https://github.com/Planos78/pixel-pet  (everything pushed to `main`)
- Local: `~/pixel-pet`
- Runs from source AND builds a `.app`.

---

## What works now ✅
- **4 creatures**, all real AI-generated pixel sprites, walking with feet on the
  ground, no flicker: **cat, persian (white, pink eyes), corgi, totoro**.
  (Totoro walks — not flying.)
- All walk the bottom, bounce at screen edges, flip to face their direction.
- **Left-click** a creature → it pauses ~3s and shows a speech bubble.
  **Drag** → move it. **Right-click** → *Quit Pixel Pet* (quits all).
- Borderless transparent windows at level 25; single-instance lock
  (`/tmp/pixel_pet.lock`); clean quit on Ctrl+C.
- Builds to `dist/PixelPet.app` via py2app.

---

## Open items / what to do next

### 1. Animation not smooth (MAIN open item)
Each creature has only **4 frames**, so the walk looks a bit choppy.
- Tried cross-fade **interpolation** in code (`INTERP` in pet.py) to fake 16
  frames → looked blurry/worse, so it's left **OFF** (`INTERP = 1`, crisp 4-frame).
- **Real fix = more REAL frames.** Generate **6–8 frames** per creature (NOT 16
  — image generators can't keep 16 frames consistent; 8 is the sweet spot).

  How:
  1. In `PROMPTS.md`, take a creature's prompt and change
     `4 frames` → `8 frames` and `512x128` → `1024x128`.
  2. Generate, download.
  3. Tell the importer it's 8 frames: edit `import_sprite.py` →
     change `FRAMES = 4` to `FRAMES = 8`, and in `pet.py` `load_frames(...)`
     change the `count=4` default to `8`. (Or make `FRAMES`/`count` a per-call
     arg — small refactor, see "Nice-to-have" below.)
  4. `python3.11 import_sprite.py <name> <file>` then rebuild.

  If 8-frame sheets generate cleanly, the walk will look genuinely smooth — no
  interpolation needed. If you'd rather keep 4 frames, just leave it; it's fine.

### 2. Pikachu was removed
Image generators (ChatGPT) **block trademarked characters** ("violates third-party
content" error), even reworded. Options to bring it back:
- Try **Gemini / Nano Banana** (looser on fan art) with the "original mascot"
  prompt style (avoid the words *Pikachu / Pokemon / electric / lightning*).
- Or pick a **non-IP creature** (yellow duck, chick, hamster, fox) — generates easily.
- Then `import_sprite.py pikachu <file>`, add it back to `PETS` in pet.py AND to
  `DATA_FILES` in setup.py.

### Nice-to-have (not blocking)
- Make frame-count a per-creature `"frames"` key in `PETS` + a `--frames N` arg
  in `import_sprite.py`, so different creatures can have different frame counts.
- Per-creature show/hide menu; remember positions; auto-start at login.

---

## Misconception to clear up
You do **not** generate 16 separate images. A sprite **sheet** is ONE image with
N frames laid out side by side (the app slices it). For smooth motion, **one
sheet with 6–8 frames** is plenty. 16 is overkill and image gen can't keep that
many consistent.

---

## Setup on a new machine / account
```bash
# 1. clone
git clone https://github.com/Planos78/pixel-pet.git
cd pixel-pet

# 2. python + deps (macOS only — PyObjC is macOS-native)
brew install python@3.11
pip3.11 install Pillow pyobjc py2app

# 3. run from source
python3.11 pet.py
#    stop: right-click a creature → Quit, or Ctrl+C, or:
#    pkill -f pet.py; rm -f /tmp/pixel_pet.lock

# 4. build the .app
python3.11 setup.py py2app
open dist/PixelPet.app
#    if macOS blocks it:
#    xattr -cr dist/PixelPet.app && open dist/PixelPet.app
```
The repo already includes generated sprites in `sprite_sheet/`, so it runs
immediately after step 2.

---

## How the code is laid out
| File | What it is |
|---|---|
| `pet.py` | The app. **`PETS` list at the top = the roster.** Each entry: `name, sheet, kind (walk/fly), size, speed, anim (lower=faster), msgs`. `INTERP` = animation interpolation (1=off). A generic `Pet` class drives each creature; `PetController` owns one 30fps timer + the single-instance lock. |
| `import_sprite.py` | Conform a generated image → `sprite_sheet/<name>.png`. Removes the white background (edge flood-fill), splits into `FRAMES` columns, fits them with ONE shared crop+scale (keeps size constant = no flicker), bottom-aligns (feet on ground). |
| `make_sprites.py` | Procedural placeholder generator (the original code-drawn sprites). Fallback only; the real sprites came from AI + import_sprite.py. |
| `PROMPTS.md` | Ready-to-paste image-gen prompts per creature. |
| `setup.py` | py2app build. **Every sprite must be listed in `DATA_FILES`.** |
| `sprite_sheet/*.png` | The 512×128 (4-frame) sheets the app loads. |
| `README.md` | User-facing overview. |

### To add / change a creature
1. Get a sprite (AI via PROMPTS.md, or `make_sprites.py`).
2. `python3.11 import_sprite.py <name> <image>` → writes `sprite_sheet/<name>.png`.
3. Add/edit its entry in `PETS` (pet.py).
4. Add `sprite_sheet/<name>.png` to `DATA_FILES` (setup.py) for the .app build.
5. `python3.11 pet.py` to test, then rebuild the .app.

### Tuning (no new art needed)
All in the `PETS` entry: `size` (px on screen), `speed` (px/tick), `anim`
(ticks per frame — lower = faster legs), `msgs` (speech lines).

---

## Source images
The original AI PNGs are in `~/Downloads/` named `ChatGPT Image 30 พ.ค. 2569 18_*.png`
(cat 18_34_00, persian 18_34_06, corgi 18_34_37, totoro 18_39_38). Re-import with
`import_sprite.py` if you ever need to redo them.
