import sqlite3

from skillandria.helpers import *
from skillandria.time_conversion import *


class MainDatabase:
    def __init__(self):
        super().__init__()
        self.db_connection = sqlite3.connect(get_db_path())
        self.cursor = self.db_connection.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS videos (path TEXT PRIMARY KEY, position INTEGER, played INTEGER, timer INTEGER)")
        self.db_connection.commit()
        self.current_data_item = {}

    def read_played_status(self, file_path):
        query = 'SELECT played FROM videos WHERE path = ?'
        result = self.db_connection.execute(query, (file_path,)).fetchone()
        return result[0] if result else False

    def read_spent_time(self, file_path):
        query = 'SELECT timer FROM videos WHERE path = ?'
        result = self.db_connection.execute(query, (file_path,)).fetchone()
        spent_time = result[0] if result else 0
        spent_time_str = seconds_to_time(spent_time)
        return spent_time_str

    def update_played_status(self, file_path, played):
        query = 'INSERT OR REPLACE INTO videos (path, played) VALUES (?, ?)'
        self.db_connection.execute(query, (file_path, played))
        self.db_connection.commit()

    def update_spent_time(self, file_path, spent_time):
        query = 'INSERT OR REPLACE INTO videos (path, timer) VALUES (?, ?)'
        self.db_connection.execute(query, (file_path, spent_time))
        self.db_connection.commit()

    def save_video_info(self, current_video_path, current_video_position, current_video_played, current_video_timer):
        if current_video_path:
            self.db_connection.execute("INSERT OR REPLACE INTO videos (path, position, played, timer) VALUES (?, ?, "
                                       "?, ?)",
                                       (current_video_path, current_video_position, current_video_played,
                                        current_video_timer))
            self.db_connection.commit()

    def load_video_position(self, current_video_path):
        if current_video_path:

            self.current_data_item = self.db_connection.execute(
                "SELECT position, played, timer FROM videos WHERE path=?", (current_video_path,)).fetchone()

            if self.current_data_item:
                return self.current_data_item[0]
            else:
                return 0

    def load_video_played(self, current_video_path):
        if current_video_path:

            self.current_data_item = self.db_connection.execute(
                "SELECT position, played, timer FROM videos WHERE path=?", (current_video_path,)).fetchone()

            if self.current_data_item:
                return bool(self.current_data_item[1])
            else:
                return 0

    def load_video_timer(self, current_video_path):
        if current_video_path:

            self.current_data_item = self.db_connection.execute(
                "SELECT position, played, timer FROM videos WHERE path=?", (current_video_path,)).fetchone()

            if self.current_data_item:
                return self.current_data_item[2]
            else:
                return 0

    def close_database(self):
        self.db_connection.close()