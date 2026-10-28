FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libegl1 \
    libfontconfig1 \
    libgomp1 \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Install docoreai and groq, then remove heavy ML deps in the
# same layer so they never land in the final image.
RUN pip install --no-cache-dir docoreai groq && \
    pip uninstall -y torch torchvision torchaudio llmlingua 2>/dev/null || true

ENV DOCOREAI_ENV_PATH=/app/data
ENV DOCOREAI_CONFIG_DIR=/app/configs

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
COPY apply_config.py /app/apply_config.py
COPY groq.py /app/groq.py
COPY configs/ /app/configs/
COPY prompts/ /app/prompts/

RUN mkdir -p /app/data \
 && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
