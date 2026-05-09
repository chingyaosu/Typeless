"""
Floating panda status window — three styles to pick from.

Set PANDA_STYLE in main.py:
  "capsule"  — horizontal bamboo capsule with 🐼 + text (clean, minimal)
  "card"     — vertical card with big 🐼 emoji centered + status below (cute)
  "bubble"   — round white panda face drawn with NSBezierPath (illustrated)
"""
import objc
from AppKit import (
    NSPanel, NSView, NSColor, NSTextField, NSScreen, NSFont,
    NSBackingStoreBuffered, NSWindowStyleMaskBorderless,
    NSFloatingWindowLevel, NSTextAlignmentCenter, NSTextAlignmentLeft,
    NSBezierPath,
)
from Foundation import NSMakeRect, NSObject, NSTimer

TOP_OFFSET = 60


class _MainThreadProxy(NSObject):
    def runBlock_(self, block):
        block()


_proxy = _MainThreadProxy.alloc().init()


def _on_main(fn):
    _proxy.performSelectorOnMainThread_withObject_waitUntilDone_(
        "runBlock:", fn, False
    )


# ───────────────────────────────────────────────────────────
# Style: bubble (illustrated panda head drawn with NSBezierPath)
# ───────────────────────────────────────────────────────────
class _PandaFaceView(NSView):
    def drawRect_(self, rect):
        w, h = rect.size.width, rect.size.height

        # Face — narrower by ~10% (more side margin)
        face_inset = 33
        face_w = w - 2 * face_inset
        face_y = 6
        face_h = h - 56

        # Ears (placed at top corners of the narrower face)
        NSColor.blackColor().set()
        ear_size = 72
        ear_y = h - ear_size - 4
        ear_offset = 20  # how far inside the face edge each ear sits
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(face_inset + ear_offset, ear_y, ear_size, ear_size)).fill()
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(face_inset + face_w - ear_offset - ear_size, ear_y, ear_size, ear_size)).fill()

        # Face
        NSColor.whiteColor().set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(face_inset, face_y, face_w, face_h), 70, 60).fill()

        # Eye patches (placed in upper face area)
        NSColor.blackColor().set()
        patch_w, patch_h = 54, 60
        patch_y = face_y + face_h - patch_h - 10
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(w / 2 - 78, patch_y, patch_w, patch_h)).fill()
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(w / 2 + 78 - patch_w, patch_y, patch_w, patch_h)).fill()

        # Eyes
        NSColor.whiteColor().set()
        eye = 16
        ey = patch_y + patch_h / 2 - eye / 2 + 4
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(w / 2 - 80 + 24, ey, eye, eye)).fill()
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(w / 2 + 80 - patch_w + 16, ey, eye, eye)).fill()

        # Pupils
        NSColor.blackColor().set()
        pup = 7
        py = ey + (eye - pup) / 2
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(w / 2 - 80 + 24 + (eye - pup) / 2, py, pup, pup)).fill()
        NSBezierPath.bezierPathWithOvalInRect_(
            NSMakeRect(w / 2 + 80 - patch_w + 16 + (eye - pup) / 2, py, pup, pup)).fill()

        # Nose
        nose = NSBezierPath.bezierPath()
        cx, ny = w / 2, patch_y - 6
        nose.moveToPoint_((cx - 8, ny + 6))
        nose.lineToPoint_((cx + 8, ny + 6))
        nose.lineToPoint_((cx, ny - 4))
        nose.closePath()
        nose.fill()


# ───────────────────────────────────────────────────────────
# Style: capsule (horizontal pill, emoji + text)
# ───────────────────────────────────────────────────────────
class _CapsuleView(NSView):
    def drawRect_(self, rect):
        w, h = rect.size.width, rect.size.height
        # Soft bamboo green tint
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.96, 0.97, 0.93, 0.95).set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            rect, h / 2, h / 2).fill()
        # Subtle border
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.6, 0.7, 0.5, 0.4).set()
        border = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            rect, h / 2, h / 2)
        border.setLineWidth_(1.5)
        border.stroke()


# ───────────────────────────────────────────────────────────
# Style: card (rounded white card)
# ───────────────────────────────────────────────────────────
class _CardView(NSView):
    def drawRect_(self, rect):
        w, h = rect.size.width, rect.size.height
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.96).set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            rect, 20, 20).fill()


# ───────────────────────────────────────────────────────────
class StatusWindow:
    def __init__(self, style: str = "capsule"):
        self.style = style
        if style == "bubble":
            self.W, self.H = 360, 200
        elif style == "card":
            self.W, self.H = 240, 180
        else:  # capsule
            self.W, self.H = 360, 70

        screen = NSScreen.mainScreen().frame()
        x = (screen.size.width - self.W) / 2
        y = screen.size.height - TOP_OFFSET - self.H

        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, self.W, self.H),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        self.panel.setLevel_(NSFloatingWindowLevel)
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setHasShadow_(True)
        self.panel.setIgnoresMouseEvents_(True)
        self.panel.setHidesOnDeactivate_(False)

        self._build()
        self._hide_timer = None

    def _build(self):
        if self.style == "bubble":
            view = _PandaFaceView.alloc().initWithFrame_(
                NSMakeRect(0, 0, self.W, self.H))
            self.panel.setContentView_(view)
            self.label = self._mk_label(
                NSMakeRect(20, 14, self.W - 40, 28),
                NSFont.boldSystemFontOfSize_(15), NSColor.blackColor()
            )
            view.addSubview_(self.label)

        elif self.style == "card":
            view = _CardView.alloc().initWithFrame_(
                NSMakeRect(0, 0, self.W, self.H))
            self.panel.setContentView_(view)

            emoji = self._mk_label(
                NSMakeRect(0, 60, self.W, 90),
                NSFont.systemFontOfSize_(80), NSColor.blackColor()
            )
            emoji.setStringValue_("🐼")
            view.addSubview_(emoji)

            self.label = self._mk_label(
                NSMakeRect(16, 18, self.W - 32, 30),
                NSFont.boldSystemFontOfSize_(15), NSColor.blackColor()
            )
            view.addSubview_(self.label)

        else:  # capsule
            view = _CapsuleView.alloc().initWithFrame_(
                NSMakeRect(0, 0, self.W, self.H))
            self.panel.setContentView_(view)

            emoji = self._mk_label(
                NSMakeRect(14, 12, 50, 46),
                NSFont.systemFontOfSize_(38), NSColor.blackColor()
            )
            emoji.setStringValue_("🐼")
            emoji.setAlignment_(NSTextAlignmentLeft)
            view.addSubview_(emoji)

            self.label = self._mk_label(
                NSMakeRect(70, 20, self.W - 90, 30),
                NSFont.boldSystemFontOfSize_(16), NSColor.blackColor()
            )
            self.label.setAlignment_(NSTextAlignmentLeft)
            view.addSubview_(self.label)

    def _mk_label(self, frame, font, color):
        f = NSTextField.alloc().initWithFrame_(frame)
        f.setBezeled_(False)
        f.setDrawsBackground_(False)
        f.setEditable_(False)
        f.setSelectable_(False)
        f.setAlignment_(NSTextAlignmentCenter)
        f.setTextColor_(color)
        f.setFont_(font)
        return f

    def _set(self, text: str, color=None, font_size: int = None):
        def fn():
            self.label.setStringValue_(text)
            self.label.setTextColor_(color if color is not None else NSColor.blackColor())
            if font_size is not None:
                self.label.setFont_(NSFont.boldSystemFontOfSize_(font_size))
            else:
                # restore default size by style
                default = 15 if self.style == "bubble" else 16
                self.label.setFont_(NSFont.boldSystemFontOfSize_(default))
            self.panel.orderFrontRegardless()
            if self._hide_timer:
                self._hide_timer.invalidate()
                self._hide_timer = None
        _on_main(fn)

    def show_recording(self):
        self._set("● Recording", NSColor.redColor(), font_size=22)

    def show_analyzing(self):
        amber = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.85, 0.65, 0.0, 1.0)
        self._set("Analyzing…", amber, font_size=20)

    def show_text(self, text: str, duration: float = 2.5):
        max_len = 36 if self.style == "bubble" else 30 if self.style == "capsule" else 20
        display = text if len(text) <= max_len else text[:max_len - 3] + "…"
        self._set(display, NSColor.blackColor())

        def schedule_hide():
            self._hide_timer = NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
                duration, False, lambda t: self.panel.orderOut_(None)
            )
        _on_main(schedule_hide)

    def hide(self):
        _on_main(lambda: self.panel.orderOut_(None))
