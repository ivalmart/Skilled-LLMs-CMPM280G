import numpy as np
import wave
import colorsys
import math
import sys
import os
from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
FPS = 30
CX, CY = W // 2, H // 2
N_PTS = 256
N_BANDS = 64
TRAIL_DECAY = 0.87


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


def analyze(path):
    w = wave.open(path, 'r')
    rate = w.getframerate()
    nframes = w.getnframes()
    raw = w.readframes(nframes)
    w.close()

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    duration = len(samples) / rate
    total = int(duration * FPS)
    spf = rate / FPS

    rms = np.zeros(total)
    centroid = np.zeros(total)
    spectrum = np.zeros((total, N_BANDS))
    waveforms = np.zeros((total, N_PTS))
    edges = np.logspace(np.log10(30), np.log10(16000), N_BANDS + 1)
    wlen = int(spf * 2)

    for i in range(total):
        center = int(i * spf)
        s = max(0, center - wlen // 2)
        e = min(len(samples), s + wlen)
        chunk = samples[s:e]
        if len(chunk) < 64:
            continue

        rms[i] = np.sqrt(np.mean(chunk ** 2))

        win = np.hanning(len(chunk))
        fft = np.abs(np.fft.rfft(chunk * win))
        freqs = np.fft.rfftfreq(len(chunk), 1.0 / rate)

        tot = np.sum(fft)
        if tot > 0:
            centroid[i] = np.sum(freqs * fft) / tot

        for b in range(N_BANDS):
            mask = (freqs >= edges[b]) & (freqs < edges[b + 1])
            if np.any(mask):
                spectrum[i, b] = np.mean(fft[mask])

        idx = np.linspace(0, len(chunk) - 1, N_PTS).astype(int)
        waveforms[i] = chunk[idx]

    # normalize rms
    mx = np.max(rms)
    if mx > 0:
        rms /= mx
    rms = np.convolve(rms, np.ones(5) / 5, mode='same')

    # normalize centroid
    valid = centroid[centroid > 0]
    if len(valid) > 0:
        lo, hi = np.percentile(valid, [5, 95])
        centroid = np.clip((centroid - lo) / (hi - lo + 1e-6), 0, 1)
    centroid = np.convolve(centroid, np.ones(8) / 8, mode='same')

    # normalize spectrum bands
    for b in range(N_BANDS):
        mx = np.percentile(spectrum[:, b], 98) if np.any(spectrum[:, b] > 0) else 1
        if mx > 0:
            spectrum[:, b] = np.clip(spectrum[:, b] / mx, 0, 1)

    # temporal smooth spectrum (exponential)
    smooth = np.zeros_like(spectrum)
    smooth[0] = spectrum[0]
    for i in range(1, total):
        smooth[i] = 0.35 * spectrum[i] + 0.65 * smooth[i - 1]
    spectrum = smooth

    # onsets
    onset_str = np.zeros(total)
    onset_str[1:] = np.maximum(0, np.diff(rms))
    thresh = np.mean(onset_str) + 1.8 * np.std(onset_str)
    onsets = onset_str > thresh
    onset_str = onset_str / (np.max(onset_str) + 1e-6)

    return {
        'n': total,
        'dur': duration,
        'rms': rms,
        'cent': centroid,
        'spec': spectrum,
        'wave': waveforms,
        'onsets': onsets,
        'ostr': onset_str,
    }


def precompute_bg():
    y, x = np.mgrid[0:H, 0:W]
    dx = (x - CX).astype(np.float64)
    dy = (y - CY).astype(np.float64)
    dist = np.sqrt(dx * dx + dy * dy)
    mx = np.sqrt(CX * CX + CY * CY)
    return 1.0 - np.clip(dist / mx, 0, 1)


def precompute_stars(n=200):
    rng = np.random.RandomState(42)
    sx = rng.randint(0, W, n)
    sy = rng.randint(0, H, n)
    brightness = rng.uniform(0.3, 1.0, n)
    phase = rng.uniform(0, 2 * np.pi, n)
    return sx, sy, brightness, phase


def render(feat, fi, trail, pulses, bg_template, stars, angles, band_idx):
    t = fi / FPS
    energy = feat['rms'][fi]
    cent = feat['cent'][fi]
    spec = feat['spec'][fi]
    wv = feat['wave'][fi]
    onset = feat['onsets'][fi]
    ostr = feat['ostr'][fi]

    # colors
    base_hue = (t * 0.012) % 1.0
    hue = (base_hue + cent * 0.3) % 1.0

    # background
    bg_intensity = 6 + energy * 8
    bg_r = bg_intensity * (0.3 + 0.2 * math.sin(hue * 2 * math.pi))
    bg_g = bg_intensity * (0.2 + 0.15 * math.sin(hue * 2 * math.pi + 2.1))
    bg_b = bg_intensity * (0.5 + 0.3 * math.sin(hue * 2 * math.pi + 4.2))
    bg = np.zeros((H, W, 3), dtype=np.float64)
    bg[:, :, 0] = bg_template * bg_r
    bg[:, :, 1] = bg_template * bg_g
    bg[:, :, 2] = bg_template * bg_b

    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)

    # stars
    sx, sy, sb, sp = stars
    for j in range(len(sx)):
        brightness = sb[j] * (0.3 + 0.7 * energy) * (0.5 + 0.5 * math.sin(t * 1.5 + sp[j]))
        if brightness > 0.15:
            c = int(brightness * 80)
            sc = hsv(hue + 0.1, 0.2, brightness * 0.3)
            draw.point((sx[j], sy[j]), fill=sc)

    # radial spectrum lines (32 lines)
    for k in range(32):
        ang = k * 2 * math.pi / 32
        b1 = int(k * N_BANDS / 32)
        b2 = min(N_BANDS - 1, b1 + 1)
        val = (spec[b1] + spec[b2]) / 2
        length = 160 + val * 200 + energy * 40
        x1 = CX + 100 * math.cos(ang)
        y1 = CY + 100 * math.sin(ang)
        x2 = CX + length * math.cos(ang)
        y2 = CY + length * math.sin(ang)
        line_v = 0.15 + val * 0.25
        lc = hsv(hue + k / 64.0, 0.4, line_v)
        draw.line([(int(x1), int(y1)), (int(x2), int(y2))], fill=lc, width=1)

    # organic blob
    base_r = 65 + energy * 130

    freq_r = spec[band_idx] * 90

    noise = (
        np.sin(angles * 3 + t * 1.2) * 14 +
        np.sin(angles * 5 - t * 0.8) * 9 +
        np.sin(angles * 7 + t * 2.1) * 6 +
        np.sin(angles * 2 - t * 0.5) * 18 * energy +
        np.sin(angles * 11 + t * 3.0) * 4 * cent
    )

    radii = base_r + freq_r + noise

    if onset:
        spike = ostr * 65 * (1 + np.sin(angles * 8 + t * 10) * 0.3)
        radii += spike
        pulses.append((fi, ostr))

    # smooth radii circularly
    k = 9
    pad = np.concatenate([radii[-k:], radii, radii[:k]])
    radii = np.convolve(pad, np.ones(k) / k, mode='same')[k:-k]

    xs = CX + radii * np.cos(angles)
    ys = CY + radii * np.sin(angles)
    pts = list(zip(xs.astype(int), ys.astype(int)))

    # draw 3 nested blobs for gradient effect
    for scale, sat, val in [(1.0, 0.85, 0.45), (0.65, 0.7, 0.6), (0.35, 0.5, 0.8)]:
        sxs = CX + radii * scale * np.cos(angles)
        sys_ = CY + radii * scale * np.sin(angles)
        spts = list(zip(sxs.astype(int), sys_.astype(int)))
        c = hsv(hue, sat, val * (0.7 + energy * 0.3))
        draw.polygon(spts, fill=c)

    # glow outline
    glow_c = hsv(hue, 0.3, 0.7 + energy * 0.3)
    for j in range(len(pts)):
        p1 = pts[j]
        p2 = pts[(j + 1) % len(pts)]
        draw.line([p1, p2], fill=glow_c, width=2)

    # waveform ring
    wave_r = 35 + energy * 25
    wpts = []
    for j in range(N_PTS):
        r = wave_r + wv[j] * 22
        x = CX + r * math.cos(angles[j])
        y = CY + r * math.sin(angles[j])
        wpts.append((int(x), int(y)))
    wc = hsv(hue + 0.15, 0.55, 0.65)
    for j in range(len(wpts)):
        draw.line([wpts[j], wpts[(j + 1) % len(wpts)]], fill=wc, width=1)

    # center glow
    glow_r = int(25 + energy * 45)
    for r in range(glow_r, 0, -4):
        frac = 1.0 - r / glow_r
        val = frac ** 1.5
        c = hsv(hue, 0.2 * (1 - frac), val * (0.6 + energy * 0.4))
        draw.ellipse([CX - r, CY - r, CX + r, CY + r], fill=c)

    # pulse rings
    alive = []
    for birth, strength in pulses:
        age = (fi - birth) / FPS
        if age > 2.5:
            continue
        alive.append((birth, strength))
        ring_r = int(120 + age * 280)
        fade = max(0, 1 - age / 2.5) * strength
        rc = hsv(hue + age * 0.1, 0.4 * fade, 0.5 * fade)
        rw = max(1, int(2.5 * (1 - age / 2.5)))
        draw.ellipse([CX - ring_r, CY - ring_r, CX + ring_r, CY + ring_r],
                     outline=rc, width=rw)
    pulses.clear()
    pulses.extend(alive)

    # soft blur for anti-aliasing
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

    arr = np.array(img, dtype=np.float64)

    # trail blend
    if trail is not None:
        blended = np.maximum(trail * TRAIL_DECAY, arr)
    else:
        blended = arr

    out_trail = blended.copy()
    out = np.clip(blended, 0, 255).astype(np.uint8)
    return out, out_trail


def main():
    print("Analyzing audio...")
    base = os.path.dirname(os.path.abspath(__file__))
    feat = analyze(os.path.join(base, 'original_song.wav'))
    n = feat['n']
    print(f"  {feat['dur']:.1f}s, {n} frames @ {FPS}fps")

    print("Precomputing visuals...")
    bg_template = precompute_bg()
    stars = precompute_stars(250)
    angles = np.linspace(0, 2 * np.pi, N_PTS, endpoint=False)
    band_idx = np.linspace(0, N_BANDS - 1, N_PTS).astype(int)

    import imageio
    import imageio_ffmpeg
    import subprocess

    base = os.path.dirname(os.path.abspath(__file__))
    temp = os.path.join(base, 'viz_temp.mp4')
    out = os.path.join(base, 'visualization.mp4')
    audio = os.path.join(base, 'original_song.wav')

    writer = imageio.get_writer(temp, fps=FPS, codec='libx264',
                                quality=8, pixelformat='yuv420p',
                                macro_block_size=1)

    trail = None
    pulses = []

    print("Rendering frames...")
    for i in range(n):
        frame, trail = render(feat, i, trail, pulses, bg_template, stars, angles, band_idx)
        writer.append_data(frame)
        if i % 50 == 0:
            print(f"  {i}/{n} ({i * 100 // n}%)")

    print(f"  {n}/{n} (100%)")
    writer.close()
    print(f"  Temp video: {os.path.getsize(temp) / (1024*1024):.1f} MB")

    print("Muxing audio...")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        ffmpeg, '-y',
        '-i', temp,
        '-i', audio,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        out
    ], check=True)

    if os.path.exists(temp):
        os.remove(temp)

    sz = os.path.getsize(out) / (1024 * 1024)
    print(f"Done: {out} ({sz:.1f} MB)")


if __name__ == '__main__':
    main()
