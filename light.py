import ctypes
from ctypes import wintypes
import atexit

gdi32 = ctypes.windll.gdi32
user32 = ctypes.windll.user32

hDC = user32.GetDC(0)

def create_gamma(percent):
    min_real = 50  # gamma mínimo real que funciona
    max_real = 100  # gamma máximo (normal)

    # Mapear percent 0..100 al rango real
    real_percent = min_real + (percent / 100.0) * (max_real - min_real)
    ramp = (wintypes.WORD * 768)()
    for i in range(256):
        # valor escalado linealmente
        value = int((i / 255.0) * 65535 * (real_percent / 100.0))
        value = max(0, min(65535, value))  # asegurar rango válido
        ramp[i] = value         # Red
        ramp[i + 256] = value   # Green
        ramp[i + 512] = value   # Blue
    return ramp

# Guardar gamma original para restaurar
original_ramp = (wintypes.WORD * 768)()
gdi32.GetDeviceGammaRamp(hDC, ctypes.byref(original_ramp))

def restore_gamma():
    gdi32.SetDeviceGammaRamp(hDC, ctypes.byref(original_ramp))

atexit.register(restore_gamma)

# Ejemplo: cambiar el brillo a cualquier porcentaje
percent = 0  # poner de 1 a 100
gamma_ramp = create_gamma(percent)
gdi32.SetDeviceGammaRamp(hDC, ctypes.byref(gamma_ramp))

print(f"Brillo ajustado al {percent}%. Ctrl+C para restaurar y salir.")

try:
    while True:
        pass
except KeyboardInterrupt:
    pass