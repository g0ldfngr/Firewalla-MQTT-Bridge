# Firewalla MQTT Bridge

Bridge Firewalla network telemetry into Home Assistant via MQTT.

## Architecture

```
Firewalla Box (192.168.0.1)
    ↓ node-firewalla library (ETP API, port 8833)
Firewalla-to-MQTT Bridge (Docker container)
    ↓ MQTT publish (QoS 1, retain)
MQTT Broker (e.g. Mosquitto on 192.168.0.100:1883)
    ↓ MQTT subscribe
Home Assistant (HACS integration → sensors, binary sensors, device trackers)
```

## Installation

### Step 1: Install the Bridge (Docker)

The bridge polls the Firewalla API and publishes data to MQTT. It runs as a standalone Docker container — no Home Assistant Supervisor required.

See [`bridge/README.md`](bridge/README.md) for full setup instructions including credential files, environment variables, and Docker Compose commands.

### Step 2: Install the HACS Integration

The integration subscribes to the MQTT topics published by the bridge and creates native HA entities.

1. In HACS → **Custom Repositories** → add this repo URL
2. Set the repository type to `Integration`
3. Install **Firewalla MQTT Bridge** and restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → Firewalla MQTT Bridge**
5. Configure the MQTT topic prefix (default: `firewalla`) and your Firewalla box IP

> The HACS integration uses Home Assistant's built-in MQTT integration for broker connectivity. Make sure the [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) is already configured in HA before adding this one.

## Dashboard

A pre-built Lovelace dashboard is included at [`dashboards/firewalla.yaml`](dashboards/firewalla.yaml).

Three views — no HACS frontend cards required, all standard HA card types:

| View | Contents |
|---|---|
| **Overview** | Status glance (cloud, WAN1/2, alarms, online devices), live throughput graphs, device counts, monthly usage |
| **WAN Details** | Per-WAN connection info (IP, gateway, type), speedtest results and history |
| **System** | CPU load gauges (1m/5m/15m), memory gauge, 24h history graphs, box info, data plan |

**Install:**

1. Go to **Settings → Dashboards → Add Dashboard**
2. Toggle **YAML mode** on
3. Paste the contents of `dashboards/firewalla.yaml`

> Entity IDs assume the default device name **"Firewalla"**. If yours differs, check your exact IDs at **Developer Tools → States** and filter by `firewalla`.

### Template Sensors (optional, recommended)

[`templates/firewalla.yaml`](templates/firewalla.yaml) provides human-readable formatting the dashboard uses for:

- **Uptime** — converts raw firmware seconds to `Xd Yh Zm` format
- **Monthly usage history-graph** — converts byte counters to GB for a readable Y-axis

**Install:**

1. Copy `templates/firewalla.yaml` into your HA config directory (e.g. `config/templates/firewalla.yaml`)
2. Add to `configuration.yaml`:

   ```yaml
   template: !include_dir_merge_list templates/
   ```

3. Restart Home Assistant
4. Edit `templates/firewalla.yaml` and replace `office_firewalla` with your entity prefix if different

Without the templates loaded the dashboard still works — the System view uses inline Jinja in a `markdown` card for uptime, and the monthly usage graph falls back to raw byte sensors.

## MQTT Topics

All topics are prefixed with `MQTT_PREFIX` (default: `firewalla`).

| Topic | Description |
|---|---|
| `firewalla/box_info` | Model, firmware version, uptime, cloud connected status |
| `firewalla/box/features` | Runtime feature flags (adblock, unbound, etc.) |
| `firewalla/network/status` | Overall network health, connection type, public IP |
| `firewalla/network/live_stats` | Real-time throughput and active connections |
| `firewalla/network/live_stats/wan/<intf>` | Per-WAN live download/upload Mbps |
| `firewalla/network/wan` | All WAN interfaces summary and count |
| `firewalla/network/wan/<intf>` | Per-WAN detail: IP, gateway, active/ready state, connection type |
| `firewalla/network/hosts_summary` | Online/offline/total device counts |
| `firewalla/network/hosts` | Full device inventory |
| `firewalla/network/host/<mac>` | Per-device traffic and presence (MAC colons replaced with `_`) |
| `firewalla/network/alarms_summary` | Active and total alarm counts |
| `firewalla/network/alarms` | Full alarm list |
| `firewalla/network/usage` | Current month upload/download bytes |
| `firewalla/network/usage/wan/<intf>` | Per-WAN monthly download/upload bytes |
| `firewalla/network/usage/yearly` | Last 12 months of data usage |
| `firewalla/network/speedtest` | Latest speedtest result and 10-entry history |
| `firewalla/network/speedtest/<intf>` | Per-WAN speedtest results |
| `firewalla/network/monitor` | Network monitor data |
| `firewalla/network/data_plan` | Data plan status, total GB, and billing reset day |
| `firewalla/system/metrics` | CPU load averages (1m/5m/15m) and memory usage % |

All messages are published with `qos: 1` and `retain: true`.

## Entities Created

### Sensors
| Entity | Source Topic |
|---|---|
| WAN1/WAN2 Download Speed (Mbit/s) | `network/live_stats/wan/eth0` / `eth1` |
| WAN1/WAN2 Upload Speed (Mbit/s) | `network/live_stats/wan/eth0` / `eth1` |
| WAN1/WAN2 Public IP | `network/wan/eth0` / `eth1` |
| WAN1/WAN2 Gateway | `network/wan/eth0` / `eth1` |
| WAN1/WAN2 Connection Type | `network/wan/eth0` / `eth1` |
| WAN1/WAN2 Download Usage (bytes) | `network/usage/wan/eth0` / `eth1` |
| WAN1/WAN2 Upload Usage (bytes) | `network/usage/wan/eth0` / `eth1` |
| WAN1/WAN2 Speedtest Download/Upload/Latency/Jitter/Packet Loss | `network/speedtest/eth0` / `eth1` |
| Online / Offline / Total Devices | `network/hosts_summary` |
| Active Alarms | `network/alarms_summary` |
| CPU Load (1m / 5m / 15m) | `system/metrics` |
| Memory Usage (%) | `system/metrics` |
| Uptime (seconds) | `box_info` |
| Model | `box_info` |
| Firmware Version | `box_info` |
| Speedtest ISP | `network/speedtest` |
| WAN Interface Count | `network/wan` |
| Data Plan Total / Reset Day | `network/data_plan` |

### Binary Sensors
- Cloud Connected
- Booting Complete
- WAN1 / WAN2 Active
- WAN1 / WAN2 Ready
- Data Plan Enabled
- Per-device Online status

### Device Trackers
- Per-device presence detection (`source_type: router`)

### Text Entities
- Per-device name (editable)

### Number Entities
- Collect Interval (30–3600 s)

### Services
- `firewalla.rescan` — force a data refresh
- `firewalla.force_update` — push all entities to update immediately

## Integration Configuration

| Option | Default | Description |
|---|---|---|
| `mqtt_prefix` | `firewalla` | MQTT topic prefix — must match `MQTT_PREFIX` set in the bridge |
| `firewalla_ip` | `192.168.0.1` | LAN IP of your Firewalla box |

The MQTT broker, port, and credentials are configured in the HA MQTT integration, not here.

## Bridge Configuration

See [`bridge/README.md`](bridge/README.md) for the full Docker environment variable reference.

| Variable | Default | Description |
|---|---|---|
| `MQTT_BROKER` | `tcp://localhost:1883` | Broker URL |
| `MQTT_PREFIX` | `firewalla` | Topic prefix |
| `MQTT_USERNAME` | *(empty)* | MQTT username |
| `MQTT_PASSWORD` | *(empty)* | MQTT password |
| `FIREWALLA_IP` | `192.168.0.1` | LAN IP of your Firewalla box |
| `COLLECT_INTERVAL` | `60` | Poll interval in seconds (min 30, max 3600) |

## Notes

- The bridge container runs as a non-root user
- All MQTT messages are retained so HA receives the last known state immediately on subscribe
- Dual WAN is supported (eth0/eth1); single-WAN setups will simply have empty WAN2 entities
- Per-device trackers and text entities are created dynamically from the device list
