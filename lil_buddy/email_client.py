"""Send and read email over SMTP/IMAP (works with Gmail app passwords)."""

import email
import imaplib
import smtplib
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr


class EmailClient:
    def __init__(self, address, password, smtp_host, smtp_port, imap_host, imap_port):
        self.address = address
        self.password = password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.imap_host = imap_host
        self.imap_port = imap_port

    # ---- sending -------------------------------------------------------

    def send(self, to, subject, body, cc=None, in_reply_to=None):
        msg = EmailMessage()
        msg["From"] = self.address
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        msg["Subject"] = subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to
        msg.set_content(body)

        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as smtp:
            smtp.login(self.address, self.password)
            smtp.send_message(msg)

    # ---- reading -------------------------------------------------------

    def _connect(self):
        imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        imap.login(self.address, self.password)
        return imap

    def _search_criteria(self, query, unread_only):
        if query and "gmail" in self.imap_host:
            # Gmail supports its normal search syntax, e.g. "from:bob subject:invoice".
            criteria = ["X-GM-RAW", '"' + query.replace('"', "") + '"']
        elif query:
            criteria = ["TEXT", '"' + query.replace('"', "") + '"']
        else:
            criteria = ["ALL"]
        if unread_only:
            criteria.append("UNSEEN")
        return criteria

    def list_emails(self, query="", unread_only=False, limit=10, folder="INBOX"):
        """Return summaries of the most recent matching emails, newest first."""
        imap = self._connect()
        try:
            imap.select(folder, readonly=True)
            _, data = imap.uid("search", None, *self._search_criteria(query, unread_only))
            uids = data[0].split()[-limit:][::-1]
            results = []
            for uid in uids:
                _, msg_data = imap.uid(
                    "fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])"
                )
                headers = email.message_from_bytes(msg_data[0][1])
                results.append({
                    "id": uid.decode(),
                    "from": _decode(headers.get("From")),
                    "subject": _decode(headers.get("Subject")),
                    "date": headers.get("Date", ""),
                })
            return results
        finally:
            imap.logout()

    def read_email(self, email_id, folder="INBOX"):
        """Return the full contents of one email. Does not mark it as read."""
        imap = self._connect()
        try:
            imap.select(folder, readonly=True)
            _, msg_data = imap.uid("fetch", email_id.encode(), "(BODY.PEEK[])")
            if not msg_data or msg_data[0] is None:
                raise ValueError(f"No email with id {email_id}")
            msg = email.message_from_bytes(msg_data[0][1])
            return {
                "id": email_id,
                "from": _decode(msg.get("From")),
                "reply_to_address": parseaddr(msg.get("Reply-To") or msg.get("From", ""))[1],
                "to": _decode(msg.get("To")),
                "cc": _decode(msg.get("Cc")),
                "subject": _decode(msg.get("Subject")),
                "date": msg.get("Date", ""),
                "message_id": msg.get("Message-ID", ""),
                "body": _plain_text_body(msg),
            }
        finally:
            imap.logout()


def _decode(value):
    if not value:
        return ""
    return str(make_header(decode_header(value)))


def _plain_text_body(msg, max_chars=20000):
    """Pull the readable text out of an email (prefers text/plain)."""
    parts = msg.walk() if msg.is_multipart() else [msg]
    html = None
    for part in parts:
        if part.get_content_disposition() == "attachment":
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True) or b""
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ctype == "text/plain":
            return text[:max_chars]
        html = html or text
    return (html or "")[:max_chars]
