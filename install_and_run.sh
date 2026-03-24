#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║       Claude Usage Widget — Einmaliger Setup & Start        ║
# ╚══════════════════════════════════════════════════════════════╝

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIDGET="$SCRIPT_DIR/claude_widget.py"
PID_FILE="$HOME/.cache/claude_widget.pid"
LOG_FILE="$HOME/.cache/claude_widget.log"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🤖  Claude Usage Widget — Setup           ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 1. Python 3 prüfen
echo -e "${YELLOW}[1/3] Python 3 …${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗  Python 3 fehlt. Bitte von https://python.org installieren.${NC}"
    exit 1
fi
echo -e "${GREEN}✓  $(python3 --version)${NC}"

# 2. rumps installieren
echo ""
echo -e "${YELLOW}[2/3] Python-Pakete installieren …${NC}"
MISSING=()
python3 -c "import rumps"    2>/dev/null || MISSING+=("rumps")
python3 -c "import pexpect" 2>/dev/null || MISSING+=("pexpect")
python3 -c "import pyte"    2>/dev/null || MISSING+=("pyte")

if [ ${#MISSING[@]} -eq 0 ]; then
    echo -e "${GREEN}✓  Alle Pakete bereits vorhanden${NC}"
else
    echo "    → Installiere: ${MISSING[*]}"
    pip3 install --quiet "${MISSING[@]}"
    echo -e "${GREEN}✓  Pakete installiert${NC}"
fi

# 3. Altes Widget stoppen
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null && echo -e "${YELLOW}  → Altes Widget (PID $OLD_PID) gestoppt${NC}" || true
    rm -f "$PID_FILE"
fi

# 4. Widget starten
echo ""
echo -e "${YELLOW}[3/3] Widget starten …${NC}"
mkdir -p "$HOME/.cache"
nohup python3 "$WIDGET" >"$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
sleep 1

if kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo -e "${GREEN}✓  Widget läuft (PID $(cat $PID_FILE))${NC}"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅  Schau in die Menüleiste oben rechts!  ${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  Stoppen:  kill \$(cat ~/.cache/claude_widget.pid)"
    echo "  Log:      tail -f $LOG_FILE"
else
    echo -e "${RED}✗  Start fehlgeschlagen — Log:${NC}"
    tail -5 "$LOG_FILE" 2>/dev/null
    exit 1
fi
