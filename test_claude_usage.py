#!/usr/bin/env python3
"""
Test: Claude /usage via pexpect + pyte
════════════════════════════════════════
pyte emuliert das Terminal richtig → sauberer Text ohne TUI-Artefakte.

Ausführen:
    python3 test_claude_usage.py
"""

import os
import re
import sys
import time
import subprocess

# pexpect + pyte installieren falls nötig
for pkg in ("pexpect", "pyte"):
    try:
        __import__(pkg)
    except ImportError:
        print(f"[*] Installiere {pkg} …")
        subprocess.run([sys.executable, "-m", "pip", "install", pkg, "--quiet"], check=True)

import pexpect
import pyte

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def render_screen(raw_bytes: bytes, width: int = 220, height: int = 50) -> str:
    """
    Verarbeitet rohe Terminal-Bytes durch pyte (VT100-Emulator).
    Gibt den gerenderten Bildschirm als plain-text zurück.
    """
    screen = pyte.Screen(width, height)
    stream = pyte.ByteStream(screen)
    stream.feed(raw_bytes)
    lines = [line.rstrip() for line in screen.display]
    # Leere Zeilen am Ende entfernen
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def read_bytes_for(child, seconds: float) -> bytes:
    """Liest rohe Bytes aus dem PTY."""
    buf = b""
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            chunk = child.read_nonblocking(size=8192, timeout=0.3)
            # pexpect gibt bytes zurück wenn encoding=None
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8", errors="replace")
            buf += chunk
        except (pexpect.TIMEOUT, pexpect.EOF):
            break
    return buf


def get_usage() -> str | None:
    HOME = os.path.expanduser("~")
    print(f"[*] Starte claude in {HOME} …")

    child = pexpect.spawn(
        "claude",
        cwd=HOME,
        timeout=5,
        encoding=None,         # ← Bytes-Modus für pyte
        codec_errors="replace",
    )

    # ── 1. Trust-Dialog ────────────────────────────────────────────────────────
    print("[*] Warte auf Trust-Dialog …")
    raw1 = read_bytes_for(child, seconds=12)
    text1 = raw1.decode("utf-8", errors="replace")
    clean1 = ANSI_ESCAPE.sub("", text1)

    if "trust" in clean1.lower() or "confirm" in clean1.lower():
        print("[*] Trust-Dialog erkannt → bestätige mit \\r …")
        child.send(b"\r")
        time.sleep(1)
        child.send(b"\r")
    else:
        print(f"[!] Trust-Dialog nicht erkannt:\n{clean1[-200:]}")

    # ── 2. Warten bis claude bereit ────────────────────────────────────────────
    print("[*] Warte auf claude-Prompt …")
    raw2 = read_bytes_for(child, seconds=15)

    # ── 3. /usage senden ───────────────────────────────────────────────────────
    print("[*] Sende /usage …")
    child.send(b"/usage\r")
    time.sleep(8)
    raw3 = read_bytes_for(child, seconds=6)

    # ── 4. Bildschirm rendern ──────────────────────────────────────────────────
    all_bytes = raw1 + raw2 + raw3
    rendered = render_screen(all_bytes)

    print("\n── Gerenderter Bildschirm ─────────────────────────────────")
    print(rendered)
    print("──────────────────────────────────────────────────────────")

    # ── 5. Aufräumen ───────────────────────────────────────────────────────────
    child.send(b"/exit\r")
    child.close()

    return rendered


def parse_usage(text: str) -> dict | None:
    """Extrahiert Session- und Wochen-Nutzung aus dem gerenderten Screen."""
    lines = text.splitlines()

    pcts   = re.findall(r"(\d+)%\s*used", text)
    resets = re.findall(r"Resets\s+(.+?)(?:\s{2,}|$)", text)

    # Fallback: Zeitstempel-Muster direkt suchen (falls "Resets " fehlt)
    if len(resets) < 2:
        times = re.findall(
            r"(\d{1,2}(?::\d{2})?(?:am|pm)\s*\([^)]+\)"
            r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+\s+at\s+\d+(?::\d+)?(?:am|pm)\s*\([^)]+\))",
            text, re.IGNORECASE
        )
        resets = times

    print(f"\n── Parsing ────────────────────────────────────────────────")
    print(f"  %-Werte : {pcts}")
    print(f"  Resets  : {resets}")

    if len(pcts) >= 2 and len(resets) >= 2:
        return {
            "session_pct":   int(pcts[0]),
            "session_reset": resets[0].strip(),
            "week_pct":      int(pcts[1]),
            "week_reset":    resets[1].strip(),
        }
    if len(pcts) >= 2 and len(resets) == 1:
        return {
            "session_pct":   int(pcts[0]),
            "session_reset": resets[0].strip(),
            "week_pct":      int(pcts[1]),
            "week_reset":    "?",
        }
    return None


if __name__ == "__main__":
    print("\n=== Claude /usage Test (pyte) ===\n")
    rendered = get_usage()
    data = parse_usage(rendered or "")
    if data:
        print(f"\n[✓] Erfolgreich!\n")
        print(f"  Session : {data['session_pct']}%  → Resets {data['session_reset']}")
        print(f"  Woche   : {data['week_pct']}%  → Resets {data['week_reset']}")
    else:
        print("\n[✗] Parsing fehlgeschlagen.")
    print("\n=== Fertig ===\n")
