#!/bin/sh
set -e

if [ -z "$DOCOREAI_CLIENT_ENV_ID" ]; then
    echo "ERROR: DOCOREAI_CLIENT_ENV_ID is not set."
    echo "  Example: DOCOREAI_CLIENT_ENV_ID=hsbc_prod"
    exit 1
fi

CLIENT=$(echo "$DOCOREAI_CLIENT_ENV_ID" | cut -d_ -f1)
ENV=$(echo "$DOCOREAI_CLIENT_ENV_ID" | cut -d_ -f2)

if [ -z "$CLIENT" ] || [ -z "$ENV" ]; then
    echo "ERROR: DOCOREAI_CLIENT_ENV_ID must be in the format {client}_{env}, e.g. hsbc_prod"
    exit 1
fi

CONFIG_FILE="/app/configs/clients/$CLIENT/$CLIENT-$ENV.csv"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "Starting DoCoreAI for client=$CLIENT env=$ENV"

mkdir -p /app/data
docoreai init
python /app/apply_config.py
docoreai start &

for i in $(seq 1 30); do
    docoreai status 2>/dev/null | grep -q "running" && break
    sleep 2
done

exec python /app/groq.py /app/prompts.csv 100
