import os
import sqlite3
from pathlib import Path

from api.lib.helpers import update_config


class Database:
    """
    Database class

    This class is used to interact with the database.
    """
    database_file = None

    def __init__(self):
        config_data = update_config("config.yml")
        self.database_file = Path(config_data.get("DATABASE_FILE"))
        self.ensure_db()

    def ensure_db(self):
        """
        Ensure the database is in the right shape
        """
        if os.path.isfile(self.database_file):
            # Database exists
            return
        else:
            # Create database
            connection = sqlite3.connect(self.database_file, timeout=10)
            cursor = connection.cursor()
            cursor.row_factory = sqlite3.Row
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY,
                    created_at INTEGER,
                    jobtype TEXT,
                    completed_at INTEGER,
                    status TEXT,
                    message TEXT,
                    details JSON,
                    results JSON
                )
            """)
            connection.commit()
            connection.close()

    def get_db(self):
        """
        Get a database connection and cursor object

        :return tuple: `(db connection, cursor)`
        """
        connection = sqlite3.connect(self.database_file, timeout=10)
        cursor = connection.cursor()
        cursor.row_factory = sqlite3.Row
        return connection, cursor

    def select(self, sql):
        """
        Select rows from the database

        :param str sql: SQL query
        :return list: List of rows
        """
        connection, cursor = self.get_db()
        cursor.execute(sql)
        try:
            for row in cursor.fetchall():
                yield row
        finally:
            connection.close()

    def insert(self, sql, values):
        """
        Insert a row into the database

        :param str sql: SQL query
        :param tuple values: Values to insert
        """
        connection, cursor = self.get_db()
        cursor.execute(sql, values)
        connection.commit()
        # Retrieve the ID of the inserted row
        last_id = cursor.lastrowid
        connection.close()
        return last_id