# screenshot
# Cherry_C9H13N created on 2025/4/25
import ctypes
import os
import time

import win32con
import win32gui
import win32ui
from PIL import Image

from constants import DEFAULT_PATH


def get_window_scaling(hwnd):
    try:
        user32 = ctypes.windll.user32
        dpi = user32.GetDpiForWindow(hwnd)
        return dpi / 96.0
    except AttributeError:
        dc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)
        ctypes.windll.user32.ReleaseDC(0, dc)
        return dpi / 96.0


def screenshot_window(window_title_keyword):
    # 查找窗口
    hwnd = None
    def enum_cb(h, _):
        nonlocal hwnd
        if win32gui.IsWindowVisible(h) and window_title_keyword.lower() in win32gui.GetWindowText(h).lower():
            hwnd = h
    win32gui.EnumWindows(enum_cb, None)

    if not hwnd:
        print("未找到窗口")
        return None

    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)

    scale = get_window_scaling(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    width = int((client_rect[2] - client_rect[0]) * scale)
    height = int((client_rect[3] - client_rect[1]) * scale)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    left = int(left * scale)
    top = int(top * scale)

    desktop_dc = win32gui.GetWindowDC(win32gui.GetDesktopWindow())
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()

    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(bmp)

    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
    bmp_info = bmp.GetInfo()
    bmp_data = bmp.GetBitmapBits(True)

    image = Image.frombuffer("RGB", (bmp_info["bmWidth"], bmp_info["bmHeight"]), bmp_data, "raw", "BGRX", 0, 1)

    os.makedirs(os.path.join(DEFAULT_PATH, "ScreenShot"), exist_ok=True)
    img_path = os.path.join(DEFAULT_PATH, "ScreenShot", f"{time.strftime('%Y%m%d-%H%M%S')}.png")
    image.save(img_path)

    win32gui.DeleteObject(bmp.GetHandle())
    mem_dc.DeleteDC()
    img_dc.DeleteDC()
    win32gui.ReleaseDC(win32gui.GetDesktopWindow(), desktop_dc)

    return img_path
