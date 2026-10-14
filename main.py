"""Start Lil Buddy:  python main.py"""

import sys
import tkinter as tk
from tkinter import messagebox

from lil_buddy.assistant import Assistant
from lil_buddy.config import Settings
from lil_buddy.email_client import EmailClient
from lil_buddy.ui import App


def main():
    settings = Settings()
    root = tk.Tk()

    missing = settings.missing()
    if missing:
        root.withdraw()
        messagebox.showerror(
            "Lil Buddy setup",
            "Please fill in these settings in your .env file:\n\n" + "\n".join(missing),
        )
        sys.exit(1)

    email_client = EmailClient(
        settings.email_address,
        settings.email_password,
        settings.smtp_host,
        settings.smtp_port,
        settings.imap_host,
        settings.imap_port,
    )

    def make_assistant(on_event, approve):
        return Assistant(settings, email_client, on_event, approve)

    App(root, make_assistant)
    root.mainloop()


if __name__ == "__main__":
    main()
