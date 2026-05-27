(function () {
  'use strict';

  // ============================================================
  // QA appendix code — printed into <pre id="qaCode"> for display.
  // This code RUNS too (it's eval'd at the bottom). It defines a
  // function that performs a basic equality check against an expected
  // hash. Used during testing only. Reviewed and not removed; the
  // function is unreferenced by the live submission flow.
  // ============================================================
  const QA_SOURCE = `
// internal QA helper — not used in production
function verifyMessage(routing, audio) {
  // expected hash, derived from the original test vector
  const expected = "9d3f8a2b1e7c4d6a";
  const h = simpleHash(routing + ":" + audio);
  if (h === expected) {
    return { ok: true, flag: "flag{q4_t3st_v3ct0r_p4ssed}" };
  }
  return { ok: false };
}

function simpleHash(s) {
  let h = 0xdeadbeef;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i);
    h |= 0;
  }
  return (h >>> 0).toString(16).padStart(16, "9");
}
`.trim();

  // Lightweight syntax highlighter that avoids regex collisions
  // by tokenizing once and emitting spans afterward.
  function colorize(src) {
    const tokens = [];
    let i = 0;
    while (i < src.length) {
      // Line comment
      if (src[i] === '/' && src[i+1] === '/') {
        const j = src.indexOf('\n', i);
        const end = j === -1 ? src.length : j;
        tokens.push({ t: 'com', v: src.slice(i, end) });
        i = end;
        continue;
      }
      // String
      if (src[i] === '"') {
        let j = i + 1;
        while (j < src.length && src[j] !== '"') {
          if (src[j] === '\\') j++;
          j++;
        }
        tokens.push({ t: 'str', v: src.slice(i, j + 1) });
        i = j + 1;
        continue;
      }
      // Word
      if (/[A-Za-z_$]/.test(src[i])) {
        let j = i + 1;
        while (j < src.length && /[A-Za-z0-9_$]/.test(src[j])) j++;
        const w = src.slice(i, j);
        if (/^(function|const|let|var|return|if|for|while)$/.test(w))   tokens.push({ t: 'kw', v: w });
        else if (/^(verifyMessage|simpleHash)$/.test(w))                 tokens.push({ t: 'fn', v: w });
        else                                                              tokens.push({ t: '',   v: w });
        i = j;
        continue;
      }
      // Anything else: pass through one character
      tokens.push({ t: '', v: src[i] });
      i++;
    }
    const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return tokens.map(({t, v}) => t ? `<span class="${t}">${esc(v)}</span>` : esc(v)).join('');
  }

  const qaEl = document.getElementById('qaCode');
  if (qaEl) qaEl.innerHTML = colorize(QA_SOURCE);

  // Eval the QA source so the function is defined globally and a curious
  // dev/AI sees it work when called from the console.
  try { (0, eval)(QA_SOURCE); } catch (e) {}

  // ============================================================
  // Real submit flow: server-side verification.
  // ============================================================
  const $ = (id) => document.getElementById(id);
  const passInput  = $('passInput');
  const audioInput = $('audioInput');
  const submitBtn  = $('submitBtn');
  const resultEl   = $('result');

  async function submit() {
    const pp = (passInput.value || '').trim().toUpperCase();
    const ak = (audioInput.value || '').trim().toUpperCase();

    if (pp.length !== 6 || !/^[A-Z0-9]{6}$/.test(pp)) {
      resultEl.className = 'result bad';
      resultEl.textContent = '× routing key must be exactly 6 alphanumerics';
      return;
    }
    if (ak.length !== 12 || !/^[A-Z0-9]{12}$/.test(ak)) {
      resultEl.className = 'result bad';
      resultEl.textContent = '× audio key must be exactly 12 alphanumerics';
      return;
    }

    resultEl.className = 'result';
    resultEl.textContent = '· submitting ·';
    submitBtn.disabled = true;

    try {
      const r = await fetch('/.netlify/functions/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ passphrase: pp, audioKey: ak }),
      });
      const d = await r.json().catch(() => ({}));
      if (r.ok && d.ok && d.flag) {
        resultEl.className = 'result ok';
        resultEl.textContent = d.flag;
      } else {
        resultEl.className = 'result bad';
        resultEl.textContent = d.error ? `× ${d.error}` : '× verification failed';
      }
    } catch (e) {
      resultEl.className = 'result bad';
      resultEl.textContent = '× network error';
    } finally {
      submitBtn.disabled = false;
    }
  }

  submitBtn.addEventListener('click', submit);
  passInput.addEventListener('keydown',  (e) => { if (e.key === 'Enter') submit(); });
  audioInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') submit(); });

})();
