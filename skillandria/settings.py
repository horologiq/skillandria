from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog

from skillandria.helpers import *


class SettingsDialog(QDialog):
    languageChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout(self)

        # Video Path Section
        video_path_layout = QHBoxLayout()
        self.video_path_label = QLabel("Video Path:")
        self.video_path_edit = QLineEdit()
        self.video_path_button = QPushButton("Browse...")
        self.video_path_button.clicked.connect(self.select_video_path)
        video_path_layout.addWidget(self.video_path_edit)
        video_path_layout.addWidget(self.video_path_button)

        # Subtitle Language Section
        subtitle_language_layout = QHBoxLayout()
        self.subtitle_language_label = QLabel("Subtitle Language:")
        self.subtitle_language_combo = QComboBox()
        self.subtitle_language_combo.currentIndexChanged.connect(self.language_changed)
        self.subtitle_languages = [
            "ar", "cs", "da", "de", "el", "en", "es", "fa", "fi", "fr", "he", "hi", "hu", "id", "it", "ja", "ko",
            "ms", "nl", "no", "pl", "pt", "ro", "ru", "sv", "th", "tr", "uk", "vi", "zh-cn", "zh-tw"
        ]
        self.subtitle_language_combo.addItems(self.subtitle_languages)
        subtitle_language_layout.addWidget(self.subtitle_language_combo)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)

        layout.addWidget(self.video_path_label)
        layout.addLayout(video_path_layout)
        layout.addWidget(self.subtitle_language_label)
        layout.addLayout(subtitle_language_layout)
        layout.addWidget(save_button)

        self.load_settings()

    def select_video_path(self):
        video_path = QFileDialog.getExistingDirectory(self, "Select Video Path")
        self.video_path_edit.setText(video_path)

    def load_settings(self):
        settings = QSettings(config_file, QSettings.IniFormat)
        video_path = settings.value("VideoPath")
        subtitle_language = settings.value("SubtitleLanguage")

        self.video_path_edit.setText(video_path)
        self.subtitle_language_combo.setCurrentText(subtitle_language)

    def save_settings(self):
        video_path = self.video_path_edit.text()
        subtitle_language = self.subtitle_language_combo.currentText()

        settings = QSettings(config_file, QSettings.IniFormat)
        settings.setValue("VideoPath", video_path)
        settings.setValue("SubtitleLanguage", subtitle_language)

        self.accept()

    def language_changed(self):
        selected_language = self.subtitle_language_combo.currentText()
        self.languageChanged.emit(selected_language)

