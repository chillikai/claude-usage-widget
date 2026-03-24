#!/usr/bin/env python3
"""
Claude Usage Widget — macOS Menubar
════════════════════════════════════
Zeigt Session- und Wochen-Nutzung identisch zu Claude Code's /usage.

Datenquelle : claude CLI  (/usage-Befehl im interaktiven Modus)
Auth        : keine — claude handhabt alles selbst, kein Keychain-Zugriff
Abhängigkeiten: rumps  pexpect  pyte

Installation:
    pip3 install rumps pexpect pyte

Start:
    python3 claude_widget.py
"""

import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import rumps

# ── Konfiguration ─────────────────────────────────────────────────────────────

REFRESH_SEC  = 120          # Alle 2 Minuten neu laden
USAGE_CACHE  = Path.home() / ".cache" / "claude_widget_usage.json"
TZ           = "Europe/Berlin"

# ── pexpect / pyte Installation ───────────────────────────────────────────────

for _pkg in ("pexpect", "pyte"):
    try:
        __import__(_pkg)
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", _pkg, "--quiet"],
                       check=True)

import pexpect
import pyte


# ── Claude CLI → /usage ───────────────────────────────────────────────────────

def _render_screen(raw_bytes: bytes, width: int = 220, height: int = 50) -> str:
    """Rendert rohe PTY-Bytes durch pyte (VT100-Emulator) → sauberer Text."""
    screen = pyte.Screen(width, height)
    stream = pyte.ByteStream(screen)
    stream.feed(raw_bytes)
    lines = [line.rstrip() for line in screen.display]
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _read_bytes(child, seconds: float) -> bytes:
    buf = b""
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            chunk = child.read_nonblocking(size=8192, timeout=0.3)
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8", errors="replace")
            buf += chunk
        except (pexpect.TIMEOUT, pexpect.EOF):
            break
    return buf


def _fetch_from_cli() -> dict | None:
    """
    Startet claude interaktiv, behandelt den Trust-Dialog,
    sendet /usage und parst die Ausgabe.
    Kein Keychain-Zugriff nötig.
    """
    HOME = os.path.expanduser("~")
    try:
        child = pexpect.spawn(
            "claude",
            cwd=HOME,
            timeout=5,
            encoding=None,          # Bytes-Modus für pyte
            codec_errors="replace",
        )

        # 1. Trust-Dialog (erscheint immer bei neuem Start)
        raw1 = _read_bytes(child, seconds=12)
        text1 = raw1.decode("utf-8", errors="replace")
        if "trust" in text1.lower() or "confirm" in text1.lower():
            child.send(b"\r")
            time.sleep(1)
            child.send(b"\r")

        # 2. Warten bis claude-Prompt bereit
        raw2 = _read_bytes(child, seconds=15)

        # 3. /usage senden
        child.send(b"/usage\r")
        time.sleep(8)
        raw3 = _read_bytes(child, seconds=6)

        # 4. Bildschirm rendern und parsen
        rendered = _render_screen(raw1 + raw2 + raw3)
        result = _parse_rendered(rendered)

        # 5. Sauber beenden
        child.send(b"/exit\r")
        child.close()

        return result

    except Exception:
        return None


def _parse_rendered(text: str) -> dict | None:
    """Extrahiert Nutzungsdaten aus dem gerenderten /usage-Bildschirm."""
    pcts   = re.findall(r"(\d+)%\s*used", text)
    resets = re.findall(r"Resets\s+(.+?)(?:\s{2,}|$)", text)

    if len(pcts) >= 2 and len(resets) >= 2:
        return {
            "session_pct":   int(pcts[0]),
            "session_reset": resets[0].strip(),
            "week_pct":      int(pcts[1]),
            "week_reset":    resets[1].strip(),
        }
    return None


# ── Cache ─────────────────────────────────────────────────────────────────────

def _load_cache() -> dict | None:
    try:
        raw = json.loads(USAGE_CACHE.read_text())
        return raw.get("data")
    except Exception:
        return None


def _save_cache(data: dict) -> None:
    try:
        USAGE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        USAGE_CACHE.write_text(json.dumps({"data": data}))
    except Exception:
        pass


# ── Formatierung ───────────────────────────────────────────────────────────────

def _bar(pct: int, width: int = 28) -> str:
    filled = max(0, min(width, round(width * pct / 100)))
    return "█" * filled + "░" * (width - filled)


def _time_until(reset_str: str) -> str:
    """
    '6:59pm (Europe/Berlin)'  →  '3h 42m'
    'Mar 25 at 11am (Europe/Berlin)'  →  '6h 10m'
    """
    tz_match = re.search(r"\(([^)]+)\)", reset_str)
    tz_str = tz_match.group(1) if tz_match else TZ
    try:
        tz   = ZoneInfo(tz_str)
        now  = datetime.now(tz)
        part = re.sub(r"\s*\([^)]+\)", "", reset_str).strip()

        dt = None

        # Format: "Mar 25 at 11am" / "Mar 25 at 6:59pm"
        for fmt in ("%b %d at %I:%M%p", "%b %d at %I%p"):
            try:
                dt = datetime.strptime(part.upper(), fmt).replace(
                    year=now.year, tzinfo=tz
                )
                if dt < now:
                    dt = dt.replace(year=now.year + 1)
                break
            except ValueError:
                pass

        # Format: "6:59pm" / "11am"
        if dt is None:
            for fmt in ("%I:%M%p", "%I%p"):
                try:
                    parsed = datetime.strptime(part.upper(), fmt)
                    dt = now.replace(
                        hour=parsed.hour,
                        minute=parsed.minute,
                        second=0, microsecond=0,
                    )
                    if dt <= now:
                        dt += timedelta(days=1)
                    break
                except ValueError:
                    pass

        if dt:
            delta   = dt - now
            total_m = max(0, int(delta.total_seconds() / 60))
            h, m    = divmod(total_m, 60)
            return f"{h}h {m}m" if h else f"{m}m"

    except Exception:
        pass
    return "–"


# ── Menubar App ────────────────────────────────────────────────────────────────

class ClaudeWidget(rumps.App):

    def __init__(self):
        super().__init__(name="Claude Usage", title="🤖 …", quit_button=None)
        self._data: dict | None = _load_cache()    # sofort anzeigen (letzter Wert)
        self._fetching = False

        if self._data:
            self._build_menu(self._data)

        # Hintergrund-Fetch starten
        self._start_fetch()

        # Timer für regelmäßige Aktualisierung
        self._timer = rumps.Timer(self._tick, REFRESH_SEC)
        self._timer.start()

    # ── Fetch ─────────────────────────────────────────────────────────────────

    def _tick(self, _):
        self._start_fetch()

    def _start_fetch(self):
        if self._fetching:
            return
        self._fetching = True
        self.title = self.title.rstrip(" ⟳") + " ⟳" if self._data else "🤖 …"
        t = threading.Thread(target=self._do_fetch, daemon=True)
        t.start()

    def _do_fetch(self):
        data = _fetch_from_cli()
        self._fetching = False
        if data:
            self._data = data
            _save_cache(data)
        self._build_menu(self._data)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_menu(self, data: dict | None):
        if not data:
            self.title = "🤖 –"
            self.menu.clear()
            self.menu = [
                rumps.MenuItem("⚠️  Konnte /usage nicht laden"),
                rumps.MenuItem("claude CLI muss installiert & eingeloggt sein"),
                None,
                rumps.MenuItem("🔄  Aktualisieren",
                               callback=lambda _: self._start_fetch()),
                None,
                rumps.MenuItem("❌  Beenden",
                               callback=rumps.quit_application),
            ]
            return

        sess_pct   = data["session_pct"]
        sess_reset = data["session_reset"]
        week_pct   = data["week_pct"]
        week_reset = data["week_reset"]

        sess_until = _time_until(sess_reset)
        sess_icon  = "🔴" if sess_pct >= 90 else "🟡" if sess_pct >= 70 else "🟢"

        # ── Menubar-Titel: Session-% + Zeit bis Reset ──────────────────────────
        self.title = f"{sess_icon} {sess_pct}%  ·  {sess_until}"

        # ── Dropdown ──────────────────────────────────────────────────────────
        items = [
            rumps.MenuItem("Current session"),
            rumps.MenuItem(f"  {_bar(sess_pct)}  {sess_pct}%"),
            rumps.MenuItem(f"  Resets {sess_reset}"),
            None,
            rumps.MenuItem("Current week  (all models)"),
            rumps.MenuItem(f"  {_bar(week_pct)}  {week_pct}%"),
            rumps.MenuItem(f"  Resets {week_reset}"),
            None,
            rumps.MenuItem("🔄  Aktualisieren",
                           callback=lambda _: self._start_fetch()),
            rumps.MenuItem("❌  Beenden",
                           callback=rumps.quit_application),
        ]

        self.menu.clear()
        for item in items:
            self.menu.add(item)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ClaudeWidget().run()
