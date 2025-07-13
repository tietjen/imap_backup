
import sqlite3
from pathlib import Path

class Indexer:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """Creates the email index table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                subject TEXT,
                from_sender TEXT,
                to_recipient TEXT,
                body TEXT,
                attachments TEXT
            )
        ''')
        self.connection.commit()

    def index_email(self, email_data):
        """Indexes a single email."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO emails (path, subject, from_sender, to_recipient, body, attachments)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                email_data['path'],
                email_data['subject'],
                email_data['from'],
                email_data['to'],
                email_data['body'],
                ",".join(email_data['attachments'])
            ))
            self.connection.commit()
            print(f"Indexed email: {email_data['path']}")
        except sqlite3.Error as e:
            print(f"Error indexing email {email_data['path']}: {e}")

    def search(self, subject=None, from_sender=None, to_recipient=None, content=None, attachment=None):
        """Searches the index for emails matching the criteria."""
        query = "SELECT path, subject, from_sender, to_recipient FROM emails WHERE 1=1"
        params = []

        if subject:
            query += " AND subject LIKE ?"
            params.append(f"%{subject}%")
        if from_sender:
            query += " AND from_sender LIKE ?"
            params.append(f"%{from_sender}%")
        if to_recipient:
            query += " AND to_recipient LIKE ?"
            params.append(f"%{to_recipient}%")
        if content:
            query += " AND body LIKE ?"
            params.append(f"%{content}%")
        if attachment:
            query += " AND attachments LIKE ?"
            params.append(f"%{attachment}%")

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
