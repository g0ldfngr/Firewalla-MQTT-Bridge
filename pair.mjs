#!/usr/bin/env node
/**
 * pair.mjs — Pair this machine with your Firewalla box and write the four
 * credential files that the MQTT bridge container needs.
 *
 * Usage:
 *   node pair.mjs
 *
 * Output (relative to this script):
 *   bridge/credentials/etp.private.pem
 *   bridge/credentials/etp.public.pem
 *   bridge/credentials/fwgroup.json
 *   bridge/credentials/etp_token.txt
 *
 * Requirements: Node.js 18+ (uses built-in fetch + crypto — no npm install needed)
 *
 * Before running:
 *   1. Open the Firewalla app on your phone
 *   2. Tap your box → Settings → Advanced → Allow Additional Pairing
 *   3. Enable "Additional Pairing" — a QR code will appear
 *   4. Screenshot or scan that QR code to get its raw JSON value
 */

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import readline from 'readline';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CRED_DIR  = path.join(__dirname, 'bridge', 'credentials');
const API_BASE  = 'https://firewalla.encipher.io/app/api/v2';

// ── Crypto helpers (mirrors node-firewalla's SecureUtil) ────────────────────

function aesDecrypt(msg, key) {
  const iv   = Buffer.alloc(16, 0);
  const bkey = Buffer.from(key.substring(0, 32), 'utf8');
  const dec  = crypto.createDecipheriv('aes-256-cbc', bkey, iv);
  return dec.update(msg, 'base64', 'utf8') + dec.final('utf8');
}

function generateKeyPair() {
  return crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048,
    publicKeyEncoding:  { type: 'spki',   format: 'pem' },
    privateKeyEncoding: { type: 'pkcs8',  format: 'pem' },
  });
}

// ── Firewalla API calls ──────────────────────────────────────────────────────

async function etpLogin(publicKey, email = '') {
  const res = await fetch(`${API_BASE}/login/eptoken`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      assertion: {
        name:       email,
        info:       { name: 'circle' },
        publicKey,
        appId:      'com.rottiesoft.circle',
        appSecret:  'fbb05afa-9145-41f1-8076-9de8be56f104',
        signature:  '',
      },
    }),
  });
  return res.json();
}

async function startRendezVous(accessToken, rid, license) {
  const res = await fetch(`${API_BASE}/ept/rendezvous/me`, {
    method: 'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      rid,
      evalue: JSON.stringify({ license }),
    }),
  });
  return res.json();
}

// ── CLI helpers ──────────────────────────────────────────────────────────────

function ask(rl, question) {
  return new Promise(resolve => rl.question(question, answer => resolve(answer.trim())));
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('\n╔══════════════════════════════════════╗');
  console.log('║   Firewalla MQTT Bridge — Pairing    ║');
  console.log('╚══════════════════════════════════════╝\n');

  console.log('Before continuing, open the Firewalla app:');
  console.log('  Box → Settings → Advanced → Allow Additional Pairing → Enable\n');
  console.log('Screenshot or scan the QR code that appears, then come back here.\n');

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  const email      = await ask(rl, 'Email for ETP token (shown in the app):        ');
  const qrRaw      = await ask(rl, 'QR code JSON (paste the full JSON string):     ');
  const boxIpInput = await ask(rl, 'Firewalla box LAN IP [192.168.1.1]:            ');
  const boxIp      = boxIpInput || '192.168.1.1';

  rl.close();

  // ── Validate QR code ────────────────────────────────────────────────────
  let qr;
  try {
    qr = JSON.parse(qrRaw);
  } catch {
    console.error('\nError: QR code is not valid JSON.');
    process.exit(1);
  }

  for (const field of ['gid', 'seed', 'license', 'ek']) {
    if (!(field in qr)) {
      console.error(`\nError: QR code is missing required field "${field}".`);
      process.exit(1);
    }
  }

  // ── Generate key pair ───────────────────────────────────────────────────
  console.log('\nGenerating RSA-2048 key pair...');
  const { publicKey, privateKey } = generateKeyPair();

  // ── Register public key → ETP token ────────────────────────────────────
  console.log('Registering with Firewalla ETP API...');
  const loginData = await etpLogin(publicKey, email);

  if (!loginData.access_token) {
    console.error('\nLogin failed. Response:', JSON.stringify(loginData, null, 2));
    process.exit(1);
  }

  const accessToken = loginData.access_token;
  console.log('Registered. Got ETP access token.');

  // ── Start rendez-vous handshake ─────────────────────────────────────────
  const aesKey = qr.license.substring(0, 8) + qr.seed;
  const rid    = aesDecrypt(qr.ek, aesKey);

  console.log('Starting rendez-vous handshake...');
  const rvData = await startRendezVous(accessToken, rid, qr.license);

  if (rvData.error) {
    console.error('\nRendez-vous failed:', JSON.stringify(rvData, null, 2));
    process.exit(1);
  }

  // ── Poll until box confirms pairing ────────────────────────────────────
  console.log('\nWaiting for the box to confirm pairing (up to 60 seconds)...');
  console.log('Make sure "Additional Pairing" is still enabled in the app.\n');

  let group;
  for (let attempt = 1; attempt <= 20; attempt++) {
    process.stdout.write(`  Polling attempt ${attempt}/20... `);
    const poll = await etpLogin(publicKey, email);

    group = (poll.groups || []).find(g => g._id === qr.gid);
    if (group) {
      console.log('confirmed!\n');
      break;
    }

    console.log('not yet');
    await sleep(3000);
  }

  if (!group) {
    console.error('\nPairing timed out after 20 attempts.');
    console.error('Ensure "Additional Pairing" is active in the app and try again.');
    process.exit(1);
  }

  // ── Build fwgroup.json ──────────────────────────────────────────────────
  const fwgroupJson = {
    gid:                group._id,
    eid:                group.eid,
    aid:                group.aid,
    symmetricKeyCipher: group.symmetricKeys[0].key,
    name:               group.name,
  };

  // ── Write credential files ──────────────────────────────────────────────
  fs.mkdirSync(CRED_DIR, { recursive: true });

  const files = {
    'etp.private.pem': privateKey,
    'etp.public.pem':  publicKey,
    'fwgroup.json':    JSON.stringify(fwgroupJson, null, 2) + '\n',
    'etp_token.txt':   accessToken + '\n',
  };

  for (const [name, content] of Object.entries(files)) {
    const dest = path.join(CRED_DIR, name);
    if (fs.existsSync(dest)) {
      console.log(`  Overwriting existing ${name}`);
    }
    fs.writeFileSync(dest, content, { mode: 0o600 });
    console.log(`  Wrote ${dest}`);
  }

  console.log('\nPairing complete!');
  console.log('\nNext steps:');
  console.log('  cd bridge');
  console.log('  cp .env.example .env   # then edit MQTT_BROKER / FIREWALLA_IP');
  console.log('  docker compose up -d --build');
}

main().catch(err => {
  console.error('\nFatal error:', err);
  process.exit(1);
});
