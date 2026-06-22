"""Constants for the Firewalla MQTT Bridge integration."""

from typing import Final

DOMAIN: Final = "firewalla"
NAME: Final = "Firewalla MQTT Bridge"
MANUFACTURER: Final = "Firewalla"

# Config entry keys
CONF_MQTT_BROKER: Final = "mqtt_broker"
CONF_MQTT_PORT: Final = "mqtt_port"
CONF_MQTT_PREFIX: Final = "mqtt_prefix"
CONF_MQTT_USERNAME: Final = "mqtt_username"
CONF_MQTT_PASSWORD: Final = "mqtt_password"
CONF_FIREWALLA_IP: Final = "firewalla_ip"

# Defaults
DEFAULT_MQTT_PREFIX: Final = "firewalla"
DEFAULT_MQTT_PORT: Final = 1833

# MQTT topic suffixes
TOPIC_STATUS: Final = "network/status"
TOPIC_LIVE_STATS: Final = "network/live_stats"
TOPIC_HOSTS_SUMMARY: Final = "network/hosts_summary"
TOPIC_HOSTS: Final = "network/hosts"
TOPIC_HOST: Final = "network/host"
TOPIC_ALARMS_SUMMARY: Final = "network/alarms_summary"
TOPIC_ALARMS: Final = "network/alarms"
TOPIC_USAGE: Final = "network/usage"
TOPIC_SPEEDTEST: Final = "network/speedtest"
TOPIC_BOX_INFO: Final = "box_info"
TOPIC_BOX_FEATURES: Final = "box/features"

# Sensor entity descriptions
SENSOR_ENTITIES: Final = [
    {
        "key": "public_ip",
        "name": "Public IP",
        "topic": TOPIC_STATUS,
        "value_template": "{{ value_json.publicIp }}",
        "device_class": "text",
        "entity_category": "diagnostic",
    },
    {
        "key": "connection_type",
        "name": "Connection Type",
        "topic": TOPIC_STATUS,
        "value_template": "{{ value_json.connectionType }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "download_mbps",
        "name": "Download Speed",
        "topic": TOPIC_LIVE_STATS,
        "value_template": "{{ value_json.downloadMbps }}",
        "unit_of_measurement": "Mbps",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "upload_mbps",
        "name": "Upload Speed",
        "topic": TOPIC_LIVE_STATS,
        "value_template": "{{ value_json.uploadMbps }}",
        "unit_of_measurement": "Mbps",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "active_connections",
        "name": "Active Connections",
        "topic": TOPIC_LIVE_STATS,
        "value_template": "{{ value_json.activeConnections }}",
        "state_class": "measurement",
    },
    {
        "key": "total_connections",
        "name": "Total Connections",
        "topic": TOPIC_LIVE_STATS,
        "value_template": "{{ value_json.totalConnections }}",
        "state_class": "measurement",
    },
    {
        "key": "online_devices",
        "name": "Online Devices",
        "topic": TOPIC_HOSTS_SUMMARY,
        "value_template": "{{ value_json.online }}",
        "state_class": "measurement",
    },
    {
        "key": "offline_devices",
        "name": "Offline Devices",
        "topic": TOPIC_HOSTS_SUMMARY,
        "value_template": "{{ value_json.offline }}",
        "state_class": "measurement",
    },
    {
        "key": "total_devices",
        "name": "Total Devices",
        "topic": TOPIC_HOSTS_SUMMARY,
        "value_template": "{{ value_json.total }}",
        "state_class": "measurement",
    },
    {
        "key": "active_alarms",
        "name": "Active Alarms",
        "topic": TOPIC_ALARMS_SUMMARY,
        "value_template": "{{ value_json.active }}",
        "state_class": "measurement",
    },
    {
        "key": "uptime",
        "name": "Uptime",
        "topic": TOPIC_BOX_INFO,
        "value_template": "{{ value_json.uptime }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "model",
        "name": "Model",
        "topic": TOPIC_BOX_INFO,
        "value_template": "{{ value_json.model }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "version",
        "name": "Version",
        "topic": TOPIC_BOX_INFO,
        "value_template": "{{ value_json.version }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "download_bytes",
        "name": "Download Usage",
        "topic": TOPIC_USAGE,
        "value_template": "{{ value_json.downloadBytes }}",
        "unit_of_measurement": "Bytes",
        "device_class": "data_size",
        "state_class": "total_increasing",
    },
    {
        "key": "upload_bytes",
        "name": "Upload Usage",
        "topic": TOPIC_USAGE,
        "value_template": "{{ value_json.uploadBytes }}",
        "unit_of_measurement": "Bytes",
        "device_class": "data_size",
        "state_class": "total_increasing",
    },
    {
        "key": "speedtest_download",
        "name": "Speedtest Download",
        "topic": TOPIC_SPEEDTEST,
        "value_template": "{{ value_json.latest.downloadMbps if value_json.latest else '' }}",
        "unit_of_measurement": "Mbps",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "speedtest_upload",
        "name": "Speedtest Upload",
        "topic": TOPIC_SPEEDTEST,
        "value_template": "{{ value_json.latest.uploadMbps if value_json.latest else '' }}",
        "unit_of_measurement": "Mbps",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "speedtest_latency",
        "name": "Speedtest Latency",
        "topic": TOPIC_SPEEDTEST,
        "value_template": "{{ value_json.latest.latency if value_json.latest else '' }}",
        "unit_of_measurement": "ms",
        "device_class": "latency",
        "state_class": "measurement",
    },
]

# Binary sensor entities
BINARY_SENSOR_ENTITIES: Final = [
    {
        "key": "cloud_connected",
        "name": "Cloud Connected",
        "topic": TOPIC_BOX_INFO,
        "value_template": "{{ value_json.cloudConnected }}",
        "device_class": "connectivity",
    },
    {
        "key": "booting_complete",
        "name": "Booting Complete",
        "topic": TOPIC_BOX_INFO,
        "value_template": "{{ value_json.bootingComplete }}",
        "device_class": "running",
    },
]

# Text entities for per-device info
TEXT_ENTITIES: Final = [
    {
        "key": "device_name",
        "name": "Device Name",
        "topic_template": "network/host/{{ mac }}",
        "value_template": "{{ value_json.name }}",
        "entity_category": "diagnostic",
    },
]

# Number entities
NUMBER_ENTITIES: Final = [
    {
        "key": "collect_interval",
        "name": "Collect Interval",
        "topic": "firewalla/config/collect_interval",
        "min": 30,
        "max": 3600,
        "step": 30,
        "unit_of_measurement": "s",
        "entity_category": "config",
    },
]
