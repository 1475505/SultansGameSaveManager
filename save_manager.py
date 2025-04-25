# save_manager
# Cherry_C9H13N created on 2025/4/25
import os
import json
import re
from constants import *


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