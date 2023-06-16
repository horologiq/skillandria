import sqlite3

from skillandria.helpers import *


class BookmarksDatabase:
    def __init__(self):
        super().__init__()
        self.db_connection = sqlite3.connect(get_bookmark_db_path())
        self.cursor = self.db_connection.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS bookmarks (video_file TEXT, position INTEGER, comment TEXT)")
        self.db_connection.commit()
        self.current_data_item = {}

    def get_bookmarks_for_video(self, video_file):
        self.cursor.execute("SELECT * FROM bookmarks WHERE video_file=?", (video_file,))
        bookmarks = self.cursor.fetchall()
        return bookmarks

    def save_bookmark(self, bookmark):
        self.cursor.execute("INSERT INTO bookmarks VALUES (?, ?, ?)", bookmark)
        self.db_connection.commit()
