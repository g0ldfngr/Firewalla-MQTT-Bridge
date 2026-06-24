#!/usr/bin/env node
/**
 * Firewalla-to-MQTT Bridge
 *
 * Pulls data from the Firewalla box API and publishes to an MQTT broker.
 *
 * Topics:
 *   firewalla/box_info              - Box identity & features
 *   firewalla/box/features          - Runtime feature flags
 *   firewalla/network/status        - Overall network health
 *   firewalla/network/live_stats    - Real-time throughput & connections
 *   firewalla/network/hosts_summary - Online/offline device counts
 *   firewalla/network/hosts         - Full device inventory
 *   firewalla/network/host/<mac>    - Per-device traffic/presence
 *   firewalla/network/alarms_summary
 *   firewalla/network/alarms
 *   firewalla/network/usage
 *   firewalla/network/usage/yearly
 *   firewalla/network/speedtest
 */

import mqtt from 'mqtt';
import {
  SecureUtil,
  FWGroup,
  NetworkService,
  HostService,
  AlarmService,
  InitService,
  FeatureService,
} from 'node-firewalla';
import fs from 'fs';
import path from 'path';

// ── Configuration ──────────────────────────────────────────────────────────

const MQTT_BROKER      = process.env.MQTT_BROKER      || 'tcp://localhost:1883';
const MQTT_PREFIX      = process.env.MQTT_PREFIX      || 'firewalla';
const MQTT_USERNAME    = process.env.MQTT_USERNAME    || '';
const MQTT_PASSWORD    = process.env.MQTT_PASSWORD    || '';
const FIREWALLA_IP     = process.env.FIREWALLA_IP     || '10.100.255.1';
const COLLECT_INTERVAL = parseInt(process.env.COLLECT_INTERVAL || '60', 10);
const KEYS_DIR         = process.env.FIREWALLA_KEYS_DIR || '/app/credentials';

// ── Load Credentials ───────────────────────────────────────────────────────

function loadCredentials() {
  const privateKey  = fs.readFileSync(path.join(KEYS_DIR, 'etp.private.pem'), 'utf8');
  const publicKey   = fs.readFileSync(path.join(KEYS_DIR, 'etp.public.pem'), 'utf8');
  const groupData   = JSON.parse(fs.readFileSync(path.join(KEYS_DIR, 'fwgroup.json'), 'utf8'));
  const etpToken    = fs.readFileSync(path.join(KEYS_DIR, 'etp_token.txt'), 'utf8').trim();
  return { privateKey, publicKey, groupData, etpToken };
}

// ── MQTT Client ────────────────────────────────────────────────────────────

let mqttClient = null;

async function connectMQTT() {
  return new Promise((resolve, reject) => {
    console.log(`[MQTT] Connecting to ${MQTT_BROKER}...`);
    const opts = {
      clientId: `firewalla-bridge-${Date.now()}`,
      clean: true,
      reconnectPeriod: 5000,
    };
    if (MQTT_USERNAME) {
      opts.username = MQTT_USERNAME;
      opts.password = MQTT_PASSWORD;
    }
    mqttClient = mqtt.connect(MQTT_BROKER, opts);

    mqttClient.once('connect', () => {
      console.log('[MQTT] Connected');
      resolve();
    });

    mqttClient.on('reconnect', () => console.log('[MQTT] Reconnecting...'));
    mqttClient.on('close',     () => console.log('[MQTT] Disconnected'));
    mqttClient.on('error',     (err) => {
      console.error('[MQTT] Error:', err.message);
      reject(err);
    });
  });
}

async function publish(topic, payload) {
  if (!mqttClient?.connected) {
    console.error('[MQTT] Not connected, skipping publish to', topic);
    return;
  }
  const msg = typeof payload === 'string' ? payload : JSON.stringify(payload);
  mqttClient.publish(`${MQTT_PREFIX}/${topic}`, msg, { qos: 1, retain: true });
}

// ── Firewalla Data Collectors ──────────────────────────────────────────────

async function collectBoxInfo(fwGroup) {
  const init      = new InitService(fwGroup);
  const initState = await init.init();
  // liveStats returns code 500 on some Firewalla models — skip silently
  let liveStats = null;
  try {
    liveStats = await init.liveStats();
  } catch (_) {}

  await publish('box_info', {
    model:           initState.model,
    version:         initState.version,
    longVersion:     initState.longVersion,
    uptime:          initState.uptime,
    publicIp:        initState.publicIp,
    publicIp6:       initState.publicIp6s?.join(',') || null,
    cloudConnected:  initState.cloudConnected,
    bootingComplete: initState.bootingComplete,
    timestamp:       new Date().toISOString(),
  });

  await publish('network/status', {
    connected:      initState.bootingComplete && initState.cloudConnected,
    connectionType: initState.network?.conn_type || 'unknown',
    publicIp:       initState.publicIp,
    gateway:        initState.network?.gateway_ip || null,
    dns:            initState.network?.dns?.join(',') || null,
    uptime:         initState.uptime,
    timestamp:      new Date().toISOString(),
  });

  if (liveStats) {
    await publish('network/live_stats', {
      downloadMbps:      liveStats.downloadMbps      || 0,
      uploadMbps:        liveStats.uploadMbps        || 0,
      activeConnections: liveStats.activeConnections  || 0,
      totalConnections:  liveStats.totalConnections   || 0,
      timestamp:         new Date().toISOString(),
    });
  }

  const features = initState.runtimeFeatures || {};
  await publish('box/features', {
    adblock:       !!features.adblock,
    unbound:       !!features.unbound,
    safeSearch:    !!features.safeSearch,
    familyProtect: !!features.familyProtect,
    timestamp:     new Date().toISOString(),
  });
}

async function collectHosts(fwGroup) {
  const hs       = new HostService(fwGroup);
  const hosts    = await hs.getAll();
  const hostList = hosts.hosts || [];

  const onlineDevices  = [];
  const offlineDevices = [];

  for (const h of hostList) {
    const isOnline = h.lastActive &&
      (Date.now() - new Date(h.lastActive).getTime() < 300_000); // 5 min
    const device = {
      name:       h.name || h.dhcpName || h.bonjourName || 'Unknown',
      ip:         h.ip,
      ipv6:       h.ipv6,
      mac:        h.mac,
      vendor:     h.macVendor || 'Unknown',
      interface:  h.intf || 'unknown',
      lastSeen:   h.lastActive,
      firstFound: h.firstFound,
      online:     isOnline,
      traffic: {
        uploadBytes:   h.flowsummary?.outbytes || 0,
        downloadBytes: h.flowsummary?.inbytes  || 0,
      },
      openPorts: h.openports ? Object.keys(h.openports) : [],
      policies: {
        adblock: h.policy?.adblock,
        blockIn: h.policy?.blockin,
        family:  h.policy?.family,
        monitor: h.policy?.monitor,
        acl:     h.policy?.acl,
      },
      tags: h.tags || [],
    };

    (isOnline ? onlineDevices : offlineDevices).push(device);
  }

  await publish('network/hosts_summary', {
    total:     hostList.length,
    online:    onlineDevices.length,
    offline:   offlineDevices.length,
    timestamp: new Date().toISOString(),
  });

  await publish('network/hosts', {
    online:    onlineDevices,
    offline:   offlineDevices,
    timestamp: new Date().toISOString(),
  });

  for (const d of [...onlineDevices, ...offlineDevices]) {
    await publish(`network/host/${d.mac.replace(/:/g, '_')}`, {
      name:      d.name,
      ip:        d.ip,
      online:    d.online,
      traffic:   d.traffic,
      openPorts: d.openPorts,
      timestamp: new Date().toISOString(),
    });
  }
}

async function collectAlarms(fwGroup) {
  const as = new AlarmService(fwGroup);
  let alarms = [];
  try {
    const result = await as.getAll();
    alarms = result?.alarms || result || [];
  } catch (e) {
    console.log('[Alarms] Error:', e.message);
  }

  const alarmList = alarms.map(a => ({
    id:        a.aid,
    type:      a.type,
    device:    a.device,
    message:   a.message,
    timestamp: a.timestamp,
    severity:  a.severity || 'info',
  }));

  await publish('network/alarms_summary', {
    total:     alarmList.length,
    active:    alarmList.filter(a => !a.ignored).length,
    timestamp: new Date().toISOString(),
  });

  await publish('network/alarms', alarmList);
}

async function collectUsage(fwGroup) {
  const ns = new NetworkService(fwGroup);

  try {
    const monthly = await ns.getMonthlyDataUsage();
    await publish('network/usage', {
      month:         monthly?.month || 'unknown',
      year:          monthly?.year  || 'unknown',
      uploadBytes:   monthly?.upload   || 0,
      downloadBytes: monthly?.download || 0,
      timestamp:     new Date().toISOString(),
    });
  } catch (e) {
    console.log('[Usage] Error fetching monthly data:', e.message);
  }

  try {
    const yearly = await ns.getLast12MonthlyDateUsage();
    await publish('network/usage/yearly', yearly || []);
  } catch (e) {
    console.log('[Usage] Error fetching yearly data:', e.message);
  }
}

async function collectSpeedtest(fwGroup) {
  const ns = new NetworkService(fwGroup);
  try {
    // API returns { results: [...] }, not a bare array
    const raw     = await ns.getSpeedtestResults();
    const results = Array.isArray(raw) ? raw : (raw?.results || []);

    const toEntry = r => ({
      downloadMbps: r.result?.download  ?? 0,
      uploadMbps:   r.result?.upload    ?? 0,
      latency:      r.result?.latency   ?? 0,
      jitter:       r.result?.jitter    ?? 0,
      isp:          r.client?.isp       ?? null,
      server:       r.server?.location  ?? null,
      timestamp:    new Date(r.timestamp * 1000).toISOString(),
    });

    await publish('network/speedtest', {
      latest:    results[0] ? toEntry(results[0]) : null,
      history:   results.slice(0, 10).map(toEntry),
      timestamp: new Date().toISOString(),
    });
  } catch (e) {
    console.log('[Speedtest] Error:', e.message);
  }
}

// ── Main ───────────────────────────────────────────────────────────────────

async function runCollection() {
  console.log('[Bridge] Starting data collection...');

  const creds = loadCredentials();
  SecureUtil.importKeyPairFromString(creds.publicKey, creds.privateKey);

  const fwGroup = new FWGroup(
    creds.groupData.gid,
    creds.groupData.eid,
    creds.groupData.aid,
    creds.groupData.symmetricKeyCipher,
    creds.groupData.name,
    FIREWALLA_IP
  );

  console.log('[Bridge] Collecting box info...');
  await collectBoxInfo(fwGroup);

  console.log('[Bridge] Collecting hosts...');
  await collectHosts(fwGroup);

  console.log('[Bridge] Collecting alarms...');
  await collectAlarms(fwGroup);

  console.log('[Bridge] Collecting usage...');
  await collectUsage(fwGroup);

  console.log('[Bridge] Collecting speedtest results...');
  await collectSpeedtest(fwGroup);

  console.log('[Bridge] Collection complete.');
}

async function main() {
  console.log('[Bridge] Firewalla-to-MQTT bridge starting');
  console.log(`[Bridge] MQTT broker:       ${MQTT_BROKER}`);
  console.log(`[Bridge] Firewalla box:     ${FIREWALLA_IP}`);
  console.log(`[Bridge] Topic prefix:      ${MQTT_PREFIX}`);
  console.log(`[Bridge] Collect interval:  ${COLLECT_INTERVAL}s`);

  await connectMQTT();
  await runCollection();

  setInterval(async () => {
    try {
      await runCollection();
    } catch (err) {
      console.error('[Bridge] Collection error:', err.message);
    }
  }, COLLECT_INTERVAL * 1000);
}

main().catch((err) => {
  console.error('[Bridge] Fatal error:', err.message);
  mqttClient?.end();
  process.exit(1);
});
