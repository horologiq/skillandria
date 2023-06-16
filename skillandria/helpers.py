import os
import sys
import appdirs

from PyQt6.QtCore import QSettings
from PyQt6.QtCore import QFile, QIODevice, QTextStream


def get_bookmark_db_path():
    data_dir = appdirs.user_data_dir(appname='skillandria')
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, 'bookmarks.db')
    return path


def get_db_path():
    data_dir = appdirs.user_data_dir(appname='skillandria')
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, 'video_data.db')
    return path


def get_icon_path(theme):
    base_path = os.path.abspath(os.path.dirname(__file__))

    if getattr(sys, 'frozen', False):
        icon_path = os.path.join(os.path.dirname(base_path), 'themes', theme)
    else:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'themes', theme)
    return icon_path


def get_theme_path(theme):
    # Get the base path of the bundled executable
    base_path = os.path.abspath(os.path.dirname(__file__))

    # Get the path to the icon files
    if getattr(sys, 'frozen', False):
        theme_path = os.path.join(os.path.dirname(base_path), 'themes', theme, 'style.qss')
    else:
        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'themes', theme, 'style.qss')
    return theme_path


def load_folder_path():
    settings = QSettings("skillandria")
    return settings.value("VideoPath", "")


def load_translation_language():
    settings = QSettings("skillandria")
    return settings.value("SubtitleLanguage", "es")


def load_stylesheet(theme_str):
    style_file = QFile(theme_str)
    if style_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        style = QTextStream(style_file).readAll()
        style_file.close()
        return style

    else:
        return ""
