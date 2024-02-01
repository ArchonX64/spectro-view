import sys
from ctypes import windll

import pandas as pd

import gui
import utils

if __name__ == "__main__":
    # Tkinter has an annoying habit of looking blurry on high resolution monitors
    # This should solve the problem on windows
    pd.options.mode.chained_assignment = None
    if 'win' in sys.platform:
        windll.shcore.SetProcessDpiAwareness(1)
    try:
        utils.resource_path("LL")
        app = gui.App()

        app.mainloop()
    except FileNotFoundError:
        pass

