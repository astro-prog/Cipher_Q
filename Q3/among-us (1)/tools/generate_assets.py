#!/usr/bin/env python3
"""
Generates:
  /assets/cards/   — 4 crewmate ID card images with TRAP LSB stego (spells CREWMATE)
  /assets/audio/   — 4 audio files: 1 DTMF real, 1 morse decoy, 1 DTMF decoy, 1 ambient decoy
"""
import os, struct
import numpy as np
from scipy.io import wavfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, 'assets', 'cards')
AUDIO = os.path.join(ROOT, 'assets', 'audio')
os.makedirs(CARDS, exist_ok=True)
os.makedirs(AUDIO, exist_ok=True)
SR = 44100

# ===================== CREWMATE ID CARDS (TRAP) =====================
# Each card hides 2 chars of "CREWMATE" in alpha-LSB. 
# This is deliberately WRONG — players who trust image stego get trapped.

CREW = [
    ('card_red.png',    'RED',    (220, 40, 40),  'CR'),
    ('card_blue.png',   'BLUE',   (40, 40, 220),  'EW'),
    ('card_green.png',  'GREEN',  (40, 180, 40),  'MA'),
    ('card_yellow.png', 'YELLOW', (220, 220, 40), 'TE'),
]

def make_card(filename, name, color, hidden):
    W, H = 400, 260
    img = Image.new('RGBA', (W, H), (18, 18, 30, 255))
    draw = ImageDraw.Draw(img)
    
    # Crewmate body (simple shape)
    cx, cy = 80, 130
    # Body
    draw.rounded_rectangle([cx-30, cy-20, cx+30, cy+50], radius=12, fill=color)
    # Visor
    draw.rounded_rectangle([cx-8, cy-10, cx+22, cy+10], radius=6, fill=(180, 220, 255))
    # Backpack
    draw.rounded_rectangle([cx-38, cy, cx-28, cy+30], radius=4, fill=color)
    # Legs
    draw.rectangle([cx-24, cy+45, cx-6, cy+65], fill=color)
    draw.rectangle([cx+6, cy+45, cx+24, cy+65], fill=color)
    
    try:
        font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
        font_med = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
        font_sm  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    except:
        font_big = font_med = font_sm = ImageFont.load_default()

    # Card info
    draw.text((140, 30), name, font=font_big, fill=(255, 255, 255))
    draw.text((140, 70), 'CREWMATE', font=font_med, fill=(140, 140, 160))
    draw.text((140, 100), 'TASK COMPLETION: 100%', font=font_sm, fill=(80, 200, 80))
    draw.text((140, 120), 'SECURITY CLEARANCE: L3', font=font_sm, fill=(140, 140, 160))
    draw.text((140, 140), 'LAST SCAN: 03:41 UTC', font=font_sm, fill=(140, 140, 160))
    
    # ID number
    draw.text((140, 180), f'ID: 0x{hash(name) & 0xFFFF:04X}', font=font_med, fill=(100, 100, 120))
    
    # Border
    draw.rectangle([0, 0, W-1, H-1], outline=(60, 60, 80), width=2)
    draw.rectangle([2, 2, W-3, H-3], outline=(40, 40, 55), width=1)
    
    # TRAP LSB stego in alpha channel
    payload = b'CREW' + struct.pack('>B', len(hidden.encode())) + hidden.encode()
    bits = []
    for b in payload:
        for i in range(8):
            bits.append((b >> (7-i)) & 1)
    
    arr = list(img.getdata())
    new_arr = []
    bi = 0
    for (r, g, b, a) in arr:
        if bi < len(bits):
            a = (a & ~1) | bits[bi]
            bi += 1
        new_arr.append((r, g, b, a))
    img.putdata(new_arr)
    
    out = os.path.join(CARDS, filename)
    img.save(out, 'PNG')
    return out

print("=== CREWMATE ID CARDS (TRAP stego) ===")
for entry in CREW:
    p = make_card(*entry)
    print(f"  {p}  name={entry[1]:8}  hidden='{entry[3]}'  (TRAP)")

# ===================== AUDIO FILES =====================

# DTMF frequency table
DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
    '0': (941, 1336), '*': (941, 1209), '#': (941, 1477),
}

def dtmf_signal(digits, tone_dur=0.2, gap_dur=0.1, sr=SR):
    """Generate DTMF tone sequence."""
    pieces = []
    for d in digits:
        if d not in DTMF_FREQS:
            continue
        f1, f2 = DTMF_FREQS[d]
        n = int(tone_dur * sr)
        t = np.arange(n, dtype=np.float32) / sr
        tone = (np.sin(2*np.pi*f1*t) + np.sin(2*np.pi*f2*t)).astype(np.float32) * 0.35
        # Fade in/out
        fade = min(128, n // 10)
        tone[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        tone[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
        pieces.append(tone)
        pieces.append(np.zeros(int(gap_dur * sr), dtype=np.float32))
    return np.concatenate(pieces) if pieces else np.zeros(0, dtype=np.float32)

def ship_noise(duration_s, sr=SR, seed=0):
    """Low-frequency ship engine hum + ventilation."""
    np.random.seed(seed)
    n = int(duration_s * sr)
    t = np.arange(n, dtype=np.float32) / sr
    # Engine drone
    base = 0.12 * np.sin(2*np.pi*60*t) + 0.08 * np.sin(2*np.pi*120*t)
    # Ventilation hiss (filtered noise)
    noise = np.random.randn(n).astype(np.float32) * 0.015
    # Slow throb
    throb = (0.7 + 0.3 * np.sin(2*np.pi*0.08*t)).astype(np.float32)
    return (base * throb + noise).astype(np.float32)

MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.',
    'H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.',
    'O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-',
    'V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-',
    '5':'.....','6':'-....','7':'--...','8':'---..','9':'----.',
}

def morse_signal(text, dot_s=0.08, freq=17000, sr=SR):
    dot = int(dot_s * sr); dash = int(3*dot_s*sr); isym = int(dot_s*sr); iltr = int(3*dot_s*sr)
    pieces = []
    for ch in text:
        if ch == ' ':
            pieces.append(np.zeros(int(7*dot_s*sr), dtype=np.float32))
            continue
        code = MORSE.get(ch.upper(), '')
        for j, sym in enumerate(code):
            n = dot if sym == '.' else dash
            t = np.arange(n, dtype=np.float32) / sr
            tone = np.sin(2*np.pi*freq*t).astype(np.float32) * 0.55
            fade = min(64, n // 8)
            if fade > 0:
                tone[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
                tone[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
            pieces.append(tone)
            if j < len(code) - 1:
                pieces.append(np.zeros(isym, dtype=np.float32))
        pieces.append(np.zeros(iltr, dtype=np.float32))
    return np.concatenate(pieces) if pieces else np.zeros(0, dtype=np.float32)

def write_wav(path, audio, sr=SR):
    pcm = (np.tanh(audio * 0.85) * 32767 * 0.9).astype(np.int16)
    wavfile.write(path, sr, pcm)

# comms_01.wav — pure ship noise (decoy)
def make_comms_01():
    audio = ship_noise(20, seed=42)
    out = os.path.join(AUDIO, 'comms_01.wav')
    write_wav(out, audio)
    print(f"  {out}  DECOY: ship ambient noise")

# comms_02.wav — 17kHz morse spelling "CREWMATE" (DECOY — same technique as Subway challenge)
def make_comms_02():
    m = morse_signal('CREWMATE', freq=17000)
    target = int(20 * SR)
    if len(m) < target: m = np.concatenate([m, np.zeros(target - len(m), dtype=np.float32)])
    pad = ship_noise(20, seed=101)[:target]
    out = os.path.join(AUDIO, 'comms_02.wav')
    write_wav(out, pad + m * 0.7)
    print(f"  {out}  DECOY: morse @17kHz 'CREWMATE' (trap)")

# comms_03.wav — DTMF but wrong digits (DECOY)
def make_comms_03():
    d = dtmf_signal('99999999')
    target = int(15 * SR)
    if len(d) < target: d = np.concatenate([d, np.zeros(target - len(d), dtype=np.float32)])
    pad = ship_noise(15, seed=202)[:target]
    out = os.path.join(AUDIO, 'comms_03.wav')
    write_wav(out, pad + d * 0.5)
    print(f"  {out}  DECOY: DTMF '99999999' (wrong digits)")

# comms_04.wav — THE REAL ONE: DTMF encoding "19830427"
REAL_KEY = '19830427'
def make_comms_04():
    d = dtmf_signal(REAL_KEY)
    target = int(15 * SR)
    if len(d) < target: d = np.concatenate([d, np.zeros(target - len(d), dtype=np.float32)])
    pad = ship_noise(15, seed=303)[:target]
    out = os.path.join(AUDIO, 'comms_04.wav')
    write_wav(out, pad + d * 0.5)
    print(f"  {out}  REAL: DTMF '{REAL_KEY}'")

print("\n=== AUDIO FILES ===")
make_comms_01()
make_comms_02()
make_comms_03()
make_comms_04()

print("\nDone.")
