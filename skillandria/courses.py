
from PyQt6.QtWidgets import (
    QMainWindow, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QFrame, QMessageBox, QScrollArea,
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from functools import partial

from skillandria.db_manager import *
from skillandria.videoplayer import VideoPlayer
from skillandria.import_dialog import *

class CourseWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.setWindowTitle("Skillandria")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.showMaximized()

    def init_ui(self):
        self.widget = QWidget()
        self.layout = QVBoxLayout()

        self.filter_layout = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search courses or tags...")
        self.search_bar.textChanged.connect(self.search_courses)
        self.filter_layout.addWidget(self.search_bar, 3)

        self.tag_filter = QComboBox()
        self.tag_filter.addItem("Filter by tag")
        self.tag_filter.currentIndexChanged.connect(self.filter_by_tag)
        self.filter_layout.addWidget(self.tag_filter, 1)

        self.sort_filter = QComboBox()
        self.sort_filter.addItem("Order by")
        self.sort_filter.addItem("Last accessed")
        self.sort_filter.addItem("Title")
        self.sort_filter.addItem("Author")
        self.sort_filter.currentIndexChanged.connect(self.sort_courses)
        self.filter_layout.addWidget(self.sort_filter, 1)

        self.layout.addLayout(self.filter_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.course_container = QWidget()
        self.course_grid = QGridLayout(self.course_container)

        self.import_button = QPushButton("Import course")
        self.import_button.clicked.connect(self.import_course_dialog)
        self.course_grid.addWidget(self.import_button, 0, 0)

        self.scroll_area.setWidget(self.course_container)
        self.layout.addWidget(self.scroll_area)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.load_filtered_courses(max_columns=3)
        self.load_tags()

    def resizeEvent(self, event):
        self.reorganize_courses()

    def reorganize_courses(self):
        window_width = self.scroll_area.viewport().width()

        course_width = 400
        spacing = 20
        max_columns = max(1, window_width // (course_width + spacing))

        self.load_filtered_courses(max_columns)

    def sort_courses(self):
        self.reorganize_courses()

    def format_duration(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}"

    def load_tags(self):
        self.tag_filter.clear()
        self.tag_filter.addItem("Filter by tag")
        tags = set(tag for course in self.db.get_courses() for tag in (course[6] or "").split(","))
        self.tag_filter.addItems(sorted(tags))

    def search_courses(self):
        search_text = self.search_bar.text()
        filtered_courses = self.db.search_courses(search_text=search_text)
        self.reorganize_courses()

    def filter_by_tag(self):
        tag = self.tag_filter.currentText()
        if tag != "Filter by tag":
            filtered_courses = self.db.search_courses(tag=tag)
            self.reorganize_courses()

    def load_filtered_courses(self, max_columns=3):
        for i in reversed(range(self.course_grid.count())):
            widget = self.course_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.course_grid.addWidget(self.import_button, 0, 0)

        sort_criteria = self.sort_filter.currentText()
        if sort_criteria == "Last accessed":
            filtered_courses = self.db.get_courses(order_by="last_accessed")
        elif sort_criteria == "Title":
            filtered_courses = self.db.get_courses(order_by="title")
        elif sort_criteria == "Author":
            filtered_courses = self.db.get_courses(order_by="author")
        else:
            filtered_courses = self.db.get_courses()

        row, col = 1, 0

        for index, course in enumerate(filtered_courses):
            title, author, duration, progress, tags, dir, course_id = course[1:]

            course_frame = QFrame()
            course_frame.setFixedSize(400, 400)

            course_frame.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid rgb(100, 100, 100);  
                    border-radius: 20px;       
                    padding: 10px;             
                    background-color: rgb(180, 180, 180);    
                }}
            """)

            frame_layout = QVBoxLayout()

            title_label = QLabel(f"<b>{title}</b>")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("background-color: lightgray; padding: 5px; border-radius: 5px;")
            frame_layout.addWidget(title_label)

            formatted_duration = self.format_duration(duration)
            course_label = QLabel(f"{author}\nDuration: {formatted_duration}\nProgress: {progress}%")
            course_label.setStyleSheet("background-color: lightgray; padding: 5px; border-radius: 5px;")
            course_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            course_label.setWordWrap(True)
            frame_layout.addWidget(course_label)

            thumbnail_label = QLabel()
            thumbnail_label.setFixedSize(350, 200)
            if dir and os.path.exists(os.path.join(dir, 'thumbnail.jpg')):
                pixmap = QPixmap(os.path.join(dir, 'thumbnail.jpg')).scaled(400, 200,
                                                                            Qt.AspectRatioMode.KeepAspectRatio)
                thumbnail_label.setPixmap(pixmap)
            else:
                thumbnail_label.setText("No Thumbnail")
                thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_layout.addWidget(thumbnail_label)

            button_layout = QHBoxLayout()

            delete_button = QPushButton()
            delete_button.setIcon(QIcon(os.path.join(get_icon_path(), "ico_remove.png")))
            delete_button.clicked.connect(partial(self.delete_course, course_id))
            button_layout.addWidget(delete_button)

            start_button = QPushButton()
            start_button.setIcon(QIcon(os.path.join(get_icon_path(), "ico_play.png")))
            start_button.clicked.connect(partial(self.open_course_details, course))
            button_layout.addWidget(start_button)

            frame_layout.addLayout(button_layout)
            course_frame.setLayout(frame_layout)

            self.course_grid.addWidget(course_frame, row, col)

            col += 1
            if col >= max_columns:
                col = 0
                row += 1

    def import_course_dialog(self):
        dialog = ImportDialog(self)
        dialog.exec()

    def open_course_details(self, course):
        self.player = VideoPlayer(course[6])
        self.player.show()

    def delete_course(self, course_id):
        confirm = QMessageBox.question(
            self, "Delete course", "Are you sure you want to delete this course?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_course(course_id)
            self.reorganize_courses()
            self.load_tags()
