import threading
import time
import Quartz

SPACE_KEYCODE = 49
OPTION_FLAG = Quartz.kCGEventFlagMaskAlternate


class HotkeyListener:
    """
    Push-to-talk: hold Option+Space to record, release either key to stop.
    Suppresses the Space keypress so it doesn't type into the active window.
    Requires Accessibility permission (System Settings > Privacy & Security > Accessibility).
    """

    def __init__(self, on_start, on_stop, on_press_immediate=None):
        self.on_start = on_start
        self.on_stop = on_stop
        # Called synchronously from the event tap — keep it FAST (e.g. play a sound)
        self.on_press_immediate = on_press_immediate
        self._option_held = False
        self._recording = False
        self._tap = None

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        mask = (
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
            | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
            | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
        )
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            mask,
            self._callback,
            None,
        )
        if not self._tap:
            print(
                "❌ 無法建立鍵盤監聽。請至「系統設定 > 隱私與安全性 > 輔助使用」授權 Terminal（或此 App）。"
            )
            return

        source = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(), source, Quartz.kCFRunLoopDefaultMode
        )
        Quartz.CGEventTapEnable(self._tap, True)
        Quartz.CFRunLoopRun()

    def _callback(self, proxy, event_type, event, refcon):
        # Re-enable the tap if macOS disabled it (happens if a previous callback was slow)
        if event_type in (Quartz.kCGEventTapDisabledByTimeout, Quartz.kCGEventTapDisabledByUserInput):
            Quartz.CGEventTapEnable(self._tap, True)
            return event

        flags = Quartz.CGEventGetFlags(event)
        self._option_held = bool(flags & OPTION_FLAG)

        if event_type == Quartz.kCGEventFlagsChanged:
            # Option released while recording → stop
            if not self._option_held and self._recording:
                self._stop()

        elif event_type == Quartz.kCGEventKeyDown:
            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode
            )
            if keycode == SPACE_KEYCODE and self._option_held and not self._recording:
                self._recording = True
                if self.on_press_immediate:
                    try:
                        self.on_press_immediate()
                    except Exception:
                        pass
                threading.Thread(target=self.on_start, daemon=True).start()
                return None

            if keycode == SPACE_KEYCODE and self._recording:
                return None  # suppress repeat space while recording

        elif event_type == Quartz.kCGEventKeyUp:
            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode
            )
            if keycode == SPACE_KEYCODE and self._recording:
                self._stop()
                return None  # suppress space up

        return event

    def _stop(self):
        self._recording = False
        threading.Thread(target=self.on_stop, daemon=True).start()
