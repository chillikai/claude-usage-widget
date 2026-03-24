# Claude Usage Widget — Projektstruktur

## 📁 Projektverzeichnis

```
Claude-Usage-Widget/
├── claude_widget.py           🔧 Hauptprogramm (Menüleisten-App)
├── install_and_run.sh         🚀 Setup & Start-Script
├── setup_launchagent.sh       ⚙️  Autostart-Setup (generiert Plist)
├── claude_widget.plist        📄 Plist-Template (nicht verwenden!)
├── README.md                  📖 Vollständige Dokumentation
├── STRUKTUR.md                📋 Diese Datei
├── test_claude_usage.py       🧪 Test-Script (Referenz)
└── widget_datenfluss.html     📊 Datenfluss-Diagramm (Grafik)
```

---

## 🚀 Quick Start

### 1. Installation & Start (erste Mal)

```bash
cd /Users/kai/Desktop/Vibe-Code-Projekts/Claude-Usage-Widget
bash install_and_run.sh
```

Das Script installiert alle Abhängigkeiten und startet das Widget.

### 2. Widget in der Menüleiste prüfen

Nach ~15 Sekunden erscheint in der oberen rechten Menüleiste ein Icon:

```
🟢 45%  ·  3h 42m
```

### 3. Autostart beim Login (optional)

```bash
cp claude_widget.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/claude_widget.plist
```

---

## 📄 Dateien erklärt

### `claude_widget.py` 🔧
Das Herzstück der App. Enthält:
- **Menüleisten-UI** via `rumps` Framework
- **Daten-Fetch** (pexpect + pyte für Claude CLI Parsing)
- **Disk-Cache** für schnelle Neustarts
- **Hintergrund-Thread** für nicht-blockierende Updates

**Konfiguration:**
```python
REFRESH_SEC = 120          # Update-Interval (2 Minuten)
TZ = "Europe/Berlin"       # Zeitzone für Reset-Zeiten
```

### `install_and_run.sh` 🚀
Einmaliges Setup-Script:
1. Prüft Python 3
2. Installiert `rumps`, `pexpect`, `pyte`
3. Stoppt evtl. alte Widget-Prozesse
4. Startet Widget im Hintergrund

### `setup_launchagent.sh` ⚙️
Generiert automatisch die LaunchAgent-Plist mit korrekten Pfaden:
```bash
bash setup_launchagent.sh
```
Das Script:
- Ermittelt automatisch Python-Pfad, Benutzer und Projektort
- Erstellt eine Plist mit den korrekten Werten
- Installiert sie in `~/Library/LaunchAgents/`
- Aktiviert das Widget für Autostart beim Login

### `claude_widget.plist` 📄
Plist-Template (wird vom `setup_launchagent.sh` Script generiert).
**Nicht manuell bearbeiten** — verwende stattdessen `bash setup_launchagent.sh`.

### `README.md` 📖
Vollständige Dokumentation:
- Setup-Anleitung
- Bedienung
- Troubleshooting
- Wie es funktioniert (Datenfluss)

### `test_claude_usage.py` 🧪
Eigenständiges Test-Script zum manuellen Testen der Claude-CLI-Anbindung.

Ausführen:
```bash
python3 test_claude_usage.py
```

Zeigt:
- Ob Claude CLI erreichbar ist
- Rendering der `/usage`-Ausgabe
- Parsing-Ergebnis

### `widget_datenfluss.html` 📊
Interaktive HTML-Visualisierung des Datenflusses. Im Browser öffnen für visuellen Überblick.

---

## 🔌 Abhängigkeiten

| Paket | Version | Zweck |
|---|---|---|
| `rumps` | latest | macOS Menüleisten-Framework |
| `pexpect` | latest | Interaktive Prozess-Steuerung |
| `pyte` | latest | VT100 Terminal-Emulator |
| `claude` (CLI) | — | Datenquelle (muss eingeloggt sein) |

Alle Python-Pakete werden automatisch von `install_and_run.sh` installiert.

---

## 📊 Datenfluss (Kurzversion)

```
1. Widget startet
   ↓
2. Cache laden (letzte Werte sofort zeigen)
   ↓
3. Background-Thread: Starte `claude` CLI via pexpect
   ↓
4. Trust-Dialog bestätigen → /usage senden
   ↓
5. Rohe Terminal-Bytes empfangen → pyte rendert → Regex parst
   ↓
6. Menüleiste aktualisieren + Cache speichern
   ↓
7. Alle 120 Sekunden wiederholen
```

Siehe `widget_datenfluss.html` für detaillierte Grafik.

---

## ⚙️ Konfiguration anpassen

In `claude_widget.py` ganz oben:

```python
REFRESH_SEC = 120          # Ändern um Update-Interval anzupassen
TZ = "Europe/Berlin"       # Zeitzone für Reset-Zeit-Anzeige
USAGE_CACHE = Path.home() / ".cache" / "claude_widget_usage.json"
```

---

## 🐛 Troubleshooting

**Widget erscheint nicht in Menüleiste:**
```bash
python3 claude_widget.py
# (direktes Starten zeigt Fehler)
```

**Log anschauen:**
```bash
tail -f ~/.cache/claude_widget.log
```

**Widget manuell stoppen:**
```bash
kill $(cat ~/.cache/claude_widget.pid)
```

**Widget neu starten:**
```bash
cd /Users/kai/Desktop/Vibe-Code-Projekts/Claude-Usage-Widget
bash install_and_run.sh
```

---

## 📍 Wichtige Pfade

| Datei | Zweck |
|---|---|
| `~/.cache/claude_widget_usage.json` | Disk-Cache (letzte Werte) |
| `~/.cache/claude_widget.pid` | PID des laufenden Prozesses |
| `~/.cache/claude_widget.log` | Log-Ausgabe |
| `~/Library/LaunchAgents/com.chilli-mind.claude-widget.plist` | Autostart-Config (generiert von `setup_launchagent.sh`) |

---

## ✅ Fertig!

Das Projekt ist bereit. Los geht's:

```bash
cd /Users/kai/Desktop/Vibe-Code-Projekts/Claude-Usage-Widget
bash install_and_run.sh
```

Bei Fragen: siehe `README.md` oder `widget_datenfluss.html`.
