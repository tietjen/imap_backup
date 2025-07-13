
import email
from email.header import decode_header
from pathlib import Path

class EmailParser:
    def __init__(self, eml_path):
        self.eml_path = Path(eml_path)
        if not self.eml_path.exists():
            raise FileNotFoundError(f"Email file not found: {self.eml_path}")
        with open(self.eml_path, 'rb') as f:
            self.msg = email.message_from_bytes(f.read())

    def _decode_header(self, header_value):
        """Decodes email headers to a readable string."""
        if not header_value:
            return ""
        decoded_parts = decode_header(header_value)
        header_str = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                header_str.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                header_str.append(part)
        return "".join(header_str)

    def get_subject(self):
        """Returns the subject of the email."""
        return self._decode_header(self.msg["Subject"])

    def get_sender(self):
        """Returns the sender of the email."""
        return self._decode_header(self.msg["From"])

    def get_recipient(self):
        """Returns the recipient(s) of the email."""
        return self._decode_header(self.msg["To"])

    def get_body(self):
        """Extracts the plain text body from the email."""
        if self.msg.is_multipart():
            for part in self.msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == 'text/plain' and "attachment" not in content_disposition:
                    try:
                        return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                    except Exception:
                        continue # Ignore decoding errors
        else:
            # Not a multipart message, just get the payload
            try:
                return self.msg.get_payload(decode=True).decode(self.msg.get_content_charset() or 'utf-8', errors='replace')
            except Exception:
                return "" # Ignore decoding errors
        return "" # Return empty string if no plain text body is found

    def get_attachments(self):
        """Returns a list of attachment filenames."""
        attachments = []
        for part in self.msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if filename:
                attachments.append(self._decode_header(filename))
        return attachments

    def get_all_parts(self):
        """Returns a dictionary with all parsed email parts."""
        return {
            "path": str(self.eml_path),
            "subject": self.get_subject(),
            "from": self.get_sender(),
            "to": self.get_recipient(),
            "body": self.get_body(),
            "attachments": self.get_attachments()
        }
