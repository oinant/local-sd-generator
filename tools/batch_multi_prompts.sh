#!/bin/bash

# batch_multi_prompts.sh - Run multiple prompts with different themes/styles
#
# Usage:
#   ./batch_multi_prompts.sh [--dry-run]
#
# Input format (via stdin or file):
#   <prompt_path>:theme:style:count
#   <prompt_path>:theme:style:count
#   ...
#
# Examples:
#   echo "prompts/char1.yaml:cyberpunk:default:50" | ./batch_multi_prompts.sh
#   cat sessions.txt | ./batch_multi_prompts.sh
#   ./batch_multi_prompts.sh < sessions.txt
#
# sessions.txt format:
#   prompts/hassaku-teasing.yaml:cyberpunk:default:50
#   prompts/hassaku-teasing.yaml:cyberpunk:sexy:30
#   prompts/hassaku-portrait.yaml:pirates:cartoon:25

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=""
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
    echo -e "${YELLOW}🔍 DRY-RUN MODE${NC}"
fi

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDGEN_PATH="/mnt/d/StableDiffusion/local-sd-generator/venv/bin/sdgen"

# Check sdgen exists
if [ ! -f "$SDGEN_PATH" ]; then
    echo -e "${RED}✗ Error: sdgen not found at $SDGEN_PATH${NC}"
    exit 1
fi

# Read all input lines into array
mapfile -t SESSIONS

# Count total sessions
TOTAL_SESSIONS=${#SESSIONS[@]}

if [ $TOTAL_SESSIONS -eq 0 ]; then
    echo -e "${RED}✗ Error: No sessions provided${NC}"
    echo "Usage: echo 'prompt.yaml:theme:style:count' | $0 [--dry-run]"
    exit 1
fi

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Multi-Prompt Batch Generator                          ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📋 Total sessions: ${TOTAL_SESSIONS}${NC}"
echo ""

# Statistics
SUCCESS_COUNT=0
FAIL_COUNT=0
START_TIME=$(date +%s)

# Process each session
CURRENT=0
for session_line in "${SESSIONS[@]}"; do
    # Skip empty lines and comments
    if [[ -z "$session_line" ]] || [[ "$session_line" =~ ^#.*$ ]]; then
        continue
    fi

    CURRENT=$((CURRENT + 1))

    # Parse session line: prompt:theme:style:count
    IFS=':' read -r PROMPT_PATH THEME STYLE COUNT <<< "$session_line"

    # Trim whitespace
    PROMPT_PATH=$(echo "$PROMPT_PATH" | xargs)
    THEME=$(echo "$THEME" | xargs)
    STYLE=$(echo "$STYLE" | xargs)
    COUNT=$(echo "$COUNT" | xargs)

    # Validate prompt path (allow both absolute and relative)
    if [[ "$PROMPT_PATH" != /* ]]; then
        # Relative path - assume relative to current working directory
        FULL_PROMPT_PATH="$(pwd)/$PROMPT_PATH"
    else
        FULL_PROMPT_PATH="$PROMPT_PATH"
    fi

    if [ ! -f "$FULL_PROMPT_PATH" ]; then
        echo -e "${RED}✗ [$CURRENT/$TOTAL_SESSIONS] Prompt not found: $FULL_PROMPT_PATH${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi

    # Extract prompt name for display
    PROMPT_NAME=$(basename "$PROMPT_PATH" .yaml)

    # Build session label
    if [ "$STYLE" = "default" ]; then
        SESSION_LABEL="$PROMPT_NAME × $THEME"
    else
        SESSION_LABEL="$PROMPT_NAME × $THEME.$STYLE"
    fi

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🚀 [$CURRENT/$TOTAL_SESSIONS] ${SESSION_LABEL} (${COUNT} images)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Build command
    CMD="$SDGEN_PATH generate -t \"$FULL_PROMPT_PATH\" --theme \"$THEME\" --use-fixed \"Rendering:beau_manga\""

    if [ "$STYLE" != "default" ]; then
        CMD="$CMD --style \"$STYLE\""
    fi

    CMD="$CMD -n $COUNT"

    if [ -n "$DRY_RUN" ]; then
        CMD="$CMD --dry-run"
    fi

    echo -e "${YELLOW}Command: $CMD${NC}"
    echo ""

    # Execute
    if eval $CMD; then
        echo -e "${GREEN}✓ Success${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}✗ Failed${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    echo ""

    # Progress and ETA
    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $CURRENT -gt 0 ]; then
        AVG_TIME=$((ELAPSED / CURRENT))
        REMAINING=$((TOTAL_SESSIONS - CURRENT))
        ETA=$((REMAINING * AVG_TIME))

        # Format ETA
        ETA_HOURS=$((ETA / 3600))
        ETA_MINS=$(((ETA % 3600) / 60))
        ETA_SECS=$((ETA % 60))

        echo -e "${CYAN}📊 Progress: $SUCCESS_COUNT/$TOTAL_SESSIONS completed | $FAIL_COUNT failed | ETA: ${ETA_HOURS}h ${ETA_MINS}m ${ETA_SECS}s${NC}"
        echo ""
    fi
done

# Final summary
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
HOURS=$((TOTAL_TIME / 3600))
MINS=$(((TOTAL_TIME % 3600) / 60))
SECS=$((TOTAL_TIME % 60))

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Batch Complete                                        ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Successful: $SUCCESS_COUNT${NC}"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}✗ Failed: $FAIL_COUNT${NC}"
fi
echo -e "${CYAN}⏱️  Total time: ${HOURS}h ${MINS}m ${SECS}s${NC}"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    exit 1
fi
