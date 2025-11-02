#!/bin/bash
# Batch Generation Script for SD Generator CLI
# Usage: ./batch_generate.sh [OPTIONS] theme:style:count [theme:style:count ...]
#
# Examples:
#   ./batch_generate.sh -t template.yaml arabesque:sexy:50 streetwear:teasing:30
#   ./batch_generate.sh --dry-run cyberpunk:default:100 pirates:teasing:50

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
TEMPLATE=""
DRY_RUN=""
SESSIONS=()
START_TIME=$(date +%s)

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--template)
            TEMPLATE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS] theme:style:count [theme:style:count ...]"
            echo ""
            echo "Options:"
            echo "  -t, --template PATH    Template file path"
            echo "  --dry-run              Dry run mode (save API requests without generating)"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Format: theme:style:count"
            echo "  - theme: Theme name (e.g., arabesque, streetwear)"
            echo "  - style: Style name (e.g., sexy, teasing, default)"
            echo "  - count: Number of images to generate"
            echo ""
            echo "Examples:"
            echo "  $0 -t template.yaml arabesque:sexy:50 streetwear:teasing:30"
            echo "  $0 --dry-run cyberpunk:default:100 pirates:teasing:50"
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
        *)
            SESSIONS+=("$1")
            shift
            ;;
    esac
done

# Validate inputs
if [ ${#SESSIONS[@]} -eq 0 ]; then
    echo -e "${RED}Error: No sessions specified${NC}"
    echo "Use -h or --help for usage information"
    exit 1
fi

if [ -z "$TEMPLATE" ]; then
    echo -e "${RED}Error: Template file required (-t option)${NC}"
    exit 1
fi

if [ ! -f "$TEMPLATE" ]; then
    echo -e "${RED}Error: Template file not found: $TEMPLATE${NC}"
    exit 1
fi

# Display batch summary
echo ""
echo -e "${CYAN}╭─────────────────────────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│${NC}              ${BLUE}Batch Generation Summary${NC}                    ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────────────────────────╯${NC}"
echo ""
echo -e "${YELLOW}Template:${NC} $TEMPLATE"
echo -e "${YELLOW}Sessions:${NC} ${#SESSIONS[@]}"
if [ -n "$DRY_RUN" ]; then
    echo -e "${YELLOW}Mode:${NC} ${BLUE}Dry-run${NC}"
fi
echo ""
echo -e "${CYAN}Sessions to run:${NC}"

TOTAL_IMAGES=0
for i in "${!SESSIONS[@]}"; do
    SESSION="${SESSIONS[$i]}"

    # Parse session format: theme:style:count
    IFS=':' read -r theme style count <<< "$SESSION"

    if [ -z "$theme" ] || [ -z "$style" ] || [ -z "$count" ]; then
        echo -e "${RED}Error: Invalid session format: $SESSION${NC}"
        echo "Expected format: theme:style:count"
        exit 1
    fi

    if ! [[ "$count" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error: Invalid count in session $SESSION: $count${NC}"
        exit 1
    fi

    TOTAL_IMAGES=$((TOTAL_IMAGES + count))
    echo -e "  $((i+1)). ${GREEN}$theme${NC} / ${BLUE}$style${NC} → ${YELLOW}$count${NC} images"
done

echo ""
echo -e "${YELLOW}Total images:${NC} $TOTAL_IMAGES"
echo ""
read -p "$(echo -e ${CYAN}Press Enter to start or Ctrl+C to cancel...${NC})"
echo ""

# Run sessions
SUCCESS_COUNT=0
FAILED_COUNT=0
FAILED_SESSIONS=()

for i in "${!SESSIONS[@]}"; do
    SESSION="${SESSIONS[$i]}"
    SESSION_NUM=$((i + 1))
    TOTAL_SESSIONS=${#SESSIONS[@]}

    # Parse session
    IFS=':' read -r theme style count <<< "$SESSION"

    # Calculate progress
    PERCENT=$(( (SESSION_NUM * 100) / TOTAL_SESSIONS ))
    ELAPSED=$(($(date +%s) - START_TIME))

    if [ $SESSION_NUM -gt 1 ]; then
        AVG_TIME=$((ELAPSED / (SESSION_NUM - 1)))
        REMAINING_SESSIONS=$((TOTAL_SESSIONS - SESSION_NUM + 1))
        ETA=$((AVG_TIME * REMAINING_SESSIONS))
        ETA_MIN=$((ETA / 60))
        ETA_SEC=$((ETA % 60))
    else
        ETA_MIN=0
        ETA_SEC=0
    fi

    echo -e "${CYAN}╭─────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│${NC} ${BLUE}Session $SESSION_NUM/$TOTAL_SESSIONS${NC} (${PERCENT}%) ${CYAN}│${NC} ETA: ${YELLOW}${ETA_MIN}m ${ETA_SEC}s${NC}"
    echo -e "${CYAN}╰─────────────────────────────────────────────────────────────╯${NC}"
    echo -e "${YELLOW}Theme:${NC} $theme"
    echo -e "${YELLOW}Style:${NC} $style"
    echo -e "${YELLOW}Count:${NC} $count"
    echo ""

    # Build command (use full path to sdgen)
    SDGEN_PATH="/mnt/d/StableDiffusion/local-sd-generator/venv/bin/sdgen"
    CMD="$SDGEN_PATH generate -t \"$TEMPLATE\" --theme \"$theme\""

    if [ "$style" != "default" ]; then
        CMD="$CMD --style \"$style\""
    fi

    CMD="$CMD -n $count"

    if [ -n "$DRY_RUN" ]; then
        CMD="$CMD --dry-run"
    fi

    # Execute
    SESSION_START=$(date +%s)

    if eval "$CMD"; then
        SESSION_DURATION=$(($(date +%s) - SESSION_START))
        SESSION_MIN=$((SESSION_DURATION / 60))
        SESSION_SEC=$((SESSION_DURATION % 60))

        echo ""
        echo -e "${GREEN}✓ Session $SESSION_NUM completed${NC} (${SESSION_MIN}m ${SESSION_SEC}s)"
        echo ""
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo ""
        echo -e "${RED}✗ Session $SESSION_NUM failed${NC}"
        echo ""
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FAILED_SESSIONS+=("$SESSION")
    fi
done

# Final summary
TOTAL_DURATION=$(($(date +%s) - START_TIME))
TOTAL_MIN=$((TOTAL_DURATION / 60))
TOTAL_SEC=$((TOTAL_DURATION % 60))

echo ""
echo -e "${CYAN}╭─────────────────────────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│${NC}              ${BLUE}Batch Generation Complete${NC}                  ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────────────────────────╯${NC}"
echo ""
echo -e "${YELLOW}Total sessions:${NC} $TOTAL_SESSIONS"
echo -e "${GREEN}✓ Success:${NC} $SUCCESS_COUNT"

if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "${RED}✗ Failed:${NC} $FAILED_COUNT"
    echo ""
    echo -e "${RED}Failed sessions:${NC}"
    for session in "${FAILED_SESSIONS[@]}"; do
        echo -e "  - $session"
    done
fi

echo ""
echo -e "${YELLOW}Total time:${NC} ${TOTAL_MIN}m ${TOTAL_SEC}s"
echo ""

# Exit with error if any session failed
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
fi

exit 0
