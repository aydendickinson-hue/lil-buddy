"""Settings, read from environment variables or a .env file in the project folder."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Settings:
    email_address: str = os.getenv("EMAIL_ADDRESS", "")
    email_password: str = os.getenv("EMAIL_APP_PASSWORD", "")
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "465"))
    imap_host: str = os.getenv("IMAP_HOST", "imap.gmail.com")
    imap_port: int = int(os.getenv("IMAP_PORT", "993"))
    your_name: str = os.getenv("YOUR_NAME", "")
    model: str = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
    effort: str = os.getenv("CLAUDE_EFFORT", "medium")

    def missing(self):
        """Names of required settings that are not filled in."""
        needed = {"EMAIL_ADDRESS": self.email_address, "EMAIL_APP_PASSWORD": self.email_password}
        return [name for name, value in needed.items() if not value]
