#!/bin/ash
# Firewalla MQTT Bridge - Container initialization
# This script runs when the container starts

set -e

echo "[Init] Setting up Firewalla MQTT Bridge"

# Ensure credentials directory exists and has correct permissions
if [ -d "/app/credentials" ]; then
    chmod 700 /app/credentials
    chmod 600 /app/credentials/*
    echo "[Init] Credentials directory configured"
else
    echo "[Init] WARNING: Credentials directory not found at /app/credentials"
    echo "[Init] Please mount your Firewalla credentials via the 'config' share"
fi

# Verify MQTT broker connectivity
MQTT_BROKER="${MQTT_BROKER:-10.100.255.22}"
MQTT_PORT="${MQTT_PORT:-1833}"

echo "[Init] Testing MQTT broker connectivity at ${MQTT_BROKER}:${MQTT_PORT}"
if command -v nc &> /dev/null; then
    if echo "" | nc -z -w 5 "${MQTT_BROKER}" "${MQTT_PORT}" 2>/dev/null; then
        echo "[Init] MQTT broker is reachable"
    else
        echo "[Init] WARNING: Cannot reach MQTT broker at ${MQTT_BROKER}:${MQTT_PORT}"
        echo "[Init] The bridge will retry connection on startup"
    fi
else
    echo "[Init] nc not available, skipping broker connectivity test"
fi

echo "[Init] Setup complete"
