import wave, struct, math, random

RATE = 44100
BPM = 92
BEAT = 60.0 / BPM

def sine(freq, t):
    return math.sin(2 * math.pi * freq * t)

def envelope(t, dur, attack=0.01, decay=0.05, sustain=0.7, release=0.15):
    rel_start = dur - release
    if t < attack:
        return t / attack
    if t < attack + decay:
        return 1.0 - (1.0 - sustain) * ((t - attack) / decay)
    if t < rel_start:
        return sustain
    if t < dur:
        return sustain * (1.0 - (t - rel_start) / release)
    return 0.0

def synth(freq, dur, vol=0.3, bright=0.4):
    samples = []
    n = int(RATE * dur)
    for i in range(n):
        t = i / RATE
        env = envelope(t, dur, attack=0.005, release=min(0.2, dur * 0.3))
        s = sine(freq, t)
        s += bright * sine(freq * 2, t)
        s += bright * 0.5 * sine(freq * 3, t)
        s += bright * 0.25 * sine(freq * 4, t)
        samples.append(s * env * vol)
    return samples

def pad(freq, dur, vol=0.18):
    samples = []
    n = int(RATE * dur)
    for i in range(n):
        t = i / RATE
        env = envelope(t, dur, attack=0.3, decay=0.1, sustain=0.8, release=0.4)
        s = sine(freq, t) + 0.5 * sine(freq * 2.001, t) + 0.3 * sine(freq * 0.999, t)
        samples.append(s * env * vol)
    return samples

def bass(freq, dur, vol=0.35):
    samples = []
    n = int(RATE * dur)
    for i in range(n):
        t = i / RATE
        env = envelope(t, dur, attack=0.008, decay=0.1, sustain=0.6, release=0.1)
        s = sine(freq, t) + 0.6 * sine(freq * 2, t) + 0.2 * sine(freq * 0.5, t)
        samples.append(s * env * vol)
    return samples

def kick(dur=0.25, vol=0.5):
    samples = []
    n = int(RATE * dur)
    for i in range(n):
        t = i / RATE
        freq = 150 * math.exp(-t * 30) + 45
        env = math.exp(-t * 12)
        samples.append(sine(freq, t) * env * vol)
    return samples

def hihat(dur=0.08, vol=0.12):
    samples = []
    n = int(RATE * dur)
    for i in range(n):
        t = i / RATE
        env = math.exp(-t * 60)
        s = random.uniform(-1, 1)
        samples.append(s * env * vol)
    return samples

def snare(dur=0.15, vol=0.3):
    samples = []
    n = int(RATE * dur)
    for i in range(n):
        t = i / RATE
        env = math.exp(-t * 20)
        tone = sine(200, t) * 0.5
        noise = random.uniform(-1, 1) * 0.7
        samples.append((tone + noise) * env * vol)
    return samples

def note(name):
    names = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}
    if name[-1].isdigit():
        octave = int(name[-1])
        pitch = name[:-1]
    else:
        octave = 4
        pitch = name
    midi = 12 * (octave + 1) + names[pitch]
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def mix(base, overlay, offset_samples):
    while len(base) < offset_samples + len(overlay):
        base.append(0.0)
    for i, s in enumerate(overlay):
        base[offset_samples + i] += s

def beats(b):
    return int(RATE * BEAT * b)

random.seed(42)

track = []

# -- Song structure: Intro(4bars) | VerseA(8bars) | Chorus(8bars) | VerseB(8bars) | Chorus(8bars) | Outro(4bars)
# Key: D minor (D E F G A Bb C)

# Chord progressions
verse_chords = [
    (['D3','F3','A3'], 4),    # Dm
    (['Bb2','D3','F3'], 4),   # Bb
    (['C3','E3','G3'], 4),    # C
    (['A2','C#3','E3'], 4),   # A
]

chorus_chords = [
    (['F3','A3','C4'], 4),    # F
    (['G3','Bb3','D4'], 4),   # Gm
    (['Bb2','D3','F3'], 4),   # Bb
    (['C3','E3','G3'], 2),    # C
    (['A2','C#3','E3'], 2),   # A
]

# Melodies (note, duration_in_beats)
verse_melody = [
    ('D5',1),('F5',1),('E5',0.5),('D5',0.5),('C5',1),
    ('D5',1),('Bb4',1),('A4',2),
    ('C5',1),('E5',1),('D5',0.5),('C5',0.5),('Bb4',1),
    ('A4',1),('G4',1),('A4',2),
]

chorus_melody = [
    ('F5',1.5),('A5',0.5),('G5',1),('F5',1),
    ('G5',1),('Bb5',1),('A5',2),
    ('Bb5',1),('D5',1),('F5',0.5),('E5',0.5),('D5',1),
    ('C5',1),('D5',1),('E5',1),('D5',1),
]

bass_verse = [
    ('D2',4),('Bb1',4),('C2',4),('A1',4),
]

bass_chorus = [
    ('F2',4),('G2',4),('Bb1',4),('C2',2),('A1',2),
]

def lay_chords(track, chords, start_beat, repeats=1):
    pos = start_beat
    for _ in range(repeats):
        for notes, dur in chords:
            for n in notes:
                mix(track, pad(note(n), BEAT * dur), beats(pos))
            pos += dur

def lay_melody(track, melody, start_beat, repeats=1):
    pos = start_beat
    for _ in range(repeats):
        for n, dur in melody:
            mix(track, synth(note(n), BEAT * dur, vol=0.25, bright=0.3), beats(pos))
            pos += dur

def lay_bass(track, bassline, start_beat, repeats=1):
    pos = start_beat
    for _ in range(repeats):
        for n, dur in bassline:
            mix(track, bass(note(n), BEAT * dur), beats(pos))
            pos += dur

def lay_drums(track, start_beat, num_bars, intensity=1.0):
    for bar in range(num_bars):
        bpos = start_beat + bar * 4
        # Kick on 1 and 3
        mix(track, kick(vol=0.45 * intensity), beats(bpos))
        mix(track, kick(vol=0.35 * intensity), beats(bpos + 2))
        # Snare on 2 and 4
        mix(track, snare(vol=0.25 * intensity), beats(bpos + 1))
        mix(track, snare(vol=0.25 * intensity), beats(bpos + 3))
        # Hi-hats on eighth notes
        for eighth in range(8):
            vol = 0.10 if eighth % 2 == 0 else 0.06
            mix(track, hihat(vol=vol * intensity), beats(bpos + eighth * 0.5))

# === INTRO (4 bars, just pads + light melody) ===
lay_chords(track, verse_chords, 0)
# gentle intro melody
intro_melody = [('A4',2),('D5',1),('F5',1),('E5',2),('D5',2),
                ('C5',1),('Bb4',1),('A4',2),('D5',1),('A4',1)]
lay_melody(track, intro_melody, 0)

# === VERSE A (8 bars) ===
v1_start = 16
lay_chords(track, verse_chords, v1_start, repeats=2)
lay_melody(track, verse_melody, v1_start, repeats=1)
# second pass with variation
verse_melody2 = [
    ('D5',1),('E5',1),('F5',0.5),('E5',0.5),('D5',1),
    ('C5',1),('A4',1),('Bb4',2),
    ('C5',1),('D5',1),('E5',0.5),('D5',0.5),('C5',1),
    ('A4',1),('Bb4',1),('A4',2),
]
lay_melody(track, verse_melody2, v1_start + 16)
lay_bass(track, bass_verse, v1_start, repeats=2)
lay_drums(track, v1_start, 8, intensity=0.7)

# === CHORUS 1 (8 bars) ===
c1_start = v1_start + 32
lay_chords(track, chorus_chords, c1_start, repeats=2)
lay_melody(track, chorus_melody, c1_start, repeats=2)
lay_bass(track, bass_chorus, c1_start, repeats=2)
lay_drums(track, c1_start, 8, intensity=1.0)

# === VERSE B (8 bars) ===
v2_start = c1_start + 32
lay_chords(track, verse_chords, v2_start, repeats=2)
verse_melody3 = [
    ('F5',0.5),('E5',0.5),('D5',1),('C5',1),('D5',1),
    ('Bb4',2),('A4',1),('G4',1),
    ('A4',1),('C5',1),('D5',1),('E5',1),
    ('F5',1),('E5',0.5),('D5',0.5),('C5',1),('A4',1),
]
lay_melody(track, verse_melody3, v2_start)
lay_melody(track, verse_melody, v2_start + 16)
lay_bass(track, bass_verse, v2_start, repeats=2)
lay_drums(track, v2_start, 8, intensity=0.8)

# === CHORUS 2 (8 bars) ===
c2_start = v2_start + 32
lay_chords(track, chorus_chords, c2_start, repeats=2)
lay_melody(track, chorus_melody, c2_start, repeats=2)
lay_bass(track, bass_chorus, c2_start, repeats=2)
lay_drums(track, c2_start, 8, intensity=1.0)

# === OUTRO (4 bars, fade) ===
outro_start = c2_start + 32
lay_chords(track, verse_chords, outro_start)
outro_melody = [('D5',2),('A4',2),('F5',1),('E5',1),('D5',2),
                ('A4',1),('Bb4',1),('A4',2),('D4',2)]
lay_melody(track, outro_melody, outro_start)
lay_bass(track, bass_verse, outro_start)
lay_drums(track, outro_start, 4, intensity=0.5)

# Fade out last 2 bars
fade_start = beats(outro_start + 8)
fade_len = len(track) - fade_start
for i in range(fade_len):
    track[fade_start + i] *= max(0, 1.0 - i / fade_len)

# Normalize
peak = max(abs(s) for s in track) or 1.0
track = [s / peak * 0.9 for s in track]

# Write WAV
with wave.open('original_song.wav', 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    for s in track:
        clamped = max(-1.0, min(1.0, s))
        w.writeframes(struct.pack('<h', int(clamped * 32767)))

print(f"Done! Generated original_song.wav ({len(track)/RATE:.1f} seconds)")
