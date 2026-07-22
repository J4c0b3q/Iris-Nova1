import sqlite3


class BaseRepository:

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def commit(self):
        self.connection.commit()