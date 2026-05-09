"""
Floating status window: shows "Recording / Analyzing / <result>" near top of screen.
Always-on-top, click-through-friendly, doesn't steal focus.
"""
import objc
from AppKit import (
    NSPanel,
    NSColor,
    NSTextField,
    NSScreen,
    NSFont,
    NSBackingStoreBuffered,
    NSWindowStyleMaskBorderless,
    NSFloatingWindowLevel,
    NSTextAlignmentCenter,
    NSApp,
)
from Foundation import NSMakeRect, NSObject, NSTimer

WIDTH = 320
HEIGHT = 64
TOP_OFFSET = 80  # distance from top of screen


class _MainThreadProxy(NSObject):
    """Helper to dispatch closures onto the main thread (AppKit requirement)."""
    def runBlock_(self, block):
        block()


_proxy = _MainThreadProxy.alloc().init()


def _on_main(fn):
    _proxy.performSelectorOnMainThread_withObject_waitUntilDone_(
        "runBlock:", fn, False
    )


class StatusWindow:
    def __init__(self):
        screen = NSScreen.mainScreen().frame()
        x = (screen.size.width - WIDTH) / 2
        y = screen.size.height - TOP_OFFSET - HEIGHT

        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, WIDTH, HEIGHT),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        self.panel.setLevel_(NSFloatingWindowLevel)
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setHasShadow_(True)
        self.panel.setIgnoresMouseEvents_(True)  # click-through
        self.panel.setHidesOnDeactivate_(False)

        content = self.panel.contentView()
        content.setWantsLayer_(True)
        layer = content.layer()
        layer.setBackgroundColor_(
            NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.82).CGColor()
        )
        layer.setCornerRadius_(14.0)

        self.label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(12, 12, WIDTH - 24, HEIGHT - 24)
        )
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setAlignment_(NSTextAlignmentCenter)
        self.label.setTextColor_(NSColor.whiteColor())
        self.label.setFont_(NSFont.systemFontOfSize_(18))
        content.addSubview_(self.label)

        self._hide_timer = None

    def _set(self, text: str, color=None):
        def fn():
            self.label.setStringValue_(text)
            if color is not None:
                self.label.setTextColor_(color)
            else:
                self.label.setTextColor_(NSColor.whiteColor())
            self.panel.orderFrontRegardless()
            if self._hide_timer:
                self._hide_timer.invalidate()
                self._hide_timer = None
        _on_main(fn)

    def show_recording(self):
        self._set("🔴  Recording…")

    def show_analyzing(self):
        self._set("⏳  Analyzing…")

    def show_text(self, text: str, duration: float = 2.5):
        # Truncate very long results
        display = text if len(text) <= 60 else text[:57] + "…"
        self._set(display, NSColor.colorWithCalibratedRed_green_blue_alpha_(
            0.6, 1.0, 0.6, 1.0
        ))
        # Auto-hide after duration
        def schedule_hide():
            self._hide_timer = NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
                duration, False, lambda t: self.panel.orderOut_(None)
            )
        _on_main(schedule_hide)

    def hide(self):
        _on_main(lambda: self.panel.orderOut_(None))
