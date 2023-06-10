import os
import re

from PyQt5.QtCore import QSettings


def time_to_milliseconds(time_str):
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = parts[2].replace(",", ".")
    milliseconds = int(float(seconds) * 1000)
    milliseconds += hours * 60 * 60 * 1000
    milliseconds += minutes * 60 * 1000
    return milliseconds


def human_sort_key(name):
    parts = re.split(r'(\d+)', name)
    return [int(part) if part.isdigit() else part for part in parts]


def load_folder_path():
    settings = QSettings("config.ini", QSettings.IniFormat)
    return settings.value("VideoPath", "")


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)


def is_video_file(file_path):
    video_extensions = [".mp4", ".avi", ".mkv", ".mov"]  # Add more video file extensions if needed
    return any(file_path.lower().endswith(extension) for extension in video_extensions)


def get_video_info(index):
    node = index.internalPointer()
    if node:
        return node.position, node.played
    return None


def reset_video_info(index):
    node = index.internalPointer()
    if node:
        node.position = 0
        node.played = False


def save_video_info(index):
    node = index.internalPointer()
    if node and os.path.isfile(node.path):
        info_path = os.path.splitext(node.path)[0] + ".nfo"
        with open(info_path, "w") as info_file:
            info_file.write("Position: {}\n".format(node.position))
            info_file.write("Played: {}\n".format(node.played))


def read_played_status(folder_path):  # Accept folder_path as a parameter
    played_status = {}
    for root, dirs, files in os.walk(folder_path):  # Use folder_path parameter
        for file in files:
            if file.endswith(".nfo"):
                nfo_file_path = os.path.join(root, file)
                video_file_path = os.path.splitext(nfo_file_path)[0]
                played = False
                with open(nfo_file_path, "r") as nfo_file:
                    for line in nfo_file:
                        if line.strip().startswith("Played="):
                            played_value = line.strip().split("=")[1]
                            played = played_value.lower() == "true"
                            break
                played_status[video_file_path] = played
    return played_status


def update_played_status(node):
    nfo_file_path = os.path.splitext(node.path)[0] + ".nfo"
    if os.path.isfile(nfo_file_path):
        with open(nfo_file_path, "r") as nfo_file:
            for line in nfo_file:
                if line.strip().startswith("Played="):
                    played_value = line.strip().split("=")[1]
                    node.played = played_value.lower() == "true"
                    break


def load_translation_language():
    settings = QSettings("config.ini", QSettings.IniFormat)
    return settings.value("SubtitleLanguage", "es")
