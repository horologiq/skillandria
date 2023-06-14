import os
import sys

from PyQt6.QtCore import QSettings
from PyQt6.QtCore import QStandardPaths
from PyQt6.QtCore import QFile, QIODevice, QTextStream

config_dir = os.path.join(os.path.abspath(QStandardPaths.standardLocations(QStandardPaths.StandardLocation.AppConfigLocation)[0]), 'skillandria')
os.makedirs(config_dir, exist_ok=True)
config_file = os.path.join(config_dir, 'skillandria')
print(config_file)


def get_icon_path(theme):
    base_path = os.path.abspath(os.path.dirname(__file__))

    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(base_path, '..', 'themes', theme)
    else:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'themes', theme)
    return icon_path


def get_theme_path(theme):
    # Get the base path of the bundled executable
    base_path = os.path.abspath(os.path.dirname(__file__))

    # Get the path to the icon files
    if getattr(sys, 'frozen', False):
        theme_path = os.path.join(base_path, '..', 'themes', theme, 'style.qss')
    else:
        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'themes', theme, 'style.qss')
    return theme_path


def time_to_milliseconds(time_str):
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = parts[2].replace(",", ".")
    milliseconds = int(float(seconds) * 1000)
    milliseconds += hours * 60 * 60 * 1000
    milliseconds += minutes * 60 * 1000
    return milliseconds


def load_folder_path():
    settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, config_file)
    return settings.value("VideoPath", "")


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return "{:01d}:{:02d}:{:02d}".format(hours, minutes, seconds)


def load_translation_language():
    settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, config_file)
    return settings.value("SubtitleLanguage", "es")


def load_stylesheet(theme_str):
    style_file = QFile(theme_str)
    if style_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        style = QTextStream(style_file).readAll()
        style_file.close()
        return style

    else:
        return ""