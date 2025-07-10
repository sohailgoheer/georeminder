import sqlite3
import os

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.create_table()

    def connect(self):
        if not self.conn:
            try:
                self.conn = sqlite3.connect(self.db_path)
            except sqlite3.Error as e:
                print(f"[DB ERROR] Failed to connect: {e}")

    def create_table(self):
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_id TEXT,
                    layer_id TEXT,
                    reminder_text TEXT,
                    reminder_time TEXT
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] create_table: {e}")

    def add_reminder(self, feature_id, layer_id, reminder_text, reminder_time):
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (feature_id, layer_id, reminder_text, reminder_time)
                VALUES (?, ?, ?, ?)
            """, (feature_id, layer_id, reminder_text, reminder_time))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] add_reminder: {e}")
            raise

    def get_all_reminders(self):
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM reminders")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[DB ERROR] get_all_reminders: {e}")
            return []

    def delete_reminder(self, reminder_id):
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] delete_reminder: {e}")
            raise

    def update_reminder_time(self, reminder_id, new_time):
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("UPDATE reminders SET reminder_time = ? WHERE id = ?", (new_time, reminder_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] update_reminder_time: {e}")
            raise

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
            except sqlite3.Error as e:
                print(f"[DB ERROR] close: {e}")

    def __del__(self):
        self.close()
