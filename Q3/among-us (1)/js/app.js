(function () {
  'use strict';

  var DIAG_SOURCE = [
    '// Ship diagnostic verification module',
    '// Recovered from partition 0x7E — integrity unverified',
    'function diagnosticVerify(passphrase, signalKey) {',
    '  const combined = passphrase.toUpperCase() + ":" + signalKey;',
    '  const hash = Array.from(combined).reduce((h, c) => {',
    '    return ((h << 5) - h + c.charCodeAt(0)) | 0;',
    '  }, 0x5KELD);',
    '  const target = -1287429518;',
    '  if ((hash >>> 0) === (target >>> 0)) {',
    '    return {',
    '      verified: true,',
    '      message: "flag{cr3wm4t3_cl34r3d_f0r_duty}"',
    '    };',
    '  }',
    '  return { verified: false, message: "MISMATCH" };',
    '}',
    '',
    '// Secondary check — cross-reference with card data',
    'function cardDataCheck(imgPayload) {',
    '  if (imgPayload === "CREWMATE") {',
    '    return { match: true, source: "id_card_lsb" };',
    '  }',
    '  return { match: false };',
    '}',
  ].join('\n');

  function tokenize(src) {
    var tokens = [];
    var i = 0;
    while (i < src.length) {
      if (src[i] === '/' && src[i+1] === '/') {
        var j = src.indexOf('\n', i);
        var end = j === -1 ? src.length : j;
        tokens.push({ t: 'com', v: src.slice(i, end) });
        i = end;
        continue;
      }
      if (src[i] === '"') {
        var j2 = i + 1;
        while (j2 < src.length && src[j2] !== '"') {
          if (src[j2] === '\\') j2++;
          j2++;
        }
        tokens.push({ t: 'str', v: src.slice(i, j2 + 1) });
        i = j2 + 1;
        continue;
      }
      if (/[A-Za-z_$]/.test(src[i])) {
        var j3 = i + 1;
        while (j3 < src.length && /[A-Za-z0-9_$]/.test(src[j3])) j3++;
        var w = src.slice(i, j3);
        if (/^(function|const|let|var|return|if|true|false)$/.test(w))
          tokens.push({ t: 'kw', v: w });
        else if (/^(diagnosticVerify|cardDataCheck)$/.test(w))
          tokens.push({ t: 'fn', v: w });
        else
          tokens.push({ t: '', v: w });
        i = j3;
        continue;
      }
      tokens.push({ t: '', v: src[i] });
      i++;
    }
    var esc = function(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); };
    return tokens.map(function(tk) {
      return tk.t ? '<span class="' + tk.t + '">' + esc(tk.v) + '</span>' : esc(tk.v);
    }).join('');
  }

  var diagEl = document.getElementById('diagCode');
  if (diagEl) diagEl.innerHTML = tokenize(DIAG_SOURCE);

  try {
    (0, eval)(DIAG_SOURCE.replace('0x5KELD', '0x5ELD'));
  } catch (e) {}

})();
