#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║   Claude Usage Widget — LaunchAgent Setup (Autostart)            ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# Dieses Script generiert automatisch die Plist-Datei mit den
# korrekten Pfaden für den aktuellen Benutzer.
#
# Ausführen:
#   bash setup_launchagent.sh
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Claude Usage Widget — LaunchAgent Setup                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Variablen ermitteln ─────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIDGET_PATH="$SCRIPT_DIR/claude_widget.py"
PYTHON_PATH=$(which python3)
USERNAME=$(whoami)
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCHAGENT_DIR/com.chilli-mind.claude-widget.plist"
CACHE_LOG="$HOME/.cache/claude_widget.log"

echo -e "${YELLOW}[1/3] Konfiguration ermitteln…${NC}"
echo "  → User:           $USERNAME"
echo "  → Widget-Ort:     $WIDGET_PATH"
echo "  → Python:         $PYTHON_PATH"
echo "  → LaunchAgent:    $PLIST_FILE"
echo ""

# ── 2. Prüfungen ───────────────────────────────────────────────────────────────

if [ ! -f "$WIDGET_PATH" ]; then
    echo -e "${RED}✗  claude_widget.py nicht gefunden in: $SCRIPT_DIR${NC}"
    exit 1
fi

if [ ! -x "$PYTHON_PATH" ]; then
    echo -e "${RED}✗  Python 3 nicht gefunden${NC}"
    exit 1
fi

echo -e "${GREEN}✓  claude_widget.py vorhanden${NC}"
echo -e "${GREEN}✓  Python 3 vorhanden${NC}"
echo ""

# ── 3. Plist generieren ────────────────────────────────────────────────────────

echo -e "${YELLOW}[2/3] LaunchAgent-Datei generieren…${NC}"

mkdir -p "$LAUNCHAGENT_DIR"
mkdir -p "$(dirname "$CACHE_LOG")"

cat > "$PLIST_FILE" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.chilli-mind.claude-widget</string>

    <key>ProgramArguments</key>
    <array>
        <string>PYTHON_PATH_PLACEHOLDER</string>
        <string>WIDGET_PATH_PLACEHOLDER</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>SessionCreate</key>
    <true/>

    <key>StandardOutPath</key>
    <string>LOG_PATH_PLACEHOLDER</string>

    <key>StandardErrorPath</key>
    <string>LOG_PATH_PLACEHOLDER</string>
</dict>
</plist>
PLIST_EOF

# Placeholder ersetzen
sed -i '' "s|PYTHON_PATH_PLACEHOLDER|$PYTHON_PATH|g" "$PLIST_FILE"
sed -i '' "s|WIDGET_PATH_PLACEHOLDER|$WIDGET_PATH|g" "$PLIST_FILE"
sed -i '' "s|LOG_PATH_PLACEHOLDER|$CACHE_LOG|g" "$PLIST_FILE"

echo -e "${GREEN}✓  Plist generiert: $PLIST_FILE${NC}"
echo ""

# ── 4. LaunchAgent laden ───────────────────────────────────────────────────────

echo -e "${YELLOW}[3/3] LaunchAgent laden…${NC}"

# Erst alt entladen falls vorhanden
launchctl unload "$PLIST_FILE" 2>/dev/null || true
sleep 1

# Neu laden
launchctl load "$PLIST_FILE"

echo -e "${GREEN}✓  LaunchAgent aktiviert${NC}"
echo ""

# ── Bestätigung ────────────────────────────────────────────────────────────────

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  Autostart beim Login ist aktiviert!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Das Widget startet beim nächsten Login automatisch."
echo ""
echo -e "${YELLOW}Zum Deaktivieren:${NC}"
echo "  launchctl unload ~/Library/LaunchAgents/com.chilli-mind.claude-widget.plist"
echo ""
