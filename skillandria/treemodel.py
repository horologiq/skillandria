import datetime
import re

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtGui import QFont, QIcon, QBrush, QColor
from moviepy.editor import VideoFileClip

from skillandria.helpers import *
from skillandria.treenode import *


class VideoTreeModel(QAbstractItemModel):
    def __init__(self, folder_path, string_from_file, icon_path, theme):
        super().__init__()
        self.icon_path = icon_path
        self.theme = theme
        self.string_from_file = string_from_file
        self.root_node = self.create_tree(folder_path)
        self.duration_cache = {}

    def human_sort_key(self, name):
        parts = re.split(r'(\d+)', name)
        return [int(part) if part.isdigit() else part for part in parts]

    def is_video_file(self, file_path):
        video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".m4v", ".wmv", ".flv", ".webm", ".mpg", ".mpeg", ".vob"]
        return any(file_path.lower().endswith(extension) for extension in video_extensions)

    def read_played_status(self, file_path):
        played = False
        nfo_file_path = os.path.splitext(file_path)[0] + ".nfo"
        if os.path.isfile(nfo_file_path):
            with open(nfo_file_path, "r") as nfo_file:
                for line in nfo_file:
                    if line.strip().startswith("Played="):
                        played_value = line.strip().split("=")[1]
                        played = played_value.lower() == "true"
                        break
        return played

    def read_spent_time(self, file_path):
        spent_time = 0
        nfo_file_path = os.path.splitext(file_path)[0] + ".nfo"
        if os.path.isfile(nfo_file_path):
            with open(nfo_file_path, "r") as nfo_file:
                for line in nfo_file:
                    if line.strip().startswith("Timer="):
                        spent_time = int(line.strip().split("=")[1])
                        break

        spent_time_str = format_time(spent_time)
        return spent_time_str

    def rowCount(self, parent):
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        if parent_node is None:
            return 0

        return parent_node.child_count()

    def columnCount(self, parent):
        return 4

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "Lecture"
            elif section == 1:
                return "Flag"
            elif section == 2:
                return "Duration"
            elif section == 3:
                return "Spent"

        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                file_name = os.path.basename(node.path)
                if os.path.isfile(node.path):
                    name_without_extension = os.path.splitext(file_name)[0]
                    return name_without_extension
                else:
                    return file_name
            elif index.column() == 2 and os.path.isfile(node.path):
                duration = self.get_video_duration(node.path)
                return str(duration)
            elif column == 3 and os.path.isfile(node.path):
                spent = self.read_spent_time(node.path)
                return str(spent)

        if role == Qt.ItemDataRole.FontRole and os.path.isdir(node.path):
            font = QFont()
            font.setBold(True)
            return font

        if role == Qt.ItemDataRole.CheckStateRole and column == 0:
            if os.path.isfile(node.path):
                return Qt.CheckState.Checked if node.played else Qt.CheckState.Unchecked

            if os.path.isdir(node.path):
                if node.all_files_played():
                    return Qt.CheckState.Checked
                elif any(child.played for child in node.children if os.path.isfile(child.path)):
                    return Qt.CheckState.PartiallyChecked

        if role == Qt.ItemDataRole.BackgroundRole:
            if node.folder_name_matches(self.string_from_file):
                if self.theme == "light":
                    return QBrush(QColor(107, 107, 107))
                else:
                    return QBrush(QColor(189, 189, 189))

        if role == Qt.ItemDataRole.DecorationRole and index.column() == 1:
            if node.folder_name_matches(self.string_from_file):
                icon = (QIcon(os.path.join(self.icon_path, "ico_studying.png")))
                return icon
            if os.path.isdir(node.path) and node.all_files_played():
                icon = (QIcon(os.path.join(self.icon_path, "trophy.png")))
                return icon

        return None

    def get_video_duration(self, file_path):
        if file_path in self.duration_cache:
            return self.duration_cache[file_path]

        try:
            clip = VideoFileClip(file_path)
            duration = clip.duration
            clip.close()
            duration_str = str(datetime.timedelta(seconds=int(duration)))
            self.duration_cache[file_path] = duration_str
            return duration_str
        except Exception:
            return ""

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        child_node = parent_node.child(row)
        if child_node:
            return self.createIndex(row, column, child_node)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_node = index.internalPointer()
        parent_node = child_node.parent

        if parent_node == self.root_node:
            return QModelIndex()

        return self.createIndex(parent_node.row(), 0, parent_node)

    def create_tree(self, folder_path):
        root_node = TreeNode(None, "root", folder_path)
        self.populate_tree(root_node)
        return root_node

    def populate_tree(self, parent_node):
        path = parent_node.path
        if os.path.isdir(path):
            items = os.listdir(path)
            items = sorted(items, key=self.human_sort_key)  # Sort the items using the human_sort_key function
            has_video_files = False  # Track if the folder has any video files
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path) and self.is_video_file(item_path):
                    child_node = TreeNode(parent=parent_node, name=item, path=item_path)
                    child_node.played = self.read_played_status(item_path)
                    parent_node.add_child(child_node)
                    has_video_files = True  # Set the flag to True if a video file is found
                elif os.path.isdir(item_path):
                    folder_node = TreeNode(parent=parent_node, name=item, path=item_path)
                    if self.populate_tree(folder_node):
                        parent_node.add_child(folder_node)
                        has_video_files = True

            return has_video_files  # Return the flag indicating if the folder has video files
        else:
            return False

    def flags(self, index):
        default_flags = super().flags(index)
        return default_flags | Qt.ItemFlag.ItemIsEnabled
