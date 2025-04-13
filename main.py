# main
# Cherry_C9H13N created on 2025/4/7
import tkinter as tk
from tkinter import ttk, Canvas
from tkinter import filedialog
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import json
import time
import re
import shutil
import win32gui
import win32ui
import win32con
import win32api
import sys
import ctypes
from ctypes import wintypes

DEFAULT_PATH = os.path.join(os.environ["USERPROFILE"], "AppData", "LocalLow", "DoubleCross", "SultansGame", "SAVEDATA")
CONFIG_FILE = os.path.join(DEFAULT_PATH, "config.json")
SETTING_FILE = os.path.join(DEFAULT_PATH, "setting.json")
CURRENT_SAVE_PATH = DEFAULT_PATH
MORE_SAVE_PATH = os.path.join(DEFAULT_PATH, "save-manager")
CURRENT_ID = ''
GAME_WINDOW_NAME = "Sultan's Game"

if getattr(sys, 'frozen', False):
    current_dir = sys._MEIPASS
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))


def is_failure_save(folder_path):
    files = os.listdir(folder_path)

    has_auto_save = "auto_save.json" in files
    has_round_end = any(re.match(r"round_\d+_end\.json", f) for f in files)

    return not has_auto_save and not has_round_end


def get_folder_info(folder_path):
    folder_name = os.path.basename(folder_path)
    item = {
        "name": folder_name,
        "description": "无描述。",
        "timestamp": int(os.path.getmtime(folder_path)),
        "path": os.path.abspath(folder_path),
        "failure": False,
        "ingame": None
    }

    # 查找最大 round 文件
    round_files = [
        f for f in os.listdir(folder_path)
        if re.match(r"round_(\d+)_end\.json", f)
    ]
    turns = [
        int(re.search(r"round_(\d+)_end\.json", f).group(1))
        for f in round_files
    ]
    item["turn"] = max(turns) + 1 if turns else 1

    # 读取 global.json
    global_path = os.path.join(folder_path, "global.json")
    if os.path.exists(global_path):
        try:
            with open(global_path, 'r', encoding='utf-8') as f:
                global_data = json.load(f)
            if isinstance(global_data, dict) and "inGame" in global_data:
                item["ingame"] = bool(global_data["inGame"])
        except Exception as e:
            print(f"读取 {global_path} 失败：{e}")
            item["failure"] = True
    else:
        item["failure"] = True

    if is_failure_save(folder_path):
        item["failure"] = True

    # 图片路径
    preview_path = os.path.join(folder_path, "preview.jpg")
    item["image"] = preview_path if os.path.exists(preview_path) else ""

    return item


def load_or_create_config():
    global CURRENT_SAVE_PATH, CURRENT_ID
    if not os.path.exists(MORE_SAVE_PATH):
        os.makedirs(MORE_SAVE_PATH)
    if not os.path.exists(os.path.join(DEFAULT_PATH, 'ScreenShot')):
        os.makedirs(os.path.join(DEFAULT_PATH, 'ScreenShot'))

    if os.path.exists(SETTING_FILE):
        with open(SETTING_FILE, "r", encoding="utf-8") as f:
            setting = json.load(f)
        CURRENT_SAVE_PATH = setting['SAVE_PATH']
        CURRENT_ID = setting['ID']
    else:
        CURRENT_ID = find_latest_numeric_folder(DEFAULT_PATH)
        setting = {'SAVE_PATH': f'{DEFAULT_PATH}',
                   'ID': f'{CURRENT_ID}'}
        with open(SETTING_FILE, "w", encoding="utf-8") as f:
            json.dump(setting, f, ensure_ascii=False, indent=2)

    existing_items = []

    # 读取旧的 config.json（如果存在）
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            existing_items = json.load(f)

    # 生成 folder_name -> item 映射（旧）
    old_items_map = {
        os.path.basename(item["path"]): item
        for item in existing_items
        if os.path.exists(item["path"])
    }

    # 扫描当前文件夹（新）
    updated_items = []

    for folder_name in os.listdir(MORE_SAVE_PATH):
        folder_path = os.path.join(MORE_SAVE_PATH, folder_name)
        if not os.path.isdir(folder_path):
            continue

        # 如果已有记录并且目录仍存在，保留并更新必要字段
        if folder_name in old_items_map:
            item = old_items_map[folder_name]
            item["timestamp"] = int(os.path.getmtime(folder_path))
            item["path"] = os.path.abspath(folder_path)
            item["failure"] = False
            item["ingame"] = None
            # 查找最大 round 文件
            round_files = [
                f for f in os.listdir(folder_path)
                if re.match(r"round_(\d+)_end\.json", f)
            ]
            turns = [
                int(re.search(r"round_(\d+)_end\.json", f).group(1))
                for f in round_files
            ]
            item["turn"] = max(turns) + 1 if turns else 1
            # 读取 global.json
            global_path = os.path.join(folder_path, "global.json")
            if os.path.exists(global_path):
                try:
                    with open(global_path, 'r', encoding='utf-8') as f:
                        global_data = json.load(f)
                    if isinstance(global_data, dict) and "inGame" in global_data:
                        item["ingame"] = bool(global_data["inGame"])
                except Exception as e:
                    print(f"读取 {global_path} 失败：{e}")
                    item["failure"] = True
            else:
                item["failure"] = True
            if is_failure_save(folder_path):
                item["failure"] = True
        else:
            item = get_folder_info(folder_path)

        updated_items.append(item)

    # 保存为 config.json
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_items, f, ensure_ascii=False, indent=2)

    cleanup_unused_images()

    return updated_items


def find_latest_numeric_folder(path):
    if not os.path.exists(DEFAULT_PATH):
        return ""

    numeric_folders = []

    for name in os.listdir(path):
        full_path = os.path.join(path, name)
        if os.path.isdir(full_path) and re.fullmatch(r"\d+", name):
            mtime = os.path.getmtime(full_path)
            numeric_folders.append((name, mtime))

    if not numeric_folders:
        return ""  # 没有符合条件的文件夹

    # 根据修改时间排序，取最新的
    latest_folder = max(numeric_folders, key=lambda x: x[1])[0]
    return latest_folder


def format_timestamp(ts):
    tz = timezone(timedelta(hours=8))
    return datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d  %H:%M:%S")


def new_folder_name():
    # 匹配 “存档数字” 的正则
    pattern = re.compile(r"^存档(\d+)$")
    max_n = 0
    # 遍历目录中的所有文件夹
    for name in os.listdir(MORE_SAVE_PATH):
        full_path = os.path.join(MORE_SAVE_PATH, name)
        if os.path.isdir(full_path):
            match = pattern.match(name)
            if match:
                n = int(match.group(1))
                if n > max_n:
                    max_n = n
    # 生成新的文件夹名
    return f"存档{max_n + 1}"


def get_window_scaling(hwnd):
    try:
        user32 = ctypes.windll.user32
        get_dpi_for_window = user32.GetDpiForWindow
        get_dpi_for_window.restype = ctypes.c_uint
        get_dpi_for_window.argtypes = [wintypes.HWND]
        dpi = get_dpi_for_window(hwnd)
        return dpi / 96.0
    except AttributeError:
        # 兼容旧系统
        dc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, dc)
        return dpi / 96.0


def screenshot_window(window_title_keyword):
    def enum_windows_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_title_keyword.lower() in title.lower():
                results.append((hwnd))

    # 获取匹配窗口句柄
    matches = []
    win32gui.EnumWindows(enum_windows_callback, matches)

    if not matches:
        print("未找到匹配窗口")
        return None

    hwnd = matches[0]
    print(f"捕获窗口：{win32gui.GetWindowText(hwnd)}")

    # 如果窗口最小化，先还原
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)

    # 激活窗口（必须要可见）
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.2)

    # 获取 DPI 缩放
    scale = get_window_scaling(hwnd)

    # 获取窗口客户区大小（排除边框和标题栏）
    client_rect = win32gui.GetClientRect(hwnd)
    width = int((client_rect[2] - client_rect[0]) * scale)
    height = int((client_rect[3] - client_rect[1]) * scale)

    # 获取客户区在屏幕上的位置（相对于桌面左上角）
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    left = int(left * scale)
    top = int(top * scale)

    # 获取桌面截图（可包含游戏画面）
    hdesktop = win32gui.GetDesktopWindow()
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()

    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)

    # 将屏幕内容复制到内存 DC 中
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

    # 转为 PIL Image
    bmpinfo = screenshot.GetInfo()
    bmpstr = screenshot.GetBitmapBits(True)
    img = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )

    # 保存
    if not os.path.exists(os.path.join(DEFAULT_PATH, 'ScreenShot')):
        os.makedirs(os.path.join(DEFAULT_PATH, 'ScreenShot'))
    img_path = os.path.join(DEFAULT_PATH, 'ScreenShot',
                            f"{datetime.fromtimestamp(int(time.time())).strftime('%Y%m%d-%H%M%S')}.png")
    img.save(img_path)
    print(f"截图保存")

    # 清理
    win32gui.DeleteObject(screenshot.GetHandle())
    mem_dc.DeleteDC()
    img_dc.DeleteDC()
    win32gui.ReleaseDC(hdesktop, desktop_dc)

    return img_path


def cleanup_unused_images():
    # 读取 config.json 中所有引用的图片路径
    if not os.path.exists(CONFIG_FILE):
        print("config.json 不存在")
        return

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 收集所有正在使用的图片绝对路径
    used_images = set()
    for item in config:
        image_path = item.get("image")
        if image_path:
            abs_path = os.path.abspath(image_path)
            used_images.add(abs_path)

    # 遍历 ScreenShot 文件夹
    for filename in os.listdir(os.path.join(DEFAULT_PATH, 'ScreenShot')):
        file_path = os.path.abspath(os.path.join(DEFAULT_PATH, 'ScreenShot', filename))

        # 如果不是正在使用的图片，则删除
        if file_path not in used_images:
            try:
                os.remove(file_path)
                print(f"删除未使用的图片：{file_path}")
            except Exception as e:
                print(f"删除图片失败：{file_path}, 错误：{e}")


class ItemListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("苏丹的游戏-存档管理器")
        self.icon = tk.PhotoImage(file=os.path.join(current_dir, "recall.png"))
        self.root.iconphoto(True, self.icon)

        self.selected_index = None
        self.images = []
        self.item_widgets = []

        self.canvas = None
        self.frame = None

        self.setup_base_ui()
        self.refresh_item_list()

    def setup_base_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        root.geometry("425x700")
        root.resizable(False, True)  # 水平不可拉伸，垂直可以拉伸

        container = tk.Frame(self.root)
        container.grid(row=0, column=0, sticky="nsew")

        self.canvas = tk.Canvas(container, borderwidth=0, background="#f5f5f5")
        self.frame = tk.Frame(self.canvas, background="#f5f5f5")
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows / macOS

        def _bind_mousewheel(widget):
            widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", _on_mousewheel))
            widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))

        _bind_mousewheel(self.canvas)

        button_frame = tk.Frame(self.root)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        settings_btn = ttk.Button(button_frame, text="设置", command=self.open_settings_dialog)
        refresh_btn = ttk.Button(button_frame, text="刷新", command=self.reload)
        save_btn = ttk.Button(button_frame, text="创建存档", command=self.save_new_item)

        settings_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        refresh_btn.pack(side="left", expand=True, fill="x", padx=(5, 5))
        save_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

    def refresh_item_list(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.item_widgets.clear()
        self.images.clear()

        for idx, item in enumerate(items):
            self.create_item_widget(idx, item)

    def reload(self):
        global items
        items = load_or_create_config()
        self.refresh_item_list()

    def set_widget_background(self, widget, color):
        try:
            widget.configure(background=color)
        except:
            pass
        for child in widget.winfo_children():
            self.set_widget_background(child, color)

    def select_item(self, idx):
        print(f"选中 item {idx}")
        for i, frame in enumerate(self.item_widgets):
            if i == idx:
                self.set_widget_background(frame, "#cce5ff")
            else:
                self.set_widget_background(frame, "white")
        self.selected_index = idx

    def open_edit_dialog(self, i):
        item = items[i]

        def browse_image():
            path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")], initialdir=os.path.dirname(item["image"]))
            if path:
                image_path_var.set(path)

        def open_folder():
            folder_path = os.path.dirname(item["path"])
            os.startfile(folder_path)

        def save_changes():
            if name_var.get():
                item["name"] = name_var.get()
            if desc_var.get():
                item["description"] = desc_var.get()
            else:
                item["description"] = "无描述。"
            if image_path_var.get():
                item["image"] = image_path_var.get()
            else:
                item["image"] = ""

            items[i] = item
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)

            # 更新 UI、刷新界面等]
            self.refresh_item_list()
            dialog.destroy()

        def info_cancel():
            self.refresh_item_list()
            dialog.destroy()

        # 获取主窗口的尺寸和位置
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        window_x = self.root.winfo_x()
        window_y = self.root.winfo_y()

        dialog_width = 300
        dialog_height = 300

        new_x = window_x + (window_width - dialog_width) // 2
        new_y = window_y + (window_height - dialog_height) // 2

        dialog = tk.Toplevel(self.root)
        dialog.title("编辑存档信息")
        dialog.geometry(f"{dialog_width}x{dialog_height}+{new_x}+{new_y}")
        dialog.resizable(False, False)
        dialog.grab_set()

        name_var = tk.StringVar(value=item["name"])
        desc_var = tk.StringVar(value=item["description"])
        image_path_var = tk.StringVar(value=item["image"])
        path_var = tk.StringVar(value=item["path"])

        tk.Label(dialog, text="存档名称：").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(dialog, textvariable=name_var, width=39).grid(row=1, column=0, padx=10, pady=0, sticky='w')

        tk.Label(dialog, text="存档描述：").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(dialog, textvariable=desc_var, width=39).grid(row=3, column=0, padx=10, pady=0, sticky='w')

        tk.Label(dialog, text="图片路径：").grid(row=4, column=0, padx=10, pady=5, sticky='w')
        ttk.Entry(dialog, textvariable=image_path_var, width=33).grid(row=5, column=0, padx=10, pady=0, sticky='w')
        ttk.Button(dialog, text="选择", command=browse_image, width=4).grid(row=5, column=0, padx=10, pady=0, sticky='e')

        tk.Label(dialog, text="存档路径：").grid(row=6, column=0, padx=10, pady=5, sticky='w')
        tk.Entry(dialog, textvariable=path_var, state="readonly", width=33).grid(row=7, column=0, padx=10, pady=0, sticky='w')
        ttk.Button(dialog, text="打开", command=open_folder, width=4).grid(row=7, column=0, padx=10, pady=0, sticky='e')

        # 保存/取消按钮
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=8, column=0, pady=15)

        ttk.Button(btn_frame, text="保存", command=save_changes).pack(side="left", expand=True, padx=5)
        ttk.Button(btn_frame, text="取消", command=info_cancel).pack(side="right", expand=True, padx=5)

        dialog.columnconfigure(1, weight=1)

    def create_item_widget(self, idx, item):
        item_frame = tk.Frame(self.frame, bd=2, relief="groove", background="white", width=400, height=98)
        item_frame.pack_propagate(False)
        item_frame.pack(fill="x", pady=5, padx=5)

        top_frame = tk.Frame(item_frame, background="white")
        top_frame.pack(fill="x")

        def create_image_widget(parent):
            max_width = 128  # 最大宽度
            max_height = 84  # 最大高度

            # 加载图片
            try:
                image = Image.open(item["image"]) if item["image"] else Image.new("RGB", (max_width, max_height))
            except:
                image = Image.new("RGB", (max_width, max_height))

            # 按比例缩放图片
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            # 转换为 Tkinter 可用的 PhotoImage
            photo = ImageTk.PhotoImage(image)
            # 创建 canvas 承载图片
            canvas = Canvas(parent, background="white", width=max_width, height=max_height, highlightthickness=0)
            canvas.create_image(max_width // 2, max_height // 2, anchor='center', image=photo)
            canvas.image = photo  # 保持引用，防止被回收

            def create_rotated_text_image(text, angle, font_size=18):
                # 创建空白图像
                font = ImageFont.truetype("msyhbd.ttc", font_size)
                font.font_variant = 'bold'
                text_size = font.getbbox(text)
                img_size = (text_size[2] + 10, text_size[3] + 10)
                img = Image.new("RGBA", img_size, (255, 0, 0, 0))  # 透明背景
                draw = ImageDraw.Draw(img)
                draw.text((5, 5), text, font=font, fill="white")
                # 旋转
                rotated = img.rotate(angle, expand=True)
                return ImageTk.PhotoImage(rotated)

            if item["failure"]:
                # 在右下角绘制红色直角三角形
                size = 54
                canvas.create_polygon(
                    max_width, max_height,  # 右下角
                    max_width - size, max_height,  # 左一点
                    max_width, max_height - size,  # 上一点
                    fill="#dd3322", outline=""
                )
                # 创建旋转文字图片
                rotated_text = create_rotated_text_image("损坏", angle=45)
                canvas.create_image(max_width - size // 2 + 6, max_height - size // 2 + 6, image=rotated_text)
                canvas.rotated_text = rotated_text  # 保持引用

            elif item["ingame"] is False:
                # 在右下角绘制蓝色直角三角形
                size = 54
                canvas.create_polygon(
                    max_width, max_height,  # 右下角
                    max_width - size, max_height,  # 左一点
                    max_width, max_height - size,  # 上一点
                    fill="#2299dd", outline=""
                )
                # 创建旋转文字图片
                rotated_text = create_rotated_text_image("完结", angle=45)
                canvas.create_image(max_width - size // 2 + 6, max_height - size // 2 + 6, image=rotated_text)
                canvas.rotated_text = rotated_text  # 保持引用

            return canvas

        image_canvas = create_image_widget(top_frame)
        image_canvas.pack(side="left", padx=5, pady=5)

        text_frame = tk.Frame(top_frame, background="white", width=200, height=72)
        text_frame.pack_propagate(False)
        text_frame.pack(side="left", fill="both", expand=True)

        # 四行文本信息
        tk.Label(text_frame, text=f"{item.get('name', '')}", background="white", anchor="w",
                 font=("等线", 12, "bold"), width=16).pack(fill="x")
        tk.Label(text_frame, text=f"{format_timestamp(item.get('timestamp', int(time.time())))}", background="white",
                 anchor="w", fg="#555555").pack(fill="x")
        tk.Label(text_frame, text=f"{item.get('description', '')}", background="white", anchor="w").pack(fill="x")
        tk.Label(text_frame, text=f"当前回合：{item.get('turn', 0)}", background="white", anchor="w").pack(fill="x")

        btn_frame = tk.Frame(top_frame, background="white")
        btn_frame.pack(side="right", padx=5)

        load_btn = ttk.Button(btn_frame, text="载入", width=6, command=lambda i=idx: self.load_save(i))
        rollback_btn = ttk.Button(btn_frame, text="回溯", width=6, command=lambda i=idx: self.rollback_item(i))
        delete_btn = ttk.Button(btn_frame, text="删除", width=6, command=lambda i=idx: self.confirm_delete(i))

        load_btn.pack(pady=2)
        rollback_btn.pack(pady=2)
        delete_btn.pack(pady=2)

        if item["failure"]:
            load_btn.state(["disabled"])
            rollback_btn.state(["disabled"])

        def bind_click_recursive(swidget, switch, callback):
            swidget.bind(switch, callback)
            for child in swidget.winfo_children():
                bind_click_recursive(child, switch, callback)

        bind_click_recursive(item_frame, "<Button-1>", lambda e, i=idx: self.select_item(i))
        bind_click_recursive(item_frame, "<Double-Button-1>", lambda e, i=idx: self.open_edit_dialog(i))

        self.item_widgets.append(item_frame)

    def load_save(self, idx):
        # 获取主窗口的尺寸和位置
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        window_x = self.root.winfo_x()
        window_y = self.root.winfo_y()

        dialog_width = 300
        dialog_height = 180

        new_x = window_x + (window_width - dialog_width) // 2
        new_y = window_y + (window_height - dialog_height) // 2

        win = tk.Toplevel(self.root)
        win.title("载入存档")
        win.geometry(f"{dialog_width}x{dialog_height}+{new_x}+{new_y}")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=f"载入存档会覆盖正在进行的游戏，是否需要帮您备份进行中的游戏存档？", wraplength=280, justify='center').pack(pady=10)

        # 创建一个带红色字体的按钮样式
        style = ttk.Style()
        style.configure("Red.TButton", foreground="red")

        backup_btn = ttk.Button(win, text="创建备份，并载入存档（推荐）", width=280)
        backup_btn.pack(padx=20, pady=2)
        cover_btn = ttk.Button(win, text="无需备份，直接载入存档覆盖", style="Red.TButton", width=280)
        cover_btn.pack(padx=20, pady=2)
        cancel_btn = ttk.Button(win, text="取消", width=280)
        cancel_btn.pack(padx=20, pady=2)

        def backup_load():
            # 备份
            item = {
                "name": new_folder_name(),
                "description": f"载入存档时自动备份的存档。",
                "timestamp": int(time.time()),
            }

            save_path = os.path.join(MORE_SAVE_PATH, new_folder_name())
            current_path = os.path.join(CURRENT_SAVE_PATH, CURRENT_ID)

            # 复制整个
            shutil.copytree(current_path, save_path)
            item["path"] = save_path

            item["failure"] = False
            item["ingame"] = None
            # 查找最大 round 文件
            round_files = [
                f for f in os.listdir(save_path)
                if re.match(r"round_(\d+)_end\.json", f)
            ]
            turns = [
                int(re.search(r"round_(\d+)_end\.json", f).group(1))
                for f in round_files
            ]
            item["turn"] = max(turns) + 1 if turns else 1

            # 读取 global.json
            global_path = os.path.join(save_path, "global.json")
            if os.path.exists(global_path):
                try:
                    with open(global_path, 'r', encoding='utf-8') as f:
                        global_data = json.load(f)
                    if isinstance(global_data, dict) and "inGame" in global_data:
                        item["ingame"] = bool(global_data["inGame"])
                except Exception as e:
                    print(f"读取 {global_path} 失败：{e}")
                    item["failure"] = True
            else:
                item["failure"] = True

            if is_failure_save(save_path):
                item["failure"] = True

            save_img = screenshot_window(GAME_WINDOW_NAME)
            item["image"] = save_img if save_img else ""

            items.append(item)

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)

            if os.path.exists(current_path):
                shutil.rmtree(current_path)

            shutil.copytree(items[idx]["path"], current_path)
            auto_save_path = os.path.join(current_path, "auto_save.json")
            if items[idx]["ingame"] and not os.path.exists(auto_save_path):
                # 查找最大 round 文件
                round_files = [
                    f for f in os.listdir(current_path)
                    if re.match(r"round_(\d+)_end\.json", f)
                ]
                turns = [
                    int(re.search(r"round_(\d+)_end\.json", f).group(1))
                    for f in round_files
                ]

                os.rename(os.path.join(current_path, f"round_{max(turns)}_end.json"), auto_save_path)

            self.refresh_item_list()
            win.destroy()

            time.sleep(0.2)
            hwnd_gui = self.root.winfo_id()
            win32gui.ShowWindow(hwnd_gui, win32con.SW_RESTORE)  # 恢复窗口（如果被最小化）
            win32gui.SetForegroundWindow(hwnd_gui)  # 置前激活
            self.refresh_item_list()
            win.destroy()

        def cover_load():
            current_path = os.path.join(CURRENT_SAVE_PATH, CURRENT_ID)
            if os.path.exists(current_path):
                shutil.rmtree(current_path)

            shutil.copytree(items[idx]["path"], current_path)
            auto_save_path = os.path.join(current_path, "auto_save.json")
            if items[idx]["ingame"] and not os.path.exists(auto_save_path):
                # 查找最大 round 文件
                round_files = [
                    f for f in os.listdir(current_path)
                    if re.match(r"round_(\d+)_end\.json", f)
                ]
                turns = [
                    int(re.search(r"round_(\d+)_end\.json", f).group(1))
                    for f in round_files
                ]

                os.rename(os.path.join(current_path, f"round_{max(turns)}_end.json"), auto_save_path)

            self.refresh_item_list()
            win.destroy()

        def load_cancel():
            self.refresh_item_list()
            win.destroy()

        backup_btn.config(command=backup_load)
        cover_btn.config(command=cover_load)
        cancel_btn.config(command=load_cancel)

    # 弹出二次确认删除的对话框
    def confirm_delete(self, idx):
        # 获取主窗口的尺寸和位置
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        window_x = self.root.winfo_x()
        window_y = self.root.winfo_y()

        dialog_width = 300
        dialog_height = 100

        new_x = window_x + (window_width - dialog_width) // 2
        new_y = window_y + (window_height - dialog_height) // 2

        win = tk.Toplevel(self.root)
        win.title("确认删除")
        win.geometry(f"{dialog_width}x{dialog_height}+{new_x}+{new_y}")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=f"您确定要删除这个存档吗？").pack(pady=10)

        confirm_btn = ttk.Button(win, text="确认")
        confirm_btn.pack(side="left", expand=True, padx=20, pady=10)
        cancel_btn = ttk.Button(win, text="取消")
        cancel_btn.pack(side="right", expand=True, padx=20, pady=10)

        def delete_confirm():
            self.delete_item(idx)

            self.refresh_item_list()
            win.destroy()

        def delete_cancel():
            self.refresh_item_list()
            win.destroy()

        confirm_btn.config(command=delete_confirm)
        cancel_btn.config(command=delete_cancel)

    def delete_item(self, idx):
        try:
            # 判断 file_path 是否在 base_dir 目录下
            if os.path.commonpath([items[idx]["path"], MORE_SAVE_PATH]) == MORE_SAVE_PATH:
                shutil.rmtree(items[idx]["path"])
            else:
                print("存档不在指定目录中，拒绝删除")
        except Exception as e:
            print(f'删除失败：{e}')

        del items[idx]

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        self.selected_index = None
        self.refresh_item_list()

    def save_new_item(self):
        # 获取主窗口的尺寸和位置
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        window_x = self.root.winfo_x()
        window_y = self.root.winfo_y()

        dialog_width = 300
        dialog_height = 180

        new_x = window_x + (window_width - dialog_width) // 2
        new_y = window_y + (window_height - dialog_height) // 2

        win = tk.Toplevel(self.root)
        win.title("创建存档")
        win.geometry(f"{dialog_width}x{dialog_height}+{new_x}+{new_y}")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="存档名称：").grid(row=0, column=0, padx=10, pady=5, sticky='w')

        name_var = tk.StringVar()
        name_var.set(new_folder_name())

        name_entry = ttk.Entry(win, textvariable=name_var, width=39)
        name_entry.grid(row=1, column=0, padx=10, pady=0, sticky='w')

        tk.Label(win, text="存档描述：").grid(row=2, column=0, padx=10, pady=5, sticky='w')

        discribe_var = tk.StringVar()
        discribe_var.set('')

        discribe_entry = ttk.Entry(win, textvariable=discribe_var, width=39)
        discribe_entry.grid(row=3, column=0, padx=10, pady=0, sticky='w')

        btn_frame = tk.Frame(win)
        btn_frame.grid(row=4, column=0, pady=15)  # , columnspan=2

        confirm_btn = ttk.Button(btn_frame, text="保存")
        confirm_btn.pack(side="left", expand=True, padx=5)
        cancel_btn = ttk.Button(btn_frame, text="取消")
        cancel_btn.pack(side="right", expand=True, padx=5)

        def save_confirm():
            item = {
                "name": 'AUTO_SAVE',
                "description": discribe_var.get() if discribe_var.get() else "无描述。",
                "timestamp": int(time.time()),
            }

            if os.path.exists(os.path.join(MORE_SAVE_PATH, name_var.get())):
                save_path = os.path.join(MORE_SAVE_PATH, new_folder_name())
                item["name"] = new_folder_name()
            else:
                save_path = os.path.join(MORE_SAVE_PATH, name_var.get())
                item["name"] = name_var.get()

            # 复制整个
            shutil.copytree(os.path.join(CURRENT_SAVE_PATH, CURRENT_ID), save_path)
            item["path"] = save_path

            item["failure"] = False
            item["ingame"] = None
            # 查找最大 round 文件
            round_files = [
                f for f in os.listdir(save_path)
                if re.match(r"round_(\d+)_end\.json", f)
            ]
            turns = [
                int(re.search(r"round_(\d+)_end\.json", f).group(1))
                for f in round_files
            ]
            item["turn"] = max(turns) + 1 if turns else 1

            # 读取 global.json
            global_path = os.path.join(save_path, "global.json")
            if os.path.exists(global_path):
                try:
                    with open(global_path, 'r', encoding='utf-8') as f:
                        global_data = json.load(f)
                    if isinstance(global_data, dict) and "inGame" in global_data:
                        item["ingame"] = bool(global_data["inGame"])
                except Exception as e:
                    print(f"读取 {global_path} 失败：{e}")
                    item["failure"] = True
            else:
                item["failure"] = True

            if is_failure_save(save_path):
                item["failure"] = True

            save_img = screenshot_window(GAME_WINDOW_NAME)
            item["image"] = save_img if save_img else ""

            items.append(item)

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)

            self.refresh_item_list()
            win.destroy()

            time.sleep(0.2)
            hwnd_gui = self.root.winfo_id()
            win32gui.ShowWindow(hwnd_gui, win32con.SW_RESTORE)  # 恢复窗口（如果被最小化）
            win32gui.SetForegroundWindow(hwnd_gui)  # 置前激活

        def save_cancel():
            self.refresh_item_list()
            win.destroy()

        confirm_btn.config(command=save_confirm)
        cancel_btn.config(command=save_cancel)

    def rollback_item(self, idx):
        item = items[idx]
        current_turn = item.get("turn", 1)

        # 获取主窗口的尺寸和位置
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        window_x = self.root.winfo_x()
        window_y = self.root.winfo_y()

        dialog_width = 300
        dialog_height = 150

        new_x = window_x + (window_width - dialog_width) // 2
        new_y = window_y + (window_height - dialog_height) // 2

        win = tk.Toplevel(self.root)
        win.title("回溯")
        win.geometry(f"{dialog_width}x{dialog_height}+{new_x}+{new_y}")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=f"该存档当前处于第 {current_turn} 回合，您想回溯到第几回合？").pack(pady=10)

        input_var = tk.StringVar()
        entry = ttk.Entry(win, textvariable=input_var)
        entry.pack()

        status_label = tk.Label(win, text="", fg="red")
        status_label.pack(pady=2)

        confirm_btn = ttk.Button(win, text="确认")
        confirm_btn.pack(side="left", expand=True, padx=20, pady=2)
        cancel_btn = ttk.Button(win, text="取消")
        cancel_btn.pack(side="right", expand=True, padx=20, pady=2)

        def validate_input():
            val = input_var.get()
            if not val.isdigit():
                status_label.config(text="输入只能为数字", fg="red")
                confirm_btn.state(["disabled"])
                return False
            val_int = int(val)
            if val_int >= current_turn:
                status_label.config(text="不能回溯到当前回合或更高", fg="red")
                confirm_btn.state(["disabled"])
                return False
            elif not os.path.exists(os.path.join(item["path"], f"round_{val_int}_end.json")):
                status_label.config(text=f"存档不完整，未能找到{val_int}回合的记录", fg="red")
                confirm_btn.state(["disabled"])
                return False
            status_label.config(text="回溯将会创建新的存档，不会覆盖现有存档", fg="green")
            confirm_btn.state(["!disabled"])
            return True

        def rollback_confirm():
            if validate_input():
                new_item = {
                    "name": new_folder_name(),
                    "description": f"由【{item['name']}】回溯至第{int(input_var.get())}回合的存档。",
                    "timestamp": int(time.time()),
                }

                save_path = os.path.join(MORE_SAVE_PATH, new_folder_name())

                # 复制整个
                shutil.copytree(item["path"], save_path)
                new_item["path"] = save_path

                # 读取 global.json
                new_item["failure"] = False
                new_item["ingame"] = None
                global_path = os.path.join(save_path, "global.json")
                if os.path.exists(global_path):
                    try:
                        with open(global_path, 'r', encoding='utf-8') as f:
                            global_data = json.load(f)
                        with open(global_path, 'w', encoding='utf-8') as f:
                            global_data["inGame"] = True
                            json.dump(global_data, f, ensure_ascii=False, separators=(',', ':'))
                            new_item["ingame"] = True
                    except Exception as e:
                        print(f"读取 {global_path} 失败：{e}")
                        new_item["failure"] = True
                else:
                    new_item["failure"] = True

                if is_failure_save(save_path):
                    new_item["failure"] = True

                new_item["turn"] = int(input_var.get())

                pattern_1 = re.compile(r"round_(\d+)_end\.json")
                pattern_2 = re.compile(r"round_(\d+)\.json")
                auto_save_path = os.path.join(save_path, "auto_save.json")

                for filename in os.listdir(save_path):
                    match_1 = pattern_1.match(filename)
                    match_2 = pattern_2.match(filename)
                    if match_1:
                        n = int(match_1.group(1))
                        file_path = os.path.join(save_path, filename)

                        if n == int(input_var.get()):
                            # 如果 auto_save.json 已存在，先删除
                            if os.path.exists(auto_save_path):
                                os.remove(auto_save_path)
                            os.rename(file_path, auto_save_path)
                            print(f"已重命名：{filename} → auto_save.json")
                        elif n > int(input_var.get()):
                            os.remove(file_path)
                            # print(f"已删除：{filename}")
                    if match_2:
                        n = int(match_2.group(1))
                        file_path = os.path.join(save_path, filename)
                        if n > int(input_var.get()):
                            os.remove(file_path)
                            # print(f"已删除：{filename}")

                new_item["image"] = item["image"]

                items.append(new_item)

                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)

                self.refresh_item_list()
                win.destroy()

        def rollback_cancel():
            self.refresh_item_list()
            win.destroy()

        confirm_btn.config(command=rollback_confirm)
        confirm_btn.state(["disabled"])
        cancel_btn.config(command=rollback_cancel)

        input_var.trace_add("write", lambda *args: validate_input())

    def open_settings_dialog(self):
        # 获取主窗口的尺寸和位置
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        window_x = self.root.winfo_x()
        window_y = self.root.winfo_y()

        dialog_width = 300
        dialog_height = 180

        new_x = window_x + (window_width - dialog_width) // 2
        new_y = window_y + (window_height - dialog_height) // 2

        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry(f"{dialog_width}x{dialog_height}+{new_x}+{new_y}")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="存档目录：").grid(row=0, column=0, padx=10, pady=5, sticky='w')

        save_var = tk.StringVar()
        save_var.set(CURRENT_SAVE_PATH)

        save_entry = ttk.Entry(win, textvariable=save_var, width=33)
        save_entry.grid(row=1, column=0, padx=10, pady=0, sticky='w')

        file_btn = ttk.Button(win, text="浏览", width=4)
        file_btn.grid(row=1, column=0, padx=10, pady=0, sticky='e')

        tk.Label(win, text="Steam ID：").grid(row=2, column=0, padx=10, pady=5, sticky='w')

        id_var = tk.StringVar()
        id_var.set(CURRENT_ID)

        id_entry = ttk.Entry(win, textvariable=id_var, width=39)
        id_entry.grid(row=3, column=0, padx=10, pady=0, sticky='w')

        btn_frame = tk.Frame(win)
        btn_frame.grid(row=4, column=0, pady=15)  # , columnspan=2

        default_btn = ttk.Button(btn_frame, text="恢复默认")
        default_btn.pack(side="left", expand=True, padx=(5, 5))
        confirm_btn = ttk.Button(btn_frame, text="确认")
        confirm_btn.pack(side="left", expand=True, padx=5)
        cancel_btn = ttk.Button(btn_frame, text="取消")
        cancel_btn.pack(side="right", expand=True, padx=5)

        def choose_folder():
            folder_path = filedialog.askdirectory(title="选择存档目录", initialdir=CURRENT_SAVE_PATH)
            if folder_path:
                print("选择的文件夹路径是：", folder_path)
                save_var.set(folder_path)

        def settings_confirm():
            global CURRENT_SAVE_PATH, CURRENT_ID
            CURRENT_SAVE_PATH = save_var.get() if save_var.get() else CURRENT_SAVE_PATH
            CURRENT_ID = id_var.get() if id_var.get() else CURRENT_ID
            setting = {'SAVE_PATH': f'{CURRENT_SAVE_PATH}',
                       'ID': f'{CURRENT_ID}'}
            with open(SETTING_FILE, "w", encoding="utf-8") as f:
                json.dump(setting, f, ensure_ascii=False, indent=2)

            self.refresh_item_list()
            win.destroy()

        def settings_cancel():
            self.refresh_item_list()
            win.destroy()

        def settings_default():
            save_var.set(DEFAULT_PATH)
            id_var.set(find_latest_numeric_folder(DEFAULT_PATH))

        file_btn.config(command=choose_folder)
        confirm_btn.config(command=settings_confirm)
        cancel_btn.config(command=settings_cancel)
        default_btn.config(command=settings_default)


if __name__ == "__main__":
    items = load_or_create_config()
    root = tk.Tk()
    app = ItemListApp(root)
    root.mainloop()
