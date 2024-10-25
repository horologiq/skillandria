import os
import cv2
import random
import re
import yt_dlp
import shutil

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QLineEdit, QPushButton, QFileDialog, QProgressBar
)


def get_video_duration(video_path):
    video = cv2.VideoCapture(video_path)
    if video.isOpened():
        fps = video.get(cv2.CAP_PROP_FPS)
        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frames / fps
        return duration
    return 0

def generate_thumbnail(video_path, thumbnail_path):
    video = cv2.VideoCapture(video_path)
    if video.isOpened():
        video.set(cv2.CAP_PROP_POS_FRAMES, random.randint(0, int(video.get(cv2.CAP_PROP_FRAME_COUNT)) // 2))  # Frame aleatorio
        success, image = video.read()
        if success:
            cv2.imwrite(thumbnail_path, image)
            return True
    return False

def import_course(directory):
    total_duration = 0
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']

    videos = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_path = os.path.join(root, file)
                videos.append(video_path)
                total_duration += get_video_duration(video_path)

    if videos:
        thumbnail_path = os.path.join(directory, 'thumbnail.jpg')
        generate_thumbnail(videos[0], thumbnail_path)
        return total_duration, thumbnail_path
    else:
        return total_duration, None




class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import course")
        self.layout = QVBoxLayout()
        self.resize(600, 250)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.create_import_from_disk_tab()
        self.create_import_from_youtube_tab()

        self.setLayout(self.layout)

    def create_import_from_disk_tab(self):
        self.disk_tab = QWidget()
        disk_layout = QVBoxLayout()

        self.title_input = QLineEdit(self.disk_tab)
        self.title_input.setPlaceholderText("Course title")
        disk_layout.addWidget(self.title_input)

        self.author_input = QLineEdit(self.disk_tab)
        self.author_input.setPlaceholderText("Course author")
        disk_layout.addWidget(self.author_input)

        self.tags_input = QLineEdit(self.disk_tab)
        self.tags_input.setPlaceholderText("Tags (separated by comma)")
        disk_layout.addWidget(self.tags_input)

        self.directory_button = QPushButton("Select directory", self.disk_tab)
        self.directory_button.clicked.connect(self.select_directory)
        disk_layout.addWidget(self.directory_button)

        self.import_button = QPushButton("Import", self.disk_tab)
        self.import_button.clicked.connect(self.import_course_from_disk)
        disk_layout.addWidget(self.import_button)

        self.disk_tab.setLayout(disk_layout)
        self.tab_widget.addTab(self.disk_tab, "Import from disk")

    def create_import_from_youtube_tab(self):
        self.youtube_tab = QWidget()
        youtube_layout = QVBoxLayout()

        self.url_input = QLineEdit(self.youtube_tab)
        self.url_input.setPlaceholderText("Enter YouTube video / playlist URL")
        youtube_layout.addWidget(self.url_input)

        self.tags_input_youtube = QLineEdit(self.youtube_tab)
        self.tags_input_youtube.setPlaceholderText("Tags (separated by comma)")
        youtube_layout.addWidget(self.tags_input_youtube)

        self.directory_button_youtube = QPushButton("Select target directory", self.youtube_tab)
        self.directory_button_youtube.clicked.connect(self.select_directory_youtube)
        youtube_layout.addWidget(self.directory_button_youtube)

        self.progress_bar = QProgressBar(self.youtube_tab)
        self.progress_bar.setValue(0)
        youtube_layout.addWidget(self.progress_bar)

        self.download_button = QPushButton("Download", self.youtube_tab)
        self.download_button.clicked.connect(self.download_from_youtube)
        youtube_layout.addWidget(self.download_button)

        self.youtube_tab.setLayout(youtube_layout)
        self.tab_widget.addTab(self.youtube_tab, "Get from YouTube")



    def select_directory(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Select directory")
        if self.directory:
            self.directory_button.setText(self.directory)
            self.populate_fields_from_directory(os.path.basename(self.directory))

    def populate_fields_from_directory(self, folder_name):
        self.title_input.clear()
        self.author_input.clear()
        self.tags_input.clear()

        # "[XXXX] [YYYY] ZZZZ"
        match1 = re.match(r'^\[(.+?)\] \[(.+?)\] (.+)$', folder_name)
        if match1:
            tag = match1.group(1).strip()
            author = match1.group(2).strip()
            title = match1.group(3).strip()
            self.tags_input.setText(tag)
            self.author_input.setText(author)
            self.title_input.setText(title)
            return

        # "XXXX - YYYY"
        match2 = re.match(r'^(.*?) - (.*)$', folder_name)
        if match2:
            author = match2.group(1).strip()
            title = match2.group(2).strip()
            self.author_input.setText(author)
            self.title_input.setText(title)
            return


    def import_course_from_disk(self):
        title = self.title_input.text()
        author = self.author_input.text()
        tags = self.tags_input.text()

        if self.directory:
            duration, thumbnail = import_course(self.directory)
            self.parent().db.add_course(title, author, duration, thumbnail, tags)
            self.parent().load_filtered_courses(max_columns=3)
            self.parent().load_tags()
            self.accept()

    def select_directory_youtube(self):
        self.directory_youtube = QFileDialog.getExistingDirectory(self, "Select target directory")
        if self.directory_youtube:
            self.directory_button_youtube.setText(self.directory_youtube)

    def download_from_youtube(self):
        url = self.url_input.text()
        tags = self.tags_input_youtube.text()

        if 'playlist' in url:
            self.download_playlist(url, tags)
        else:
            self.download_video(url, tags)

    def download_video(self, url, tags):
        try:
            self.download_button.setText("Processing...")
            self.download_button.setEnabled(False)

            with yt_dlp.YoutubeDL({'skip_download': True}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                title = info_dict.get('title', 'Unknown Title')
                author = info_dict.get('uploader', 'Unknown Author')
                duration = info_dict.get('duration', 0)
                thumbnail_url = info_dict.get('thumbnail', None)
                chapters = info_dict.get("chapters", None)
                ext = info_dict.get('ext', 'mp4')  # Obtener extensión real

            folder_name = f"[{tags}] [{author}] {title}"
            folder_path = os.path.join(self.directory_youtube, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            video_output_path = os.path.join(folder_path, f"{title}.{ext}")

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': video_output_path,
                'writesubtitles': True,  # Descargar subtítulos
                'subtitleslangs': ['en'],  # Cambia a tu preferencia, 'en' es para inglés
                'progress_hooks': [self.download_progress_hook],
                'postprocessors': [{'key': 'FFmpegSplitChapters'}] if chapters else [],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if thumbnail_url:
                self.download_thumbnail(thumbnail_url, folder_path)

            if chapters:
                self.delete_original_file(video_output_path)
                self.move_chapter_videos(folder_path)
                self.clean_all_filenames_in_directory(folder_path, title)

            self.parent().db.add_course(title, author, duration, os.path.join(folder_path, "thumbnail.jpg"), tags)
            self.parent().load_filtered_courses(max_columns=3)
            self.accept()

        except Exception as e:
            print(f"Error downloading video: {e}")

        finally:
            self.download_button.setText("Download")
            self.download_button.setEnabled(True)
            self.accept()


    def download_playlist(self, url, tags):
        try:
            self.download_button.setText("Processing...")
            self.download_button.setEnabled(False)

            with yt_dlp.YoutubeDL({'skip_download': True}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                playlist_title = info_dict.get('playlist_title', 'Unknown Playlist')
                author = info_dict.get('uploader', 'Unknown Author')
                thumbnail_url = info_dict.get('entries', [])[0].get('thumbnail', None)
                total_duration = sum(entry.get('duration', 0) for entry in info_dict.get('entries', []))

            folder_name = f"[{tags}] [{author}] {playlist_title}"
            folder_path = os.path.join(self.directory_youtube, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(folder_path, '%(playlist_index)02d - %(title)s.%(ext)s'),
                'writesubtitles': True,
                'subtitleslangs': ['en'],
                'progress_hooks': [self.download_progress_hook],
                'postprocessors': [{'key': 'FFmpegSplitChapters'}],  # Divide en capítulos si existen
                'yes_playlist': True,  # Descargar toda la playlist
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if thumbnail_url:
                self.download_thumbnail(thumbnail_url, folder_path)

            for entry in info_dict['entries']:
                title = entry.get('title', 'Unknown Title')
                video_output_path = os.path.join(folder_path, f"{title}.mp4")

                if 'chapters' in entry:
                    self.delete_original_file(video_output_path)
                    self.move_chapter_videos(folder_path)
                    self.clean_all_filenames_in_directory(folder_path, title)

            self.parent().db.add_course(playlist_title, author, total_duration,
                                        os.path.join(folder_path, "thumbnail.jpg"), tags)

            self.parent().load_filtered_courses(max_columns=3)

        except Exception as e:
            print(f"Error downloading playlist: {e}")

        finally:
            self.download_button.setText("Download")
            self.download_button.setEnabled(True)
            self.accept()

    def delete_original_file(self, filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error al eliminar el archivo {filepath}: {e}")
            return False


    def move_chapter_videos(self, folder_path):
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
        for root, _, files in os.walk(os.path.abspath(os.getcwd())):
            for file in files:
                if any(file.endswith(ext) for ext in video_extensions):
                    original_path = os.path.join(root, file)
                    destination_path = os.path.join(folder_path, file)
                    try:
                        shutil.move(original_path, destination_path)
                    except Exception as e:
                        print(f"Error al mover el archivo {file}: {e}")

    def clean_filename(self, filename, original_title):
        title_pattern = re.escape(original_title)
        new_filename = re.sub(title_pattern, '', filename)
        new_filename = re.sub(r'\s*\[[A-Za-z0-9_-]{11}\](?=\.\w+$)', '', new_filename)
        new_filename = re.sub(r'^\s*-\s*|\s*-\s*$', '', new_filename).strip()
        return new_filename

    def clean_all_filenames_in_directory(self, directory, original_title):
        for filename in os.listdir(directory):
            original_path = os.path.join(directory, filename)

            if os.path.isfile(original_path):
                new_filename = self.clean_filename(filename, original_title)
                new_path = os.path.join(directory, new_filename)
                os.rename(original_path, new_path)


    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = d.get('total_bytes', 1)
            progress_percentage = (downloaded_bytes / total_bytes) * 100
            self.progress_bar.setValue(int(progress_percentage))  # Convertir a entero

    def download_thumbnail(self, thumbnail_url, folder_path):
        try:
            import urllib.request
            thumbnail_path = os.path.join(folder_path, "thumbnail.jpg")
            urllib.request.urlretrieve(thumbnail_url, thumbnail_path)
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")

