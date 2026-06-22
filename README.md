# Firewalla MQTT Bridge

A Home Assistant Supervisor add-on that bridges Firewalla network data to an MQTT broker for Home Assistant dashboards.

## Features

- **Real-time network monitoring**: Throughput, connections, device status
- **Device inventory**: Online/offline status, traffic counters, open ports
- **Security alerts**: Firewalla alarms and events
- **Data usage**: Monthly and yearly bandwidth statistics
- **Speedtest results**: Latest and historical speedtest data
- **Box health**: Model, version, uptime, public IP

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

## Installation

1. Add this repository to your Home Assistant Supervisor:
   ```
   https://github.com/adamradloff/network-ops
   ```

2. Install the "Firewalla MQTT Bridge" add-on

3. Configure the add-on settings (MQTT broker, Firewalla IP, etc.)

4. Copy your Firewalla credentials to the add-on's config share:
   - `etp.private.pem`
   - `etp.public.pem`
   - `fwgroup.json`
   - `etp_token.txt`

5. Start the add-on

## Home Assistant Integration

Once the add-on is running, configure Home Assistant's MQTT integration to subscribe to the `firewalla/` topics. You can then create sensors, dashboards, and automations using the data.

Example sensor configuration:
```yaml
sensor:
  - name: "Firewalla Download Speed"
    state_topic: "firewalla/network/live_stats"
    value_template: "{{ value_json.downloadMbps }}"
    unit_of_measurement: "Mbps"
```

## Notes

- The add-on runs as a non-root user for security
- No ports are exposed externally (publisher-only)
- Health check verifies MQTT connectivity
- Credentials are mounted via the config share (read-only)
