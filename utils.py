import os
import ctypes
import psutil

user32 = ctypes.windll.user32
shcore = ctypes.windll.shcore if hasattr(ctypes.windll, "shcore") else None

def set_dpi_awareness():
    try:
        shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass

def set_low_priority():
    try:
        child = psutil.Process(os.getpid())
        child.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        parent = child.parent()
        if parent:
            parent.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except:
        pass
