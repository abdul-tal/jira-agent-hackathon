#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Jira Assistant - Starting UI...    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if API is running
echo -e "${YELLOW}📡 Checking API status...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is running${NC}"
else
    echo -e "${YELLOW}⚠️  API is not running!${NC}"
    echo ""
    echo "Please start the API server first:"
    echo -e "${BLUE}python main.py${NC}"
    echo ""
    echo "Or press Enter to continue anyway..."
    read -r
fi

echo ""
echo -e "${YELLOW}🚀 Starting Streamlit UI...${NC}"
echo ""
echo -e "${GREEN}UI will open at: http://localhost:8501${NC}"
echo ""

# Start Streamlit
streamlit run streamlit_app.py

