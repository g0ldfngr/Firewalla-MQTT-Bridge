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
TOPIC_NETWORK_MONITOR: Final = "network/monitor"
TOPIC_DATA_PLAN: Final = "network/data_plan"

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
        "key": "wan1_download_bytes",
        "name": "WAN1 Download Usage",
        "topic": "network/usage/wan/eth0",
        "value_template": "{{ value_json.downloadBytes }}",
        "unit_of_measurement": "B",
        "device_class": "data_size",
        "state_class": "total_increasing",
    },
    {
        "key": "wan1_upload_bytes",
        "name": "WAN1 Upload Usage",
        "topic": "network/usage/wan/eth0",
        "value_template": "{{ value_json.uploadBytes }}",
        "unit_of_measurement": "B",
        "device_class": "data_size",
        "state_class": "total_increasing",
    },
    {
        "key": "wan2_download_bytes",
        "name": "WAN2 Download Usage",
        "topic": "network/usage/wan/eth1",
        "value_template": "{{ value_json.downloadBytes }}",
        "unit_of_measurement": "B",
        "device_class": "data_size",
        "state_class": "total_increasing",
    },
    {
        "key": "wan2_upload_bytes",
        "name": "WAN2 Upload Usage",
        "topic": "network/usage/wan/eth1",
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
    {
        "key": "cpu_load_5",
        "name": "CPU Load (5m)",
        "topic": TOPIC_SYSTEM_METRICS,
        "value_template": "{{ value_json.load5 }}",
        "state_class": "measurement",
        "entity_category": "diagnostic",
    },
    {
        "key": "cpu_load_15",
        "name": "CPU Load (15m)",
        "topic": TOPIC_SYSTEM_METRICS,
        "value_template": "{{ value_json.load15 }}",
        "state_class": "measurement",
        "entity_category": "diagnostic",
    },
    # WAN1 (eth0) additional detail
    {
        "key": "wan1_gateway",
        "name": "WAN1 Gateway",
        "topic": "network/wan/eth0",
        "value_template": "{{ value_json.gateway }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "wan1_conn_type",
        "name": "WAN1 Connection Type",
        "topic": "network/wan/eth0",
        "value_template": "{{ value_json.connType }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "wan1_speedtest_jitter",
        "name": "WAN1 Speedtest Jitter",
        "topic": "network/speedtest/eth0",
        "value_template": "{{ value_json.latest.jitter if value_json.latest else '' }}",
        "unit_of_measurement": "ms",
        "state_class": "measurement",
    },
    {
        "key": "wan1_speedtest_packet_loss",
        "name": "WAN1 Speedtest Packet Loss",
        "topic": "network/speedtest/eth0",
        "value_template": "{{ value_json.latest.packetLoss if value_json.latest else '' }}",
        "unit_of_measurement": "%",
        "state_class": "measurement",
    },
    # WAN2 (eth1) additional detail
    {
        "key": "wan2_gateway",
        "name": "WAN2 Gateway",
        "topic": "network/wan/eth1",
        "value_template": "{{ value_json.gateway }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "wan2_conn_type",
        "name": "WAN2 Connection Type",
        "topic": "network/wan/eth1",
        "value_template": "{{ value_json.connType }}",
        "entity_category": "diagnostic",
    },
    {
        "key": "wan2_speedtest_jitter",
        "name": "WAN2 Speedtest Jitter",
        "topic": "network/speedtest/eth1",
        "value_template": "{{ value_json.latest.jitter if value_json.latest else '' }}",
        "unit_of_measurement": "ms",
        "state_class": "measurement",
    },
    {
        "key": "wan2_speedtest_packet_loss",
        "name": "WAN2 Speedtest Packet Loss",
        "topic": "network/speedtest/eth1",
        "value_template": "{{ value_json.latest.packetLoss if value_json.latest else '' }}",
        "unit_of_measurement": "%",
        "state_class": "measurement",
    },
    # Data plan
    {
        "key": "data_plan_total_gb",
        "name": "Data Plan Total",
        "topic": TOPIC_DATA_PLAN,
        "value_template": "{{ value_json.totalGB }}",
        "unit_of_measurement": "B",
        "device_class": "data_size",
        "entity_category": "diagnostic",
    },
    {
        "key": "data_plan_reset_day",
        "name": "Data Plan Reset Day",
        "topic": TOPIC_DATA_PLAN,
        "value_template": "{{ value_json.resetDay }}",
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
    {
        "key": "wan1_active",
        "name": "WAN1 Active",
        "topic": "network/wan/eth0",
        "value_template": "{{ value_json.active }}",
        "device_class": "connectivity",
    },
    {
        "key": "wan1_ready",
        "name": "WAN1 Ready",
        "topic": "network/wan/eth0",
        "value_template": "{{ value_json.ready }}",
        "device_class": "connectivity",
    },
    {
        "key": "wan2_active",
        "name": "WAN2 Active",
        "topic": "network/wan/eth1",
        "value_template": "{{ value_json.active }}",
        "device_class": "connectivity",
    },
    {
        "key": "wan2_ready",
        "name": "WAN2 Ready",
        "topic": "network/wan/eth1",
        "value_template": "{{ value_json.ready }}",
        "device_class": "connectivity",
    },
    {
        "key": "data_plan_enabled",
        "name": "Data Plan Enabled",
        "topic": TOPIC_DATA_PLAN,
        "value_template": "{{ value_json.enabled }}",
        "entity_category": "diagnostic",
    },
]
