FROM python:3.12-slim

# Fixa a versão do Chrome: instalar sempre a stable do dia faz o ambiente mudar entre
# builds sem alteração de código, e o comportamento do fingerprint varia com a versão.
ARG CHROME_VERSION=140.0.7339.207

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CHROME_PROFILE_DIR=/data/chrome-profile \
    CHROME_EXECUTABLE=/opt/chrome/chrome

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl unzip \
        xvfb xauth \
        libgl1-mesa-dri libglx-mesa0 libegl-mesa0 \
        fonts-liberation fonts-noto-color-emoji \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project \
    && uv run patchright install-deps chromium \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/chrome.zip \
        "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" \
    && unzip -q /tmp/chrome.zip -d /opt \
    && mv /opt/chrome-linux64 /opt/chrome \
    && rm /tmp/chrome.zip \
    && /opt/chrome/chrome --version

COPY api ./api
COPY bot ./bot
COPY core ./core
COPY docker-entrypoint.sh ./

RUN chmod +x docker-entrypoint.sh && mkdir -p /data/chrome-profile

ENV PATH="/app/.venv/bin:$PATH" \
    PORT=8000

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
