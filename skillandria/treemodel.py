import re

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtGui import QFont, QIcon, QBrush, QColor

from skillandria.main_db import *
from skillandria.treenode import *
from skillandria.helpers import *


class VideoTreeModel(QAbstractItemModel):
    def __init__(self, folder_path, string_from_file, icon_path):
        super().__init__()

        self.db_worker = MainDatabase()

        self.icon_path = icon_path
        self.string_from_file = string_from_file
        self.root_node = None
        self.set_root(folder_path)

    def set_root(self, folder_path):
        self.beginResetModel()
        self.root_node = self.create_tree(folder_path)
        self.endResetModel()

    @staticmethod
    def human_sort_key(name):
        parts = re.split(r'(\d+)', name)
        return [int(part) if part.isdigit() else part for part in parts]

    @staticmethod
    def is_video_file(file_path):
        video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".m4v", ".wmv", ".flv", ".webm", ".mpg", ".mpeg", ".vob"]
        return any(file_path.lower().endswith(extension) for extension in video_extensions)

    def rowCount(self, parent):
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        if parent_node is None:
            return 0

        return parent_node.child_count()

    def columnCount(self, parent):
        return 2

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "Lecture"
            elif section == 1:
                return "Timer"

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
            elif column == 1 and os.path.isfile(node.path):
                spent = self.db_worker.read_spent_time(node.path)
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
            if self.string_from_file is not None:
                if node.folder_name_matches(self.string_from_file):
                    return QBrush(QColor(234, 227, 208))


        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            if os.path.isdir(node.path) and node.all_files_played():
                icon = QIcon(os.path.join(self.icon_path, "trophy.png"))
                return icon
            if self.string_from_file is not None:
                if node.folder_name_matches(self.string_from_file):
                    icon = QIcon(os.path.join(self.icon_path, "ico_studying.png"))
                    return icon
        return None

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
            items = sorted(items, key=self.human_sort_key)
            has_video_files = False
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path) and self.is_video_file(item_path):
                    child_node = TreeNode(parent=parent_node, name=item, path=item_path)
                    child_node.played = self.db_worker.read_played_status(item_path)
                    parent_node.add_child(child_node)
                    has_video_files = True
                elif os.path.isdir(item_path):
                    folder_node = TreeNode(parent=parent_node, name=item, path=item_path)
                    if self.populate_tree(folder_node):
                        parent_node.add_child(folder_node)
                        has_video_files = True

            return has_video_files
        else:
            return False

    def flags(self, index):
        default_flags = super().flags(index)
        return default_flags | Qt.ItemFlag.ItemIsEnabled

    def save_video_info(self, current_video_path, current_video_position, current_video_played, current_video_timer):
        self.db_worker.save_video_info(current_video_path, current_video_position, current_video_played,
                                       current_video_timer)

    def load_video_position(self, current_video_path):
        return self.db_worker.load_video_position(current_video_path)

    def load_video_played(self, current_video_path):
        return self.db_worker.load_video_played(current_video_path)

    def load_video_timer(self, current_video_path):
        return self.db_worker.load_video_timer(current_video_path)

    def close_database(self):
        self.db_worker.close_database()
