#!/usr/bin/env node
'use strict';
const crypto = require('crypto');

const FLAG       = 'flag{he_was_a_courier_not_a_vandal}';
const PASSPHRASE = 'JAKEX7';
const AUDIOKEY   = 'AUDIOKEY1234';

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
console.log(`// flag       = ${FLAG}`);
console.log(`// passphrase = ${PASSPHRASE}`);
console.log(`// audioKey   = ${AUDIOKEY}`);
