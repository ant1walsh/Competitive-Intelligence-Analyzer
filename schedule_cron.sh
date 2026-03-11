#!/bin/bash
# =============================================================================
# Cron Manager for Daily Competitive Intelligence Agent
# =============================================================================
# Usage:
#   bash schedule_cron.sh install    - Install the daily 7 AM cron job
#   bash schedule_cron.sh remove     - Remove the cron job
#   bash schedule_cron.sh list       - Show current cron jobs
#   bash schedule_cron.sh view-log   - Tail the agent log in real-time
#   bash schedule_cron.sh run        - Run the agent immediately (manual trigger)
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SCRIPT="$SCRIPT_DIR/daily_competitive_intel.py"
LOG_FILE="$SCRIPT_DIR/agent.log"
CRON_TAG="# daily-competitive-intel"

# Detect python3 path
PYTHON=$(which python3)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
check_env() {
    local missing=()
    [[ -z "$FRIENDLI_API_KEY" ]] && missing+=("FRIENDLI_API_KEY")
    [[ -z "$SERPAPI_KEY" ]] && missing+=("SERPAPI_KEY")
    [[ -z "$SLACK_WEBHOOK_URL" ]] && missing+=("SLACK_WEBHOOK_URL")
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "ERROR: The following environment variables are not set:"
        for var in "${missing[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Add them to your ~/.zshrc and run: source ~/.zshrc"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
install() {
    check_env

    # Check if already installed
    if crontab -l 2>/dev/null | grep -q "$CRON_TAG"; then
        echo "Cron job already installed. Run 'bash schedule_cron.sh remove' first to reinstall."
        exit 0
    fi

    CRON_LINE="0 7 * * * cd \"$SCRIPT_DIR\" && FRIENDLI_API_KEY=\"$FRIENDLI_API_KEY\" SERPAPI_KEY=\"$SERPAPI_KEY\" SLACK_WEBHOOK_URL=\"$SLACK_WEBHOOK_URL\" $PYTHON \"$AGENT_SCRIPT\" >> \"$LOG_FILE\" 2>&1 $CRON_TAG"

    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -

    echo "✅ Cron job installed — agent will run daily at 7:00 AM."
    echo "   Log file: $LOG_FILE"
    echo ""
    echo "To verify: bash schedule_cron.sh list"
}

remove() {
    if ! crontab -l 2>/dev/null | grep -q "$CRON_TAG"; then
        echo "No cron job found to remove."
        exit 0
    fi
    crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab -
    echo "✅ Cron job removed."
}

list() {
    echo "=== Current cron jobs ==="
    crontab -l 2>/dev/null || echo "(no cron jobs)"
}

view_log() {
    if [[ ! -f "$LOG_FILE" ]]; then
        echo "Log file not found: $LOG_FILE"
        echo "The agent hasn't run yet, or the log path is different."
        exit 1
    fi
    echo "=== Tailing $LOG_FILE (Ctrl+C to stop) ==="
    tail -f "$LOG_FILE"
}

run_now() {
    check_env
    echo "=== Running agent now ==="
    "$PYTHON" "$AGENT_SCRIPT"
}

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
case "$1" in
    install)   install ;;
    remove)    remove ;;
    list)      list ;;
    view-log)  view_log ;;
    run)       run_now ;;
    *)
        echo "Usage: bash schedule_cron.sh [install|remove|list|view-log|run]"
        echo ""
        echo "  install   Install the daily 7 AM cron job"
        echo "  remove    Remove the cron job"
        echo "  list      Show all current cron jobs"
        echo "  view-log  Tail the agent log in real-time"
        echo "  run       Run the agent immediately"
        exit 1
        ;;
esac
