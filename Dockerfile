FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip && \
    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

COPY . .

RUN useradd -m -u 10001 afra && \
    mkdir -p /var/lib/afra-runtime && \
    chown -R afra:afra /app /var/lib/afra-runtime

USER afra

EXPOSE 8080

ENV AFRA_ENVIRONMENT=production
ENV AFRA_HEALTH_PORT=8080
ENV AFRA_STATE_DIR=/var/lib/afra-runtime

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1

CMD ["python", "-m", "divar_bot"]
