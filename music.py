"""Original RAX3D luxury story music (procedural, royalty-free).
Timeline matches spotlight style: whoosh build 0-2.2s, impact at 2.2s, groove after, chime when product appears."""
import numpy as np, wave, sys
SR = 44100

def note(n):  # midi -> Hz
    return 440 * 2 ** ((n - 69) / 12)

def env(n, a, d, s=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * (s + (1 - s) * np.exp(-t / d))
    return e

def pad(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):
            ff = f * 2 ** (det / 12)
            for h, amp in ((1, 1), (2, .35), (3, .15)):
                y += amp * np.sin(2 * np.pi * ff * h * t + np.random.rand() * 6.28)
    y /= len(freqs) * 3
    a = np.minimum(1, t / .9) * np.minimum(1, (dur - t) / .9)
    return y * a

def pluck(f, dur, bright=.5):
    n = int(dur * SR); p = max(2, int(SR / f))
    buf = np.random.uniform(-1, 1, p); y = np.zeros(n)
    for i in range(n):
        y[i] = buf[i % p]
        buf[i % p] = .996 * (bright * buf[i % p] + (1 - bright) * buf[(i + 1) % p])
    return y * env(n, .002, .6)

def bell(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for r, a, d in ((1, 1, 1.4), (2.76, .5, .8), (5.4, .25, .4), (8.9, .12, .25)):
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return y * np.minimum(1, t / .003)

def kick(dur=.45):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 18) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)

def shaker(dur=.08):
    n = int(dur * SR); y = np.random.randn(n); y = y - np.convolve(y, np.ones(4) / 4, 'same')
    return y * np.exp(-np.arange(n) / SR * 60)

def whoosh(dur):
    n = int(dur * SR); x = np.random.randn(n); t = np.arange(n) / SR
    out = np.zeros(n); a = 0.0; ycur = 0.0
    for i in range(n):  # sweeping one-pole lowpass
        a = .01 + .25 * (t[i] / dur) ** 2
        ycur += a * (x[i] - ycur); out[i] = ycur
    return out * (t / dur) ** 2

def add(buf, x, at, g=1.0):
    i = int(at * SR); j = min(len(buf), i + len(x))
    if i < len(buf): buf[i:j] += g * x[:j - i]

def make(dur=7.0, land=2.2, appear=2.8, bpm=96, seed=3, out='music.wav'):
    np.random.seed(seed)
    N = int(dur * SR); L = np.zeros(N); R = np.zeros(N)
    # chords: Fmaj9 - Am7 - Dm9 - Bbmaj7 (warm, premium)
    chords = [[53, 57, 60, 64, 67], [57, 60, 64, 67], [50, 57, 60, 64, 65], [46, 53, 57, 62]]
    bar = 60 / bpm * 4; t = 0; k = 0
    while t < dur:
        c = chords[k % 4]; p = pad([note(m) for m in c], min(bar + .9, dur - t + .01))
        add(L, p, t, .16); add(R, p, t, .16); t += bar; k += 1
    # whoosh build + impact
    w = whoosh(land); add(L, w, 0, .22); add(R, w, 0, .22)
    imp = kick(1.2) * 1.2; add(L, imp, land, .55); add(R, imp, land, .55)
    for f in (note(77), note(81), note(84)):
        b = bell(f, 2.5); add(L, b, land, .05); add(R, b, land + .012, .05)
    # groove after landing
    beat = 60 / bpm; t = land + beat; i = 0
    arp = [65, 69, 72, 76, 72, 69]
    while t < dur - .3:
        if i % 2 == 0: add(L, kick(), t, .38); add(R, kick(), t, .38)
        s = shaker(); add(L, s, t + beat / 2, .05); add(R, s, t + beat / 2 + .004, .05)
        c = chords[int(t / bar) % 4]
        for h in range(2):
            m = c[(i * 2 + h) % len(c)] + 12
            pl = pluck(note(m), .9, .55); tt = t + h * beat / 2
            add(L, pl, tt, .10 if h else .07); add(R, pl, tt + .008, .07 if h else .10)
        t += beat; i += 1
    # chime when product appears (+ repeats for cycling items)
    for at in (appear,) if isinstance(appear, (int, float)) else appear:
        for j, m in enumerate((84, 88, 91)):
            b = bell(note(m), 2.0); add(L, b, at + j * .07, .07); add(R, b, at + j * .07 + .01, .07)
    st = np.stack([L, R], 1)
    fade = np.minimum(1, (dur - np.arange(N) / SR) / .9)[:, None]; st *= fade
    st /= (np.abs(st).max() + 1e-9); st = np.tanh(st * 2.4) / np.tanh(2.4)
    st *= .92 / (np.abs(st).max() + 1e-9)
    with wave.open(out, 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((st * 32767).astype(np.int16).tobytes())
    return out

def mux(video, wav, out):
    import subprocess
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', video, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', out], check=True)

if __name__ == '__main__':
    make(float(sys.argv[1]) if len(sys.argv) > 1 else 7.0)
