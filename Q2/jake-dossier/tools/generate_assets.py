#!/usr/bin/env python3
"""
Generates all challenge assets:
  /assets/gallery/  — 6 stylized city images, each carrying ONE clue character
  /assets/audio/    — 4 audio files (1 real + 3 decoys)
"""
import os
import struct
import numpy as np
from scipy.io import wavfile
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAL = os.path.join(ROOT, 'assets', 'gallery')
AUD = os.path.join(ROOT, 'assets', 'audio')
os.makedirs(GAL, exist_ok=True)
os.makedirs(AUD, exist_ok=True)

SR = 44100

# -------- CITY IMAGES --------
# Each city carries 1 character. The character is encoded into the image's
# alpha-LSB (subtle stego, requires actually opening the image with a tool).
# The CITY itself is shown by a distinctive landmark silhouette.

CITIES = [
    # (filename,  city,         landmark_text,    char,  bg_top,    bg_bot)
    ('img_01.png','COPENHAGEN', 'LITTLE MERMAID', 'J',  '#3a5f8a','#1a2540'),
    ('img_02.png','HAMBURG',    'ELBPHILHARMONIE','A',  '#5a4a3a','#2a1f15'),
    ('img_03.png','LONDON',     'BIG BEN',        'K',  '#4a3a5a','#1f1530'),
    ('img_04.png','NEW YORK',   'EMPIRE STATE',   'E',  '#5a3a3a','#2a1010'),
    ('img_05.png','TOKYO',      'TOKYO TOWER',    'X',  '#3a5a4a','#15302a'),
    ('img_06.png','MUMBAI',     'GATEWAY OF INDIA','7', '#5a5a3a','#302a10'),
]

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def make_city_image(filename, city, landmark, char, bg_top, bg_bot):
    W, H = 600, 400
    img = Image.new('RGBA', (W, H))
    px = img.load()
    top = hex_to_rgb(bg_top)
    bot = hex_to_rgb(bg_bot)

    # gradient sky
    for y in range(H):
        t = y / H
        r = int(top[0] + (bot[0]-top[0])*t)
        g = int(top[1] + (bot[1]-top[1])*t)
        b = int(top[2] + (bot[2]-top[2])*t)
        for x in range(W):
            px[x, y] = (r, g, b, 255)

    draw = ImageDraw.Draw(img)

    # silhouette skyline
    np.random.seed(hash(city) & 0xffff)
    skyline_y = H - 80
    for i in range(40):
        bx = i * (W // 40)
        bw = (W // 40) - 2
        bh = np.random.randint(20, 100)
        draw.rectangle([bx, skyline_y - bh, bx + bw, H], fill=(8, 8, 14, 255))
        # window dots
        for wy in range(skyline_y - bh + 8, H - 4, 12):
            for wx in range(bx + 3, bx + bw - 3, 6):
                if np.random.random() > 0.6:
                    draw.point((wx, wy), fill=(255, 220, 100, 255))

    # try to load a font
    try:
        font_big   = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except:
        font_big = font_small = ImageFont.load_default()

    # city label — visible
    draw.text((20, 20), city, font=font_big, fill=(255, 255, 255, 240))
    draw.text((20, 56), landmark, font=font_small, fill=(255, 255, 255, 160))

    # JAKE marker — every image has the same red hoodie character signature
    # (so they all clearly belong to the same dossier)
    draw.text((W - 90, H - 30), 'TAG #', font=font_small, fill=(255, 100, 140, 200))
    draw.text((W - 50, H - 32), '___',  font=font_big, fill=(255, 45, 135, 230))

    # Embed the char in alpha-LSBs.
    # 4 bytes (uint32 BE) of magic + 1 byte length + UTF-8 bytes.
    payload = b'JAKE' + struct.pack('>B', len(char.encode())) + char.encode()
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

    out = os.path.join(GAL, filename)
    img.save(out, 'PNG')
    return out

print("=== generating city images ===")
for entry in CITIES:
    p = make_city_image(*entry)
    print(f"  {p}  city={entry[1]:12}  hidden_char='{entry[3]}'")

# -------- AUDIO FILES --------
# 4 files, only ONE is real.

MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.',
    'H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.',
    'O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-',
    'V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-',
    '5':'.....','6':'-....','7':'--...','8':'---..','9':'----.',
}

def morse_signal(text, dot_s=0.08, freq=17000, sr=SR):
    dot   = int(dot_s * sr)
    dash  = int(3 * dot_s * sr)
    isym  = int(dot_s * sr)
    iltr  = int(3 * dot_s * sr)
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
                tone[:fade]  *= np.linspace(0, 1, fade, dtype=np.float32)
                tone[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
            pieces.append(tone)
            if j < len(code) - 1:
                pieces.append(np.zeros(isym, dtype=np.float32))
        pieces.append(np.zeros(iltr, dtype=np.float32))
    return np.concatenate(pieces) if pieces else np.zeros(0, dtype=np.float32)

def ambient(duration_s, sr=SR, seed=0):
    np.random.seed(seed)
    n = int(duration_s * sr)
    t = np.arange(n, dtype=np.float32) / sr
    base = (
        0.18 * np.sin(2*np.pi*55*t)
      + 0.10 * np.sin(2*np.pi*82.4*t)
      + 0.06 * np.sin(2*np.pi*110*t)
    ).astype(np.float32)
    drift = (0.6 + 0.4 * np.sin(2*np.pi*0.07*t)).astype(np.float32)
    base *= drift
    return base

# clip_01.wav — pure ambient, no payload (decoy)
def make_clip_01():
    audio = ambient(20, seed=1)
    pcm = (np.tanh(audio * 0.85) * 32767 * 0.85).astype(np.int16)
    out = os.path.join(AUD, 'clip_01.wav')
    wavfile.write(out, SR, pcm)
    print(f"  {out}  DECOY: pure ambient")

# clip_02.wav — short voice-like sweep with FAKE flag suggestion
# We can't synthesize TTS reliably here so we encode the FAKE flag in
# audible-range morse (so it's findable by a determined player but is wrong).
def make_clip_02():
    fake_payload = morse_signal('FAKE FLAG IS NOT THIS ONE', freq=2400)
    pad = ambient(max(15, len(fake_payload)/SR + 2), seed=2)[:len(fake_payload)]
    if len(pad) < len(fake_payload):
        pad = np.concatenate([pad, np.zeros(len(fake_payload)-len(pad), dtype=np.float32)])
    mix = pad + fake_payload * 0.3
    pcm = (np.tanh(mix * 0.85) * 32767 * 0.85).astype(np.int16)
    out = os.path.join(AUD, 'clip_02.wav')
    wavfile.write(out, SR, pcm)
    print(f"  {out}  DECOY: audible-morse fake flag")

# clip_03.wav — high-freq morse spelling junk word "GHOSTRIDE" (decoy)
def make_clip_03():
    junk = morse_signal('GHOSTRIDE', freq=17000)
    target_n = int(15 * SR)
    if len(junk) < target_n:
        junk = np.concatenate([junk, np.zeros(target_n - len(junk), dtype=np.float32)])
    else:
        junk = junk[:target_n]
    pad = ambient(15, seed=3)[:target_n]
    mix = pad + junk * 0.7
    pcm = (np.tanh(mix * 0.85) * 32767 * 0.9).astype(np.int16)
    out = os.path.join(AUD, 'clip_03.wav')
    wavfile.write(out, SR, pcm)
    print(f"  {out}  DECOY: morse 'GHOSTRIDE' (looks legit, isn't)")

# clip_04.wav — THE REAL ONE. High-freq morse @17 kHz spelling AUDIOKEY1234
AUDIO_KEY = 'AUDIOKEY1234'
def make_clip_04():
    real = morse_signal(AUDIO_KEY, freq=17000)
    target_n = int(30 * SR)
    if len(real) < target_n:
        real = np.concatenate([real, np.zeros(target_n - len(real), dtype=np.float32)])
    else:
        real = real[:target_n]
    pad = ambient(30, seed=4)[:target_n]
    mix = pad + real * 0.7
    pcm = (np.tanh(mix * 0.85) * 32767 * 0.9).astype(np.int16)
    out = os.path.join(AUD, 'clip_04.wav')
    wavfile.write(out, SR, pcm)
    print(f"  {out}  REAL: morse @17kHz AUDIOKEY1234")

print("\n=== generating audio files ===")
make_clip_01()
make_clip_02()
make_clip_03()
make_clip_04()

print("\nDone.")
