"""RAX3D general follow ad v3 (works on any platform): instant color burst hook -> CTA rows with tap simulation -> slogan end card."""
import sys, math, subprocess, wave
sys.path.insert(0, '/home/claude/p1')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from anim import W, H, FPS, ease, ease_back, put, sweep, make_particles, draw_particles, to_story, WM
from promo import ar_layer, ar_plain, icon

COL = [(25, 25, 28), (210, 32, 38), (20, 100, 215), (238, 236, 230), (34, 150, 70), (240, 120, 20), (236, 92, 150), (205, 160, 60)]
LBL = (70, 50, 20, 255)

def tint_logo(c, w=330):
    wa = np.asarray(WM.split()[3]); wl = np.asarray(WM.convert('L')).astype(float) / 255
    k = (.55 + .6 * wl)[..., None]
    if sum(c) > 600: k = (.78 + .3 * wl)[..., None]
    if sum(c) < 100: k = (.9 + 2.2 * wl)[..., None]
    arr = np.zeros((WM.height, WM.width, 4), np.uint8); arr[..., :3] = np.clip(np.array(c, float) * k, 0, 255); arr[..., 3] = wa
    im = Image.fromarray(arr, 'RGBA'); return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)

def tap_dot(t):
    """touch indicator: white dot + expanding ripple; t = time since press"""
    S = 260; im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im); c = S / 2
    for k in range(2):
        rt = t - k * .12
        if 0 < rt < .6:
            r = 30 + 100 * ease(rt / .6); a = int(200 * (1 - rt / .6))
            d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, a), width=6)
    r = 34 * (1 - .25 * max(0, 1 - abs(t) / .15)) if t > -1 else 34
    sh = Image.new('RGBA', (S, S)); ImageDraw.Draw(sh).ellipse([c - r - 4, c - r + 6, c + r + 4, c + r + 14], fill=(60, 40, 10, 90))
    im = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), im); d = ImageDraw.Draw(im)
    d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255, 235), outline=(214, 172, 86, 255), width=4)
    return im

def mini_heart(size, col=(237, 73, 86)):
    im = Image.new('RGBA', (size, size)); d = ImageDraw.Draw(im); r = size * .25; cx, cy = size / 2, size * .4
    d.ellipse([cx - 2 * r, cy - r, cx, cy + r], fill=col + (255,)); d.ellipse([cx, cy - r, cx + 2 * r, cy + r], fill=col + (255,))
    d.polygon([(cx - 1.97 * r, cy + .25 * r), (cx, cy), (cx + 1.97 * r, cy + .25 * r), (cx, cy + 2.3 * r)], fill=col + (255,))
    return im

def red_heart_icon(size=150):
    base = icon('heart', size); a = np.asarray(base).copy()
    dark = (a[..., 0] < 80) & (a[..., 3] > 100)
    a[dark, 0], a[dark, 1], a[dark, 2] = 237, 73, 86
    return Image.fromarray(a, 'RGBA')

def bubble(text_layer, prog):
    w = text_layer.width + 60; h = text_layer.height + 44
    im = Image.new('RGBA', (w + 10, h + 40)); d = ImageDraw.Draw(im); o = 36
    d.rounded_rectangle([0, o, w, h + o], radius=36, fill=(255, 255, 255, 245), outline=(214, 172, 86, 255), width=3)
    d.polygon([(w - 90, o + 2), (w - 50, o + 2), (w - 40, 0)], fill=(255, 255, 255, 245))
    d.line([(w - 90, o + 1), (w - 40, 0), (w - 50, o + 1)], fill=(214, 172, 86, 255), width=3)
    # reveal text right->left (Arabic)
    tw = text_layer.width; vis = int(tw * prog)
    if vis > 0:
        crop = text_layer.crop((tw - vis, 0, tw, text_layer.height))
        im.alpha_composite(crop, (30 + tw - vis, 22 + 36))
    return im

def render_follow3(bg, out, dur=11.0, seed=7):
    base, top = to_story(Image.open(bg)); base = base.convert('RGBA').filter(ImageFilter.GaussianBlur(18))
    veil = Image.new('RGBA', (W, H), (250, 243, 230, 120)); base.alpha_composite(veil)
    P = make_particles({}, seed)
    T1 = ar_layer('خلك قريب منّا', 112)
    T2 = ar_plain('جديدنا ينزل أول بأول… خلك متابع', 44, (110, 78, 30, 255), 'Bold')
    T3 = ar_layer('اطلب قطعتك… باللون اللي تبيه', 72, glow=.4)
    TW = [tint_logo(c) for c in COL]
    rows = [('follow', 'تابعنا', 'تمت المتابعة'), ('bell', 'فعّل الجرس', 'الجرس مفعّل'), ('heart', 'لايك', 'لايك ❤'), ('comment', 'كومنت', 'كومنت')]
    ICON = {k: icon(k, 150) for k, _, _ in rows}; ICON_RED = red_heart_icon(150)
    L0 = [ar_plain(a, 62, LBL, 'ExtraBold') for _, a, _ in rows]
    L1 = [ar_plain(b.replace(' ❤', ''), 52, (40, 120, 60, 255) if i < 2 else LBL, 'ExtraBold') for i, (_, _, b) in enumerate(rows)]
    CMT = ar_plain('أبي هذي القطعة بالأحمر!', 46, (40, 30, 15, 255), 'Bold')
    color_end, cta_t = 3.8, 4.1
    taps = [6.0, 7.1, 8.2, 9.3]; tap_times = taps
    row_y = [640 + j * 215 for j in range(4)]; icon_x = W / 2 + 280 - 85
    MH = mini_heart(56)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', out], stdin=subprocess.PIPE)
    n = len(COL); per = .35
    for i in range(int(FPS * dur)):
        t = i / FPS; fr = base.copy()
        ci = int(t / per) % n
        # background color wash during color scene
        if t < color_end + .4:
            wa_ = .16 * (1 - max(0, (t - color_end) / .4))
            wash = Image.new('RGBA', (W, H), COL[ci] + (int(255 * wa_),)); fr.alpha_composite(wash)
        fr.alpha_composite(draw_particles(P, t, {}))
        if t < .25:  # opening flash
            fr.alpha_composite(Image.new('RGBA', (W, H), (255, 250, 240, int(255 * (1 - t / .25)))))
        # titles
        a1 = ease((t - .35) / .5); put(fr, sweep(T1, (t - 1.2) / .9) if 1.2 < t < 2.1 else T1, W / 2, 330 + 30 * (1 - a1), a1)
        put(fr, T2, W / 2, 440, ease((t - .7) / .5))
        # color burst (instant hook)
        if t < color_end + .5:
            fade = 1 - max(0, (t - color_end) / .5); cx, cy = W / 2, 1000
            collapse = ease(max(0, (t - color_end + .1) / .5))
            for j, c in enumerate(COL):
                tj = t - j * .05
                if tj <= 0: continue
                e = ease_back(min(1, tj / .45)) * (1 - collapse)
                ang = -math.pi / 2 + j * 2 * math.pi / n + .35 * t
                R = 255 * e; x = cx + R * math.cos(ang); y = cy + R * math.sin(ang)
                r = 62 * min(1, tj / .3) * (1 + .1 * math.sin(t * 6 + j) + (.25 if j == ci else 0))
                lay = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(lay)
                d.ellipse([x - r - 12, y - r - 12, x + r + 12, y + r + 12], fill=(255, 235, 190, int(110 * fade)))
                lay = lay.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(lay)
                d.ellipse([x - r, y - r, x + r, y + r], fill=c + (int(255 * fade),), outline=(255, 255, 255, int(235 * fade)), width=5)
                fr.alpha_composite(lay)
            put(fr, TW[ci], cx, cy, min(1, t / .3) * fade, .7 + .3 * ease_back(min(1, t / .45)) + .05 * math.sin(t * 7))
            put(fr, T3, W / 2, 1420, ease((t - .9) / .5) * fade)
        # CTA rows
        for j, (k, _, _) in enumerate(rows):
            tj = t - cta_t - j * .35
            if tj <= 0: continue
            e = ease_back(min(1, tj / .55)); al = min(1, tj / .25)
            side = 1 if j % 2 == 0 else -1; off = side * 760 * (1 - e); y = row_y[j]
            done = t >= taps[j] + .12
            press = max(0, 1 - abs(t - taps[j] - .06) / .12)
            rw = 560; x0 = W / 2 - rw / 2 + off; rs = 1 - .05 * press
            sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle([x0, y - 82, x0 + rw, y + 92], radius=88, fill=(90, 60, 15, int(70 * al)))
            fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
            fill = (236, 250, 238, int(240 * al)) if (done and j < 2) else (255, 249, 238, int(235 * al))
            gl = Image.new('RGBA', (W, H)); ImageDraw.Draw(gl).rounded_rectangle([x0 + rw * (1 - rs) / 2, y - 88 * rs, x0 + rw - rw * (1 - rs) / 2, y + 88 * rs], radius=88, fill=fill, outline=(214, 172, 86, int(255 * al)), width=4)
            fr.alpha_composite(gl)
            ii = ICON_RED if (k == 'heart' and done) else ICON[k]
            if k == 'bell' and t > taps[j]:
                wob = 16 * math.sin((t - taps[j]) * 18) * math.exp(-(t - taps[j]) * 2.2); ii = ii.rotate(wob, resample=Image.BICUBIC)
            sc = rs * (1 + (.15 * math.exp(-(t - taps[j]) * 5) if (k == 'heart' and done) else 0))
            put(fr, ii, x0 + rw - 85, y, al, sc)
            lb = L1[j] if (done and j < 3 and k != 'heart') else L0[j]
            put(fr, lb, x0 + (rw - 170) / 2 + 10, y + 4, al)
            if k == 'heart' and done:  # floating mini hearts
                for q in range(6):
                    ht = t - taps[j] - q * .08
                    if 0 < ht < 1.2:
                        hx = x0 + rw - 85 + 40 * math.sin(q * 2.1 + ht * 4); hy = y - 40 - 260 * ease(ht / 1.2)
                        put(fr, MH, hx, hy, 1 - ht / 1.2, .6 + .4 * ease(ht / .3))
            if k == 'comment' and t > taps[j] + .2:
                pr = min(1, (t - taps[j] - .3) / .9)
                b = bubble(CMT, max(0, pr)); ba = ease((t - taps[j] - .2) / .25)
                put(fr, b, W / 2 - 40, y + 210, ba, .8 + .2 * ease_back(min(1, (t - taps[j] - .2) / .3)))
        # tap indicator travelling between icons
        for j, tt in enumerate(taps):
            st = tt - .45
            if st <= t < tt + .55 and t >= cta_t + 1.6:
                p0 = (W / 2 + 120, 1500) if j == 0 else (icon_x, row_y[j - 1])
                mv = ease(min(1, (t - st) / .4)); x = p0[0] + (icon_x - p0[0]) * mv; y = p0[1] + (row_y[j] - p0[1]) * mv + 30
                put(fr, tap_dot(t - tt), x + 25, y + 25, min(1, (t - st) / .15) * (1 - max(0, (t - tt - .35) / .2)))
        ff.stdin.write(np.asarray(fr.convert('RGB')).tobytes())
    ff.stdin.close(); ff.wait()
    return taps, color_end, cta_t

def add_clicks(wav_in, wav_out, times, gain=.45):
    w = wave.open(wav_in); sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(float) / 32767; w.close()
    n = int(.05 * sr); tt = np.arange(n) / sr
    click = (np.sin(2 * np.pi * 2200 * tt) * .6 + np.random.randn(n) * .4) * np.exp(-tt * 140)
    for t0 in times:
        i = int(t0 * sr); j = min(len(a), i + n)
        a[i:j, 0] += gain * click[:j - i]; a[i:j, 1] += gain * click[:j - i]
    a = np.clip(a, -1, 1)
    with wave.open(wav_out, 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr); f.writeframes((a * 32767).astype(np.int16).tobytes())
