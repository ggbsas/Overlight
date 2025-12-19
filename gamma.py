import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def set_gamma_brightness(opacity_percent):
    level = max(0.5, (100 - opacity_percent) / 100.0)
    hdc = user32.GetDC(None)
    ramp = (wintypes.WORD * 768)()
    for i in range(256):
        val = int(i * level * 257)
        if val > 65535:
            val = 65535

        ramp[i] = ramp[i+256] = ramp[i+512] = val
    gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp))
    user32.ReleaseDC(None, hdc)

def reset_gamma_ramp():
    try:
        hdc = user32.GetDC(None)
        ramp = (wintypes.WORD * 768)()
        for i in range(256):
            val = int(i * 257)
            if val > 65535:
                val = 65535

            ramp[i] = ramp[i + 256] = ramp[i + 512] = val
        gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp))
        user32.ReleaseDC(None, hdc)
    except:
        pass