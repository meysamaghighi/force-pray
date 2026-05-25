"""Fullscreen 'go pray' blocker. Hard to dismiss, but not impossible.

Dismiss options:
  1. Wait out the countdown (default 7 minutes).
  2. Press-and-HOLD the green button for 10 seconds.
  3. Type the emergency phrase exactly: 'ya allah forgive me i need to work'
     (intentionally long so accidental dismissal is hard).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta

EMERGENCY_PHRASE = "ya allah forgive me i need to work"
DEFAULT_COUNTDOWN_SEC = 7 * 60
HOLD_SECONDS = 10

ARABIC_HEADING = "حَيَّ عَلَى الصَّلَاة"  # 'Hayya 'alas-salah' — come to prayer
SWEDISH_SUB = "Skynda till bön"


def speak(text: str) -> None:
    """Use macOS 'say' so the call is also audible. Non-blocking."""
    try:
        subprocess.Popen(["/usr/bin/say", "-v", "Samantha", text])
    except Exception:
        pass


def play_sound() -> None:
    try:
        subprocess.Popen(["/usr/bin/afplay", "/System/Library/Sounds/Glass.aiff"])
    except Exception:
        pass


class Blocker:
    def __init__(self, prayer: str, countdown_sec: int = DEFAULT_COUNTDOWN_SEC):
        self.prayer = prayer
        self.remaining = countdown_sec
        self.end_at = datetime.now() + timedelta(seconds=countdown_sec)
        self.hold_progress = 0.0  # seconds held
        self.hold_active = False
        self.typed_buffer = ""
        self.dismissed = False

        root = tk.Tk()
        self.root = root
        root.title("force-pray")
        root.configure(bg="#0a0a0a")
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        # On macOS this raises the window above all spaces / fullscreen apps:
        try:
            root.call("::tk::unsupported::MacWindowStyle", "style", root._w, "plain", "none")
        except tk.TclError:
            pass
        root.focus_force()
        root.bind("<Escape>", lambda _e: None)  # eat escape
        root.bind("<Key>", self._on_key)
        root.protocol("WM_DELETE_WINDOW", lambda: None)  # ignore window close

        # Layout
        big = tkfont.Font(family="Helvetica Neue", size=84, weight="bold")
        med = tkfont.Font(family="Helvetica Neue", size=48, weight="bold")
        sml = tkfont.Font(family="Helvetica Neue", size=22)
        tiny = tkfont.Font(family="Menlo", size=14)

        wrap = tk.Frame(root, bg="#0a0a0a")
        wrap.pack(expand=True)

        tk.Label(wrap, text=ARABIC_HEADING, font=big, fg="#e8c87a", bg="#0a0a0a").pack(pady=(20, 6))
        tk.Label(wrap, text=SWEDISH_SUB, font=sml, fg="#9aa1a8", bg="#0a0a0a").pack()
        tk.Label(wrap, text=f"It's time for {prayer}.", font=med, fg="#ffffff", bg="#0a0a0a").pack(pady=(40, 8))
        tk.Label(
            wrap,
            text="Step away from the keyboard. The work can wait.",
            font=sml,
            fg="#9aa1a8",
            bg="#0a0a0a",
        ).pack()

        self.timer_label = tk.Label(wrap, text="", font=med, fg="#7dd3fc", bg="#0a0a0a")
        self.timer_label.pack(pady=(60, 10))

        self.hold_button = tk.Label(
            wrap,
            text="◉  Hold to dismiss (10s)",
            font=sml,
            fg="#0a0a0a",
            bg="#2f6a3a",
            padx=24,
            pady=14,
        )
        self.hold_button.pack(pady=20)
        self.hold_button.bind("<ButtonPress-1>", self._hold_start)
        self.hold_button.bind("<ButtonRelease-1>", self._hold_stop)

        self.hold_bar = tk.Frame(wrap, bg="#1f1f1f", width=420, height=10)
        self.hold_bar.pack()
        self.hold_bar_fill = tk.Frame(self.hold_bar, bg="#3ec46d", width=0, height=10)
        self.hold_bar_fill.place(x=0, y=0)

        tk.Label(
            wrap,
            text="…or type the emergency phrase if you truly cannot stop.",
            font=tiny,
            fg="#6b7280",
            bg="#0a0a0a",
        ).pack(pady=(40, 4))
        self.typed_label = tk.Label(wrap, text="", font=tiny, fg="#9aa1a8", bg="#0a0a0a")
        self.typed_label.pack()

        play_sound()
        speak(f"It's time for {prayer}. Go pray.")
        self._tick()

    def _on_key(self, event: tk.Event) -> None:
        ch = event.char
        if not ch:
            return
        ch = ch.lower()
        expected = EMERGENCY_PHRASE[len(self.typed_buffer):len(self.typed_buffer)+1]
        if ch == expected:
            self.typed_buffer += ch
        else:
            self.typed_buffer = ""
            if ch == EMERGENCY_PHRASE[0]:
                self.typed_buffer = ch
        # show masked progress
        shown = "·" * len(self.typed_buffer)
        self.typed_label.configure(text=f"{shown}  ({len(self.typed_buffer)}/{len(EMERGENCY_PHRASE)})")
        if self.typed_buffer == EMERGENCY_PHRASE:
            self._dismiss(reason="emergency phrase")

    def _hold_start(self, _e: tk.Event) -> None:
        self.hold_active = True
        self.hold_button.configure(bg="#4ea35e")

    def _hold_stop(self, _e: tk.Event) -> None:
        self.hold_active = False
        self.hold_progress = 0
        self.hold_bar_fill.configure(width=0)
        self.hold_button.configure(bg="#2f6a3a")

    def _tick(self) -> None:
        if self.dismissed:
            return
        remaining = (self.end_at - datetime.now()).total_seconds()
        if remaining <= 0:
            self._dismiss(reason="countdown")
            return
        mm, ss = divmod(int(remaining), 60)
        self.timer_label.configure(text=f"Window closes automatically in {mm:02d}:{ss:02d}")

        if self.hold_active:
            self.hold_progress += 0.1
            ratio = min(1.0, self.hold_progress / HOLD_SECONDS)
            self.hold_bar_fill.configure(width=int(420 * ratio))
            if self.hold_progress >= HOLD_SECONDS:
                self._dismiss(reason="held")
                return
        self.root.after(100, self._tick)

    def _dismiss(self, reason: str) -> None:
        self.dismissed = True
        print(f"[blocker] dismissed: {reason}", flush=True)
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self) -> None:
        self.root.mainloop()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--prayer", default="Prayer")
    p.add_argument("--seconds", type=int, default=DEFAULT_COUNTDOWN_SEC)
    args = p.parse_args(argv)
    Blocker(prayer=args.prayer, countdown_sec=args.seconds).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
