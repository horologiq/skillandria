from PyQt6.QtCore import QTime, QSize, QTimer, QUrl, Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, \
    QPushButton, QSlider, QTextEdit, QLabel, QGridLayout, QFrame, QMessageBox, \
    QHeaderView, QSpacerItem, QSizePolicy, QTreeView, QComboBox, QFileDialog

from skillandria.bookmarks_db import BookmarksDatabase
from skillandria.helpers import *
from skillandria.time_conversion import *
from skillandria.translation import TranslationThread
from skillandria.treemodel import VideoTreeModel


class VideoPlayer(QMainWindow):
    languageChanged = pyqtSignal(str)

    def __init__(self, path, parent=None):
        super().__init__(parent)


        # Init

        self.bookmarks_db = BookmarksDatabase()
        self.string_from_file = None
        self.subtitle_list = None
        self.settings = QSettings("skillandria")
        self.setWindowTitle(os.path.basename(path))
        self.resize(800, 600)
        self.start_time = 0
        self.end_time = 0
        self.bookmark_list = []
        self.current_bookmark_position = None
        self.icon_path = get_icon_path()
        self.translation_language = load_translation_language()
        self.folder_path = path
        self.subtitle_connected = False
        self.current_video_path = ""
        self.current_video_position = 0
        self.current_video_timer = 0
        self.current_video_played = False
        self.showMaximized()
        self.is_fullscreen = False
        self.is_pip_mode = False

        # Base

        self.central_widget = QWidget(self)

        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.horizontal_splitter = QSplitter(Qt.Orientation.Horizontal, self.central_widget)

        self.left_section = QWidget(self)
        self.left_section_layout = QVBoxLayout(self.left_section)

        # Top: Info labels & timers

        self.info_section = QWidget(self)
        self.info_section.setFixedHeight(100)
        self.info_section_layout = QGridLayout(self.info_section)

        self.filename_label = QLabel("")
        self.progress_label = QLabel("")
        self.timer_label = QLabel("00:00:00")

        self.progress_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.timer_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.filename_label.setFrameShape(QFrame.Shape.HLine)
        self.filename_label.setStyleSheet("font-weight: bold;")

        self.info_section_layout.setSpacing(5)
        self.info_section_layout.addWidget(self.filename_label, 0, 1, 1, 3)
        self.info_section_layout.addWidget(self.progress_label, 1, 1, 1, 1)
        self.info_section_layout.addWidget(self.timer_label, 1, 2, 1, 1)
        self.info_section_layout.setColumnStretch(1, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.current_time = 0
        self.total_time = 0
        self.timer_running = 0


        # Central left: Video widget

        self.player = QMediaPlayer(self)

        self.audioOutput = QAudioOutput()
        self.player.setAudioOutput(self.audioOutput)

        self.video_widget = QVideoWidget(self)
        self.video_window = self.video_widget.windowHandle()
        self.player.setVideoOutput(self.video_widget)

        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)
        self.player.mediaStatusChanged.connect(self.check_media_status)

        self.left_section_layout.addWidget(self.video_widget)


        # Lower left: Play button, timeline, bookmark stamps, subtitle

        self.play_button = QPushButton("", self)
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_play.png")))
        self.play_button.setIconSize(QSize(100, 100))
        self.play_button.setStyleSheet("border: none; background: transparent;")
        self.play_button.setEnabled(False)

        self.timeline_area = QWidget(self)
        self.timeline_area_layout = QHBoxLayout(self.timeline_area)
        self.timeline_area.setFixedHeight(80)

        self.timeline_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.sliderMoved.connect(self.set_position)

        self.timeline_area_right_section = QWidget(self)
        self.timeline_area_right_section_layout = QVBoxLayout(self.timeline_area_right_section)

        self.timeline_bookmarks_area = QWidget(self)

        self.timeline_area_right_section_layout.addWidget(self.timeline_slider)
        self.timeline_area_right_section_layout.addWidget(self.timeline_bookmarks_area)

        self.timeline_area_layout.addWidget(self.play_button)
        self.timeline_area_layout.addWidget(self.timeline_area_right_section)



        self.button_layout = QHBoxLayout()

        self.hide_button = QPushButton()
        self.hide_button.clicked.connect(self.toggle_subtitle_area)
        self.hide_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_sub.png")))
        self.button_layout.addWidget(self.hide_button)

        self.full_screen_button = QPushButton()
        self.full_screen_button.clicked.connect(self.toggle_full_screen)
        self.full_screen_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_screen.png")))
        self.button_layout.addWidget(self.full_screen_button)


        self.pip_button = QPushButton("PIP", self)
        self.pip_button.clicked.connect(self.toggle_pip_mode)
        self.button_layout.addWidget(self.pip_button)

        self.subtitle_speed_combo = QComboBox()
        self.subtitle_speed_combo.currentIndexChanged.connect(self.speed_changed)
        self.speeds = [
            "0.5", "1", "1.5", "2"
        ]

        self.subtitle_speed_combo.addItems(self.speeds)
        self.subtitle_speed_combo.setCurrentIndex(1)
        self.button_layout.addWidget(self.subtitle_speed_combo)

        self.timeline_area_layout.addLayout(self.button_layout)

        self.left_section_layout.addWidget(self.timeline_area)


        horizontal_spacer = QSpacerItem(800, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.left_section_layout.addItem(horizontal_spacer)

        self.subtitle_textedit = QTextEdit(self)
        self.translation_section = QWidget(self)
        self.translation_section_layout = QHBoxLayout(self.translation_section)
        self.translation_textedit = QTextEdit(self)
        self.subtitle_language_combo = QComboBox()

        self.subtitle_language_combo.currentIndexChanged.connect(self.language_changed)
        self.subtitle_languages = [
            "ar", "cs", "da", "de", "el", "en", "es", "fa", "fi", "fr", "he", "hi", "hu", "id", "it", "ja", "ko",
            "ms", "nl", "no", "pl", "pt", "ro", "ru", "sv", "th", "tr", "uk", "vi", "zh-cn", "zh-tw"
        ]
        self.subtitle_language_combo.addItems(self.subtitle_languages)

        self.translation_section_layout.addWidget(self.translation_textedit)
        self.translation_section_layout.addWidget(self.subtitle_language_combo)

        self.left_section_layout.addWidget(self.subtitle_textedit)
        self.left_section_layout.addWidget(self.translation_section)

        self.subtitle_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.subtitle_textedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.translation_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.translation_textedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.translation_textedit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.subtitle_textedit.setReadOnly(True)
        self.translation_textedit.setReadOnly(True)

        self.subtitle_textedit.setFixedHeight(24)
        self.subtitle_textedit.textChanged.connect(self.translate_subtitle)
        self.translation_textedit.setFixedHeight(24)
        self.translation_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.translation_section_layout.setContentsMargins(0, 0, 0, 0)
        self.translation_section_layout.setSpacing(0)

        self.subtitle_textedit.hide()
        self.translation_section.hide()

        self.horizontal_splitter.addWidget(self.left_section)


        # Right: Playlist, bookmarks & buttons row

        self.right_section = QWidget(self)
        self.right_section_layout = QVBoxLayout(self.right_section)

        self.right_section_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.right_section.setLayout(self.right_section_layout)

        self.tree_view = QTreeView(self)

        self.load_last_played_video()

        self.model = VideoTreeModel(self.folder_path, self.string_from_file, self.icon_path)

        self.tree_view.setModel(self.model)
        self.tree_view.clicked.connect(self.select_item)
        self.tree_view.setExpandsOnDoubleClick(False)
        self.tree_view.setAnimated(False)
        self.tree_view.setIndentation(15)
        self.tree_view.setRootIsDecorated(False)
        self.tree_view.setColumnWidth(0, 300)

        header_view = self.tree_view.header()
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.right_section_layout.addWidget(self.tree_view)

        self.fav_button_layout = QHBoxLayout()

        self.bookmark_button = QPushButton()
        self.bookmark_button.clicked.connect(self.create_bookmark)
        self.bookmark_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_fav.png")))
        self.fav_button_layout.addWidget(self.bookmark_button)

        self.icon_dropdown = QComboBox(self)

        self.icon_dropdown.addItem(QIcon(os.path.join(self.icon_path, "fav_1.png")), "")
        self.icon_dropdown.addItem(QIcon(os.path.join(self.icon_path, "fav_2.png")), "")
        self.icon_dropdown.addItem(QIcon(os.path.join(self.icon_path, "fav_3.png")), "")
        self.icon_dropdown.addItem(QIcon(os.path.join(self.icon_path, "fav_4.png")), "")

        self.fav_button_layout.addWidget(self.icon_dropdown)

        self.remove_bookmark_button = QPushButton()
        self.remove_bookmark_button.clicked.connect(self.remove_bookmark)
        self.remove_bookmark_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_remove.png")))
        self.fav_button_layout.addWidget(self.remove_bookmark_button)
        self.bookmark_timestamp_label = QLabel("", self)
        self.bookmark_timestamp_label.setStyleSheet("font-weight: bold;")
        self.fav_button_layout.addWidget(self.bookmark_timestamp_label)

        self.right_section_layout.addLayout(self.fav_button_layout)

        self.bookmark_text_edit = QTextEdit(self)
        self.bookmark_text_edit.setStyleSheet("QFrame { border: none; }")
        self.right_section_layout.addWidget(self.bookmark_text_edit)

        self.bookmarks_layout = QVBoxLayout(self.bookmark_text_edit)
        self.bookmark_text_edit.setLayout(self.bookmarks_layout)


        self.control_container = QWidget(self)
        self.control_layout = QHBoxLayout(self.control_container)


        # ...

        self.horizontal_splitter.addWidget(self.right_section)
        self.layout.addWidget(self.info_section)
        self.layout.addWidget(self.horizontal_splitter)
        self.horizontal_splitter.splitterMoved.connect(self.handle_splitter_moved)
        self.left_section_size = self.left_section.sizeHint().width()
        self.right_section_size = self.right_section.sizeHint().width()

        self.load_settings_in_ui()
        self.select_last_played_video()
        self.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if abs(event.size().width() - event.oldSize().width()) > 10:
            if self.current_video_path:
                self.load_bookmarks(self.current_video_path)

    def toggle_subtitle_area(self):
        if self.subtitle_textedit.isVisible():
            self.subtitle_textedit.hide()
            self.translation_section.hide()
        else:
            self.subtitle_textedit.show()
            self.translation_section.show()

    def create_bookmark(self):
        current_position = self.player.position()

        comment = self.bookmark_text_edit.toPlainText()
        if comment:
            video_file = self.current_video_path
            icon_index = self.icon_dropdown.currentIndex()
            bookmark = (video_file, current_position, comment, icon_index)
            self.bookmark_list.append(bookmark)
            self.bookmarks_db.save_bookmark(bookmark)

            self.clear_layout()

            self.add_bookmark_icon(current_position, comment, icon_index)

            self.load_bookmarks(self.current_video_path)

    def clear_layout(self):
        for child in self.timeline_bookmarks_area.children():
            child.deleteLater()


    def add_bookmark_icon(self, position, comment, icon_index):
        duration = self.player.duration()

        if duration > 0:
            relative_position = int((position / duration) * self.timeline_bookmarks_area.width())

            bookmark_button = QPushButton(self)
            bookmark_button.setIcon(QIcon(os.path.join(self.icon_path, "fav_" + str(icon_index + 1) + ".png")))
            bookmark_button.setIconSize(QSize(20, 20))
            bookmark_button.setStyleSheet("border: none; background: transparent;")

            bookmark_button.setParent(self.timeline_bookmarks_area)
            bookmark_button.setGeometry(relative_position - 10, 0, 20, 20)

            bookmark_button.setProperty("bookmark_position", position)
            bookmark_button.clicked.connect(lambda: (self.show_bookmark_text(comment, position), self.go_to_bookmark(position)))
            bookmark_button.show()



    def go_to_bookmark(self, position):
        self.player.setPosition(position)
        self.current_bookmark_position = position

    def show_bookmark_text(self, comment, position):
        self.bookmark_text_edit.setPlainText(comment)

        timestamp = format_timestamp(position)
        self.bookmark_timestamp_label.setText(f"Timestamp: {timestamp}")

    def remove_bookmark(self):
        if self.current_bookmark_position is not None:
            for index, bookmark in enumerate(self.bookmark_list):
                if bookmark[1] == self.current_bookmark_position:
                    del self.bookmark_list[index]
                    self.bookmarks_db.delete_bookmark(bookmark)
                    self.current_bookmark_position = None

                    self.load_bookmarks(self.current_video_path)
                    self.bookmark_text_edit.clear()
                    self.bookmark_timestamp_label.setText("")
                    break
        else:
            QMessageBox.information(self, "Error", "No active bookmark to delete.")

    def load_bookmarks(self, video_file):
        self.clear_layout()
        self.bookmark_list = self.bookmarks_db.get_bookmarks_for_video(video_file)
        self.bookmark_list.sort(key=lambda x: x[1])
        self.bookmark_text_edit.clear()

        for bookmark in self.bookmark_list:
            position = bookmark[1]
            comment = bookmark[2]
            icon_index = bookmark[3]
            self.add_bookmark_icon(position, comment, icon_index)


    def load_last_played_video(self):
        # Load the last played video from config
        last_video = self.settings.value("LastVideo")
        if last_video is not None:
            self.string_from_file = last_video
        else:
            self.string_from_file = None

    def select_last_played_video(self):
        if self.string_from_file is not None:
            model = self.tree_view.model()
            for row in range(model.rowCount(QModelIndex())):
                index = model.index(row, 0, QModelIndex())
                node = index.internalPointer()
                if node.path == self.string_from_file:
                    self.tree_view.setCurrentIndex(index)
                    parent_index = index.parent()
                    if parent_index.isValid():
                        self.tree_view.expand(parent_index)
                    self.select_item()
                    break

    def update_video_info(self):

        filename = os.path.splitext(os.path.basename(self.current_video_path))[0]
        foldername = os.path.basename(os.path.dirname(self.current_video_path))

        cropped_filename = filename[:35] + "..." if len(filename) > 600 else filename
        cropped_foldername = foldername[:35] + "..." if len(foldername) > 600 else foldername

        self.filename_label.setText(cropped_foldername + "\n" + cropped_filename)

    def update_timer(self):
        if self.timer_running:
            self.current_video_timer += 1
            current_video_timer_formatted = QTime(0, 0).addSecs(self.current_video_timer)
            self.timer_label.setText(current_video_timer_formatted.toString("hh:mm:ss"))

            if self.player.duration() > 0:
                duration = self.player.duration()
                time = QTime(0, 0, 0).addMSecs(duration)
                duration_string = time.toString("hh:mm:ss")
                position_string = QTime(0, 0, 0).addMSecs(self.player.position()).toString("hh:mm:ss")
                progress = int((self.player.position() / self.player.duration()) * 100)

                self.progress_label.setText(position_string + " / " + duration_string + "\n" + str(progress) + "%")

        self.update_video_info()

    def handle_splitter_moved(self, index):
        if index == 0:
            self.left_section_size = self.left_section.sizeHint().width()

            if self.left_section_size == 0:
                self.subtitle_textedit.hide()
                self.translation_section.hide()
            else:
                self.subtitle_textedit.show()
                self.translation_section.show()

    def language_changed(self):
        language = self.subtitle_languages[self.subtitle_language_combo.currentIndex()]
        self.translation_language = language


    def speed_changed(self):
        self.player.setPlaybackRate(float(self.subtitle_speed_combo.currentText()))


    def translate_subtitle(self):
        if self.subtitle_textedit.isVisible():
            subtitle_text = self.subtitle_textedit.toPlainText()

            if subtitle_text:
                if hasattr(self, 'translation_thread'):
                    self.translation_thread.stop()
                    self.translation_thread.wait()
                self.translation_thread = TranslationThread(subtitle_text, self.translation_language)
                self.translation_thread.translation_done.connect(self.update_translation)
                self.translation_thread.start()
            else:
                self.translation_textedit.clear()

    def update_translation(self, translation):
        self.translation_textedit.setPlainText(translation)

    def select_item(self):
        index = self.tree_view.currentIndex()
        node = index.internalPointer()
        if node.is_folder:
            if self.tree_view.isExpanded(index):
                self.tree_view.collapse(index)
            else:
                self.tree_view.expand(index)
        else:
            self.play_button.setEnabled(True)

    def play_video(self, index):
        if index.isValid() and index.column() == 0:
            node = index.internalPointer()

            if os.path.isfile(node.path):

                if self.current_video_path != node.path:

                    path = self.current_video_path
                    pos = self.current_video_position
                    played = self.current_video_played
                    timer = self.current_video_timer

                    if self.current_video_path is not None:
                        self.player.stop()

                    self.model.save_video_info(path, pos, played, timer)

                    self.current_video_timer = 0
                    self.current_video_position = 0
                    self.current_video_played = False
                    self.current_video_path = node.path

                    self.model.string_from_file = node.path

                    try:
                        self.player.setSource(QUrl.fromLocalFile(self.current_video_path))
                    except Exception as e:
                        print(f"Error setting source: {e}")

                    self.current_video_position = self.model.load_video_position(self.current_video_path)
                    self.current_video_played = self.model.load_video_played(self.current_video_path)
                    self.current_video_timer = self.model.load_video_timer(self.current_video_path)

                    self.timeline_slider.setRange(0, self.player.duration())
                    self.subtitle_textedit.clear()
                    self.translation_textedit.clear()

                    self.player.setPosition(self.current_video_position)

                    subtitle_path = os.path.splitext(node.path)[0] + ".srt"
                    if os.path.isfile(subtitle_path):
                        with open(subtitle_path, "r") as subtitle_file:
                            subtitles = subtitle_file.read()
                            self.subtitle_textedit.setPlainText(subtitles)
                            self.parse_subtitles(subtitles)
                            if not self.subtitle_connected:
                                self.player.positionChanged.connect(self.display_subtitle)
                                self.subtitle_connected = True
                    else:
                        self.subtitle_textedit.clear()
                        self.subtitle_list = []
                        if self.subtitle_connected:
                            self.player.positionChanged.disconnect(self.display_subtitle)
                            self.subtitle_connected = False

                self.update_video_info()


    def parse_subtitles(self, subtitles):
        subtitle_lines = subtitles.split("\n\n")
        self.subtitle_list = []
        for line in subtitle_lines:
            lines = line.split("\n")
            if len(lines) >= 3:
                timing = lines[1]
                text = "\n".join(lines[2:])
                if " --> " in timing:
                    start_time, end_time = timing.split(" --> ")
                    self.subtitle_list.append((start_time, end_time, text))


    def display_subtitle(self, position):
        current_subtitle = self.subtitle_textedit.toPlainText()
        for start_time, end_time, text in self.subtitle_list:
            start_ms = time_to_milliseconds(start_time)
            end_ms = time_to_milliseconds(end_time)
            if start_ms <= position <= end_ms:
                new_subtitle = text
                if new_subtitle != current_subtitle:
                    self.subtitle_textedit.setPlainText(new_subtitle)
                break
        else:
            if current_subtitle != "":
                self.subtitle_textedit.clear()

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_play.png")))
        else:
            index = self.tree_view.currentIndex()
            node = index.internalPointer()

            if index.column() == 1:
                first_column_index = index.sibling(index.row(), 0)
                node = first_column_index.internalPointer()

            if node.path == self.current_video_path or os.path.isdir(node.path):
                self.player.setAudioOutput(self.audioOutput)
                self.player.setPosition(self.current_video_position)
                self.player.play()
                self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_pause.png")))
            else:
                self.play_video(first_column_index if index.column() == 1 else index)
                self.start_timer()
                self.player.play()
                self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_pause.png")))
                self.settings.setValue("LastVideo", self.current_video_path)

    def stop_video(self):
        self.player.stop()
        self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_play.png")))
        self.stop_timer()
        self.save_settings()

    def toggle_full_screen(self):
        if not self.is_fullscreen:
            self.showFullScreen()
            self.right_section.hide()
            self.info_section.hide()
            self.is_fullscreen = True
        else:
            self.showMaximized()
            self.right_section.show()
            self.info_section.show()
            self.is_fullscreen = False

        self.left_section.updateGeometry()

    def toggle_pip_mode(self):
        if not self.is_pip_mode:
            self.right_section.hide()
            self.info_section.hide()
            self.resize(600, 320)
            self.showNormal()
            self.move(1000, 600)
            self.show()
            self.is_pip_mode = True
        else:
            self.right_section.show()
            self.info_section.show()
            self.resize(800, 600)
            self.showMaximized()
            self.show()
            self.is_pip_mode = False

    def check_bookmark(self, position):
        threshold = 5000

        for bookmark in self.bookmark_list:
            bookmark_position = bookmark[1]
            if abs(bookmark_position - position) < threshold:
                comment = bookmark[2]
                self.current_bookmark_position = bookmark_position
                self.show_bookmark_text(comment, bookmark_position)
                break

    def update_duration(self):
        duration = self.player.duration()
        if duration > 0:
            self.timeline_slider.setRange(0, duration)
            self.load_bookmarks(self.current_video_path)
        else:
            print("Duration not valid")

    def update_position(self, position):
        self.timeline_slider.setValue(position)
        self.current_video_position = position

        self.check_bookmark(position)

    def set_position(self, position):
        self.player.setPosition(position)
        self.current_video_position = position

    def check_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            index = self.tree_view.currentIndex()
            node = index.internalPointer()
            if os.path.isfile(node.path):
                node.played = True
                self.tree_view.update(index)
                self.current_video_played = True
                self.stop_video()
                self.player.setPosition(0)

    def start_timer(self):
        self.timer_running = 1
        self.timer_label.setStyleSheet("background-color: #eae3d0")

    def stop_timer(self):
        self.timer_running = 0
        self.timer_label.setStyleSheet("")

    def save_last_file_played(self):
        self.settings.setValue("LastVideo", self.current_video_path)

    def closeEvent(self, event):

        reply = QMessageBox.question(
            self, "Confirmation", "Are you sure you want to leave this session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:

            self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_play.png")))
            self.model.save_video_info(self.current_video_path, self.current_video_position, self.current_video_played,
                                       self.current_video_timer)
            self.player.stop()

            self.stop_timer()
            self.model.close_database()
            self.save_settings()

            if hasattr(self, 'translation_thread'):
                self.translation_thread.stop()
                self.translation_thread.wait()
            event.accept()

            event.accept()
            super().closeEvent(event)

        else:
            event.ignore()

    def select_video_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Video Folder", self.folder_path)
        if folder_path:
            self.folder_path = folder_path
            self.model = VideoTreeModel(folder_path, self.string_from_file, self.icon_path)
            self.tree_view.setModel(self.model)
            self.settings.setValue("VideoPath", self.folder_path)

    def load_settings_in_ui(self):
        subtitle_language = self.settings.value("SubtitleLanguage")
        self.subtitle_language_combo.setCurrentText(subtitle_language)

    def save_settings(self):
        subtitle_language = self.subtitle_language_combo.currentText()
        self.settings.setValue("SubtitleLanguage", subtitle_language)
