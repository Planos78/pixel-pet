# Pixel Pet 🐈‍⬛

A macOS desktop menagerie — pixel-art creatures that roam your screen on top
of all windows with true per-pixel transparency. PyObjC/Cocoa + Pillow.
No tkinter, pygame, or Electron.

## The menagerie
| Creature | Behaviour |
|---|---|
| 🐈‍⬛ Black cat | walks the bottom |
| 🐈 White Persian (pink eyes) | walks the bottom |
| 🐕 Corgi | walks the bottom |
| ⚡ Pikachu | walks the bottom |
| 🌳 Totoro | flies / bobs across the upper screen |

All appear at once. Edit the `PETS` list in [pet.py](pet.py) to add, remove,
resize, or re-speech any creature.

## Features
- Walkers pad along the bottom; flyers drift + bob up top
- **Left click** a creature → it pauses ~3s and says something
- **Drag** → move it anywhere
- **Right click** → menu with *Quit Pixel Pet* (quits the whole menagerie)
- Per-creature speech bubbles (rounded-rect body + triangle tail)
- Borderless transparent windows at level 25, single-instance lock,
  clean quit on Ctrl+C / right-click

## Setup
```bash
brew install python@3.11
pip3.11 install Pillow pyobjc
python3.11 make_sprites.py     # (re)generate the sprite sheets
```

## Run from source
```bash
python3.11 pet.py
```
Stop: right-click any creature → *Quit Pixel Pet*, `Ctrl+C`, or
`pkill -f pet.py; rm -f /tmp/pixel_pet.lock`.

## Build a .app
```bash
pip3.11 install py2app
python3.11 setup.py py2app
open dist/PixelPet.app
```
If macOS blocks it: `xattr -cr dist/PixelPet.app && open dist/PixelPet.app`

## Custom sprites
Each creature loads `sprite_sheet/<name>.png` — a 512×128 sheet of 4 frames
(128×128 each), facing left. White backgrounds are auto-removed on load. The
included sprites are programmatic placeholders from `make_sprites.py`; swap in
real ChatGPT/Canva art any time for a more lifelike look.

Pikachu and Totoro are fan-made pixel renditions for personal use only.
Original *Desktop Pet — Pixel Cat* concept by June Aekkaluk.
