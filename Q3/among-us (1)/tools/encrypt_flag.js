#!/usr/bin/env node
'use strict';
const crypto = require('crypto');

const FLAG       = 'flag{the_impostor_was_among_us_all_along}';
const PASSPHRASE = 'IMPOST0R';   // from zero-width chars in chat
const AUDIOKEY   = '19830427';   // from DTMF tones in comms_04.wav

const password = PASSPHRASE + ':' + AUDIOKEY;
const salt = crypto.randomBytes(16);
const iv   = crypto.randomBytes(12);
const key  = crypto.scryptSync(password, salt, 32, { N: 16384, r: 8, p: 1 });

const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
const ct = Buffer.concat([cipher.update(FLAG, 'utf8'), cipher.final()]);
const tag = cipher.getAuthTag();

console.log("// Paste into netlify/functions/verify.js");
console.log(`const SALT_HEX   = '${salt.toString('hex')}';`);
console.log(`const IV_HEX     = '${iv.toString('hex')}';`);
console.log(`const CIPHER_HEX = '${ct.toString('hex')}';`);
console.log(`const TAG_HEX    = '${tag.toString('hex')}';`);
