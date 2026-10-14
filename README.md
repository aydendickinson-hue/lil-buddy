# Lil Buddy

A small desktop assistant. Type a task, and it handles it, including reading your inbox and emailing other people for you. **Every email is shown to you first**, so you can edit it, send it, or reject it.

Example tasks:

- "Email jane@example.com and ask if Thursday at 2pm works for a call."
- "Check my unread email and summarize anything important."
- "Find the latest email from my landlord and reply saying I'll pay rent on Friday."

## Setup

1. Install Python 3.10 or newer. On Linux you may also need Tkinter: `sudo apt install python3-tk`.
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill it in:
   - `ANTHROPIC_API_KEY`: from https://console.anthropic.com
   - `EMAIL_ADDRESS`: your Gmail address
   - `EMAIL_APP_PASSWORD`: a Gmail **app password**, created at https://myaccount.google.com/apppasswords (this requires 2-Step Verification). Do not use your normal password.
   - `YOUR_NAME`: used to sign emails
4. Run it:
   ```
   python main.py
   ```

Press Enter to send a task, or Shift+Enter for a new line. **New chat** clears the conversation.

## How the code is laid out

| File | What it does |
|---|---|
| `main.py` | Starts the app and wires the pieces together. |
| `lil_buddy/ui.py` | The window. **Edit this file to change the UI.** Colors, font and size are at the top. |
| `lil_buddy/assistant.py` | Talks to Claude, defines the tools (send/list/read email), and holds the system prompt. |
| `lil_buddy/email_client.py` | Sends email (SMTP) and reads it (IMAP). |
| `lil_buddy/config.py` | Reads settings from `.env`. |

The UI and the assistant are kept separate. The assistant only needs two functions from the UI:

- `on_event(kind, text)` shows progress messages.
- `approve(draft)` returns the email to send (possibly edited), or `None` to cancel.

That means you can replace `ui.py` with a web page, a terminal, or anything else without touching the assistant.

### Adding a new ability

1. Add a tool definition to `TOOLS` in `assistant.py`.
2. Handle it in `Assistant._dispatch`.

## Notes

- Reading email never marks messages as read.
- Emails the assistant reads are treated as information, not instructions, and nothing is sent without your approval. That protects you from a malicious email trying to make the assistant do something.
- If Claude's safety checks decline a request, the app automatically retries it on a fallback model (the `fallbacks: "default"` API option in `assistant.py`).
- The conversation only lasts until you close the window.
