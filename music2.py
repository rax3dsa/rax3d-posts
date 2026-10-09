"""Extra original music styles for RAX3D stories."""
import numpy as np, wave, sys
sys.path.insert(0, '/home/claude/p1')
from music import SR, note, env, pad, pluck, bell, kick, shaker, whoosh, add, mux

def clap(dur=.18):
    n = int(dur * SR); y = np.random.randn(n); t = np.arange(n) / SR
    e = np.exp(-t * 30) + .6 * np.exp(-np.maximum(0, t - .012) * 30) * (t > .012)
    y = y - np.convolve(y, np.ones(6) / 6, 'same'); return y * e

def hat(dur=.05):
    n = int(dur * SR); y = np.random.randn(n); y = y - np.convolve(y, np.ones(3) / 3, 'same')
    return y * np.exp(-np.arange(n) / SR * 90)

def doum(dur=.5):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(85 * np.exp(-t * 6) + 60) / SR) * np.exp(-t * 6)

def tak(dur=.12):
    n = int(dur * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 420 * t) * .6 + np.random.randn(n) * .5
    return tone * np.exp(-t * 45)

def taiko(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 4) + 38) / SR) * np.exp(-t * 3.2)
    return body + np.random.randn(n) * np.exp(-t * 25) * .3

def strings(freqs, dur, attack=1.5):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    vib = 1 + .004 * np.sin(2 * np.pi * 5.2 * t)
    for f in freqs:
        for det in (-.08, .0, .08):
            ph = 2 * np.pi * np.cumsum(f * 2 ** (det / 12) * vib) / SR
            for h in range(1, 7): y += np.sin(h * ph) / h
    y /= len(freqs) * 3 * 2
    return y * np.minimum(1, t / attack) * np.minimum(1, (dur - t) / .8)

def oud(f, dur):
    y = pluck(f, dur, .35)
    y += .3 * pluck(f * 2.001, dur, .3)
    return y * env(len(y), .001, .45)

def finish(L, R, dur, out):
    st = np.stack([L, R], 1); N = len(L)
    st *= np.minimum(1, (dur - np.arange(N) / SR) / .9)[:, None]
    st /= np.abs(st).max() + 1e-9; st = np.tanh(st * 2.4) / np.tanh(2.4); st *= .92 / np.abs(st).max()
    with wave.open(out, 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((st * 32767).astype(np.int16).tobytes())
    return out

def chimes(L, R, appear, notes=(84, 88, 91), g=.07):
    for at in appear:
        for j, m in enumerate(notes):
            b = bell(note(m), 2.0); add(L, b, at + j * .07, g); add(R, b, at + j * .07 + .01, g)

def energetic(dur, land, appear, out, seed=5):
    np.random.seed(seed); N = int(dur * SR); L = np.zeros(N); R = np.zeros(N); bpm = 124; beat = 60 / bpm
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    w = whoosh(land); add(L, w, 0, .3); add(R, w, 0, .3)
    # riser of hats before drop
    t = land - 1.0
    for k in range(16): add(L, hat(), t + k * (1.0 / 16), .05 + k * .01); add(R, hat(), t + k * (1.0 / 16), .05 + k * .01)
    add(L, kick(1.0), land, .6); add(R, kick(1.0), land, .6)
    t = land; i = 0
    while t < dur - .2:
        add(L, kick(), t, .5); add(R, kick(), t, .5)
        if i % 2 == 1: c = clap(); add(L, c, t, .18); add(R, c, t + .006, .18)
        add(L, hat(), t + beat / 2, .07); add(R, hat(), t + beat / 2, .07)
        ch = chords[(i // 4) % 4]
        bass = pluck(note(ch[0] - 12), beat * .9, .7); add(L, bass, t + beat / 2, .22); add(R, bass, t + beat / 2, .22)
        for h in range(4):
            m = ch[h % 3] + 12 + (12 if h == 3 else 0)
            p = pluck(note(m), .4, .75); add(L, p, t + h * beat / 4, .06); add(R, p, t + h * beat / 4 + .006, .06)
        t += beat; i += 1
    bar = beat * 4; t = land; k = 0
    while t < dur:
        p = pad([note(m + 12) for m in chords[k % 4]], min(bar + .5, dur - t + .01)); add(L, p, t, .08); add(R, p, t, .08); t += bar; k += 1
    chimes(L, R, appear, (88, 91, 96), .06)
    return finish(L, R, dur, out)

def calm(dur, land, appear, out, seed=7):
    np.random.seed(seed); N = int(dur * SR); L = np.zeros(N); R = np.zeros(N)
    chords = [[52, 59, 64, 66, 71], [48, 55, 62, 64, 67], [45, 52, 59, 64], [47, 54, 59, 62, 66]]
    bar = 2.6; t = 0; k = 0
    while t < dur:
        p = pad([note(m) for m in chords[k % 4]], min(bar + 1.2, dur - t + .01)); add(L, p, t, .2); add(R, p, t, .2); t += bar; k += 1
    w = whoosh(land) * .6; add(L, w, 0, .12); add(R, w, 0, .12)
    for f in (note(76), note(83), note(88)):
        b = bell(f, 3.0); add(L, b, land, .07); add(R, b, land + .02, .07)
    # sparse piano-like notes
    mel = [76, 79, 83, 81, 79, 76, 74, 76]; t = land + .4; i = 0
    while t < dur - .5:
        p = pluck(note(mel[i % len(mel)]), 1.6, .3) + .4 * bell(note(mel[i % len(mel)]), 1.6) * .3
        add(L, p, t, .12); add(R, p, t + .015, .12); t += .62; i += 1
    chimes(L, R, appear, (83, 88, 95), .05)
    return finish(L, R, dur, out)

def arabic(dur, land, appear, out, seed=9):
    np.random.seed(seed); N = int(dur * SR); L = np.zeros(N); R = np.zeros(N)
    # D Hijaz: D Eb F# G A Bb C D
    scale = [62, 63, 66, 67, 69, 70, 72, 74]
    drone = pad([note(50), note(57)], dur); add(L, drone, 0, .12); add(R, drone, 0, .12)
    w = whoosh(land); add(L, w, 0, .2); add(R, w, 0, .2)
    add(L, doum(1.0), land, .7); add(R, doum(1.0), land, .7)
    for f in (note(74), note(81)):
        b = bell(f, 2.2); add(L, b, land, .05); add(R, b, land + .015, .05)
    # maqsum rhythm: D T - T D - T -  (8 eighths)
    bpm = 100; e = 60 / bpm / 2; pat = ['D', 'T', '', 'T', 'D', '', 'T', '']
    t = land; i = 0
    while t < dur - .2:
        s = pat[i % 8]
        if s == 'D': add(L, doum(), t, .5); add(R, doum(), t, .5)
        if s == 'T': tk = tak(); add(L, tk, t, .22); add(R, tk, t + .004, .22)
        t += e; i += 1
    # oud melody phrase in Hijaz
    phrase = [0, 1, 2, 3, 4, 3, 2, 1, 2, 1, 0, -1, 0, 2, 4, 5, 4, 3, 2, 1, 0]
    t = .3; i = 0
    while t < dur - .4:
        idx = phrase[i % len(phrase)]; m = scale[idx] if idx >= 0 else 60
        o = oud(note(m), .9); add(L, o, t, .2); add(R, o, t + .01, .2)
        if i % 4 == 3: o2 = oud(note(m), .5); add(L, o2, t + e / 2, .12); add(R, o2, t + e / 2, .12)
        t += e * (2 if t < land else 1); i += 1
    chimes(L, R, appear, (74, 78, 81), .05)
    return finish(L, R, dur, out)

def cinematic(dur, land, appear, out, seed=11):
    np.random.seed(seed); N = int(dur * SR); L = np.zeros(N); R = np.zeros(N)
    s1 = strings([note(m) for m in (38, 45, 50, 53, 57)], land + .3, attack=land); add(L, s1, 0, .25); add(R, s1, 0, .25)
    w = whoosh(land); add(L, w, 0, .3); add(R, w, 0, .3)
    # braam at impact
    n = int(2.5 * SR); t = np.arange(n) / SR; br = np.zeros(n)
    for f in (note(26), note(38), note(45)):
        ph = 2 * np.pi * f * t; br += np.tanh(3 * np.sin(ph)) / 3
    br *= np.exp(-t * 1.2) * np.minimum(1, t / .02); add(L, br, land, .45); add(R, br, land, .45)
    add(L, taiko(), land, .6); add(R, taiko(), land, .6)
    chords = [[38, 50, 53, 57], [34, 46, 50, 53], [41, 48, 53, 57], [36, 48, 52, 55]]
    bar = 2.0; t = land; k = 0
    while t < dur:
        s = strings([note(m) for m in chords[k % 4]], min(bar + .6, dur - t + .01), attack=.4); add(L, s, t, .22); add(R, s, t, .22); t += bar; k += 1
    beat = 60 / 90; t = land + beat * 2; i = 0
    while t < dur - .4:
        g = .45 if i % 4 == 0 else .25
        add(L, taiko(.8), t, g); add(R, taiko(.8), t, g); t += beat if i % 4 != 2 else beat / 2; i += 1
    chimes(L, R, appear, (74, 81, 86), .06)
    return finish(L, R, dur, out)

STYLES = {'energetic': energetic, 'calm': calm, 'arabic': arabic, 'cinematic': cinematic}

if __name__ == '__main__':
    v = '/mnt/user-data/outputs/rax3d_posts/v3/story-chips.mp4'
    for name, fn in STYLES.items():
        w = fn(10.0, 2.2, [2.8, 5.2, 7.6], f'/home/claude/p1/m_{name}.wav')
        mux(v, w, f'/mnt/user-data/outputs/rax3d_posts/v3/music-{name}.mp4'); print('ok', name)
