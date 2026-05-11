'use strict';

const crypto = require('crypto');

const SALT_HEX   = '8beed1befeee60de94eccf498c2766f9';
const IV_HEX     = '93000e8e944a41a966ecf2d4';
const CIPHER_HEX = 'c18033cad3ddb80d1b16dfa1223e1451ff6d1ed65716a66fcaf5087f4874968a477df9';
const TAG_HEX    = '06ce49183de2d231b2cd5eaee7bd3982';

const HITS = new Map();
const WINDOW_MS = 30_000;
const MAX_HITS  = 8;

function throttled(ip) {
  const now = Date.now();
  const arr = (HITS.get(ip) || []).filter(t => now - t < WINDOW_MS);
  arr.push(now);
  HITS.set(ip, arr);
  return arr.length > MAX_HITS;
}

function json(status, obj) {
  return {
    statusCode: status,
    headers: {
      'Content-Type'                : 'application/json',
      'Cache-Control'               : 'no-store',
      'Access-Control-Allow-Origin' : '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
    body: JSON.stringify(obj),
  };
}

exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') return json(204, {});
  if (event.httpMethod !== 'POST')    return json(405, { ok: false, error: 'method' });

  const ip = (event.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'anon';
  if (throttled(ip)) return json(429, { ok: false, error: 'too many attempts' });

  let body;
  try { body = JSON.parse(event.body || '{}'); }
  catch { return json(400, { ok: false, error: 'bad json' }); }

  const passphrase = String(body.passphrase || '').toUpperCase();
  const audioKey   = String(body.audioKey   || '').toUpperCase();

  if (passphrase.length !== 6 || audioKey.length !== 12) {
    return json(400, { ok: false, error: 'invalid input length' });
  }
  if (!/^[A-Z0-9]{6}$/.test(passphrase) || !/^[A-Z0-9]{12}$/.test(audioKey)) {
    return json(400, { ok: false, error: 'invalid character set' });
  }

  const password = passphrase + ':' + audioKey;
  const salt = Buffer.from(SALT_HEX, 'hex');
  const iv   = Buffer.from(IV_HEX, 'hex');
  const ct   = Buffer.from(CIPHER_HEX, 'hex');
  const tag  = Buffer.from(TAG_HEX, 'hex');

  const key = crypto.scryptSync(password, salt, 32, { N: 16384, r: 8, p: 1 });

  try {
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAuthTag(tag);
    const plain = Buffer.concat([decipher.update(ct), decipher.final()]).toString('utf8');
    return json(200, { ok: true, flag: plain });
  } catch {
    return json(403, { ok: false, error: 'verification failed' });
  }
};
