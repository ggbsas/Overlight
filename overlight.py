# overlay_clickthrough_win.py
# Overlay negro "dimmer" clic-through para Windows (multi-monitor).
# UP = aclarar (-step), DOWN = oscurecer (+step), ESC = salir.
# Probado en Python 3.8+ en Windows x86/x64.

import ctypes
from ctypes import wintypes
import sys

# DLLs
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# --- Constantes ---
WS_EX_LAYERED      = 0x00080000
WS_EX_TRANSPARENT  = 0x00000020
WS_EX_TOPMOST      = 0x00000008
WS_POPUP           = 0x80000000
LWA_ALPHA          = 0x00000002

SW_SHOW            = 5
WM_HOTKEY          = 0x0312
WM_DESTROY         = 0x0002
WM_CLOSE           = 0x0010

VK_UP     = 0x26
VK_DOWN   = 0x28
VK_ESCAPE = 0x1B

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# --- Tipos portables entre 32/64 bits ---
PTR_SIZE = ctypes.sizeof(ctypes.c_void_p)
if PTR_SIZE == 8:
    LRESULT = ctypes.c_longlong
else:
    LRESULT = ctypes.c_long

# Prototipos para evitar conversion issues
user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

# Declaramos WNDPROC con el tipo correcto según arquitectura
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

# Definimos una estructura WNDCLASS compatible (no usar wintypes.WNDCLASS directamente)
class MY_WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", ctypes.c_void_p),
        ("hCursor", ctypes.c_void_p),
        ("hbrBackground", ctypes.c_void_p),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]

# Prototipos de funciones (opcionales pero ayudan a ctypes a validar)
user32.RegisterClassW.argtypes = [ctypes.POINTER(MY_WNDCLASS)]
user32.RegisterClassW.restype = wintypes.ATOM

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.DWORD, wintypes.BYTE, wintypes.DWORD]
user32.SetLayeredWindowAttributes.restype = wintypes.BOOL

user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL

user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UpdateWindow.argtypes = [wintypes.HWND]

user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]

user32.DestroyWindow.argtypes = [wintypes.HWND]

gdi32.CreateSolidBrush.argtypes = [wintypes.DWORD]
gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL

# --- Variables globales (mantener referencias para evitar GC) ---
_wndproc_ref = None
_hbrush = None
_class_name = None
_hwnd = None

def make_overlay(initial_percent=50, step_percent=5):
    """Crea overlay fullscreen clic-through sobre la pantalla virtual (multi-monitor)
    initial_percent: 0..100 (0 invisible, 100 negro opaco)
    step_percent: cuánto cambia cada hotkey
    """
    global _wndproc_ref, _hbrush, _class_name, _hwnd

    hInstance = kernel32.GetModuleHandleW(None)
    if not hInstance:
        raise ctypes.WinError(ctypes.get_last_error())

    _class_name = "PyDimOverlayClass"

    # Callback de ventana
    @WNDPROC
    def wnd_proc(hWnd, msg, wParam, lParam):
        if msg == WM_CLOSE:
            user32.DestroyWindow(hWnd)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hWnd, msg, wParam, lParam)

    _wndproc_ref = wnd_proc  # mantener referencia

    # Crear brocha negra
    _hbrush = gdi32.CreateSolidBrush(0x000000)
    if not _hbrush:
        raise ctypes.WinError(ctypes.get_last_error())

    # Registrar clase
    wndclass = MY_WNDCLASS()
    wndclass.style = 0
    wndclass.lpfnWndProc = _wndproc_ref
    wndclass.cbClsExtra = 0
    wndclass.cbWndExtra = 0
    wndclass.hInstance = hInstance
    wndclass.hIcon = None
    wndclass.hCursor = None
    wndclass.hbrBackground = _hbrush
    wndclass.lpszMenuName = None
    wndclass.lpszClassName = _class_name

    atom = user32.RegisterClassW(ctypes.byref(wndclass))
    if not atom:
        err = ctypes.get_last_error()
        if err and err != 1410:  # ERROR_CLASS_ALREADY_EXISTS
            raise ctypes.WinError(err)

    # Obtener virtual screen (multimonitor)
    x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)

    exstyle = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
    style = WS_POPUP

    _hwnd = user32.CreateWindowExW(
        exstyle,
        _class_name,
        None,
        style,
        x, y, width, height,
        None, None, hInstance, None
    )
    if not _hwnd:
        raise ctypes.WinError(ctypes.get_last_error())

    user32.ShowWindow(_hwnd, SW_SHOW)
    user32.UpdateWindow(_hwnd)

    def set_opacity(percent):
        percent = max(0, min(100, int(percent)))
        alpha = int(255 * (percent / 100.0))
        if not user32.SetLayeredWindowAttributes(_hwnd, 0, alpha, LWA_ALPHA):
            raise ctypes.WinError(ctypes.get_last_error())

    # Registrar hotkeys globales
    if not user32.RegisterHotKey(None, 1, 0, VK_UP):
        print("Advertencia: no se pudo registrar hotkey UP. Prueba ejecutar como administrador.")
    if not user32.RegisterHotKey(None, 2, 0, VK_DOWN):
        print("Advertencia: no se pudo registrar hotkey DOWN.")
    if not user32.RegisterHotKey(None, 3, 0, VK_ESCAPE):
        print("Advertencia: no se pudo registrar hotkey ESC.")

    current = max(0, min(100, int(initial_percent)))
    step = max(1, int(step_percent))
    set_opacity(current)
    print(f"Overlay activo. UP = aclarar (-{step}%), DOWN = oscurecer (+{step}%), ESC = salir. Brillo actual: {current}%")

    msg = wintypes.MSG()
    try:
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0:
                break
            if ret == -1:
                raise ctypes.WinError(ctypes.get_last_error())

            if msg.message == WM_HOTKEY:
                kid = int(msg.wParam)
                if kid == 1:
                    current = max(0, current - step)
                    set_opacity(current)
                    print(f"Brillo: {current}%")
                elif kid == 2:
                    current = min(100, current + step)
                    set_opacity(current)
                    print(f"Brillo: {current}%")
                elif kid == 3:
                    print("ESC presionado: saliendo.")
                    break

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        try:
            user32.UnregisterHotKey(None, 1)
            user32.UnregisterHotKey(None, 2)
            user32.UnregisterHotKey(None, 3)
        except Exception:
            pass
        if _hwnd:
            user32.DestroyWindow(_hwnd)
        if _hbrush:
            gdi32.DeleteObject(_hbrush)
        try:
            user32.UnregisterClassW(_class_name, hInstance)
        except Exception:
            pass

if __name__ == "__main__":
    try:
        make_overlay(initial_percent=50, step_percent=5)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
