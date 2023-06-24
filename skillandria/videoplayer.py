from PyQt6.QtCore import QTime, QSize, QTimer, QUrl, Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, \
    QPushButton, QSlider, QTextEdit, QLabel, QGridLayout, QFrame, QMessageBox, \
    QHeaderView, QSpacerItem, QSizePolicy, QTreeView, QInputDialog, QListWidget, QListWidgetItem, QComboBox, QFileDialog

from googletrans import Translator

from skillandria.bookmarks_db import BookmarksDatabase
from skillandria.helpers import *
from skillandria.time_conversion import *
from skillandria.treemodel import VideoTreeModel


class VideoPlayer(QMainWindow):
    languageChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.bookmarks_db = BookmarksDatabase()

        self.string_from_file = None

        self.subtitle_list = None
        self.settings = QSettings("skillandria")
        self.setWindowTitle("Skillandria")

        self.resize(800, 600)

        self.start_time = 0
        self.end_time = 0

        self.bookmark_list = []

        self.theme = self.load_theme()

        self.icon_path = get_icon_path(self.theme)
        self.theme_path = get_theme_path(self.theme)

        self.translation_language = load_translation_language()
        self.folder_path = self.load_folder_path()

        self.subtitle_connected = False

        # Main widget
        self.central_widget = QWidget(self)

        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Horizontal splitter
        self.horizontal_splitter = QSplitter(Qt.Orientation.Horizontal, self.central_widget)

        # First section: Video widget and subtitle text field
        self.left_section = QWidget(self)
        self.player = QMediaPlayer(self)
        self.audioOutput = QAudioOutput()
        self.player.setAudioOutput(self.audioOutput)

        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)
        self.player.mediaStatusChanged.connect(self.check_media_status)

        self.left_section_layout = QVBoxLayout(self.left_section)
        self.left_section_layout.addWidget(self.video_widget)

        # Add horizontal spacer before subtitle text field to span to the right
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

        # Second section: Playlist, buttons, and timeline slider
        self.right_section = QWidget(self)
        self.right_section_layout = QVBoxLayout(self.right_section)

        self.right_section_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.right_section.setLayout(self.right_section_layout)

        # Top right
        self.top_right_section_layout = QGridLayout()

        self.play_button = QPushButton("", self)
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_play.png")))
        self.play_button.setIconSize(QSize(100, 100))

        self.play_button.setEnabled(False)

        self.filename_label = QLabel("")
        self.progress_label = QLabel("")
        self.timer_label = QLabel("00:00:00")

        # Set frame properties for the label
        self.filename_label.setFrameShape(QFrame.Shape.HLine)

        self.progress_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.timer_label.setFrameShape(QFrame.Shape.StyledPanel)

        # Apply bold font to the filename label
        self.filename_label.setStyleSheet("font-weight: bold;")

        self.top_right_section_layout.setSpacing(5)  # Set the desired spacing value

        self.top_right_section_layout.addWidget(self.play_button, 0, 0, 2, 1)  # Button in top-left, spanning two rows
        self.top_right_section_layout.addWidget(self.filename_label, 0, 1, 1, 3)  # Duration label in top-right

        self.top_right_section_layout.addWidget(self.progress_label, 1, 1, 1, 1)  # Timer label
        self.top_right_section_layout.addWidget(self.timer_label, 1, 2, 1, 1)

        # Set column stretch to ensure the filename label takes up all the available width
        self.top_right_section_layout.setColumnStretch(1, 1)

        # Add the right section layout to the main layout
        self.right_section_layout.addLayout(self.top_right_section_layout)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # Update every second
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every minute

        # Initialize the timer
        self.current_time = 0
        self.total_time = 0
        self.timer_running = 0

        # Slider
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.sliderMoved.connect(self.set_position)

        self.right_section_layout.addWidget(self.timeline_slider)

        # Playlist
        self.tree_view = QTreeView(self)

        self.load_last_played_video()

        self.model = VideoTreeModel(self.folder_path, self.string_from_file, self.icon_path, self.theme)

        self.tree_view.setModel(self.model)
        self.tree_view.clicked.connect(self.select_item)
        self.tree_view.setExpandsOnDoubleClick(False)  # Disable expanding on double-click
        self.tree_view.setAnimated(False)
        self.tree_view.setIndentation(15)
        self.tree_view.setRootIsDecorated(False)  # Show the root node
        self.tree_view.setColumnWidth(0, 300)  # Width for the first column

        header_view = self.tree_view.header()
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # first column to the left
        header_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.right_section_layout.addWidget(self.tree_view)

        # Fav controls
        self.fav_button_layout = QHBoxLayout()

        self.bookmark_button = QPushButton()
        self.bookmark_button.clicked.connect(self.create_bookmark)
        self.bookmark_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_fav.png")))
        self.fav_button_layout.addWidget(self.bookmark_button)

        self.icon_dropdown = QComboBox(self)
        self.icon_dropdown.addItem("To review")
        self.icon_dropdown.addItem("To research")
        self.icon_dropdown.addItem("Key point")
        self.icon_dropdown.addItem("I love this!")
        self.fav_button_layout.addWidget(self.icon_dropdown)

        self.remove_bookmark_button = QPushButton()
        self.remove_bookmark_button.clicked.connect(
            lambda: self.remove_bookmark(self.bookmarks_frame.selectedItems()[0]))
        self.remove_bookmark_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_remove.png")))
        self.fav_button_layout.addWidget(self.remove_bookmark_button)

        self.right_section_layout.addLayout(self.fav_button_layout)

        # Bookmarks
        self.bookmarks_frame = QListWidget(self)
        self.bookmarks_frame.setStyleSheet("QFrame { border: none; }")
        self.right_section_layout.addWidget(self.bookmarks_frame)

        self.bookmarks_frame.itemDoubleClicked.connect(self.go_to_bookmark)

        self.bookmarks_layout = QVBoxLayout(self.bookmarks_frame)
        self.bookmarks_frame.setLayout(self.bookmarks_layout)

        # Adjust size policy and stretch factor
        self.bookmarks_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_section_layout.setStretch(1, 1)

        # Buttons row
        self.button_layout = QHBoxLayout()

        self.hide_button = QPushButton()
        self.hide_button.clicked.connect(self.toggle_subtitle_area)
        self.hide_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_sub.png")))
        self.button_layout.addWidget(self.hide_button)

        self.full_screen_button = QPushButton()
        self.full_screen_button.clicked.connect(self.toggle_full_screen)
        self.full_screen_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_screen.png")))
        self.button_layout.addWidget(self.full_screen_button)

        self.half_speed_button = QPushButton()
        self.half_speed_button.clicked.connect(self.set_half_speed)
        self.half_speed_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_slow.png")))
        self.button_layout.addWidget(self.half_speed_button)

        self.normal_speed_button = QPushButton()
        self.normal_speed_button.clicked.connect(self.set_normal_speed)
        self.normal_speed_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_normal.png")))
        self.button_layout.addWidget(self.normal_speed_button)

        self.double_speed_button = QPushButton()
        self.double_speed_button.clicked.connect(self.set_double_speed)
        self.double_speed_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_fast.png")))
        self.button_layout.addWidget(self.double_speed_button)

        self.settings_button = QPushButton("")
        self.settings_button.clicked.connect(self.toggle_theme)
        self.settings_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_theme.png")))
        self.button_layout.addWidget(self.settings_button)

        self.open_folder_button = QPushButton("")
        self.open_folder_button.clicked.connect(self.select_video_path)
        self.open_folder_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_open.png")))
        self.button_layout.addWidget(self.open_folder_button)

        self.right_section_layout.addLayout(self.button_layout)

        # Create a container widget for the timer and control buttons
        self.control_container = QWidget(self)
        self.control_layout = QHBoxLayout(self.control_container)

        self.horizontal_splitter.addWidget(self.right_section)

        self.layout.addWidget(self.horizontal_splitter)

        self.current_video_path = ""
        self.current_video_position = 0
        self.current_video_timer = 0
        self.current_video_played = False

        self.horizontal_splitter.splitterMoved.connect(self.handle_splitter_moved)

        self.left_section_size = self.left_section.sizeHint().width()
        self.right_section_size = self.right_section.sizeHint().width()

        self.load_settings_in_ui()

        self.select_last_played_video()

        self.show()

    def toggle_subtitle_area(self):
        if self.subtitle_textedit.isVisible():
            self.subtitle_textedit.hide()
            self.translation_section.hide()
        else:
            self.subtitle_textedit.show()
            self.translation_section.show()

    def create_bookmark(self):
        current_position = self.player.position()
        comment, ok = QInputDialog.getText(self, "Bookmark", "Enter a comment for the bookmark:")
        if ok and comment:
            video_file = self.current_video_path
            icon_index = self.icon_dropdown.currentIndex()
            bookmark = (video_file, current_position, comment, icon_index)
            self.bookmark_list.append(bookmark)
            self.bookmarks_db.save_bookmark(bookmark)

            # Create a list item to display the bookmark
            item = QListWidgetItem(f"{milliseconds_to_time(current_position)} - {comment}")
            icon_index = bookmark[3]
            icon_path = os.path.join(self.icon_path, f"fav_{icon_index + 1}.png")
            icon = QIcon(icon_path)
            item.setIcon(icon)
            item.setData(Qt.ItemDataRole.UserRole, current_position)  # Store the position as data
            self.bookmarks_frame.addItem(item)

    def go_to_bookmark(self, item):
        position = item.data(Qt.ItemDataRole.UserRole)
        self.player.setPosition(position)

    def remove_bookmark(self, item):
        position = item.data(Qt.ItemDataRole.UserRole)

        # Remove the bookmark from the list and the database
        for index, bookmark in enumerate(self.bookmark_list):
            if bookmark[1] == position:
                del self.bookmark_list[index]
                self.bookmarks_db.delete_bookmark(bookmark)
                break

        # Remove the selected item from the bookmarks list
        self.bookmarks_frame.takeItem(self.bookmarks_frame.row(item))

    def load_bookmarks(self, video_file):
        self.bookmark_list = self.bookmarks_db.get_bookmarks_for_video(video_file)
        self.bookmarks_frame.clear()
        for bookmark in self.bookmark_list:
            position = bookmark[1]
            comment = bookmark[2]
            item = QListWidgetItem(f"{milliseconds_to_time(position)} - {comment}")
            icon_index = bookmark[3]
            icon_path = os.path.join(self.icon_path, f"fav_{icon_index + 1}.png")
            icon = QIcon(icon_path)
            item.setIcon(icon)
            item.setData(Qt.ItemDataRole.UserRole, position)  # Store the position as data
            self.bookmarks_frame.addItem(item)

    def load_theme(self):
        if self.settings.value("DarkThemeEnabled") == "true":
            self.setStyleSheet(load_stylesheet(get_theme_path("dark")))
            self.repaint()
            return "dark"
        else:
            self.setStyleSheet(load_stylesheet(get_theme_path("light")))
            self.repaint()
            return "light"

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
        # Update the filename label with the current video filename

        filename = os.path.splitext(os.path.basename(self.current_video_path))[0]
        foldername = os.path.basename(os.path.dirname(self.current_video_path))

        cropped_filename = filename[:35] + "..." if len(filename) > 15 else filename
        cropped_foldername = foldername[:35] + "..." if len(foldername) > 15 else foldername

        self.filename_label.setText(cropped_foldername + "\n" + cropped_filename)

    def update_timer(self):
        if self.timer_running:
            self.current_video_timer += 1
            current_video_timer_formatted = QTime(0, 0).addSecs(self.current_video_timer)
            self.timer_label.setText(current_video_timer_formatted.toString("hh:mm:ss"))

            # Duration
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

            # Check if the left section is minimized
            if self.left_section_size == 0:
                self.subtitle_textedit.hide()
                self.translation_section.hide()
            else:
                self.subtitle_textedit.show()
                self.translation_section.show()

    def language_changed(self):
        language = self.subtitle_languages[self.subtitle_language_combo.currentIndex()]
        self.translation_language = language

    def translate_subtitle(self):
        if self.subtitle_textedit.isVisible():
            subtitle_text = self.subtitle_textedit.toPlainText()
            if subtitle_text:  # and self.translation_delay > 10:
                translator = Translator()
                try:
                    if subtitle_text.strip() != '':  # Check if the subtitle text is not empty or contains only
                        # whitespace
                        translation = translator.translate(subtitle_text, dest=self.translation_language).text

                        # googletranslate version 3.0 breaks, version 3.1 needs to pass translation instead
                        # translation.text
                        self.translation_textedit.setPlainText(translation)
                    else:
                        self.translation_textedit.clear()
                except Exception as e:

                    # print(f"translation.text: {self.translation}")
                    print(f"Translation error: {e}")
            else:
                self.translation_textedit.clear()

    def select_item(self):
        index = self.tree_view.currentIndex()
        node = index.internalPointer()
        if node.is_folder:
            # Toggle the expanded state of the folder
            if self.tree_view.isExpanded(index):
                self.tree_view.collapse(index)
                # self.play_button.setEnabled(False)
            else:
                self.tree_view.expand(index)
                # self.play_button.setEnabled(False)
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

                    # Save the video information before switching to a different video
                    self.model.save_video_info(path, pos, played, timer)

                    # Only reset the timer if switching to a different video
                    self.current_video_timer = 0
                    self.current_video_position = 0
                    self.current_video_played = False
                    self.current_video_path = node.path

                    self.model.string_from_file = node.path

                    # Set the media content without playing
                    try:
                        self.player.setSource(QUrl.fromLocalFile(self.current_video_path))
                    except Exception as e:
                        print(f"Error setting source: {e}")

                    # Load video information
                    self.current_video_position = self.model.load_video_position(self.current_video_path)
                    self.current_video_played = self.model.load_video_played(self.current_video_path)
                    self.current_video_timer = self.model.load_video_timer(self.current_video_path)

                    # Load bookmarks
                    self.load_bookmarks(self.current_video_path)

                    self.timeline_slider.setRange(0, self.player.duration())
                    self.subtitle_textedit.clear()
                    self.translation_textedit.clear()

                    self.player.setPosition(self.current_video_position)  # Set the position in the media player

                    # Load and show subtitles if available
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
        # Parse the subtitles and store them in the subtitle_list
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
        # It's only modifying the textedit field if there was an actual change
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

            if index.column() == 1:  # User selected the second column
                # Get the index of the item in the first column
                first_column_index = index.sibling(index.row(), 0)
                node = first_column_index.internalPointer()

            if node.path == self.current_video_path or os.path.isdir(node.path):
                self.player.setAudioOutput(self.audioOutput)
                self.player.setPosition(self.current_video_position)
                self.player.play()
                self.play_button.setIcon(QIcon(os.path.join(self.icon_path, "ico_pause.png")))
            else:
                index_text = node.path
                if index_text is None:
                    index_text = ""
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "Are you sure you want to start the lecture\n\n'" + index_text + "'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
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
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def set_half_speed(self):
        self.player.setPlaybackRate(0.75)

    def set_normal_speed(self):
        self.player.setPlaybackRate(1.0)

    def set_double_speed(self):
        self.player.setPlaybackRate(1.5)

    def update_duration(self, duration):
        self.timeline_slider.setRange(0, duration)

    def update_position(self, position):
        self.timeline_slider.setValue(position)
        self.current_video_position = position

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
        if self.theme == "dark":
            self.timer_label.setStyleSheet("background-color: #59564e")
        else:
            self.timer_label.setStyleSheet("background-color: #eae3d0")

    def stop_timer(self):
        self.timer_running = 0
        self.timer_label.setStyleSheet("")

    def save_last_file_played(self):
        self.settings.setValue("LastVideo", self.current_video_path)

    def closeEvent(self, event):

        reply = QMessageBox.question(
            self, "Confirmation", "Are you sure you want to close?",
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

            event.accept()
            super().closeEvent(event)

        else:
            event.ignore()

    def select_video_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Video Folder", self.folder_path)
        if folder_path:
            self.folder_path = folder_path
            self.model = VideoTreeModel(folder_path, self.string_from_file, self.icon_path, self.theme)
            self.tree_view.setModel(self.model)
            self.settings.setValue("VideoPath", self.folder_path)

    def load_settings_in_ui(self):
        subtitle_language = self.settings.value("SubtitleLanguage")
        self.subtitle_language_combo.setCurrentText(subtitle_language)

    def save_settings(self):
        subtitle_language = self.subtitle_language_combo.currentText()
        self.settings.setValue("SubtitleLanguage", subtitle_language)

    def toggle_theme(self):

        if self.theme == "dark":
            self.settings.setValue("DarkThemeEnabled", False)
            self.theme = "light"
            self.model.theme = "light"
            self.setStyleSheet(load_stylesheet(get_theme_path("light")))
            self.timer_label.setStyleSheet("background-color: #eae3d0")

            self.repaint()

        elif self.theme == "light":
            self.settings.setValue("DarkThemeEnabled", True)
            self.theme = "dark"
            self.model.theme = "dark"
            self.setStyleSheet(load_stylesheet(get_theme_path("dark")))
            self.timer_label.setStyleSheet("background-color: #59564e")

            self.repaint()

        get_theme_path(self.theme)
        get_icon_path(self.theme)

        print(self.theme)

    def load_folder_path(self):
        folder_path = self.settings.value("VideoPath")
        if folder_path:
            return folder_path
        else:
            return get_default_path()
