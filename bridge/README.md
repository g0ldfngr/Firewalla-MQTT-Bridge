# Firewalla MQTT Bridge — Docker

Polls the Firewalla box API on a configurable interval and publishes network data to an MQTT broker. Runs as a standalone Docker container with no Home Assistant Supervisor required.

## Prerequisites

- Docker + Docker Compose on your host
- A running MQTT broker (e.g. Mosquitto) reachable from the container
- Firewalla credential files exported from your Firewalla account (see below)

## Credential Files

The bridge authenticates with your Firewalla box using four files. Place them all in `bridge/credentials/` before starting the container:

| File | Description |
|---|---|
| `etp.private.pem` | ETP private key |
| `etp.public.pem` | ETP public key |
| `fwgroup.json` | Group identity (gid, eid, aid, symmetricKeyCipher, name) |
| `etp_token.txt` | ETP bearer token |

These files come from the Firewalla MSP / developer API setup. See the [node-firewalla](https://github.com/firewalla/node-firewalla) docs for how to obtain them.

## Installation

```bash
# 1. Clone the repo (or just copy the bridge/ directory)
git clone https://github.com/g0ldfngr/Firewalla-MQTT-Bridge.git
cd Firewalla-MQTT-Bridge/bridge

# 2. Create the credentials directory and drop in your four credential files
mkdir credentials
cp /path/to/etp.private.pem   credentials/
cp /path/to/etp.public.pem    credentials/
cp /path/to/fwgroup.json      credentials/
cp /path/to/etp_token.txt     credentials/

# 3. Configure environment
cp .env.example .env
$EDITOR .env          # set MQTT_BROKER, FIREWALLA_IP, credentials, etc.

# 4. Build and start
docker compose up -d --build

# 5. Tail logs to confirm it's working
docker compose logs -f
```

## Configuration

All options are set via environment variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `MQTT_BROKER` | `tcp://localhost:1883` | Broker URL (`tcp://` plain, `ssl://` for TLS) |
| `MQTT_PREFIX` | `firewalla` | Topic prefix for all published messages |
| `MQTT_USERNAME` | *(empty)* | MQTT username — leave blank if no auth |
| `MQTT_PASSWORD` | *(empty)* | MQTT password |
| `FIREWALLA_IP` | `192.168.0.1` | LAN IP of your Firewalla box |
| `COLLECT_INTERVAL` | `60` | Poll interval in seconds (min 30, max 3600) |

## MQTT Topics

All topics are prefixed with `MQTT_PREFIX` (default: `firewalla`).

| Topic | Description |
|---|---|
| `firewalla/box_info` | Model, firmware version, uptime, public IP |
| `firewalla/box/features` | Runtime feature flags (adblock, unbound, etc.) |
| `firewalla/network/status` | Connection type, gateway, DNS, cloud connected |
| `firewalla/network/live_stats` | Real-time download/upload Mbps, active connections |
| `firewalla/network/hosts_summary` | Total / online / offline device counts |
| `firewalla/network/hosts` | Full device inventory (online and offline lists) |
| `firewalla/network/host/<mac>` | Per-device presence, IP, and traffic (MAC colons replaced with `_`) |
| `firewalla/network/alarms_summary` | Total and active alarm counts |
| `firewalla/network/alarms` | Full alarm list |
| `firewalla/network/usage` | Current month upload/download bytes |
| `firewalla/network/usage/yearly` | Last 12 months of data usage |
| `firewalla/network/speedtest` | Latest speedtest result + 10-entry history |

All messages are published with `qos: 1` and `retain: true`, so your MQTT client will receive the last known value immediately on subscribe.

## Integrating with Home Assistant

If you want HA entities from these topics, this repo also includes a HACS custom integration (`custom_components/firewalla/`) that auto-discovers sensors, binary sensors, and device trackers from the MQTT data. See the root [README](../README.md) for HACS install instructions.

Alternatively, the `configuration.yaml` in the repo's git history (commit `f9815a0`) has a full set of manually-defined MQTT sensor entries you can paste into your HA config.

## Updating

```bash
git pull
docker compose up -d --build
```

## Troubleshooting

**Container exits immediately** — check that all four credential files exist in `credentials/` and are readable.

**"Cannot reach MQTT broker"** — verify `MQTT_BROKER` in `.env` is correct and the broker is up. The container uses bridge networking by default; make sure the broker IP is reachable from within Docker (use the host's LAN IP, not `localhost`).

**No data after first run** — tail the logs with `docker compose logs -f` and look for `[Bridge] Collection complete.` If you see API errors, your credential files may be expired or incorrect.
