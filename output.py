import subprocess
import time
import Quartz

# macOS key codes
V_KEY = 9
A_KEY = 0
C_KEY = 8
X_KEY = 7
Z_KEY = 6
RETURN_KEY = 36


def paste_text(text: str):
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    time.sleep(0.05)
    _keystroke(V_KEY, Quartz.kCGEventFlagMaskCommand)


def execute_command(command: str):
    if command == "undo":
        _keystroke(Z_KEY, Quartz.kCGEventFlagMaskCommand)
    elif command == "select_all":
        _keystroke(A_KEY, Quartz.kCGEventFlagMaskCommand)
    elif command == "copy":
        _keystroke(C_KEY, Quartz.kCGEventFlagMaskCommand)
    elif command == "cut":
        _keystroke(X_KEY, Quartz.kCGEventFlagMaskCommand)
    elif command == "newline":
        _keystroke(RETURN_KEY, 0)


def _keystroke(keycode: int, flags: int):
    src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)

    down = Quartz.CGEventCreateKeyboardEvent(src, keycode, True)
    Quartz.CGEventSetFlags(down, flags)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, down)

    time.sleep(0.02)

    up = Quartz.CGEventCreateKeyboardEvent(src, keycode, False)
    Quartz.CGEventSetFlags(up, flags)
    Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, up)
