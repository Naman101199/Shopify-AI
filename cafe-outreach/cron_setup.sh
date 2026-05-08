#!/bin/bash
# Sets up a daily cron job to run the outreach pipeline at 9:00 AM.
# Run once: bash cron_setup.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"
LOG_FILE="$SCRIPT_DIR/logs/pipeline.log"

CRON_JOB="0 9 * * * cd $SCRIPT_DIR && $PYTHON pipeline.py >> $LOG_FILE 2>&1"

# Add to crontab without duplicating
( crontab -l 2>/dev/null | grep -v "pipeline.py"; echo "$CRON_JOB" ) | crontab -

echo "Cron job added successfully."
echo "The pipeline will run every day at 9:00 AM."
echo "Logs: $LOG_FILE"
echo ""
echo "To verify: crontab -l"
echo "To remove: crontab -e (delete the pipeline.py line)"
