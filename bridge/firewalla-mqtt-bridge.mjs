#!/usr/bin/env node
/**
 * Firewalla-to-MQTT Bridge
 *
 * Topics published:
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
 *   firewalla/network/wan           - All WAN interfaces summary
 *   firewalla/network/wan/<uuid>    - Per-WAN interface detail
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
  FWGroupApi,
  FWGetMessage,
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

// Device is considered online if last seen within 30 minutes
const ONLINE_THRESHOLD_MS = 30 * 60 * 1000;

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

// last60 is [[epoch_sec, bytes], ...] in 60-second buckets. Returns Mbps from
// the most recent complete bucket.
function last60ToMbps(arr) {
  if (!Array.isArray(arr) || arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => b[0] - a[0]);
  const bytes  = sorted[0][1] ?? 0;
  return parseFloat((bytes / 60 * 8 / 1_000_000).toFixed(3));
}

async function collectBoxInfo(fwGroup) {
  const init      = new InitService(fwGroup);
  const initState = await init.init();

  // liveStats fails on Firewalla Gold (box returns code 500 internally).
  // Derive throughput from initState.last60 instead.
  const last60     = initState.last60     || {};
  const sysMetrics = initState.sysMetrics || {};
  const netMetrics = initState.networkMetrics || {};
  const nicStates  = initState.nicStates  || {};

  const downloadMbps = last60ToMbps(last60.download);
  const uploadMbps   = last60ToMbps(last60.upload);

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

  // Derived from last60 — reflects the most recent 60-second window
  await publish('network/live_stats', {
    downloadMbps,
    uploadMbps,
    // Active/total connections not available on Firewalla Gold via this API
    activeConnections: 0,
    totalConnections:  0,
    timestamp:         new Date().toISOString(),
  });

  // Per-interface live stats using networkMetrics rx/tx median (bytes/sec → Mbps)
  const publicIpsMap = initState.publicIps || {};
  for (const [iface, stats] of Object.entries(netMetrics)) {
    if (!stats?.rx && !stats?.tx) continue;
    const dlMbps = stats?.rx?.median
      ? parseFloat((parseInt(stats.rx.median) * 8 / 1_000_000).toFixed(3)) : 0;
    const ulMbps = stats?.tx?.median
      ? parseFloat((parseInt(stats.tx.median) * 8 / 1_000_000).toFixed(3)) : 0;
    const safeName = iface.replace(/[^a-zA-Z0-9_]/g, '_');
    await publish(`network/live_stats/wan/${safeName}`, {
      downloadMbps: dlMbps,
      uploadMbps:   ulMbps,
      publicIp:     publicIpsMap[iface] || null,
      timestamp:    new Date().toISOString(),
    });
  }

  // System health metrics
  await publish('system/metrics', {
    memUsagePct:  parseFloat(((sysMetrics.memUsage ?? 0) * 100).toFixed(1)),
    totalMemMB:   Math.round(sysMetrics.totalMem ?? 0),
    load1:        sysMetrics.load1  ?? null,
    load5:        sysMetrics.load5  ?? null,
    load15:       sysMetrics.load15 ?? null,
    timestamp:    new Date().toISOString(),
  });

  // Per-interface network metrics (rx/tx byte-rate percentiles)
  const ifaceStats = {};
  for (const [iface, stats] of Object.entries(netMetrics)) {
    if (stats?.rx || stats?.tx) {
      ifaceStats[iface] = {
        rxMedianBps:  stats.rx ? parseInt(stats.rx.median ?? 0) : 0,
        rxMaxBps:     stats.rx ? parseInt(stats.rx.max    ?? 0) : 0,
        txMedianBps:  stats.tx ? parseInt(stats.tx.median ?? 0) : 0,
        txMaxBps:     stats.tx ? parseInt(stats.tx.max    ?? 0) : 0,
        carrier:      nicStates[iface]?.carrier === '1',
        linkSpeed:    nicStates[iface]?.speed ?? null,
      };
    }
  }
  await publish('network/interfaces', {
    interfaces: ifaceStats,
    timestamp:  new Date().toISOString(),
  });

  const features = initState.runtimeFeatures || {};
  await publish('box/features', {
    adblock:       !!features.adblock,
    unbound:       !!features.unbound,
    safeSearch:    !!features.safeSearch,
    familyProtect: !!features.familyProtect,
    dualWan:       !!features.dual_wan,
    timestamp:     new Date().toISOString(),
  });

  return initState;
}

async function collectWAN(initState) {
  const publicIps      = initState.publicIps      || {};
  const networkProfiles = initState.networkProfiles;
  const virtWanGroups  = initState.virtWanGroups  || [];

  // networkProfiles can be an object keyed by UUID or an array
  const profileMap = {};
  if (Array.isArray(networkProfiles)) {
    for (const p of networkProfiles) {
      profileMap[p.uuid] = p;
    }
  } else if (networkProfiles && typeof networkProfiles === 'object') {
    Object.assign(profileMap, networkProfiles);
  }

  const wans = [];
  for (const [uuid, publicIp] of Object.entries(publicIps)) {
    const profile = profileMap[uuid] || {};
    const wan = {
      uuid,
      name:       profile.name       || profile.intf  || uuid,
      intf:       profile.intf       || uuid,
      publicIp,
      connType:   profile.conn_type  || 'unknown',
      active:     profile.active     ?? true,
      ready:      profile.ready      ?? true,
      gateway:    profile.gateway_ip || profile.gateway || null,
      dns:        Array.isArray(profile.dns) ? profile.dns.join(',') : (profile.dns || null),
      timestamp:  new Date().toISOString(),
    };
    wans.push(wan);

    const safeName = uuid.replace(/[^a-zA-Z0-9]/g, '_');
    await publish(`network/wan/${safeName}`, wan);
  }

  // Also expose virtWanGroups (load-balancing / failover config)
  const wanGroups = virtWanGroups.map(g => ({
    uuid:      g.uuid,
    name:      g.name,
    type:      g.type,   // 'primary_standby' | 'load_balance' etc.
    ready:     g.ready,
    active:    g.active,
    wans:      (g.wans || []).map(w => w.uuid || w),
  }));

  await publish('network/wan', {
    count:     wans.length,
    interfaces: wans,
    groups:    wanGroups,
    timestamp: new Date().toISOString(),
  });
}

async function collectHosts(fwGroup) {
  const hs       = new HostService(fwGroup);
  const hosts    = await hs.getAll();
  const hostList = hosts.hosts || hosts || [];

  const onlineDevices  = [];
  const offlineDevices = [];

  for (const h of hostList) {
    // lastActive is a Unix timestamp in seconds (float) — multiply by 1000 for ms
    const lastActiveMs = h.lastActive ? h.lastActive * 1000 : 0;
    const isOnline = lastActiveMs > 0 && (Date.now() - lastActiveMs < ONLINE_THRESHOLD_MS);

    const device = {
      name:       h.name || h.dhcpName || h.bonjourName || 'Unknown',
      ip:         h.ip,
      ipv6:       h.ipv6,
      mac:        h.mac,
      vendor:     h.macVendor || 'Unknown',
      interface:  h.intf || 'unknown',
      lastSeen:   lastActiveMs ? new Date(lastActiveMs).toISOString() : null,
      firstFound: h.firstFound ? new Date(h.firstFound * 1000).toISOString() : null,
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
    // API returns totalUpload/totalDownload (bytes) and monthlyBeginTs/monthlyEndTs (epoch seconds)
    const beginDate = monthly?.monthlyBeginTs
      ? new Date(monthly.monthlyBeginTs * 1000)
      : null;

    await publish('network/usage', {
      month:         beginDate ? beginDate.getMonth() + 1 : null,
      year:          beginDate ? beginDate.getFullYear()  : null,
      monthStart:    beginDate ? beginDate.toISOString()  : null,
      uploadBytes:   monthly?.totalUpload   || 0,
      downloadBytes: monthly?.totalDownload || 0,
      // Daily breakdown arrays: [[epoch_sec, bytes], ...]
      uploadDaily:   Array.isArray(monthly?.upload)   ? monthly.upload   : [],
      downloadDaily: Array.isArray(monthly?.download) ? monthly.download : [],
      timestamp:     new Date().toISOString(),
    });
  } catch (e) {
    console.log('[Usage] Error fetching monthly data:', e.message);
  }

  // Per-WAN monthly usage via undocumented firmware endpoint
  try {
    const wanUsage = await FWGroupApi.sendMessageToBox(
      fwGroup, new FWGetMessage('monthlyDataUsageOnWans')
    );
    if (wanUsage && typeof wanUsage === 'object') {
      for (const [uuid, data] of Object.entries(wanUsage)) {
        if (!data || (data.totalUpload == null && data.totalDownload == null)) continue;
        const beginDate = data.monthlyBeginTs ? new Date(data.monthlyBeginTs * 1000) : null;
        const safeName  = uuid.replace(/[^a-zA-Z0-9_]/g, '_');
        await publish(`network/usage/wan/${safeName}`, {
          wan:           uuid,
          month:         beginDate ? beginDate.getMonth() + 1 : null,
          year:          beginDate ? beginDate.getFullYear()  : null,
          monthStart:    beginDate ? beginDate.toISOString()  : null,
          uploadBytes:   data.totalUpload   || 0,
          downloadBytes: data.totalDownload || 0,
          timestamp:     new Date().toISOString(),
        });
      }
    }
  } catch (e) {
    console.log('[Usage] Error fetching per-WAN monthly data:', e.message);
  }

  try {
    const yearly = await ns.getLast12MonthlyDateUsage();
    await publish('network/usage/yearly', yearly || []);
  } catch (e) {
    console.log('[Usage] Error fetching yearly data:', e.message);
  }
}

async function collectSpeedtest(fwGroup, initState) {
  const ns = new NetworkService(fwGroup);
  try {
    const raw     = await ns.getSpeedtestResults();
    const results = Array.isArray(raw) ? raw : (raw?.results || []);

    const publicIps = initState?.publicIps || {};
    // Build reverse map: publicIp -> WAN uuid
    const ipToWan = {};
    for (const [uuid, ip] of Object.entries(publicIps)) {
      ipToWan[ip] = uuid;
    }

    const toEntry = r => ({
      downloadMbps: r.result?.download  ?? 0,
      uploadMbps:   r.result?.upload    ?? 0,
      latency:      r.result?.latency   ?? 0,
      jitter:       r.result?.jitter    ?? 0,
      packetLoss:   r.result?.ploss     ?? 0,
      isp:          r.client?.isp       ?? null,
      publicIp:     r.client?.publicIp  ?? null,
      wanUUID:      r.client?.publicIp  ? (ipToWan[r.client.publicIp] || null) : null,
      server:       r.server?.location  ?? null,
      timestamp:    new Date(r.timestamp * 1000).toISOString(),
    });

    const allEntries = results.slice(0, 20).map(toEntry);

    // Group by WAN (by publicIp) to get per-WAN latest
    const byWan = {};
    for (const entry of allEntries) {
      const key = entry.wanUUID || entry.publicIp || 'default';
      if (!byWan[key]) byWan[key] = [];
      byWan[key].push(entry);
    }

    await publish('network/speedtest', {
      latest:    allEntries[0] || null,
      history:   allEntries,
      byWan,
      timestamp: new Date().toISOString(),
    });

    // Publish per-WAN speedtest topics
    for (const [wanKey, entries] of Object.entries(byWan)) {
      const safeName = wanKey.replace(/[^a-zA-Z0-9]/g, '_');
      await publish(`network/speedtest/${safeName}`, {
        latest:    entries[0] || null,
        history:   entries,
        timestamp: new Date().toISOString(),
      });
    }
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
  const initState = await collectBoxInfo(fwGroup);

  console.log('[Bridge] Collecting WAN interfaces...');
  await collectWAN(initState);

  console.log('[Bridge] Collecting hosts...');
  await collectHosts(fwGroup);

  console.log('[Bridge] Collecting alarms...');
  await collectAlarms(fwGroup);

  console.log('[Bridge] Collecting usage...');
  await collectUsage(fwGroup);

  console.log('[Bridge] Collecting speedtest results...');
  await collectSpeedtest(fwGroup, initState);

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
