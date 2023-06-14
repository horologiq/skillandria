from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, \
    QCheckBox

from skillandria.helpers import *


class SettingsDialog(QDialog):
    languageChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Settings")
        self.setFixedSize(400, 200)

        self.layout = QVBoxLayout(self)

        self.settings = QSettings("skillandria")

        # Video Path Section
        self.video_path_layout = QHBoxLayout()
        self.video_path_label = QLabel("Video Path:")
        self.video_path_edit = QLineEdit()
        self.video_path_button = QPushButton("Browse...")
        self.video_path_button.clicked.connect(self.select_video_path)
        self.video_path_layout.addWidget(self.video_path_edit)
        self.video_path_layout.addWidget(self.video_path_button)

        # Subtitle Language Section
        self.subtitle_language_layout = QHBoxLayout()
        self.subtitle_language_label = QLabel("Subtitle Language:")
        self.subtitle_language_combo = QComboBox()
        self.subtitle_language_combo.currentIndexChanged.connect(self.language_changed)
        self.subtitle_languages = [
            "ar", "cs", "da", "de", "el", "en", "es", "fa", "fi", "fr", "he", "hi", "hu", "id", "it", "ja", "ko",
            "ms", "nl", "no", "pl", "pt", "ro", "ru", "sv", "th", "tr", "uk", "vi", "zh-cn", "zh-tw"
        ]
        self.subtitle_language_combo.addItems(self.subtitle_languages)
        self.subtitle_language_layout.addWidget(self.subtitle_language_combo)

        # Theme Section
        self.theme_layout = QHBoxLayout()
        self.theme_label = QLabel("Theme:")
        self.theme_checkbox = QCheckBox("Dark Theme")

        self.theme_layout.addWidget(self.theme_label)
        self.theme_layout.addWidget(self.theme_checkbox)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)

        self.layout.addWidget(self.video_path_label)
        self.layout.addLayout(self.video_path_layout)
        self.layout.addWidget(self.subtitle_language_label)
        self.layout.addLayout(self.subtitle_language_layout)
        self.layout.addLayout(self.theme_layout)
        self.layout.addWidget(self.save_button)

        self.load_settings()

        self.show()

    def select_video_path(self):
        video_path = QFileDialog.getExistingDirectory(self, "Select Video Path")
        self.video_path_edit.setText(video_path)

    def load_settings(self):
        video_path = self.settings.value("VideoPath")
        subtitle_language = self.settings.value("SubtitleLanguage")

        if self.settings.contains("DarkThemeEnabled"):
            dark_theme_enabled = self.settings.value("DarkThemeEnabled", type=bool)
        else:
            dark_theme_enabled = False

        self.video_path_edit.setText(video_path)
        self.subtitle_language_combo.setCurrentText(subtitle_language)
        self.theme_checkbox.setChecked(dark_theme_enabled)

    def save_settings(self):
        video_path = self.video_path_edit.text()
        subtitle_language = self.subtitle_language_combo.currentText()
        dark_theme_enabled = self.theme_checkbox.isChecked()

        self.settings.setValue("VideoPath", video_path)
        self.settings.setValue("SubtitleLanguage", subtitle_language)
        self.settings.setValue("DarkThemeEnabled", dark_theme_enabled)

        self.accept()

    def language_changed(self):
        selected_language = self.subtitle_language_combo.currentText()
        self.languageChanged.emit(selected_language)
