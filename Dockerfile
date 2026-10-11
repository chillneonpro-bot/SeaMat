FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SEAMAT_HOST=0.0.0.0 \
    SEAMAT_PORT=8088 \
    SEAMAT_SHOW_BROWSER=0

WORKDIR /app

COPY requirements-lock.txt ./
RUN python -m pip install --no-cache-dir -r requirements-lock.txt

COPY main.py ./
COPY seamat ./seamat
COPY data/evidence ./data/evidence
COPY examples ./examples

RUN mkdir -p /app/data/documents /app/data/backups && \
    adduser --disabled-password --gecos "" --uid 10001 seamat && \
    chown -R seamat:seamat /app

USER seamat
EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8088/health', timeout=4)"

CMD ["python", "main.py"]
