#!/usr/bin/env bash
set -euo pipefail

# bashio ist im Base-Image vorhanden
LISTEN_PORT="$(bashio::config 'listen_port')"

export ADDON_LISTEN_PORT="${LISTEN_PORT}"

# Health-Log
echo "[travel_time] Starting with port=${LISTEN_PORT} headless=${HEADLESS} browser=${BROWSER} slow_mo=${SLOW_MO}"

python3 /app/main.py
