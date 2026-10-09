"""RAX3D promo story (Snapchat / WhatsApp status): 'new post' announcement + follow/bell/like/comment CTA."""
import sys, math, subprocess
sys.path.insert(0, '/home/claude/p1')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from anim import W, H, FPS, ease, ease_back, put, sweep, make_particles, draw_particles, to_story, WM, pill_layer, gold_layer

FD = '/home/claude/p1/fonts/'
GOLD_TOP, GOLD_BOT = (196, 146, 60), (120, 80, 25)
DARK = (28, 20, 10)

def ar_layer(text, size, weight='ExtraBold', glow=.55):
    f = ImageFont.truetype(FD + f'Tajawal-{weight}.ttf', size)
    d0 = ImageDraw.Draw(Image.new('L', (10, 10)))
    bb = d0.textbbox((0, 0), text, font=f, direction='rtl', language='ar')
    w, h = bb[2] - bb[0] + 60, bb[3] - bb[1] + 60
    m = Image.new('L', (w, h)); ImageDraw.Draw(m).text((30 - bb[0], 30 - bb[1]), text, font=f, fill=255, direction='rtl', language='ar')
    g = Image.new('RGBA', (w, h)); gd = ImageDraw.Draw(g)
    for y in range(h):
        t = y / h; gd.line([(0, y), (w, y)], fill=tuple(int(GOLD_TOP[i] + (GOLD_BOT[i] - GOLD_TOP[i]) * t) for i in range(3)) + (255,))
    g.putalpha(m)
    gl = Image.new('RGBA', (w, h), (255, 240, 210, 0)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * glow)))
    o = Image.new('RGBA', (w, h)); o.alpha_composite(gl); o.alpha_composite(g); return o

def ar_plain(text, size, color, weight='Bold'):
    f = ImageFont.truetype(FD + f'Tajawal-{weight}.ttf', size)
    d0 = ImageDraw.Draw(Image.new('L', (10, 10)))
    bb = d0.textbbox((0, 0), text, font=f, direction='rtl', language='ar')
    w, h = bb[2] - bb[0] + 20, bb[3] - bb[1] + 20
    o = Image.new('RGBA', (w, h)); ImageDraw.Draw(o).text((10 - bb[0], 10 - bb[1]), text, font=f, fill=color, direction='rtl', language='ar')
    return o

# ---------- icons (drawn at 4x then downsampled) ----------
def icon(kind, size=150):
    S = size * 4; im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im)
    # gold disc
    disc = Image.new('RGBA', (S, S)); dd = ImageDraw.Draw(disc)
    for r in range(S // 2, 0, -2):
        k = r / (S / 2); c = tuple(int(255 - (255 - v) * (1 - k * .6)) if False else int(v1 + (v2 - v1) * k) for v1, v2 in zip((246, 214, 140), (176, 124, 44)))
        dd.ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], fill=c + (255,))
    im.alpha_composite(disc); c = DARK + (255,); s = S
    if kind == 'heart':
        r = s * .13; cx, cy = s / 2, s * .45
        d.ellipse([cx - 2 * r, cy - r, cx, cy + r], fill=c); d.ellipse([cx, cy - r, cx + 2 * r, cy + r], fill=c)
        d.polygon([(cx - 1.97 * r, cy + .25 * r), (cx, cy), (cx + 1.97 * r, cy + .25 * r), (cx, cy + 2.3 * r)], fill=c)
    elif kind == 'bell':
        cx = s / 2
        d.pieslice([cx - s * .2, s * .24, cx + s * .2, s * .64], 180, 360, fill=c)
        d.polygon([(cx - s * .2, s * .44), (cx + s * .2, s * .44), (cx + s * .27, s * .66), (cx - s * .27, s * .66)], fill=c)
        d.rounded_rectangle([cx - s * .29, s * .64, cx + s * .29, s * .70], radius=s * .02, fill=c)
        d.ellipse([cx - s * .06, s * .69, cx + s * .06, s * .79], fill=c)
        d.ellipse([cx - s * .035, s * .19, cx + s * .035, s * .26], fill=c)
    elif kind == 'follow':
        d.ellipse([s * .27, s * .22, s * .5, s * .45], fill=c)
        d.pieslice([s * .17, s * .48, s * .6, s * .92], 180, 360, fill=c)
        d.rounded_rectangle([s * .6, s * .45, s * .82, s * .51], radius=s * .02, fill=c)
        d.rounded_rectangle([s * .68, s * .37, s * .74, s * .59], radius=s * .02, fill=c)
    elif kind == 'comment':
        d.ellipse([s * .2, s * .24, s * .8, s * .7], fill=c)
        d.polygon([(s * .3, s * .58), (s * .44, s * .66), (s * .24, s * .8)], fill=c)
        for x in (.37, .5, .63): d.ellipse([s * x - s * .035, s * .435, s * x + s * .035, s * .505], fill=(240, 205, 130, 255))
    return im.resize((size, size), Image.LANCZOS)

def phone_card(post_img, w=560):
    p = Image.open(post_img).convert('RGBA'); ph = int(w * p.height / p.width)
    p = p.resize((w, ph), Image.LANCZOS)
    pad, top_bar, bot_bar = 22, 86, 110
    cw, chh = w + pad * 2, ph + top_bar + bot_bar + pad
    card = Image.new('RGBA', (cw, chh)); d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, chh - 1], radius=48, fill=(255, 252, 246, 255), outline=(214, 172, 86, 255), width=4)
    # header: avatar + handle
    av = WM.resize((60, int(WM.height * 60 / WM.width)), Image.LANCZOS)
    d.ellipse([pad + 4, 18, pad + 58, 72], fill=(20, 16, 10, 255)); card.alpha_composite(av, (pad + 1, 45 - av.height // 2))
    f = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', 28)
    d.text((pad + 74, 45), 'rax3d.sa', font=f, fill=(30, 24, 14, 255), anchor='lm')
    m = Image.new('L', (w, ph)); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, ph - 1], radius=18, fill=255)
    card.paste(p, (pad, top_bar), m)
    # action row icons (outline style)
    y = top_bar + ph + 30; ic = (30, 24, 14, 255)
    hx = pad + 30; d.ellipse([hx - 18, y - 4, hx + 2, y + 16], outline=ic, width=5); d.ellipse([hx - 2, y - 4, hx + 18, y + 16], outline=ic, width=5)
    d.line([(hx - 17, y + 10), (hx, y + 30), (hx + 17, y + 10)], fill=ic, width=5)
    bx = pad + 95; d.ellipse([bx - 20, y - 6, bx + 20, y + 30], outline=ic, width=5)
    sx = pad + 160; d.polygon([(sx - 20, y - 4), (sx + 22, y + 12), (sx - 20, y + 30), (sx - 10, y + 12)], outline=ic)
    return card, (pad + w // 2, top_bar + ph // 2), (pad + 30, y + 12)

def big_heart(size):
    im = Image.new('RGBA', (size, size)); d = ImageDraw.Draw(im); r = size * .25; cx, cy = size / 2, size * .4
    c = (255, 255, 255, 255)
    d.ellipse([cx - 2 * r, cy - r, cx, cy + r], fill=c); d.ellipse([cx, cy - r, cx + 2 * r, cy + r], fill=c)
    d.polygon([(cx - 1.93 * r, cy + .35 * r), (cx + 1.93 * r, cy + .35 * r), (cx, cy + 2.3 * r)], fill=c)
    sh = Image.new('RGBA', (size, size), (0, 0, 0, 0)); sh.putalpha(im.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: v // 3))
    o = Image.new('RGBA', (size, size)); o.alpha_composite(sh); o.alpha_composite(im); return o

def render_promo(bg, out, post_img=None, dur=10.0, seed=4):
    base, top = to_story(Image.open(bg)); base = base.convert('RGBA')
    yy = np.arange(H)[:, None].astype(float)
    a = np.repeat(np.maximum(np.clip((900 - yy) / 700, 0, 1) * .6, np.clip((yy - 1300) / 400, 0, 1) * .55), W, axis=1)
    mist = Image.new('RGBA', (W, H), (250, 242, 228, 0)); mist.putalpha(Image.fromarray((a * 255).astype(np.uint8))); base.alpha_composite(mist)
    soft = base.filter(ImageFilter.GaussianBlur(4))
    P = make_particles({'confetti': [(212, 170, 80), (240, 220, 170), (255, 250, 240)]}, seed)
    wm = WM.resize((300, int(WM.height * 300 / WM.width)), Image.LANCZOS)
    T1 = ar_layer('نزل منشور جديد!', 112) if post_img else ar_layer('خلك قريب منّا', 112)
    T2 = ar_plain('شوفه الحين على انستقرام' if post_img else 'جديدنا ينزل أول بأول على انستقرام', 44, (110, 78, 30, 255), 'Bold')
    card = None
    if post_img: card, ctr, hpos = phone_card(post_img, 520)
    icons = [('follow', 'تابعنا'), ('bell', 'فعّل الجرس'), ('heart', 'لايك'), ('comment', 'كومنت')]
    IC = [(icon(k, 150), ar_plain(lbl, 36 if post_img else 62, (70, 50, 20, 255), 'ExtraBold')) for k, lbl in icons]
    hd = gold_layer('@rax3d.sa', ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', 50), 2)
    heart = big_heart(260)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    cta_t = 4.6 if post_img else 1.8
    row_y = 1450 if post_img else 1250
    for i in range(int(FPS * dur)):
        t = i / FPS; s = 1 + .05 * t / dur
        fr = soft.resize((int(W * s), int(H * s)), Image.BILINEAR); ox, oy = (fr.width - W) // 2, (fr.height - H) // 2; fr = fr.crop((ox, oy, ox + W, oy + H))
        # golden light sweep
        if t < 2.2:
            p = ease(t / 2.0); sx = 150 + (W / 2 - 150) * p; sy = 400 + 500 * p; rad = 300
            m = Image.new('L', (W, H), int(255 * .5 * (1 - ease((t - 1.6) / .6)))); ImageDraw.Draw(m).ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=0)
            dk = Image.new('RGBA', (W, H), (25, 15, 5, 0)); dk.putalpha(m.filter(ImageFilter.GaussianBlur(90))); fr.alpha_composite(dk)
        fr.alpha_composite(draw_particles(P, t, {'confetti': 1}))
        put(fr, wm, W / 2, 150, ease((t - .2) / .7) * .95, 1 + .3 * (1 - ease_back(min(1, max(0, (t - .2) / .7)))))
        a1 = ease((t - .6) / .6); tl = sweep(T1, (t - 1.6) / 1.0) if 1.6 < t < 2.6 else T1
        put(fr, tl, W / 2, 330 + 30 * (1 - a1), a1, .9 + .1 * ease_back(min(1, max(0, (t - .6) / .6))))
        put(fr, T2, W / 2, 440, ease((t - 1.0) / .6))
        if card:
            ac = ease((t - 1.5) / .9); bob = 6 * math.sin(t * 1.4) * ac
            cy = 920 + 260 * (1 - ac) + bob
            cardf = card
            # double-tap heart on post at 3.0s
            if 2.9 < t < 4.1:
                k = (t - 2.9) / 1.2; sc = .3 + .9 * ease_back(min(1, k / .35)); al = 1 - ease((k - .6) / .4)
                cardf = card.copy(); h2 = heart.resize((int(260 * sc), int(260 * sc)), Image.BILINEAR)
                h2.putalpha(h2.split()[3].point(lambda v: int(v * al)))
                cardf.alpha_composite(h2, (ctr[0] - h2.width // 2, ctr[1] - h2.height // 2))
            if t > 3.1:  # small heart filled red in action row
                d = ImageDraw.Draw(cardf if cardf is not card else (cardf := card.copy())); hx, hy = hpos
                d.ellipse([hx - 18, hy - 16, hx + 2, hy + 4], fill=(237, 73, 86, 255)); d.ellipse([hx - 2, hy - 16, hx + 18, hy + 4], fill=(237, 73, 86, 255))
                d.polygon([(hx - 17, hy - 2), (hx + 17, hy - 2), (hx, hy + 18)], fill=(237, 73, 86, 255))
            sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle([W / 2 - cardf.width / 2 + 10, cy - cardf.height / 2 + 30, W / 2 + cardf.width / 2 - 10, cy + cardf.height / 2 + 30], radius=50, fill=(60, 40, 10, int(90 * ac)))
            fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
            put(fr, cardf, W / 2, cy, ac, .55 + .45 * ac if card else 1)
            # shrink card when CTA arrives
        # CTA icons row
        if not post_img:
            for j, (ic, lb) in enumerate(IC):
                tj = t - cta_t - j * .45
                if tj <= 0: continue
                e = ease_back(min(1, tj / .7)); al = min(1, tj / .3)
                side = 1 if j % 2 == 0 else -1; off = side * 760 * (1 - e)
                y = 640 + j * 215
                wob = 0
                if icons[j][0] == 'bell' and tj > .8: wob = 12 * math.sin((tj - .8) * 14) * math.exp(-((tj - .8) % 2.0) * 2.5)
                sc = 1.0
                if icons[j][0] == 'heart' and tj > .8: sc = 1 + .07 * max(0, math.sin((tj - .8) * 6))
                ii = ic.rotate(wob, resample=Image.BICUBIC) if wob else ic
                rw = 560; x0 = W / 2 - rw / 2 + off
                ix = x0 + rw - 85; lx = x0 + (rw - 170) / 2 + 10
                sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle([x0, y - 82, x0 + rw, y + 92], radius=88, fill=(90, 60, 15, int(70 * al)))
                fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
                gl = Image.new('RGBA', (W, H)); ImageDraw.Draw(gl).rounded_rectangle([x0, y - 88, x0 + rw, y + 88], radius=88, fill=(255, 249, 238, int(235 * al)), outline=(214, 172, 86, int(255 * al)), width=4)
                fr.alpha_composite(gl)
                put(fr, ii, ix, y, al, sc); put(fr, lb, lx, y + 4, al)
            ah = ease((t - cta_t - 2.4) / .6)
            if ah > 0:
                pill, _ = pill_layer('FOLLOW @RAX3D.SA')
                pp = sweep(pill, ((t - cta_t - 3.2) % 2.0) / 1.0) if t > cta_t + 3.2 else pill
                put(fr, pp, W / 2, 1600, ah, ease_back(min(1, ah)))
            ff.stdin.write(np.asarray(fr.convert('RGB')).tobytes()); continue
        for j, (ic, lb) in enumerate(IC):
            tj = t - cta_t - j * .35
            if tj <= 0: continue
            x = W / 2 + (1.5 - j) * 235; e = ease_back(min(1, tj / .45)); al = min(1, tj / .25)
            wob = 0
            if icons[j][0] == 'bell' and tj > .6: wob = 12 * math.sin((tj - .6) * 14) * math.exp(-((tj - .6) % 2.0) * 2.5)
            if icons[j][0] == 'heart' and tj > .6: e *= 1 + .07 * max(0, math.sin((tj - .6) * 6))
            ii = ic.rotate(wob, resample=Image.BICUBIC) if wob else ic
            gl = Image.new('RGBA', (W, H)); ImageDraw.Draw(gl).ellipse([x - 95, row_y - 95, x + 95, row_y + 95], fill=(255, 225, 150, int(110 * al)))
            fr.alpha_composite(gl.filter(ImageFilter.GaussianBlur(25)))
            put(fr, ii, x, row_y, al, e); put(fr, lb, x, row_y + 125, al)
        ah = ease((t - cta_t - 1.6) / .6)
        if ah > 0:
            pill, _ = pill_layer('FOLLOW @RAX3D.SA')
            pp = sweep(pill, ((t - cta_t - 2.4) % 2.0) / 1.0) if t > cta_t + 2.4 else pill
            put(fr, pp, W / 2, row_y + 270, ah, ease_back(min(1, ah)))
        ff.stdin.write(np.asarray(fr.convert('RGB')).tobytes())
    ff.stdin.close(); ff.wait()
