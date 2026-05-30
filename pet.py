"""Pixel Pet — a macOS desktop pet (PyObjC/Cocoa + Pillow).

A pixel-art cat walks across the bottom of the screen on top of all windows
with true per-pixel transparency. Left-click to make it sit, drag to move it,
right-click for a Quit menu. Speech bubbles pop above it.

    python3.11 pet.py        # run from source
"""

import os
import sys
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
SIZE = 80                 # on-screen cat size (px)
FPS = 30                  # animation/movement ticks per second
ANIM_TICK_WALK = 6        # advance walk frame every N ticks
ANIM_TICK_SIT = 15        # advance sit frame every N ticks
WALK_SPEED = 2.0          # px moved per tick while walking
WINDOW_LEVEL = 25         # above apps, below system UI
SIT_DURATION = 3          # seconds the cat sits after a click
BUBBLE_DURATION = 3       # seconds a speech bubble stays up
WALK_BUBBLE_EVERY = 8     # seconds between walking speech bubbles

SIT_MSGS = ["~meow meow", "purrr...", "nya~", "(˘ω˘)"]
WALK_MSGS = ["where my fish nya", "i am speed ~", "*sniff sniff*", "zoomies!!"]

LOCK_PATH = "/tmp/pixel_pet.lock"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(BASE_DIR, "sprite_sheet")

STATE_WALK = "walk"
STATE_SIT = "sit"


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
class CatView(NSView):
    """Draws the current cat frame; forwards mouse events to the controller."""

    def drawRect_(self, rect):
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())
        img = self.controller.currentCatImage()
        if img is not None:
            NSGraphicsContext.currentContext().setImageInterpolation_(
                NSImageInterpolationNone)
            img.drawInRect_fromRect_operation_fraction_(
                self.bounds(), NSMakeRect(0, 0, 0, 0),
                NSCompositingOperationSourceOver, 1.0)

    def mouseDown_(self, event):
        self.controller.catMouseDown_(event)

    def mouseDragged_(self, event):
        self.controller.catMouseDragged_(event)

    def mouseUp_(self, event):
        self.controller.catMouseUp_(event)

    def rightMouseDown_(self, event):
        self.controller.catRightMouseDown_(event)


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


# ---- Controller ------------------------------------------------------------
class PetController(NSObject):

    def setup(self):
        self._acquire_lock()

        vf = NSScreen.mainScreen().visibleFrame()
        self.min_x = vf.origin.x
        self.max_x = vf.origin.x + vf.size.width - SIZE
        self.cat_y = vf.origin.y
        self.cat_x = float(self.max_x)

        self.state = STATE_WALK
        self.direction = -1            # -1 = facing/moving left, +1 = right
        self.ticks = 0
        self.sit_start = 0
        self.is_dragging = False
        self.drag_moved = False
        self.drag_offset = NSMakePoint(0, 0)
        self.next_walk_bubble = FPS * WALK_BUBBLE_EVERY
        self.bubble_visible = False
        self.bubble_hide_tick = None
        self.bubble_w = 0.0
        self.bubble_h = 0.0
        self.should_quit = False

        # sprites
        self.walk_left = load_frames(os.path.join(SPRITE_DIR, "walk_sprite.png"))
        self.walk_right = load_frames(os.path.join(SPRITE_DIR, "walk_sprite.png"),
                                      flip=True)
        self.sit_frames = load_frames(os.path.join(SPRITE_DIR, "sit_sprite.png"))

        self._build_cat_window()
        self._build_bubble_window()
        self._reposition_cat()

        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / FPS, self, "tick:", None, True)

    # -- window construction --
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

    def _build_cat_window(self):
        rect = NSMakeRect(self.cat_x, self.cat_y, SIZE, SIZE)
        self.cat_window = self._make_window(rect, accepts_mouse=True)
        self.cat_view = CatView.alloc().initWithFrame_(
            NSMakeRect(0, 0, SIZE, SIZE))
        self.cat_view.controller = self
        self.cat_window.setContentView_(self.cat_view)
        self.cat_window.orderFrontRegardless()

    def _build_bubble_window(self):
        self.bubble_window = self._make_window(
            NSMakeRect(0, 0, 10, 10), accepts_mouse=False)
        self.bubble_view = BubbleView.alloc().initWithFrame_(
            NSMakeRect(0, 0, 10, 10))
        self.bubble_view.text = ""
        self.bubble_window.setContentView_(self.bubble_view)

    # -- drawing source --
    def currentCatImage(self):
        if self.state == STATE_SIT:
            return self.sit_frames[(self.ticks // ANIM_TICK_SIT) % 4]
        frames = self.walk_left if self.direction == -1 else self.walk_right
        return frames[(self.ticks // ANIM_TICK_WALK) % 4]

    # -- main loop --
    def tick_(self, timer):
        if self.should_quit:
            self.cleanupAndQuit()
            return

        self.ticks += 1

        if self.state == STATE_WALK and not self.is_dragging:
            self.cat_x += self.direction * WALK_SPEED
            if self.cat_x <= self.min_x:
                self.cat_x = float(self.min_x)
                self.direction = 1
            elif self.cat_x >= self.max_x:
                self.cat_x = float(self.max_x)
                self.direction = -1
            if self.ticks >= self.next_walk_bubble:
                self.showBubble_for_(random.choice(WALK_MSGS),
                                     FPS * BUBBLE_DURATION)
                self.next_walk_bubble = self.ticks + FPS * WALK_BUBBLE_EVERY

        elif self.state == STATE_SIT:
            if self.ticks - self.sit_start >= FPS * SIT_DURATION:
                self.state = STATE_WALK

        if self.bubble_hide_tick is not None and self.ticks >= self.bubble_hide_tick:
            self.hideBubble()

        self._reposition_cat()
        self.cat_view.setNeedsDisplay_(True)

    def _reposition_cat(self):
        self.cat_window.setFrameOrigin_(NSMakePoint(int(self.cat_x), int(self.cat_y)))
        if self.bubble_visible:
            self._reposition_bubble()

    def _reposition_bubble(self):
        bx = self.cat_x + SIZE / 2.0 - self.bubble_w / 2.0
        by = self.cat_y + SIZE - 6
        self.bubble_window.setFrame_display_(
            NSMakeRect(bx, by, self.bubble_w, self.bubble_h), True)

    # -- speech bubbles --
    def showBubble_for_(self, text, ticks):
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(13),
            NSForegroundColorAttributeName: NSColor.blackColor(),
        }
        size = NSString.stringWithString_(text).sizeWithAttributes_(attrs)
        self.bubble_w = size.width + 18
        self.bubble_h = size.height + 22
        self.bubble_view.text = text
        self.bubble_visible = True
        self.bubble_hide_tick = self.ticks + ticks
        self._reposition_bubble()
        self.bubble_view.setNeedsDisplay_(True)
        self.bubble_window.orderFrontRegardless()

    def hideBubble(self):
        self.bubble_visible = False
        self.bubble_hide_tick = None
        self.bubble_window.orderOut_(None)

    # -- mouse --
    def catMouseDown_(self, event):
        self.is_dragging = True
        self.drag_moved = False
        self.drag_offset = event.locationInWindow()

    def catMouseDragged_(self, event):
        self.drag_moved = True
        mouse = NSEvent.mouseLocation()
        self.cat_x = mouse.x - self.drag_offset.x
        self.cat_y = mouse.y - self.drag_offset.y
        self._reposition_cat()

    def catMouseUp_(self, event):
        was_drag = self.drag_moved
        self.is_dragging = False
        self.drag_moved = False
        if not was_drag:
            self.startSit()

    def startSit(self):
        self.state = STATE_SIT
        self.sit_start = self.ticks
        self.showBubble_for_(random.choice(SIT_MSGS), FPS * SIT_DURATION)

    def catRightMouseDown_(self, event):
        menu = NSMenu.alloc().init()
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Pixel Pet", "quit:", "")
        item.setTarget_(self)
        menu.addItem_(item)
        NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self.cat_view)

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
        self.bubble_window.orderOut_(None)
        self.cat_window.orderOut_(None)
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
