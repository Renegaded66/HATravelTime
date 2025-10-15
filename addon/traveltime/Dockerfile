FROM ghcr.io/home-assistant/amd64-base-debian:latest

# Systemabhängigkeiten inkl. python3-venv für virtuelle Umgebungen
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv chromium \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# main.py ins Image kopieren
COPY main.py .

# Virtuelles Environment erstellen
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Playwright + Browser installieren
RUN pip install --no-cache-dir playwright flask nest-asyncio waitress && playwright install chromium

# Service Script kopieren
COPY run.sh /etc/services.d/travel_time/run
RUN chmod +x /etc/services.d/travel_time/run
