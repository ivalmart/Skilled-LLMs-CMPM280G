import wave, struct, math, random

RATE = 44100
BPM = 128
BEAT = 60.0 / BPM
BAR = BEAT * 4
TOTAL_BARS = 32
DURATION = TOTAL_BARS * BAR

def mix(samples_list):
    length = max(len(s) for s in samples_list)
    out = [0.0] * length
    for s in samples_list:
        for i in range(len(s)):
            out[i] += s[i]
    return out

def normalize(samples, peak=0.9):
    mx = max(abs(s) for s in samples) or 1.0
    return [s / mx * peak for s in samples]

def silence(dur):
    return [0.0] * int(RATE * dur)

def sine(freq, dur, vol=1.0, phase=0.0):
    n = int(RATE * dur)
    return [vol * math.sin(2 * math.pi * freq * i / RATE + phase) for i in range(n)]

def saw(freq, dur, vol=1.0):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = (freq * i / RATE) % 1.0
        out.append(vol * (2.0 * t - 1.0))
    return out

def square(freq, dur, vol=1.0, pw=0.5):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = (freq * i / RATE) % 1.0
        out.append(vol if t < pw else -vol)
    return out

def noise(dur, vol=1.0):
    n = int(RATE * dur)
    return [vol * (random.random() * 2 - 1) for _ in range(n)]

def env(samples, attack=0.005, decay=0.05, sustain=0.3, release=0.1):
    n = len(samples)
    a = int(RATE * attack)
    d = int(RATE * decay)
    r = int(RATE * release)
    s_end = max(n - r, a + d)
    out = []
    for i in range(n):
        if i < a:
            g = i / max(a, 1)
        elif i < a + d:
            g = 1.0 - (1.0 - sustain) * (i - a) / max(d, 1)
        elif i < s_end:
            g = sustain
        else:
            g = sustain * (1.0 - (i - s_end) / max(r, 1))
        g = max(0.0, min(1.0, g))
        out.append(samples[i] * g)
    return out

def lpf(samples, cutoff=2000.0):
    rc = 1.0 / (2.0 * math.pi * cutoff)
    dt = 1.0 / RATE
    alpha = dt / (rc + dt)
    out = [samples[0]]
    for i in range(1, len(samples)):
        out.append(out[-1] + alpha * (samples[i] - out[-1]))
    return out

def kick(vol=0.9):
    dur = 0.3
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        freq = 150 * math.exp(-t * 20) + 40
        amp = math.exp(-t * 8)
        out.append(vol * amp * math.sin(2 * math.pi * freq * t))
    return out

def snare(vol=0.5):
    dur = 0.2
    body = env(sine(200, dur, 0.6), attack=0.001, decay=0.05, sustain=0.0, release=0.1)
    ns = env(noise(dur, 0.7), attack=0.001, decay=0.08, sustain=0.0, release=0.05)
    return [vol * (body[i] + ns[i]) for i in range(len(body))]

def hihat(open_hat=False, vol=0.3):
    dur = 0.15 if open_hat else 0.05
    ns = noise(dur, vol)
    return env(lpf(ns, 8000), attack=0.001, decay=0.03 if not open_hat else 0.1, sustain=0.0, release=0.02)

def clap(vol=0.4):
    dur = 0.15
    ns = env(noise(dur, vol), attack=0.001, decay=0.02, sustain=0.1, release=0.08)
    return lpf(ns, 3000)

def place(buf, snippet, pos_sec):
    start = int(RATE * pos_sec)
    for i in range(len(snippet)):
        idx = start + i
        if idx < len(buf):
            buf[idx] += snippet[i]

def note_freq(note, octave=4):
    notes = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}
    return 440.0 * 2 ** ((notes[note] + (octave - 4) * 12 - 9) / 12.0)

# Build the track
total_samples = int(RATE * DURATION)
drums = [0.0] * total_samples
bass_track = [0.0] * total_samples
lead_track = [0.0] * total_samples
pad_track = [0.0] * total_samples

# Drum patterns per bar
# Kick: 1 and 3 (four-on-the-floor)
# Snare/clap: 2 and 4
# Hihats: 8ths with some 16ths

for bar in range(TOTAL_BARS):
    bar_start = bar * BAR
    section = bar // 8  # 0=intro, 1=build, 2=drop, 3=outro

    # Kick - four on the floor (skip some in intro)
    if section == 0:
        for b in [0, 2]:
            place(drums, kick(0.7), bar_start + b * BEAT)
    elif section == 1:
        for b in range(4):
            place(drums, kick(0.8), bar_start + b * BEAT)
        if bar % 2 == 1 and bar >= 10:
            for b in range(8):
                place(drums, kick(0.5), bar_start + b * BEAT / 2)
    elif section == 2:
        for b in range(4):
            place(drums, kick(0.95), bar_start + b * BEAT)
    else:
        for b in [0, 2]:
            place(drums, kick(0.6), bar_start + b * BEAT)

    # Snare/clap on 2 and 4
    if section >= 1:
        for b in [1, 3]:
            place(drums, clap(0.35 if section == 1 else 0.5), bar_start + b * BEAT)
            place(drums, snare(0.3 if section == 1 else 0.45), bar_start + b * BEAT)

    # Hihats
    hat_vol = 0.15 if section == 0 else 0.25
    for b in range(8):
        t = bar_start + b * BEAT / 2
        is_open = (b % 4 == 2)
        place(drums, hihat(is_open, hat_vol), t)
    # 16th hat ghost notes in drop
    if section == 2:
        for b in range(16):
            if b % 2 == 1:
                place(drums, hihat(False, 0.1), bar_start + b * BEAT / 4)

# Bass line
bass_pattern_a = [('E', 2), ('E', 2), ('G', 2), ('A', 2)]
bass_pattern_b = [('E', 2), ('D', 2), ('C', 2), ('D', 2)]

for bar in range(TOTAL_BARS):
    bar_start = bar * BAR
    section = bar // 8

    if section < 1:
        continue

    pattern = bass_pattern_a if (bar % 4 < 2) else bass_pattern_b
    bass_vol = 0.4 if section == 1 else (0.7 if section == 2 else 0.3)

    for beat_idx, (note, octave) in enumerate(pattern):
        freq = note_freq(note, octave)
        t = bar_start + beat_idx * BEAT
        dur = BEAT * 0.9

        # Saw bass with filter
        raw = saw(freq, dur, bass_vol)
        raw2 = saw(freq * 1.005, dur, bass_vol * 0.5)  # slight detune
        combined = [raw[i] + raw2[i] for i in range(len(raw))]
        cutoff = 600 if section == 1 else 1200
        filtered = lpf(combined, cutoff)
        shaped = env(filtered, attack=0.005, decay=0.05, sustain=0.8, release=0.05)
        place(bass_track, shaped, t)

        # Sub bass
        sub = env(sine(freq / 2, dur, bass_vol * 0.5), attack=0.01, decay=0.05, sustain=0.7, release=0.05)
        place(bass_track, sub, t)

# Lead melody
melody = [
    ('B', 4, 0.5), ('E', 5, 0.5), ('D', 5, 0.25), ('B', 4, 0.25),
    ('A', 4, 0.5), ('G', 4, 0.5), ('A', 4, 0.5), ('B', 4, 0.5),
    ('E', 5, 0.5), ('D', 5, 0.5), ('B', 4, 0.25), ('A', 4, 0.25),
    ('G', 4, 1.0), ('E', 4, 0.5), ('G', 4, 0.5),
]

for bar in range(TOTAL_BARS):
    section = bar // 8
    if section not in [2, 3]:
        continue

    bar_start = bar * BAR
    lead_vol = 0.35 if section == 2 else 0.2
    t = bar_start
    mel_idx = (bar % 4) * 4  # cycle through melody

    for i in range(4):
        idx = (mel_idx + i) % len(melody)
        note, octave, dur_beats = melody[idx]
        freq = note_freq(note, octave)
        dur = dur_beats * BEAT

        # Supersaw lead
        layers = []
        for detune in [-0.06, -0.03, 0, 0.03, 0.06]:
            layers.append(saw(freq * (1 + detune * 0.1), dur, lead_vol / 5))
        combined = mix(layers)
        filtered = lpf(combined, 4000)
        shaped = env(filtered, attack=0.02, decay=0.1, sustain=0.6, release=0.15)
        place(lead_track, shaped, t)
        t += dur

# Pad chords
chords = [
    [('E', 3), ('G', 3), ('B', 3)],
    [('C', 3), ('E', 3), ('G', 3)],
    [('D', 3), ('F#', 3), ('A', 3)],
    [('A', 2), ('C', 3), ('E', 3)],
]

for bar in range(TOTAL_BARS):
    section = bar // 8
    if section == 0:
        continue

    bar_start = bar * BAR
    chord = chords[bar % 4]
    pad_vol = 0.1 if section == 1 else (0.2 if section == 2 else 0.12)

    for note, octave in chord:
        freq = note_freq(note, octave)
        raw = sine(freq, BAR * 0.95, pad_vol)
        raw2 = sine(freq * 1.003, BAR * 0.95, pad_vol * 0.5)
        combined = [raw[i] + raw2[i] for i in range(len(raw))]
        shaped = env(combined, attack=0.3, decay=0.2, sustain=0.7, release=0.5)
        place(pad_track, shaped, bar_start)

# Riser/sweep before drop (bar 14-15)
riser_start = 14 * BAR
riser_dur = 2 * BAR
riser_n = int(RATE * riser_dur)
riser = []
for i in range(riser_n):
    t = i / RATE
    progress = t / riser_dur
    freq = 200 + progress * progress * 8000
    vol = 0.15 * progress
    riser.append(vol * (math.sin(2 * math.pi * freq * t) + 0.3 * (random.random() * 2 - 1) * progress))
riser = lpf(riser, 6000)
place(lead_track, riser, riser_start)

# Final mix
print("Mixing...")
final = mix([drums, bass_track, lead_track, pad_track])
final = normalize(final, 0.85)

# Write WAV
print("Writing WAV...")
with wave.open("edm_track.wav", "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(RATE)
    for s in final:
        s = max(-1.0, min(1.0, s))
        wf.writeframes(struct.pack('<h', int(s * 32767)))

print(f"Done! edm_track.wav ({DURATION:.1f}s, {BPM} BPM, {TOTAL_BARS} bars)")
