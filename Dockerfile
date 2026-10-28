FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libegl1 \
    libfontconfig1 \
    libgomp1 \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir docoreai && \
    pip uninstall -y torch torchvision torchaudio llmlingua 2>/dev/null || true

ENV DOCOREAI_ENV_PATH=/app/data
ENV DOCOREAI_CONFIG_DIR=/app/configs

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
COPY apply_config.py /app/apply_config.py
COPY configs/ /app/configs/

RUN mkdir -p /app/data \
 && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
