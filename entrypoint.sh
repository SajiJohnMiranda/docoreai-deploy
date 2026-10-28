#!/bin/sh
set -e

if [ -z "$DOCOREAI_CLIENT_ENV_ID" ]; then
    echo "ERROR: DOCOREAI_CLIENT_ENV_ID is not set."
    echo "  Example: DOCOREAI_CLIENT_ENV_ID=hsbc_prod"
    exit 1
fi

# Parse client and environment from DOCOREAI_CLIENT_ENV_ID (e.g. hsbc_prod -> hsbc, prod)
CLIENT=$(echo "$DOCOREAI_CLIENT_ENV_ID" | cut -d_ -f1)
ENV=$(echo "$DOCOREAI_CLIENT_ENV_ID" | cut -d_ -f2)

if [ -z "$CLIENT" ] || [ -z "$ENV" ]; then
    echo "ERROR: DOCOREAI_CLIENT_ENV_ID must be in the format {client}_{env}, e.g. hsbc_prod"
    exit 1
fi

CONFIG_FILE="/app/configs/clients/$CLIENT/$CLIENT-$ENV.csv"
PROMPTS_FILE="/app/prompts/$CLIENT-$ENV.csv"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    exit 1
fi

if [ ! -f "$PROMPTS_FILE" ]; then
    echo "ERROR: Prompts file not found: $PROMPTS_FILE"
    exit 1
fi

echo "Starting DoCoreAI for client=$CLIENT env=$ENV"

mkdir -p /app/data
docoreai init
python /app/apply_config.py
docoreai start &

# Wait until DoCoreAI marks itself ready (polls every 2s, max 60s)
for i in $(seq 1 30); do
    docoreai status 2>/dev/null | grep -q "running" && break
    sleep 2
done

exec python /app/groq.py "$PROMPTS_FILE" 100
