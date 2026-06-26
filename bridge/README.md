# Firewalla MQTT Bridge — Docker

Polls the Firewalla box API on a configurable interval and publishes network data to an MQTT broker. Runs as a standalone Docker container with no Home Assistant Supervisor required.

## Prerequisites

- Docker + Docker Compose on your host
- A running MQTT broker (e.g. Mosquitto) reachable from the container
- Node.js 18+ (only needed to run the one-time pairing script)

## Pairing

Before starting the container you need to pair this machine with your Firewalla box. A pairing script at the root of the repo handles the whole process — it generates a key pair, registers with the Firewalla API, and writes the four credential files automatically.

**In the Firewalla app, before running the script:**

1. Tap your box → Settings → Advanced → Allow Additional Pairing
2. Enable **Additional Pairing** — a QR code will appear
3. Screenshot or scan the QR to get its raw JSON value

**Then run:**

```bash
# From the repo root
node pair.mjs
```

The script will prompt for:

- An email address (used as a label in the app — any address works)
- The QR code JSON you copied from the app
- Your Firewalla box LAN IP (default `192.168.1.1`)

It polls the Firewalla API until the box confirms the pairing (up to 60 seconds), then writes the credential files:

```text
bridge/credentials/
├── etp.private.pem      # RSA private key
├── etp.public.pem       # RSA public key
├── fwgroup.json         # Box group identity
└── etp_token.txt        # ETP bearer token
```

All files are written with mode `0600`. The credentials directory is bind-mounted read-only into the container.

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/g0ldfngr/Firewalla-MQTT-Bridge.git
cd Firewalla-MQTT-Bridge

# 2. Pair with your Firewalla box (writes bridge/credentials/ automatically)
node pair.mjs

# 3. Configure the bridge environment
cp bridge/.env.example bridge/.env
$EDITOR bridge/.env     # set MQTT_BROKER, FIREWALLA_IP, etc.

# 4. Build and start
cd bridge
docker compose up -d --build

# 5. Tail logs to confirm it's working
docker compose logs -f
```

## Configuration

All options are set via environment variables in `bridge/.env`:

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
cd bridge && docker compose up -d --build
```

## Troubleshooting

**Container exits immediately** — check that all four credential files exist in `bridge/credentials/` and are readable. Re-run `node pair.mjs` from the repo root to regenerate them.

**Pairing script times out** — make sure Additional Pairing is still enabled in the Firewalla app when the script is polling. The QR code expires; if it does, disable and re-enable Additional Pairing to get a fresh one.

**"Cannot reach MQTT broker"** — verify `MQTT_BROKER` in `.env` is correct and the broker is up. The container uses bridge networking by default; make sure the broker IP is reachable from within Docker (use the host's LAN IP, not `localhost`).

**No data after first run** — tail the logs with `docker compose logs -f` and look for `[Bridge] Collection complete.` If you see API errors, your credential files may be expired — re-run `node pair.mjs` to re-pair.
