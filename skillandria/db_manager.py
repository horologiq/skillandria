import sqlite3

from skillandria.helpers import *


class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(get_courses_db_path())
        self.cursor = self.conn.cursor()
        self.current_data_item = {}
        self.create_table()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            duration INTEGER NOT NULL,
            progress INTEGER DEFAULT 0,
            tags TEXT,  -- Nuevas etiquetas
            dir TEXT,  -- Nueva columna añadida
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def add_course(self, title, author, duration, path, tags):
        # Guardar en la base de datos
        query = """INSERT INTO courses (title, author, duration, tags, dir)
                   VALUES (?, ?, ?, ?, ?)"""
        self.cursor.execute(query, (title, author, duration, tags, os.path.dirname(path)))
        self.conn.commit()

    def search_courses(self, search_text="", tag=None):
        if tag:
            query = 'SELECT * FROM courses WHERE tags LIKE ? ORDER BY last_accessed'
            cursor = self.conn.execute(query, (f'%{tag}%',))
        else:
            query = 'SELECT * FROM courses WHERE title LIKE ? OR tags LIKE ? ORDER BY last_accessed'
            cursor = self.conn.execute(query, (f'%{search_text}%', f'%{search_text}%'))
        return cursor.fetchall()

    def get_courses(self, order_by=None):
        query = 'SELECT id, title, author, duration, progress, tags, dir, last_accessed FROM courses'
        if order_by:
            query += f' ORDER BY {order_by}'
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def update_course_progress(self, course_id, progress):
        query = '''
        UPDATE courses
        SET progress = ?, last_accessed = CURRENT_TIMESTAMP
        WHERE id = ?
        '''
        self.conn.execute(query, (progress, course_id))
        self.conn.commit()

    def get_course_by_id(self, course_id):
        query = 'SELECT * FROM courses WHERE id = ?'
        cursor = self.conn.execute(query, (course_id,))
        return cursor.fetchone()

    def delete_course(self, course_id):
        try:
            self.cursor.execute("DELETE FROM courses WHERE last_accessed = ?", (course_id,))  # Cambiado a "courses"
            self.conn.commit()
            print(course_id)
        except sqlite3.Error as e:
            print(f"Error al eliminar el curso: {e}")
