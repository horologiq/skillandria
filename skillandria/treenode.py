import os


class TreeNode:
    def __init__(self, parent=None, name="", path=""):
        self.parent = parent
        self.name = name
        self.path = path
        self.children = []
        self.played = False
        self.is_folder = os.path.isdir(path)

    def precalculate_played_status(self):
        if self.is_folder:
            for child in self.children:
                child.precalculate_played_status()
            self.played = all(child.played for child in self.children if not child.is_folder)
        else:
            self.played = self.played

    def folder_name_matches(self, string_from_file):

        path_parts = self.path.split(os.path.sep)
        file_parts = string_from_file.split(os.path.sep)
        for folder, file_part in zip(path_parts, file_parts):
            if folder != file_part:
                return False
        return True

    def add_child(self, child):
        self.children.append(child)

    def remove_child(self, child):
        self.children.remove(child)

    def child_count(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0

    def all_files_played(self):
        if self.is_folder:
            return all(child.all_files_played() for child in self.children)
        else:
            return self.played
