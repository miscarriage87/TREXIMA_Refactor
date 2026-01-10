#!/bin/bash
# TREXIMA Development Server Starter
# Startet Backend und Frontend parallel

cd "$(dirname "$0")"

# Farben fuer Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   TREXIMA Development Server${NC}"
echo -e "${BLUE}========================================${NC}"

# Aktiviere virtuelle Umgebung
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "trexima-venv" ]; then
    source trexima-venv/bin/activate
fi

# Funktion zum Beenden aller Hintergrundprozesse
cleanup() {
    echo -e "\n${GREEN}Beende Server...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Backend starten
echo -e "${GREEN}[1/2] Starte Backend auf Port 5000...${NC}"
python run_web.py --debug &
BACKEND_PID=$!

# Warte kurz, damit Backend initialisiert
sleep 2

# Frontend starten
echo -e "${GREEN}[2/2] Starte Frontend auf Port 5173...${NC}"
cd trexima-frontend && npm run dev &
FRONTEND_PID=$!

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Server gestartet!${NC}"
echo -e "${GREEN}Backend:  http://localhost:5000${NC}"
echo -e "${GREEN}Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Druecke Ctrl+C zum Beenden${NC}\n"

# Warte auf beide Prozesse
wait
