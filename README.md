# Firewalla MQTT Bridge

Bridge Firewalla network telemetry into Home Assistant.

## Architecture

```
Firewalla Box (10.100.255.1)
    ↓ node-firewalla library (ETP API, port 8833)
Firewalla-to-MQTT Bridge (Supervisor add-on)
    ↓ MQTT publish (QoS 1, retain)
MQTT Broker (e.g. mosquitto on 10.100.255.22:1833)
    ↓ MQTT subscribe
Home Assistant (HACS integration → sensors, binary sensors, device trackers)
```

## Installation

### Step 1: Install the Bridge (Supervisor Add-on)

The bridge publishes Firewalla data to MQTT. Install it from the Supervisor Add-on Store:

1. Add this repository to your Home Assistant Supervisor:
   ```
   https://github.com/g0ldfngr/Firewalla-MQTT-Bridge
   ```
2. Install the "Firewalla MQTT Bridge" add-on
3. Configure the add-on settings (MQTT broker, Firewalla IP, etc.)
4. Copy your Firewalla credentials to the add-on's config share:
   - `etp.private.pem`
   - `etp.public.pem`
   - `fwgroup.json`
   - `etp_token.txt`
5. Start the add-on

### Step 2: Install the HACS Integration

The integration consumes MQTT data and creates native HA entities. **Use the `hacs` branch:**

1. In HACS → Custom Repositories → add this repo
2. Set the **repository type** to `integration`
3. Set the **branch** to `hacs`
4. Install and restart Home Assistant
5. Go to Settings → Devices & Services → Add Integration → "Firewalla MQTT Bridge"
6. Configure your MQTT broker and Firewalla IP

## MQTT Topics

| Topic | Description |
|-------|-------------|
| `firewalla/network/status` | Network health, connection type, public IP |
| `firewalla/network/live_stats` | Real-time throughput and connections |
| `firewalla/network/hosts_summary` | Online/offline device counts |
| `firewalla/network/hosts` | Full device inventory |
| `firewalla/network/host/<mac>` | Per-device traffic and status |
| `firewalla/network/alarms_summary` | Active alarm count |
| `firewalla/network/alarms` | Security alerts list |
| `firewalla/network/usage` | Monthly data usage |
| `firewalla/network/usage/yearly` | Yearly usage history |
| `firewalla/network/speedtest` | Speedtest results |
| `firewalla/network/box_info` | Box identity and features |

## HACS Entities Created

### Sensors
- Public IP, Connection Type
- Download/Upload Speed (Mbps)
- Active/Total Connections
- Online/Offline/Total Devices
- Active Alarms
- Uptime, Model, Version
- Download/Upload Usage (Bytes)
- Speedtest Download/Upload/Latency

### Binary Sensors
- Cloud Connected
- Booting Complete
- Per-device Online status

### Device Trackers
- Per-device presence detection (source_type: router)

### Text Entities
- Per-device name

### Number Entities
- Collect Interval (30-3600s)

### Services
- `firewalla.rescan` — Force a data refresh
- `firewalla.force_update` — Force all entities to update

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `mqtt_broker` | `10.100.255.22` | MQTT broker address |
| `mqtt_port` | `1833` | MQTT broker port |
| `mqtt_prefix` | `firewalla` | MQTT topic prefix |
| `mqtt_username` | `mosquitto` | MQTT broker username |
| `mqtt_password` | (empty) | MQTT broker password |
| `firewalla_ip` | `10.100.255.1` | Firewalla box IP |
| `collect_interval` | `60` | Collection interval in seconds |

## Notes

- The add-on runs as a non-root user for security
- No ports are exposed externally (publisher-only)
- Health check verifies MQTT connectivity
- Credentials are mounted via the config share (read-only)
- HACS integration requires the add-on (or any Firewalla-to-MQTT bridge) running
- **Branch `main`** — Supervisor add-on only
- **Branch `hacs`** — HACS integration only (clean `custom_components/` layout)
