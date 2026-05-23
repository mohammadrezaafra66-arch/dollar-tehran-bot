import sqlite3


class SQLiteManager:
    def __init__(self, db_path='data/afra.db'):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)
