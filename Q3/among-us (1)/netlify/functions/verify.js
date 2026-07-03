'use strict';
const crypto = require('crypto');

const SALT_HEX   = '1e9e108fb0131fad812b15a0382362be';
const IV_HEX     = 'c7be9a8088ff04ac30ec0258';
const CIPHER_HEX = '6f5d897eccdaa6cd645b753948d68b3f6e1c7e9017cd63cae040571f051db488b0b1f4d1f76490d768';
const TAG_HEX    = '310e287b8671fc23cac2ae13b74f4c26';

const HITS = new Map();
function throttled(ip) {
  const now = Date.now();
  const arr = (HITS.get(ip) || []).filter(t => now - t < 30000);
  arr.push(now); HITS.set(ip, arr);
  return arr.length > 6;
}

function json(s, o) {
  return { statusCode: s, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' }, body: JSON.stringify(o) };
}

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return json(204, {});
  if (event.httpMethod !== 'POST') return json(405, { ok: false, error: 'method' });
  const ip = (event.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'anon';
  if (throttled(ip)) return json(429, { ok: false, error: 'rate limited' });
  let body;
  try { body = JSON.parse(event.body || '{}'); } catch { return json(400, { ok: false, error: 'bad json' }); }
  const pp = String(body.passphrase || '').toUpperCase();
  const ak = String(body.audioKey || '').toUpperCase();
  if (pp.length !== 8 || ak.length !== 8) return json(400, { ok: false, error: 'invalid length' });
  if (!/^[A-Z0-9]{8}$/.test(pp) || !/^[A-Z0-9]{8}$/.test(ak)) return json(400, { ok: false, error: 'invalid chars' });
  const password = pp + ':' + ak;
  const key = crypto.scryptSync(password, Buffer.from(SALT_HEX,'hex'), 32, { N:16384, r:8, p:1 });
  try {
    const d = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(IV_HEX,'hex'));
    d.setAuthTag(Buffer.from(TAG_HEX,'hex'));
    const plain = Buffer.concat([d.update(Buffer.from(CIPHER_HEX,'hex')), d.final()]).toString('utf8');
    return json(200, { ok: true, flag: plain });
  } catch { return json(403, { ok: false, error: 'verification failed' }); }
};
