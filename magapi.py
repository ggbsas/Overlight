import ctypes
from ctypes import wintypes

class MAGFULLSCREEN_COLOR_EFFECT(ctypes.Structure):
    _fields_ = [
        ("transform", ctypes.c_float * 25)
    ]

class MagBrightnessController:
    def __init__(self):
        self.mag_dll = None
        self.initialized = False

        try:
            self.mag_dll = ctypes.WinDLL("magnification.dll")
            self.mag_dll.MagInitialize.restype = wintypes.BOOL
            self.mag_dll.MagUninitialize.restype = wintypes.BOOL
            self.mag_dll.MagSetFullscreenColorEffect.argtypes = [ctypes.POINTER(MAGFULLSCREEN_COLOR_EFFECT)]
            self.mag_dll.MagSetFullscreenColorEffect.restype = wintypes.BOOL

            if not self.mag_dll.MagInitialize():
                return

            self.initialized = True
        except:
            pass

_controller = MagBrightnessController()

def set_magapi_brightness(opacity_percent):
    if not _controller.initialized:
        return False

    level = max(0.0, min(1.0, (100 - opacity_percent) / 100.0))

    matrix = MAGFULLSCREEN_COLOR_EFFECT(
        (ctypes.c_float * 25)(
            level, 0, 0, 0, 0,
            0, level, 0, 0, 0,
            0, 0, level, 0, 0,
            0, 0, 0, 1, 0,
            0, 0, 0, 0, 1
        )
    )

    return _controller.mag_dll.MagSetFullscreenColorEffect(ctypes.byref(matrix))

def reset_magapi_ramp():
    if not _controller.initialized:
        return

    identity = MAGFULLSCREEN_COLOR_EFFECT(
        (ctypes.c_float * 25)(
            1, 0, 0, 0, 0,
            0, 1, 0, 0, 0,
            0, 0, 1, 0, 0,
            0, 0, 0, 1, 0,
            0, 0, 0, 0, 1
        )
    )

    _controller.mag_dll.MagSetFullscreenColorEffect(ctypes.byref(identity))
    _controller.mag_dll.MagUninitialize()
    _controller.initialized = False
