import sys
from ctypes import windll

import gui

if __name__ == "__main__":
    # Tkinter has an annoying habit of looking blurry on high resolution monitors
    # This should solve the problem on windows
    if 'win' in sys.platform:
        windll.shcore.SetProcessDpiAwareness(1)
    try:
        app = gui.App()

        app.startup()
    except FileNotFoundError:
        pass

