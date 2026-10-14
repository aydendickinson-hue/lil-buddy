"""A deliberately plain Tkinter window. Change anything here freely:
the assistant only needs on_event() and approve() (see assistant.py).
"""

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

# ---- Look and feel: tweak these ---------------------------------------------
TITLE = "Lil Buddy"
FONT = ("Helvetica", 12)
WINDOW_SIZE = "700x550"
COLORS = {"you": "#1a5fb4", "assistant": "#000000", "tool": "#777777", "error": "#c01c28"}
LABELS = {"you": "You", "assistant": "Buddy", "tool": "  •", "error": "Error"}


class App:
    def __init__(self, root, make_assistant):
        self.root = root
        self.events = queue.Queue()  # worker thread -> UI thread
        self.busy = False

        root.title(TITLE)
        root.geometry(WINDOW_SIZE)

        # Conversation log
        self.log = scrolledtext.ScrolledText(root, wrap="word", font=FONT, state="disabled")
        self.log.pack(fill="both", expand=True, padx=8, pady=8)
        for kind, color in COLORS.items():
            self.log.tag_config(kind, foreground=color)

        # Task entry + buttons
        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=8, pady=(0, 8))
        self.entry = tk.Text(bottom, height=3, font=FONT, wrap="word")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self._on_enter)
        buttons = tk.Frame(bottom)
        buttons.pack(side="left", padx=(8, 0))
        self.send_button = tk.Button(buttons, text="Send", width=8, command=self.submit)
        self.send_button.pack()
        tk.Button(buttons, text="New chat", width=8, command=self.new_chat).pack(pady=(4, 0))

        self.status = tk.Label(root, text="Ready", anchor="w")
        self.status.pack(fill="x", padx=8, pady=(0, 4))

        self.assistant = make_assistant(on_event=self._post_event, approve=self._request_approval)
        self.write("assistant", "Hi! Give me a task, e.g. \"Email jane@example.com and ask "
                                "if Thursday at 2pm works for a call.\"")
        self.entry.focus_set()
        root.after(100, self._drain_events)

    # ---- user actions ----------------------------------------------------

    def _on_enter(self, event):
        if event.state & 0x1:  # Shift+Enter inserts a newline
            return None
        self.submit()
        return "break"

    def submit(self):
        task = self.entry.get("1.0", "end").strip()
        if not task or self.busy:
            return
        self.entry.delete("1.0", "end")
        self.write("you", task)
        self._set_busy(True)
        threading.Thread(target=self._work, args=(task,), daemon=True).start()

    def new_chat(self):
        if self.busy:
            return
        self.assistant.reset()
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.write("assistant", "Started a new chat.")

    # ---- background work -------------------------------------------------

    def _work(self, task):
        try:
            self.assistant.run(task)
        except Exception as exc:
            self._post_event("error", str(exc))
        finally:
            self.events.put(("done", None))

    def _post_event(self, kind, text):
        """Called from the worker thread; the UI thread picks it up in _drain_events."""
        self.events.put((kind, text))

    def _request_approval(self, draft):
        """Called from the worker thread. Blocks until you approve or reject in the UI."""
        answer = {}
        finished = threading.Event()
        self.events.put(("approve", (draft, answer, finished)))
        finished.wait()
        return answer.get("draft")

    def _drain_events(self):
        while not self.events.empty():
            kind, payload = self.events.get()
            if kind == "done":
                self._set_busy(False)
            elif kind == "approve":
                ApprovalDialog(self.root, *payload)
            else:
                self.write(kind, payload)
        self.root.after(100, self._drain_events)

    # ---- display helpers -------------------------------------------------

    def write(self, kind, text):
        self.log.configure(state="normal")
        self.log.insert("end", f"{LABELS.get(kind, kind)}: {text}\n\n", kind)
        self.log.configure(state="disabled")
        self.log.see("end")

    def _set_busy(self, busy):
        self.busy = busy
        self.send_button.configure(state="disabled" if busy else "normal")
        self.status.configure(text="Working..." if busy else "Ready")


class ApprovalDialog:
    """Shows a drafted email. You can edit it, then Send or Reject."""

    def __init__(self, root, draft, answer, finished):
        self.draft, self.answer, self.finished = draft, answer, finished
        self.win = tk.Toplevel(root)
        self.win.title("Approve email?")
        self.win.geometry("600x450")
        self.win.protocol("WM_DELETE_WINDOW", self.reject)

        self.fields = {}
        for name in ("to", "cc", "subject"):
            row = tk.Frame(self.win)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=name.capitalize() + ":", width=8, anchor="w").pack(side="left")
            entry = tk.Entry(row, font=FONT)
            entry.insert(0, draft.get(name, ""))
            entry.pack(side="left", fill="x", expand=True)
            self.fields[name] = entry

        self.body = scrolledtext.ScrolledText(self.win, wrap="word", font=FONT)
        self.body.insert("1.0", draft.get("body", ""))
        self.body.pack(fill="both", expand=True, padx=8, pady=4)

        buttons = tk.Frame(self.win)
        buttons.pack(pady=8)
        tk.Button(buttons, text="Send", width=10, command=self.approve).pack(side="left", padx=4)
        tk.Button(buttons, text="Reject", width=10, command=self.reject).pack(side="left", padx=4)

    def approve(self):
        self.answer["draft"] = {
            **self.draft,
            **{name: entry.get().strip() for name, entry in self.fields.items()},
            "body": self.body.get("1.0", "end").rstrip(),
        }
        self._close()

    def reject(self):
        self.answer["draft"] = None
        self._close()

    def _close(self):
        self.win.destroy()
        self.finished.set()
