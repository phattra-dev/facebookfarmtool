import sqlite3
import os
from typing import List, Dict, Optional

class AccountDBManager:
    """Manages all database operations for Facebook accounts."""

    def __init__(self, db_path: str = 'accounts.db'):
        """
        Initialize the database manager and connect to the SQLite database.
        If the database file doesn't exist, it will be created.
        """
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        """Establish a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        except sqlite3.Error as e:
            raise Exception(f"Failed to connect to database: {e}")

    def create_table(self):
        """Create the 'accounts' table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS accounts (
            uid TEXT PRIMARY KEY NOT NULL,
            password TEXT,
            token TEXT,
            cookie TEXT,
            category TEXT DEFAULT 'Default',
            status TEXT DEFAULT 'Unknown',
            last_login TEXT,
            login_count INTEGER DEFAULT 0,
            task_count INTEGER DEFAULT 0,
            created_date TEXT,
            session_file TEXT
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_sql)
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Failed to create table: {e}")

    def add_account(self, uid: str, password: str = "", token: str = "", cookie: str = "", category: str = "Default") -> bool:
        """
        Insert a new account into the database.
        Returns True if successful, False otherwise.
        """
        insert_sql = """
        INSERT INTO accounts (uid, password, token, cookie, category, status, last_login, login_count, task_count, created_date, session_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        try:
            cursor = self.conn.cursor()
            created_date = self._get_current_date()
            session_file = f"session_{uid}.json"
            cursor.execute(insert_sql, (
                uid, password, token, cookie, category, 'Unknown', None, 0, 0, created_date, session_file
            ))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # UID already exists
            return False
        except sqlite3.Error as e:
            print(f"Error adding account {uid}: {e}")
            return False

    def get_all_accounts(self) -> List[Dict]:
        """Retrieve all accounts from the database."""
        select_sql = "SELECT * FROM accounts;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error fetching all accounts: {e}")
            return []
    
    def get_accounts_count_by_status(self, category_filter: str = None) -> Dict[str, int]:
        """Get count of accounts by status for better performance."""
        if category_filter and category_filter != "All Categories":
            select_sql = "SELECT status, COUNT(*) as count FROM accounts WHERE category = ? GROUP BY status;"
            params = (category_filter,)
        else:
            select_sql = "SELECT status, COUNT(*) as count FROM accounts GROUP BY status;"
            params = ()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql, params)
            rows = cursor.fetchall()
            counts = {row['status']: row['count'] for row in rows}
            return counts
        except sqlite3.Error as e:
            print(f"Error fetching account counts: {e}")
            return {}
    
    def get_total_accounts_count(self, category_filter: str = None) -> int:
        """Get total count of accounts for better performance."""
        if category_filter and category_filter != "All Categories":
            select_sql = "SELECT COUNT(*) as count FROM accounts WHERE category = ?;"
            params = (category_filter,)
        else:
            select_sql = "SELECT COUNT(*) as count FROM accounts;"
            params = ()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql, params)
            row = cursor.fetchone()
            return row['count'] if row else 0
        except sqlite3.Error as e:
            print(f"Error fetching total account count: {e}")
            return 0
    
    def get_avg_login_count(self, category_filter: str = None) -> float:
        """Get average login count for better performance."""
        if category_filter and category_filter != "All Categories":
            select_sql = "SELECT AVG(login_count) as avg_login FROM accounts WHERE category = ?;"
            params = (category_filter,)
        else:
            select_sql = "SELECT AVG(login_count) as avg_login FROM accounts;"
            params = ()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql, params)
            row = cursor.fetchone()
            return float(row['avg_login']) if row and row['avg_login'] is not None else 0.0
        except sqlite3.Error as e:
            print(f"Error fetching average login count: {e}")
            return 0.0
    
    def get_accounts_added_today(self, category_filter: str = None) -> int:
        """Get count of accounts added today."""
        today = self._get_current_date()
        if category_filter and category_filter != "All Categories":
            select_sql = "SELECT COUNT(*) as count FROM accounts WHERE category = ? AND created_date = ?;"
            params = (category_filter, today)
        else:
            select_sql = "SELECT COUNT(*) as count FROM accounts WHERE created_date = ?;"
            params = (today,)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql, params)
            row = cursor.fetchone()
            return row['count'] if row else 0
        except sqlite3.Error as e:
            print(f"Error fetching accounts added today: {e}")
            return 0
    
    def get_most_used_category(self) -> str:
        """Get the most used category."""
        select_sql = "SELECT category, COUNT(*) as count FROM accounts GROUP BY category ORDER BY count DESC LIMIT 1;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql)
            row = cursor.fetchone()
            return row['category'] if row else "Default"
        except sqlite3.Error as e:
            print(f"Error fetching most used category: {e}")
            return "Default"
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories from the database efficiently."""
        select_sql = "SELECT DISTINCT category FROM accounts ORDER BY category;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            return [row['category'] for row in rows]
        except sqlite3.Error as e:
            print(f"Error fetching categories: {e}")
            return ["Default"]
    
    def get_accounts_by_category(self, category_filter: str = None) -> List[Dict]:
        """Get accounts filtered by category efficiently."""
        if category_filter and category_filter != "All Categories":
            select_sql = "SELECT * FROM accounts WHERE category = ?;"
            params = (category_filter,)
        else:
            select_sql = "SELECT * FROM accounts;"
            params = ()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error fetching accounts by category: {e}")
            return []
    
    def get_accounts_count_by_category_and_status(self, category: str) -> Dict[str, int]:
        """Get count of accounts by status for a specific category efficiently."""
        select_sql = "SELECT status, COUNT(*) as count FROM accounts WHERE category = ? GROUP BY status;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql, (category,))
            rows = cursor.fetchall()
            counts = {row['status']: row['count'] for row in rows}
            return counts
        except sqlite3.Error as e:
            print(f"Error fetching account counts by category: {e}")
            return {}

    def get_account_by_uid(self, uid: str) -> Optional[Dict]:
        """Retrieve a single account by its UID."""
        select_sql = "SELECT * FROM accounts WHERE uid = ?;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(select_sql, (uid,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error fetching account {uid}: {e}")
            return None

    def update_account_status(self, uid: str, status: str, increment_login_count: bool = False, increment_task_count: bool = False) -> bool:
        """
        Update the status of an account.
        Optionally increment the login_count or task_count.
        """
        update_fields = ["status = ?", "last_login = ?"]
        params = [status, self._get_current_date()]

        if increment_login_count:
            update_fields.append("login_count = login_count + 1")
        if increment_task_count:
            update_fields.append("task_count = task_count + 1")

        update_sql = f"UPDATE accounts SET {', '.join(update_fields)} WHERE uid = ?;"
        params.append(uid)

        try:
            cursor = self.conn.cursor()
            cursor.execute(update_sql, params)
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating status for account {uid}: {e}")
            return False

    def update_account_category(self, uid: str, new_category: str) -> bool:
        """Update the category of an account."""
        update_sql = "UPDATE accounts SET category = ? WHERE uid = ?;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(update_sql, (new_category, uid))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating category for account {uid}: {e}")
            return False

    def delete_account(self, uid: str) -> bool:
        """Delete an account from the database."""
        delete_sql = "DELETE FROM accounts WHERE uid = ?;"
        try:
            cursor = self.conn.cursor()
            cursor.execute(delete_sql, (uid,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting account {uid}: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def _get_current_date(self) -> str:
        """Helper method to get the current date in YYYY-MM-DD format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    def __del__(self):
        """Destructor to ensure the database connection is closed."""
        self.close()