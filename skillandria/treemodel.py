from datetime import timedelta
from PyQt5.QtCore import QAbstractItemModel, QModelIndex
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QBrush, QColor

from skillandria.helpers import *
from skillandria.treenode import TreeNode

from moviepy.editor import VideoFileClip

class VideoTreeModel(QAbstractItemModel):
    def __init__(self, folder_path, string_from_file):
        super().__init__()
        self.root_node = self.create_tree(folder_path)
        self.exclude_empty_folders()
        self.string_from_file = string_from_file
        self.played_status = read_played_status(folder_path)  # Pass folder_path as a parameter

        # Cache for storing video durations
        self.duration_cache = {}

        # Precalculate the played status of nodes
        self.precalculate_played_status()

    def precalculate_played_status(self):
        self.root_node.precalculate_played_status()

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
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Lecture"
            elif section == 1:
                return "Flag"
            elif section == 2:
                return "Duration"
            elif section == 3:
                return "Spent"
            # Add more conditions for additional columns if needed

        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()
        column = index.column()  # Get the current column

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return os.path.basename(node.path)
            elif index.column() == 2 and os.path.isfile(node.path):
                duration = self.get_video_duration(node.path)
                return str(duration)

        if role == Qt.FontRole and os.path.isdir(node.path):
            font = QFont()
            font.setBold(True)
            return font

        if role == Qt.CheckStateRole and column == 0:
            if os.path.isfile(node.path):
                return Qt.Checked if node.played else Qt.Unchecked

            if os.path.isdir(node.path):
                if node.all_files_played():
                    return Qt.Checked
                elif any(child.played for child in node.children if os.path.isfile(child.path)):
                    return Qt.PartiallyChecked

        if role == Qt.BackgroundRole:
            if node.folder_name_matches(self.string_from_file):
                return QBrush(QColor(209, 237, 224))

        if role == Qt.DecorationRole and index.column() == 1:
            if node.folder_name_matches(self.string_from_file):
                icon = (QIcon(os.path.join(icon_path, "ico_studying.png")))
                return icon
            if os.path.isdir(node.path) and node.all_files_played():
                icon = (QIcon(os.path.join(icon_path, "trophy.png")))
                return icon

        return None

    def get_video_duration(self, file_path):
        if file_path in self.duration_cache:
            # Duration already cached, return it
            return self.duration_cache[file_path]

        try:
            clip = VideoFileClip(file_path)
            duration = clip.duration
            clip.close()
            duration_str = str(timedelta(seconds=int(duration)))
            # Cache the duration for future access
            self.duration_cache[file_path] = duration_str
            return duration_str
        except ImportError:
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
        root_node = TreeNode(None, "", folder_path)
        self.populate_tree(root_node)
        update_played_status(root_node)  # Update the "Played" status for the root node
        return root_node

    def populate_tree(self, parent_node):
        path = parent_node.path
        if os.path.isdir(path):
            items = os.listdir(path)
            items = sorted(items, key=human_sort_key)
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path) and is_video_file(item_path):
                    child_node = TreeNode(parent=parent_node, name=item, path=item_path)
                    update_played_status(child_node)  # Update the "Played" status
                    parent_node.add_child(child_node)
                elif os.path.isdir(item_path):
                    folder_node = TreeNode(parent=parent_node, name=item, path=item_path)
                    self.populate_tree(folder_node)
                    update_played_status(folder_node)  # Update the "Played" status
                    parent_node.add_child(folder_node)

    def exclude_empty_folders_recursive(self, parent_node):
        children_to_remove = []
        for child_node in parent_node.children:
            if child_node.is_folder:
                self.exclude_empty_folders_recursive(child_node)

            if child_node.is_folder and len(child_node.children) == 0:
                children_to_remove.append(child_node)

        for child_node in children_to_remove:
            parent_node.remove_child(child_node)

    def exclude_empty_folders(self):
        self.exclude_empty_folders_recursive(self.root_node)

    def flags(self, index):
        default_flags = super().flags(index)
        return default_flags | Qt.ItemIsEnabled  # Add the Qt.ItemIsEnabled flag
