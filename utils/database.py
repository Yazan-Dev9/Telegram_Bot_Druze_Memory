import sqlite3
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_name="martyrs.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self._create_tables()
            logger.info("Connected to the database.")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to the database: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from the database.")

    def _create_tables(self):
        try:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS martyrs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    mother_name TEXT,
                    birth_date TEXT,
                    death_date TEXT,
                    death_cause TEXT,
                    residence TEXT,
                    photo TEXT,  -- Store the file path
                    notes TEXT,
                    approved INTEGER DEFAULT 0 --  0: pending, 1: approved
                )
            """
            )
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY
                )
            """
            )
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS blocked_users (
                    user_id INTEGER PRIMARY KEY
                )
            """
            )
            self.conn.commit()
            logger.info("Tables created (if they didn't exist).")
        except sqlite3.Error as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def add_admin(self, user_id):
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,)
            )
            self.conn.commit()
            logger.info(f"Admin added with ID: {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to add admin: {e}")
            return False

    def remove_admin(self, user_id):
        try:
            self.cursor.execute(
                "DELETE FROM admins WHERE user_id = ?", (user_id,))
            self.conn.commit()
            logger.info(f"Admin removed with ID: {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to remove admin: {e}")
            return False

    def is_admin(self, user_id):
        try:
            self.cursor.execute(
                "SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Failed to check admin status: {e}")
            return False

    def block_user(self, user_id):
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)", (
                    user_id,)
            )
            self.conn.commit()
            logger.info(f"User blocked with ID: {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to block user: {e}")
            return False

    def unblock_user(self, user_id):
        try:
            self.cursor.execute(
                "DELETE FROM blocked_users WHERE user_id = ?", (user_id,)
            )
            self.conn.commit()
            logger.info(f"User unblocked with ID: {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to unblock user: {e}")
            return False

    def is_blocked(self, user_id):
        try:
            self.cursor.execute(
                "SELECT 1 FROM blocked_users WHERE user_id = ?", (user_id,)
            )
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Failed to check blocked status: {e}")
            return False

    def search_martyr(self, martyr_name):
        try:
            self.cursor.execute(
                "SELECT * FROM martyrs WHERE name = ?", (martyr_name,))
            row = self.cursor.fetchone()
            if row:
                martyr = {
                    "id": row[0],
                    "name": row[1],
                    "mother_name": row[2],
                    "birth_date": row[3],
                    "death_date": row[4],
                    "death_cause": row[5],
                    "residence": row[6],
                    "photo": row[7],
                    "notes": row[8],
                    "approved": row[9],  # Retrieve approval status
                }
                return martyr
            else:
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to search for martyr: {e}")
            return None

    def save_martyr_data(self, data):
        try:
            self.cursor.execute(
                """
                INSERT INTO martyrs (name, mother_name, birth_date, death_date, death_cause, residence, photo, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["name"],
                    data["mother_name"],
                    data["birth_date"],
                    data["death_date"],
                    data["death_cause"],
                    data["residence"],
                    data.get("photo"),
                    data.get("notes"),
                ),
            )
            self.conn.commit()
            row = self.cursor.fetchone()
            if row:
                martyr = {
                    "id": row[0],
                    "name": row[1],
                    "mother_name": row[2],
                    "birth_date": row[3],
                    "death_date": row[4],
                    "death_cause": row[5],
                    "residence": row[6],
                    "photo": row[7],
                    "notes": row[8],
                    "approved": row[9],
                }
                return martyr
            else:
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to search for martyr: {e}")
            return None

    def get_pending_martyrs(self):
        try:
            self.cursor.execute(
                "SELECT id, name FROM martyrs WHERE approved = 0")
            rows = self.cursor.fetchall()
            martyrs = [{"id": row[0], "name": row[1]} for row in rows]
            return martyrs
        except sqlite3.Error as e:
            logger.error(f"Failed to get pending martyrs: {e}")
            return []

    def approve_martyr(self, martyr_id):
        try:
            self.cursor.execute(
                "UPDATE martyrs SET approved = 1 WHERE id = ?", (martyr_id,)
            )
            self.conn.commit()
            logger.info(f"Martyr approved with ID: {martyr_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to approve martyr: {e}")
            return False

    def get_all_martyrs(self):
        try:
            self.cursor.execute("SELECT * FROM martyrs WHERE approved = 1")
            rows = self.cursor.fetchall()
            martyrs = []
            for row in rows:
                martyr = {
                    "id": row[0],
                    "name": row[1],
                    "mother_name": row[2],
                    "birth_date": row[3],
                    "death_date": row[4],
                    "death_cause": row[5],
                    "residence": row[6],
                    "photo": row[7],
                    "notes": row[8],
                    "approved": row[9],
                }
                martyrs.append(martyr)
            return martyrs
        except sqlite3.Error as e:
            logger.error(f"Failed to get all martyrs: {e}")
        return []


database_manager = DatabaseManager()
