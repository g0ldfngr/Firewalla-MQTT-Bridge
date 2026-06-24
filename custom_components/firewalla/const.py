"""Constants for the Firewalla MQTT Bridge integration."""

from typing import Final

DOMAIN: Final = "firewalla"
NAME: Final = "Firewalla MQTT Bridge"
MANUFACTURER: Final = "Firewalla"

# Config entry keys
CONF_MQTT_PREFIX: Final = "mqtt_prefix"
CONF_FIREWALLA_IP: Final = "firewalla_ip"

# Defaults
DEFAULT_MQTT_PREFIX: Final = "firewalla"

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
TOPIC_WAN: Final = "network/wan"
TOPIC_SYSTEM_METRICS: Final = "system/metrics"

# Sensor entity descriptions
SENSOR_ENTITIES: Final = [
    {
        "key": "public_ip",
        "name": "Public IP",
        "topic": TOPIC_STATUS,
        "value_template": "{{ value_json.publicIp }}",
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
        "key": "wan1_download_mbps",
        "name": "WAN1 Download Speed",
        "topic": "network/live_stats/wan/eth0",
        "value_template": "{{ value_json.downloadMbps }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "wan1_upload_mbps",
        "name": "WAN1 Upload Speed",
        "topic": "network/live_stats/wan/eth0",
        "value_template": "{{ value_json.uploadMbps }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "wan2_download_mbps",
        "name": "WAN2 Download Speed",
        "topic": "network/live_stats/wan/eth1",
        "value_template": "{{ value_json.downloadMbps }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "wan2_upload_mbps",
        "name": "WAN2 Upload Speed",
        "topic": "network/live_stats/wan/eth1",
        "value_template": "{{ value_json.uploadMbps }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
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
        "name": "Total Download Usage",
        "topic": TOPIC_USAGE,
        "value_template": "{{ value_json.downloadBytes }}",
        "unit_of_measurement": "B",
        "device_class": "data_size",
        "state_class": "total_increasing",
    },
    {
        "key": "upload_bytes",
        "name": "Total Upload Usage",
        "topic": TOPIC_USAGE,
        "value_template": "{{ value_json.uploadBytes }}",
        "unit_of_measurement": "B",
        "device_class": "data_size",
        "state_class": "total_increasing",
    },
    {
        "key": "speedtest_isp",
        "name": "Speedtest ISP",
        "topic": TOPIC_SPEEDTEST,
        "value_template": "{{ value_json.latest.isp if value_json.latest else '' }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "wan_count",
        "name": "WAN Interfaces",
        "topic": TOPIC_WAN,
        "value_template": "{{ value_json.count }}",
        "state_class": "measurement",
        "entity_category": "diagnostic",
    },
    # WAN 1 (eth0) sensors
    {
        "key": "wan1_public_ip",
        "name": "WAN1 Public IP",
        "topic": "network/wan/eth0",
        "value_template": "{{ value_json.publicIp }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "wan1_speedtest_download",
        "name": "WAN1 Speedtest Download",
        "topic": "network/speedtest/eth0",
        "value_template": "{{ value_json.latest.downloadMbps if value_json.latest else '' }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "wan1_speedtest_upload",
        "name": "WAN1 Speedtest Upload",
        "topic": "network/speedtest/eth0",
        "value_template": "{{ value_json.latest.uploadMbps if value_json.latest else '' }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "wan1_speedtest_latency",
        "name": "WAN1 Speedtest Latency",
        "topic": "network/speedtest/eth0",
        "value_template": "{{ value_json.latest.latency if value_json.latest else '' }}",
        "unit_of_measurement": "ms",
        "state_class": "measurement",
    },
    # WAN 2 (eth1) sensors
    {
        "key": "wan2_public_ip",
        "name": "WAN2 Public IP",
        "topic": "network/wan/eth1",
        "value_template": "{{ value_json.publicIp }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "wan2_speedtest_download",
        "name": "WAN2 Speedtest Download",
        "topic": "network/speedtest/eth1",
        "value_template": "{{ value_json.latest.downloadMbps if value_json.latest else '' }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "wan2_speedtest_upload",
        "name": "WAN2 Speedtest Upload",
        "topic": "network/speedtest/eth1",
        "value_template": "{{ value_json.latest.uploadMbps if value_json.latest else '' }}",
        "unit_of_measurement": "Mbit/s",
        "device_class": "data_rate",
        "state_class": "measurement",
    },
    {
        "key": "wan2_speedtest_latency",
        "name": "WAN2 Speedtest Latency",
        "topic": "network/speedtest/eth1",
        "value_template": "{{ value_json.latest.latency if value_json.latest else '' }}",
        "unit_of_measurement": "ms",
        "state_class": "measurement",
    },
    # System health
    {
        "key": "mem_usage_pct",
        "name": "Memory Usage",
        "topic": TOPIC_SYSTEM_METRICS,
        "value_template": "{{ value_json.memUsagePct }}",
        "unit_of_measurement": "%",
        "state_class": "measurement",
        "entity_category": "diagnostic",
    },
    {
        "key": "cpu_load_1",
        "name": "CPU Load (1m)",
        "topic": TOPIC_SYSTEM_METRICS,
        "value_template": "{{ value_json.load1 }}",
        "state_class": "measurement",
        "entity_category": "diagnostic",
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
