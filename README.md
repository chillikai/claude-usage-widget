# Claude Usage Widget

Ein macOS-Menüleisten-Widget das deinen Claude-Nutzungsstand anzeigt — identisch zu Claude Code's `/usage`-Befehl.

```
🟡 45%  ·  3h 42m
```

---

## Was es anzeigt

Das Widget zeigt in der Menüleiste kontinuierlich:

- **Session-Auslastung** (aktuelles 5-Stunden-Fenster) in Prozent
- **Zeit bis zum Reset** der aktuellen Session

Ein Klick öffnet das Dropdown mit zwei Fortschrittsbalken:

```
Current session
  ████████████████░░░░░░░░░░░░  45%
  Resets 6:59pm (Europe/Berlin)

Current week  (all models)
  ██████████████████████████░░  79%
  Resets 11am (Europe/Berlin)
```

Das Ampel-Icon wechselt je nach Auslastung: 🟢 unter 70 % · 🟡 70–89 % · 🔴 ab 90 %.

---

## Voraussetzungen

| Voraussetzung | Prüfen |
|---|---|
| macOS 12 oder neuer | — |
| Python 3.10+ (z. B. via Miniconda) | `python3 --version` |
| Claude Code CLI installiert & eingeloggt | `claude --version` |

> **Wichtig:** Das Widget nutzt ausschließlich die `claude`-CLI für Datenzugriff. Es werden keine Browser-Cookies, kein Keychain und keine Passwörter benötigt.

---

## ⚡ Quick Start (nur 2 Befehle!)

```bash
git clone https://github.com/chillikai/claude-usage-widget.git
cd claude-usage-widget && bash install_and_run.sh
```

**Fertig!** Das Widget erscheint in ca. 15 Sekunden oben rechts in deiner Menüleiste. 🟡

Für **Autostart beim Login** (optional):
```bash
bash setup_launchagent.sh
```

---

## Installation & Start (Detailliert)

### 1. Repository klonen

```bash
git clone https://github.com/chillikai/claude-usage-widget.git
cd claude-usage-widget
```

### 2. Setup-Script ausführen

```bash
bash install_and_run.sh
```

Das Script:
1. Prüft ob Python 3 vorhanden ist
2. Installiert fehlende Python-Pakete (`rumps`, `pexpect`, `pyte`)
3. Stoppt ein eventuell laufendes altes Widget
4. Startet das neue Widget im Hintergrund

### 3. Widget in der Menüleiste finden

Nach dem Start erscheint das Widget oben rechts in der macOS-Menüleiste. Beim ersten Start dauert es **ca. 15 Sekunden** bis die Werte geladen sind (claude CLI muss starten).

---

## Autostart beim Login (optional)

Um das Widget automatisch beim Mac-Start zu laden, das Setup-Script ausführen:

```bash
bash setup_launchagent.sh
```

Das Script:
1. Ermittelt automatisch Benutzernamen und Projektspeicherort
2. Generiert die LaunchAgent-Plist mit korrekten Pfaden
3. Installiert diese in `~/Library/LaunchAgents/`

**Fertig!** Das Widget startet beim nächsten Login automatisch.

Den Autostart wieder deaktivieren:

```bash
launchctl unload ~/Library/LaunchAgents/com.chilli-mind.claude-widget.plist
```

---

## Bedienung

| Aktion | Ergebnis |
|---|---|
| Klick auf Menüleisten-Icon | Öffnet Dropdown mit beiden Fortschrittsbalken |
| Klick auf „🔄 Aktualisieren" | Lädt sofort neue Daten von der Claude CLI |
| Klick auf „❌ Beenden" | Beendet das Widget |

---

## Konfiguration

In `claude_widget.py` stehen oben drei Einstellungen:

```python
REFRESH_SEC = 120          # Automatisches Update-Interval (Sekunden)
TZ          = "Europe/Berlin"   # Zeitzone für Reset-Zeiten
USAGE_CACHE = Path.home() / ".cache" / "claude_widget_usage.json"
```

---

## Wie es funktioniert

Das Widget hat **keinen direkten API-Zugriff** auf claude.ai — stattdessen liest es die Daten direkt aus der Claude Code CLI, genau wie wenn man `/usage` im Terminal eintippt.

```
Widget startet
    │
    ├─▶ Disk-Cache laden (letzter bekannter Wert sofort anzeigen)
    │
    └─▶ Background-Thread (non-blocking)
            │
            ├─ pexpect öffnet virtuelles Terminal (PTY)
            ├─ startet: claude  (in ~/  als Arbeitsverzeichnis)
            ├─ Trust-Dialog erscheint → \r senden (Option 1 bestätigen)
            ├─ Wartet bis claude bereit ist
            ├─ Sendet: /usage
            │
            ├─ Rohe Terminal-Bytes empfangen (ANSI-Codes + Cursor-Bewegungen)
            ├─ pyte emuliert VT100-Terminal → rendert sauberen Text
            ├─ Regex extrahiert: session_pct, session_reset, week_pct, week_reset
            │
            ├─ Speichert Ergebnis in ~/.cache/claude_widget_usage.json
            └─ Aktualisiert Menüleiste + Dropdown

    Alle 120 Sekunden wiederholen
```

**Warum pyte?** Die `/usage`-Ausgabe ist eine TUI (Terminal UI) die Cursor-Bewegungsbefehle nutzt um Balken und Text zu positionieren. Ein einfaches ANSI-Stripping reicht nicht aus — `pyte` emuliert den kompletten VT100-Terminal und gibt den tatsächlich sichtbaren Bildschirminhalt zurück.

**Kein Keychain-Zugriff:** Die `claude`-CLI handhabt ihre Authentifizierung vollständig selbst. Das Widget übergibt keine Credentials und greift auf keine gespeicherten Passwörter zu.

---

## Dateien im Überblick

| Datei | Beschreibung |
|---|---|
| `claude_widget.py` | Hauptprogramm — Menüleisten-App + Daten-Fetch |
| `install_and_run.sh` | Einmaliger Setup & Start im Hintergrund |
| `claude_widget.plist` | LaunchAgent für Autostart beim Login |
| `~/.cache/claude_widget_usage.json` | Disk-Cache (letzte bekannte Werte) |
| `~/.cache/claude_widget.pid` | PID des laufenden Widget-Prozesses |
| `~/.cache/claude_widget.log` | Log-Ausgabe des Widgets |

---

## Troubleshooting

**Widget erscheint nicht in der Menüleiste**

Das Widget muss direkt in einem Terminal (nicht per `nohup`) gestartet werden, um Zugriff auf macOS Window Server zu haben:
```bash
python3 claude_widget.py
```
Alternativ: LaunchAgent mit `SessionCreate=true` verwenden (siehe `claude_widget.plist`).

**Widget zeigt dauerhaft „🤖 –"**

- Ist `claude` im PATH? → `which claude`
- Ist Claude Code eingeloggt? → `claude` im Terminal starten und prüfen
- Log anschauen: `tail -f ~/.cache/claude_widget.log`

**Widget lädt sehr langsam**

Normal — jeder Datenabruf startet eine neue `claude`-Session (~10–15 Sekunden). Der Disk-Cache stellt sicher, dass zuletzt geladene Werte sofort angezeigt werden.

**Widget manuell stoppen**

```bash
kill $(cat ~/.cache/claude_widget.pid)
```

---

## Abhängigkeiten

| Paket | Zweck | Installieren |
|---|---|---|
| `rumps` | macOS Menüleisten-App Framework | `pip3 install rumps` |
| `pexpect` | Interaktive Prozess-Steuerung via PTY | `pip3 install pexpect` |
| `pyte` | VT100 Terminal-Emulator (für sauberes Parsing) | `pip3 install pyte` |
