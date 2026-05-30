"""Pixel Pet — a macOS desktop menagerie (PyObjC/Cocoa + Pillow).

Several pixel-art creatures roam the screen on top of all windows with true
per-pixel transparency. Walkers (cat, persian cat, corgi, pikachu) pad along
the bottom; flyers (totoro) drift and bob across the upper screen.

  - Left click a creature → it pauses for a moment and says something
  - Drag    → move it anywhere
  - Right click → menu with "Quit Pixel Pet" (quits the whole menagerie)

    python3.11 pet.py        # run from source
"""

import os
import sys
import math
import signal
import random
import fcntl
from io import BytesIO

from PIL import Image

from Foundation import NSObject, NSData, NSString, NSMakeRect, NSMakePoint
from AppKit import (
    NSApplication, NSWindow, NSView, NSColor, NSImage, NSBezierPath,
    NSScreen, NSTimer, NSMenu, NSMenuItem, NSEvent, NSFont, NSGraphicsContext,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorStationary,
    NSCompositingOperationSourceOver, NSImageInterpolationNone,
    NSApplicationActivationPolicyAccessory,
    NSFontAttributeName, NSForegroundColorAttributeName,
)

# ---- Constants -------------------------------------------------------------
FPS = 30                  # animation/movement ticks per second
WINDOW_LEVEL = 25         # above apps, below system UI
PAUSE_DURATION = 3        # seconds a creature pauses after a click
BUBBLE_DURATION = 3       # seconds a speech bubble stays up
BUBBLE_EVERY = 8          # default seconds between idle speech bubbles
FLY_AMP = 40.0            # vertical bob amplitude for flyers (px)
FLY_FREQ = 0.05           # bob speed (radians per tick)

LOCK_PATH = "/tmp/pixel_pet.lock"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(BASE_DIR, "sprite_sheet")

# Each creature: sprite sheet (4 frames, facing left), behaviour, size, speed,
# animation tick (lower = faster), and its own speech lines.
PETS = [
    {"name": "cat", "sheet": "cat.png", "kind": "walk", "size": 86,
     "speed": 2.0, "anim": 6,
     "msgs": ["~meow meow", "nya~", "zoomies!!", "where my fish"]},
    {"name": "persian", "sheet": "persian.png", "kind": "walk", "size": 86,
     "speed": 1.5, "anim": 7,
     "msgs": ["mrrp~", "so fluffy", "pet me?", "(=^･ω･^=)"]},
    {"name": "corgi", "sheet": "corgi.png", "kind": "walk", "size": 92,
     "speed": 2.6, "anim": 6,
     "msgs": ["woof!", "borf borf", "such speed", "wiggle~"]},
    {"name": "pikachu", "sheet": "pikachu.png", "kind": "walk", "size": 88,
     "speed": 2.2, "anim": 6,
     "msgs": ["pika!", "pika pika!", "pikachuuu", "zzzap ⚡"]},
    {"name": "totoro", "sheet": "totoro.png", "kind": "fly", "size": 120,
     "speed": 1.2, "anim": 10,
     "msgs": ["totoro~", "*rumble*", "...", "🌳"]},
]


# ---- Sprite loading --------------------------------------------------------
def _remove_white_bg(img, thresh=240):
    """Make a white background transparent. Skipped if the image already
    carries transparency (assumed pre-keyed, e.g. our generated sprites)."""
    if img.getchannel("A").getextrema()[0] < 255:
        return img
    out = []
    for r, g, b, a in img.getdata():
        out.append((r, g, b, 0) if r >= thresh and g >= thresh and b >= thresh
                   else (r, g, b, a))
    img.putdata(out)
    return img


def _pil_to_nsimage(pil_img):
    buf = BytesIO()
    pil_img.save(buf, format="PNG")
    raw = buf.getvalue()
    data = NSData.dataWithBytes_length_(raw, len(raw))
    return NSImage.alloc().initWithData_(data)


def load_frames(path, count=4, flip=False):
    """Slice a horizontal sprite sheet into `count` NSImage frames."""
    pil = Image.open(path).convert("RGBA")
    pil = _remove_white_bg(pil)
    w, h = pil.size
    fw = w // count
    frames = []
    for i in range(count):
        frame = pil.crop((i * fw, 0, (i + 1) * fw, h))
        if flip:
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        frames.append(_pil_to_nsimage(frame))
    return frames


# ---- Views -----------------------------------------------------------------
class PetView(NSView):
    """Draws one creature's current frame; forwards mouse events to its Pet."""

    def drawRect_(self, rect):
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())
        img = self.pet.current_image()
        if img is not None:
            NSGraphicsContext.currentContext().setImageInterpolation_(
                NSImageInterpolationNone)
            img.drawInRect_fromRect_operation_fraction_(
                self.bounds(), NSMakeRect(0, 0, 0, 0),
                NSCompositingOperationSourceOver, 1.0)

    def mouseDown_(self, event):
        self.pet.on_down(event)

    def mouseDragged_(self, event):
        self.pet.on_drag(event)

    def mouseUp_(self, event):
        self.pet.on_up(event)

    def rightMouseDown_(self, event):
        self.pet.on_right(event)


class BubbleView(NSView):
    """A rounded speech bubble with a tail, following the PDF spec exactly."""

    def drawRect_(self, rect):
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())
        text = NSString.stringWithString_(getattr(self, "text", "") or "")
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(13),
            NSForegroundColorAttributeName: NSColor.blackColor(),
        }
        size = text.sizeWithAttributes_(attrs)
        b = self.bounds()
        tail_h = 8
        body = NSMakeRect(b.origin.x + 1, b.origin.y + tail_h + 1,
                          b.size.width - 2, b.size.height - tail_h - 2)
        stroke = NSColor.colorWithWhite_alpha_(0.75, 1.0)

        # bubble body — rounded rect via the dedicated API (no manual arcs)
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(body, 9, 9)
        NSColor.whiteColor().set()
        path.fill()
        stroke.set()
        path.setLineWidth_(1.0)
        path.stroke()

        # tail — a separate triangle below the body center, pointing down
        cx = b.origin.x + b.size.width / 2.0
        tail = NSBezierPath.bezierPath()
        tail.moveToPoint_(NSMakePoint(cx - 7, body.origin.y + 1))
        tail.lineToPoint_(NSMakePoint(cx + 7, body.origin.y + 1))
        tail.lineToPoint_(NSMakePoint(cx, b.origin.y + 1))
        tail.closePath()
        NSColor.whiteColor().set()
        tail.fill()
        stroke.set()
        tail.stroke()

        # text centered in the body
        tx = body.origin.x + (body.size.width - size.width) / 2.0
        ty = body.origin.y + (body.size.height - size.height) / 2.0
        text.drawAtPoint_withAttributes_(NSMakePoint(tx, ty), attrs)


# ---- Pet (one creature) ----------------------------------------------------
class Pet:
    """State + windows + behaviour for a single creature. Plain Python class
    (not an ObjC subclass), so method names are unconstrained."""

    def __init__(self, controller, spec):
        self.c = controller
        self.name = spec["name"]
        self.kind = spec["kind"]
        self.size = spec["size"]
        self.speed = spec["speed"]
        self.anim = spec["anim"]
        self.msgs = spec["msgs"]
        self.bubble_every = spec.get("bubble_every", BUBBLE_EVERY)

        path = os.path.join(SPRITE_DIR, spec["sheet"])
        self.frames_left = load_frames(path)
        self.frames_right = load_frames(path, flip=True)

        self.x = self.y = self.base_y = 0.0
        self.direction = -1
        self.offset = 0
        self.anim_idx = 0
        self.paused = False
        self.pause_start = 0
        self.dragging = False
        self.drag_moved = False
        self.drag_offset = NSMakePoint(0, 0)
        self.next_bubble = FPS * self.bubble_every
        self.bubble_visible = False
        self.bubble_hide = None
        self.bubble_w = self.bubble_h = 0.0

    def x_bounds(self):
        lo = self.c.vf.origin.x
        return lo, lo + self.c.vf.size.width - self.size

    def build(self, x, y, direction, offset):
        self.x = float(x)
        self.y = self.base_y = float(y)
        self.direction = direction
        self.offset = offset
        self.next_bubble = FPS * self.bubble_every + offset

        self.window = self.c._make_window(
            NSMakeRect(self.x, self.y, self.size, self.size), True)
        self.view = PetView.alloc().initWithFrame_(
            NSMakeRect(0, 0, self.size, self.size))
        self.view.pet = self
        self.window.setContentView_(self.view)
        self.window.orderFrontRegardless()

        self.bubble_window = self.c._make_window(NSMakeRect(0, 0, 10, 10), False)
        self.bubble_view = BubbleView.alloc().initWithFrame_(NSMakeRect(0, 0, 10, 10))
        self.bubble_view.text = ""
        self.bubble_window.setContentView_(self.bubble_view)
        self.reposition()

    def current_image(self):
        frames = self.frames_left if self.direction == -1 else self.frames_right
        return frames[self.anim_idx]

    def _bob(self, ticks):
        self.y = self.base_y + FLY_AMP * math.sin((ticks + self.offset) * FLY_FREQ)

    def update(self, ticks):
        lo, hi = self.x_bounds()
        if self.dragging:
            pass
        elif self.paused:
            if ticks - self.pause_start >= FPS * PAUSE_DURATION:
                self.paused = False
            if self.kind == "fly":
                self._bob(ticks)
        else:
            self.x += self.direction * self.speed
            if self.x <= lo:
                self.x = float(lo)
                self.direction = 1
            elif self.x >= hi:
                self.x = float(hi)
                self.direction = -1
            if self.kind == "fly":
                self._bob(ticks)
            if ticks >= self.next_bubble:
                self.show_bubble(random.choice(self.msgs), ticks)
                self.next_bubble = ticks + FPS * self.bubble_every

        if self.paused and self.kind == "walk":
            self.anim_idx = 0
        else:
            self.anim_idx = ((ticks + self.offset) // self.anim) % 4

        if self.bubble_hide is not None and ticks >= self.bubble_hide:
            self.hide_bubble()

        self.reposition()
        self.view.setNeedsDisplay_(True)

    def reposition(self):
        self.window.setFrameOrigin_(NSMakePoint(int(self.x), int(self.y)))
        if self.bubble_visible:
            self._reposition_bubble()

    def _reposition_bubble(self):
        bx = self.x + self.size / 2.0 - self.bubble_w / 2.0
        by = self.y + self.size - 6
        self.bubble_window.setFrame_display_(
            NSMakeRect(bx, by, self.bubble_w, self.bubble_h), True)

    def show_bubble(self, text, ticks):
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(13),
            NSForegroundColorAttributeName: NSColor.blackColor(),
        }
        size = NSString.stringWithString_(text).sizeWithAttributes_(attrs)
        self.bubble_w = size.width + 18
        self.bubble_h = size.height + 22
        self.bubble_view.text = text
        self.bubble_visible = True
        self.bubble_hide = ticks + FPS * BUBBLE_DURATION
        self._reposition_bubble()
        self.bubble_view.setNeedsDisplay_(True)
        self.bubble_window.orderFrontRegardless()

    def hide_bubble(self):
        self.bubble_visible = False
        self.bubble_hide = None
        self.bubble_window.orderOut_(None)

    # -- mouse (called from PetView) --
    def on_down(self, event):
        self.dragging = True
        self.drag_moved = False
        self.drag_offset = event.locationInWindow()

    def on_drag(self, event):
        self.drag_moved = True
        mouse = NSEvent.mouseLocation()
        self.x = mouse.x - self.drag_offset.x
        self.y = self.base_y = mouse.y - self.drag_offset.y
        self.reposition()

    def on_up(self, event):
        moved = self.drag_moved
        self.dragging = False
        self.drag_moved = False
        if not moved:
            self.paused = True
            self.pause_start = self.c.ticks
            self.show_bubble(random.choice(self.msgs), self.c.ticks)

    def on_right(self, event):
        menu = NSMenu.alloc().init()
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Pixel Pet", "quit:", "")
        item.setTarget_(self.c)
        menu.addItem_(item)
        NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self.view)

    def hide_windows(self):
        self.bubble_window.orderOut_(None)
        self.window.orderOut_(None)


# ---- Controller ------------------------------------------------------------
class PetController(NSObject):

    def setup(self):
        self._acquire_lock()
        self.ticks = 0
        self.should_quit = False
        self.vf = NSScreen.mainScreen().visibleFrame()
        self.pets = []

        walkers = [s for s in PETS if s["kind"] == "walk"]
        nwalk = max(1, len(walkers))
        wi = 0
        for idx, spec in enumerate(PETS):
            pet = Pet(self, spec)
            if spec["kind"] == "walk":
                slot = (wi + 0.5) / nwalk
                x = self.vf.origin.x + slot * self.vf.size.width - pet.size / 2.0
                y = self.vf.origin.y
                direction = -1 if wi % 2 == 0 else 1
                wi += 1
            else:
                x = self.vf.origin.x + self.vf.size.width * 0.6
                y = self.vf.origin.y + self.vf.size.height * 0.5
                direction = -1
            pet.build(x, y, direction, offset=idx * 17)
            self.pets.append(pet)

        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / FPS, self, "tick:", None, True)

    def _make_window(self, rect, accepts_mouse):
        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False)
        win.setOpaque_(False)
        win.setBackgroundColor_(NSColor.clearColor())
        win.setLevel_(WINDOW_LEVEL)
        win.setHasShadow_(False)
        win.setIgnoresMouseEvents_(not accepts_mouse)
        win.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces |
            NSWindowCollectionBehaviorStationary)
        return win

    def tick_(self, timer):
        if self.should_quit:
            self.cleanupAndQuit()
            return
        self.ticks += 1
        for pet in self.pets:
            pet.update(self.ticks)

    def quit_(self, sender):
        self.cleanupAndQuit()

    def requestQuit(self):
        self.should_quit = True

    # -- lifecycle --
    def _acquire_lock(self):
        self.lock_fd = open(LOCK_PATH, "w")
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            sys.stderr.write("Pixel Pet is already running.\n")
            sys.exit(1)
        self.lock_fd.write(str(os.getpid()))
        self.lock_fd.flush()

    def _release_lock(self):
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            os.remove(LOCK_PATH)
        except Exception:
            pass

    def cleanupAndQuit(self):
        if getattr(self, "timer", None) is not None:
            self.timer.invalidate()
        for pet in getattr(self, "pets", []):
            pet.hide_windows()
        self._release_lock()
        NSApplication.sharedApplication().terminate_(None)


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    controller = PetController.alloc().init()
    controller.setup()

    # Clean quit on Ctrl+C — the 30fps timer lets the handler run promptly.
    signal.signal(signal.SIGINT, lambda *_: controller.requestQuit())

    app.run()


if __name__ == "__main__":
    main()
