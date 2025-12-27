#!/bin/bash
# LeGO-LOAM Debug Log Collection and Analysis Script
# Collects logs from running LeGO-LOAM system and performs analysis

set -e

LOG_DIR="/tmp/lego_loam_logs"
ARCHIVE_DIR="./lego_loam_debug_session"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LeGO-LOAM Debug Log Collection & Analysis                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --collect    Collect logs from running system"
    echo "  -a, --analyze    Analyze collected logs"
    echo "  -r, --run        Run collection and analysis"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Collect logs while LeGO-LOAM is running"
    echo "  $0 --collect"
    echo ""
    echo "  # Analyze collected logs"
    echo "  $0 --analyze"
    echo ""
    echo "  # Do both at once"
    echo "  $0 --run"
    echo ""
}

# Function to collect logs
collect_logs() {
    echo -e "${YELLOW}Collecting logs from LeGO-LOAM system...${NC}"
    echo ""
    
    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${RED}✗ Log directory not found: $LOG_DIR${NC}"
        echo "  Make sure LeGO-LOAM is running with debug enabled."
        return 1
    fi

    # Create archive directory
    mkdir -p "$ARCHIVE_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    SESSION_DIR="$ARCHIVE_DIR/session_$TIMESTAMP"
    mkdir -p "$SESSION_DIR"

    # Copy log files
    if [ -f "$LOG_DIR/lego_loam_debug.log" ]; then
        cp "$LOG_DIR/lego_loam_debug.log" "$SESSION_DIR/"
        echo -e "${GREEN}✓${NC} Copied main log file"
    else
        echo -e "${RED}✗${NC} Main log file not found"
        return 1
    fi

    # Create metadata
    cat > "$SESSION_DIR/metadata.txt" << EOF
LeGO-LOAM Debug Session Metadata
================================
Collection Time: $(date)
System: $(uname -a)
Log Directory: $LOG_DIR
Session Directory: $SESSION_DIR

Files Included:
- lego_loam_debug.log: Main debug output from all nodes
- metadata.txt: This file

To analyze these logs, run:
  python3 /workspace/analyze_logs.py $SESSION_DIR/lego_loam_debug.log

EOF

    echo -e "${GREEN}✓${NC} Created session metadata"
    echo ""
    echo -e "${GREEN}✓ Logs collected successfully!${NC}"
    echo "  Location: $SESSION_DIR"
    echo ""
    
    # Show file size
    if [ -f "$SESSION_DIR/lego_loam_debug.log" ]; then
        SIZE=$(du -h "$SESSION_DIR/lego_loam_debug.log" | cut -f1)
        LINES=$(wc -l < "$SESSION_DIR/lego_loam_debug.log")
        echo "  Log file size: $SIZE ($LINES lines)"
    fi
}

# Function to analyze logs
analyze_logs() {
    echo -e "${YELLOW}Analyzing LeGO-LOAM logs...${NC}"
    echo ""

    LOG_FILE="$LOG_DIR/lego_loam_debug.log"
    
    if [ ! -f "$LOG_FILE" ]; then
        # Try to find most recent session
        if [ -d "$ARCHIVE_DIR" ]; then
            LATEST=$(ls -d "$ARCHIVE_DIR"/session_* 2>/dev/null | tail -1)
            if [ ! -z "$LATEST" ]; then
                LOG_FILE="$LATEST/lego_loam_debug.log"
            fi
        fi
    fi

    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}✗ No log file found${NC}"
        echo "  Checked: $LOG_DIR/lego_loam_debug.log"
        return 1
    fi

    echo "Analyzing log file: $LOG_FILE"
    echo "File size: $(du -h "$LOG_FILE" | cut -f1)"
    echo ""

    # Run Python analysis
    if command -v python3 &> /dev/null; then
        if [ -f "/workspace/analyze_logs.py" ]; then
            python3 /workspace/analyze_logs.py "$LOG_FILE"
        else
            echo -e "${RED}✗ Analysis script not found: /workspace/analyze_logs.py${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Python3 not found${NC}"
        return 1
    fi
}

# Function to clear old logs
clear_logs() {
    echo -e "${YELLOW}Clearing old log files...${NC}"
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        mkdir -p "$LOG_DIR"
        echo -e "${GREEN}✓ Log directory cleared${NC}"
    fi
}

# Parse arguments
if [ $# -eq 0 ]; then
    usage
    exit 0
fi

case "$1" in
    -c|--collect)
        collect_logs
        ;;
    -a|--analyze)
        analyze_logs
        ;;
    -r|--run)
        collect_logs
        echo ""
        analyze_logs
        ;;
    --clear)
        clear_logs
        ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        echo "Unknown option: $1"
        usage
        exit 1
        ;;
esac
