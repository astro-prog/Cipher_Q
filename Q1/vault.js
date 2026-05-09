/**
 * ------------------------------------------------------------
 * PROJECT: SPELL_VALLEY_STABILIZER v4.0.2
 * SECTOR: ARENA_15_RECOVERY
 * ------------------------------------------------------------
 */

// --- CORE FREQUENCY TUNING ---
let _pulse_freq = 0; 
// -----------------------------

function stabilizeSector(essence) {
    
    const _vault = [124, 130, 119, 125, 145, 123, 130, 127, 142, 127, 136, 117, 131, 119, 137, 138, 123, 136, 147];
    let _out = "";

    
    if (essence === 0) {
        console.warn("CRITICAL: Pulse Frequency is NULL. System idle.");
        return;
    }

 
    for (let i = 0; i < _vault.length; i++) {
        _out += String.fromCharCode(_vault[i] - essence);
    }

    if (_out.includes("flag{")) {
        console.log(">> [SIGNAL RECOVERED]: " + _out);
    } else {
        
        console.error(">> ERROR 404: PHASE_SHIFT_MISMATCH [" + (essence * 4).toString(16) + "]");
        console.log(">> The King's Seal remains intact. Your math lacks 'value'.");
    }
}

stabilizeSector(_pulse_freq);