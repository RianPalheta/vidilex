import sqlite3
from utils import MediaFile, DB_PATH

class DB():
    def __init__(self):
        self.connection = sqlite3.connect(DB_PATH)
        self.cursor = self.connection.cursor()
        
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_files (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL
            )
            """
        )
        
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                content TEXT
            )
            """
        )
        
        self.connection.commit()
    
    def save_processed_file(self, media: MediaFile):
        self.cursor.execute(
            """
            INSERT INTO processed_files (id, title)
            VALUES (?, ?)
            """,
            (media['id'], media['title'])
        )
        
        self.connection.commit()
    
    def file_already_processed(self, file_id: str):
        self.cursor.execute("SELECT id FROM processed_files WHERE id=?", (file_id,))
        result = self.cursor.fetchone()
        self.connection.commit()
        return result is not None
    
    def clear_processed_files(self):
        self.cursor.execute("DELETE FROM processed_files")
        self.connection.commit()

    def save_setting(self, key: str, content: str):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO settings (key, content)
            VALUES (?, ?)
            """,
            (key, content)
        )
        self.connection.commit()

    def get_setting(self, key: str) -> str | None:
        self.cursor.execute("SELECT content FROM settings WHERE key=?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def delete_setting(self, key: str):
        self.cursor.execute("DELETE FROM settings WHERE key=?", (key,))
        self.connection.commit()