import imaplib
import ssl
from pathlib import Path
import email
import re
from email.header import decode_header
from email.utils import parsedate_to_datetime
import datetime
import os


class Fetcher:
    def __init__(self, server, port, use_tls=True):
        self.server = server
        self.port = port
        self.use_tls = use_tls
        self.connection = None

    def connect(self):
        """Connects to the IMAP server."""
        try:
            if self.use_tls:
                context = ssl.create_default_context()
                self.connection = imaplib.IMAP4_SSL(
                    self.server, self.port, ssl_context=context)
            else:
                self.connection = imaplib.IMAP4(self.server, self.port)
            print(f"Successfully connected to {self.server}")
        except Exception as e:
            print(f"Error connecting to {self.server}: {e}")
            raise

    def login(self, username, password):
        """Logs in a user."""
        if not self.connection:
            self.connect()
        try:
            self.connection.login(username, password)
            print(f"Successfully logged in as {username}")
        except Exception as e:
            print(f"Error logging in as {username}: {e}")
            raise

    def _decode_header(self, header_value):
        """Decodes email headers to a readable string."""
        if not header_value:
            return ""
        decoded_parts = decode_header(header_value)
        header_str = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                header_str.append(part.decode(
                    encoding or 'utf-8', errors='replace'))
            else:
                header_str.append(part)
        return "".join(header_str)

    def _sanitize_filename(self, text):
        """Sanitizes a string to be a valid filename."""
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        # Remove characters that are not alphanumeric, underscore, or hyphen
        text = re.sub(r'[^\w-]', '', text)
        # Ensure it's not empty
        if not text:
            return "no_subject"
        return text[:200]  # Limit length

    def list_mailboxes(self):
        """Lists all mailboxes for the logged-in user."""
        if not self.connection:
            raise ConnectionError("Not connected to the server.")

        status, mailboxes = self.connection.list()
        if status == 'OK':
            parsed_mailboxes = []
            for mailbox_bytes in mailboxes:
                mailbox_str = mailbox_bytes.decode()
                # The mailbox name is the last part of the string, after the separator.
                # The separator can be ' / ' or ' . '.
                parts = re.split(r'"\."', mailbox_str)
                if len(parts) > 1:
                    # The mailbox name might be quoted
                    mailbox = parts[-1].strip(' "')
                    parsed_mailboxes.append(mailbox)
            return parsed_mailboxes
        else:
            print("Failed to list mailboxes.")
            return []

    def fetch_emails(self, username, storage_dir, mailbox='INBOX', criteria='ALL'):
        """Fetches emails from a specific mailbox based on criteria."""
        if not self.connection:
            raise ConnectionError("Not connected to the server.")

        user_dir = Path(storage_dir) / username
        mailbox_dir = user_dir / mailbox
        mailbox_dir.mkdir(parents=True, exist_ok=True)

        status, _ = self.connection.select(mailbox, readonly=True)
        if status != 'OK':
            print(f"Failed to select mailbox {mailbox}")
            return

        # The IMAP search command requires the criteria to be passed as separate arguments
        status, data = self.connection.search(None, *criteria.split())
        if status != 'OK':
            print(f"No messages found in {mailbox} for criteria {criteria}")
            return

        email_ids = data[0].split()
        print(f"Found {len(email_ids)} emails in {mailbox}.")

        for email_id in email_ids:
            status, msg_data = self.connection.fetch(email_id, '(RFC822)')
            if status == 'OK':
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg_bytes = response_part[1]
                        msg = email.message_from_bytes(msg_bytes)

                        subject = self._decode_header(msg["Subject"])
                        date_str = msg.get("Date")
                        if date_str:
                            dt = parsedate_to_datetime(date_str)
                            date_prefix = dt.strftime('%Y-%m-%d_%H-%M-%S')
                            creation_date = dt.timestamp()
                        else:
                            date_prefix = "no_date"
                            creation_date = None

                        if not subject:
                            sanitized_subject = f"email_{email_id.decode()}"
                        else:
                            sanitized_subject = self._sanitize_filename(
                                subject)

                        filename_base = f"{date_prefix}_{sanitized_subject}"
                        filename = f"{filename_base}.eml"
                        filepath = mailbox_dir / filename

                        counter = 1
                        while filepath.exists():
                            filename = f"{filename_base}_{counter}.eml"
                            filepath = mailbox_dir / filename
                            counter += 1

                        with open(filepath, 'wb') as f:
                            f.write(msg_bytes)
                            if creation_date:
                                os.utime(
                                    filepath, (creation_date, creation_date))
                        print(f"Saved email {email_id.decode()} to {filepath}")

    def close(self):
        """Closes the connection."""
        if self.connection:
            self.connection.logout()
            print("Logged out and connection closed.")
