ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM ${BUILD_FROM}

# Python + Dependencies
RUN apk add --no-cache python3 py3-pip

# App reinkopieren
WORKDIR /app
COPY app /app

# Damit Python vendor/ findet
ENV PYTHONPATH=/app/vendor

# Browserpfad für Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/app/browsers

# Startscript
CMD ["python3", "/app/main.py"]
