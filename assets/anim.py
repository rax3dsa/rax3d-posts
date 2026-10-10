"""RAX3D animated story engine: 1080x1920, 7s @30fps, H.264."""
import numpy as np, subprocess, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 7.0
F = '/usr/share/fonts/'
WM = Image.open('/home/claude/p1/wordmark_neutral.png').convert('RGBA')

def ease(t):  # easeOutCubic clamp
    t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def ease_back(t):
    t = max(0, min(1, t)); c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

# ---------- background prep ----------
def to_story(bg):
    """bg: PIL image. 9:16 -> resize; 4:5 -> fit width and extend top/bottom softly."""
    bg = bg.convert('RGB')
    r = bg.width / bg.height
    if abs(r - 9 / 16) < 0.02:
        return bg.resize((W, H), Image.LANCZOS), 0
    b = bg.resize((W, int(bg.height * W / bg.width)), Image.LANCZOS)
    top = H - b.height; out = Image.new('RGB', (W, H))
    # top: stretched blurred top strip
    strip = b.crop((0, 0, W, 60)).resize((W, top + 260), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    out.paste(strip, (0, 0))
    # bottom: mirrored floor, blurred
    rest = H - top - b.height
    if rest > 0:
        fl = b.crop((0, b.height - rest - 40, W, b.height)).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(18))
        out.paste(fl, (0, top + b.height - 40))
    # feathered paste of main image
    m = Image.new('L', b.size, 255); md = ImageDraw.Draw(m)
    for i in range(160):
        a = int(255 * i / 160); md.line([(0, i), (W, i)], fill=a)
    for i in range(50):
        a = int(255 * i / 50); md.line([(0, b.height - 1 - i), (W, b.height - 1 - i)], fill=a)
    out.paste(b, (0, top), m)
    return out, top

def edge_masks(img):
    """feathered masks for left/right prop zones (props sit at edges/corners)."""
    x = np.linspace(0, 1, W)[None, :]
    y = np.linspace(0, 1, H)[:, None]
    left = np.clip((0.30 - x) / 0.12, 0, 1) * np.clip((y - 0.18) / 0.15, 0, 1)
    right = np.clip((x - 0.70) / 0.12, 0, 1) * np.clip((y - 0.18) / 0.15, 0, 1)
    bottom = np.clip((y - 0.80) / 0.10, 0, 1) * (1 - np.clip(1 - np.abs(x - .5) / .22, 0, 1))
    L = np.clip(left + bottom * (x < .5), 0, 1); R = np.clip(right + bottom * (x >= .5), 0, 1)
    return (Image.fromarray((L * 255).astype(np.uint8)), Image.fromarray((R * 255).astype(np.uint8)))

def zoom(img, s, dx=0, dy=0):
    w, h = img.size; nw, nh = int(w * s), int(h * s)
    z = img.resize((nw, nh), Image.BILINEAR)
    x = (nw - w) // 2 + int(dx); y = (nh - h) // 2 + int(dy)
    return z.crop((x, y, x + w, y + h))

# ---------- text ----------
def gold_layer(text, font, track=0):
    ws = [font.getlength(ch) for ch in text]; tw = sum(ws) + track * (len(text) - 1)
    asc, desc = font.getmetrics(); th = asc + desc
    m = Image.new('L', (int(tw) + 60, th + 60), 0); md = ImageDraw.Draw(m); x = 30
    for ch, w in zip(text, ws): md.text((x, 30), ch, font=font, fill=255); x += w + track
    g = Image.new('RGBA', m.size); gd = ImageDraw.Draw(g)
    for yy in range(m.size[1]):
        t = yy / m.size[1]; gd.line([(0, yy), (m.size[0], yy)], fill=(int(185 - 70 * t), int(135 - 60 * t), int(55 - 32 * t), 255))
    g.putalpha(m)
    glow = Image.new('RGBA', m.size, (255, 235, 200, 0)); glow.putalpha(m.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .55)))
    out = Image.new('RGBA', m.size); out.alpha_composite(glow); out.alpha_composite(g)
    return out

def pill_layer(txt='DM TO ORDER'):
    fp = ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Bold.ttf', 40)
    tw = fp.getlength(txt) + 6 * (len(txt) - 1); pw, ph = int(tw + 110), 96
    mask = Image.new('L', (pw, ph)); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph // 2, fill=255)
    gg = Image.new('RGBA', (pw, ph)); gd = ImageDraw.Draw(gg)
    for x in range(pw):
        k = 1 - abs(x / pw - .5) * 2
        gd.line([(x, 0), (x, ph)], fill=(int(170 + 80 * k), int(120 + 80 * k), int(40 + 60 * k), 255))
    gg.putalpha(mask); d = ImageDraw.Draw(gg); x = 55
    for ch in txt: d.text((x, ph // 2), ch, font=fp, fill=(15, 12, 8, 255), anchor='lm'); x += fp.getlength(ch) + 6
    return gg, mask

def put(canvas, layer, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01: return
    l = layer
    if abs(scale - 1) > 0.003:
        l = l.resize((max(1, int(l.width * scale)), max(1, int(l.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        a = l.split()[3].point(lambda v: int(v * alpha)); l = l.copy(); l.putalpha(a)
    canvas.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))

# ---------- particles ----------
def make_particles(fx, seed=1):
    rnd = random.Random(seed); P = []
    for _ in range(38):  # golden bokeh, always
        P.append(dict(k='bokeh', x=rnd.uniform(0, W), y=rnd.uniform(0, H), r=rnd.uniform(8, 34),
                      vy=rnd.uniform(-40, -12), vx=rnd.uniform(-8, 8), ph=rnd.uniform(0, 6.28), a=rnd.uniform(.25, .6)))
    for _ in range(14):
        P.append(dict(k='spark', x=rnd.uniform(60, W - 60), y=rnd.uniform(200, H - 300), ph=rnd.uniform(0, 6.28), s=rnd.uniform(10, 26)))
    if fx.get('confetti'):
        cols = fx['confetti']
        for _ in range(55):
            P.append(dict(k='conf', x=rnd.uniform(0, W), y=rnd.uniform(-H, 0), vy=rnd.uniform(120, 230), sw=rnd.uniform(20, 60),
                          ph=rnd.uniform(0, 6.28), rot=rnd.uniform(1, 4), c=rnd.choice(cols), w=rnd.uniform(10, 18)))
    if fx.get('embers'):
        for _ in range(45):
            P.append(dict(k='ember', x=rnd.uniform(0, W), y=rnd.uniform(0, H), vy=rnd.uniform(-160, -70), ph=rnd.uniform(0, 6.28), r=rnd.uniform(2, 5)))
    if fx.get('dust'):
        for _ in range(90):
            P.append(dict(k='dust', x=rnd.uniform(0, W), y=rnd.uniform(H * .2, H), vx=rnd.uniform(40, 120), ph=rnd.uniform(0, 6.28), r=rnd.uniform(1.5, 4)))
    if fx.get('steam'):
        for i in range(7):
            P.append(dict(k='steam', x0=rnd.choice([rnd.uniform(.05,.25),rnd.uniform(.75,.95)]) * W, ph=rnd.uniform(0, 6.28), sp=rnd.uniform(.6, 1.1)))
    return P

def draw_particles(P, t, fx):
    lay = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(lay)
    for p in P:
        if p['k'] == 'bokeh':
            y = (p['y'] + p['vy'] * t) % H; x = p['x'] + p['vx'] * t + 10 * math.sin(t + p['ph'])
            a = p['a'] * (0.6 + 0.4 * math.sin(2 * t + p['ph'])); r = p['r']
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 226, 160, int(255 * a * .55)))
        elif p['k'] == 'spark':
            k = max(0, math.sin(1.7 * t + p['ph'])) ** 6; s = p['s'] * k
            if s > 1:
                c = (255, 245, 215, int(255 * k)); x, y = p['x'], p['y']
                d.polygon([(x, y - s), (x + s * .18, y), (x, y + s), (x - s * .18, y)], fill=c)
                d.polygon([(x - s, y), (x, y + s * .18), (x + s, y), (x, y - s * .18)], fill=c)
    lay = lay.filter(ImageFilter.GaussianBlur(2.2))
    sharp = Image.new('RGBA', (W, H)); sd = ImageDraw.Draw(sharp)
    for p in P:
        if p['k'] == 'steam':
            for j in range(10):
                tt = (t * .35 * p['sp'] + j / 10) % 1
                y = H * .78 - tt * 520; x = p['x0'] + 40 * math.sin(tt * 6 + p['ph'] + t)
                r = 18 + tt * 60; a = int(38 * math.sin(tt * math.pi))
                sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 240, a))
    if fx.get('steam'): lay.alpha_composite(sharp.filter(ImageFilter.GaussianBlur(22)))
    crisp = Image.new('RGBA', (W, H)); cd = ImageDraw.Draw(crisp); any_c = False
    for p in P:
        if p['k'] == 'conf':
            y = p['y'] + p['vy'] * t
            if -30 < y < H + 30:
                any_c = True
                x = p['x'] + p['sw'] * math.sin(t * 2 + p['ph']); w = p['w'] * 1.4; h = w * abs(math.sin(t * p['rot'] + p['ph'])) * .55 + 3
                cd.rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], fill=p['c'] + (255,))
        elif p['k'] == 'ember':
            any_c = True
            y = (p['y'] + p['vy'] * t) % H; x = p['x'] + 25 * math.sin(t * 1.5 + p['ph'])
            a = int(255 * (0.5 + 0.5 * math.sin(t * 6 + p['ph']))); r = p['r']
            cd.ellipse([x - r * 2.5, y - r * 2.5, x + r * 2.5, y + r * 2.5], fill=(255, 150, 50, a // 4))
            cd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 110, a))
        elif p['k'] == 'dust':
            any_c = True
            x = (p['x'] + p['vx'] * t) % W; y = p['y'] + 12 * math.sin(t + p['ph']); r = p['r']
            cd.ellipse([x - r, y - r, x + r, y + r], fill=(245, 215, 160, int(150 + 80 * math.sin(t * 2 + p['ph']))))
    if any_c: lay.alpha_composite(crisp.filter(ImageFilter.GaussianBlur(0.8)))
    if fx.get('rays'):
        rl = Image.new('L', (W, H)); rd = ImageDraw.Draw(rl)
        for i in range(6):
            ang = -0.9 + i * .32 + .06 * math.sin(t * .8 + i)
            x2 = W * .85 + math.cos(ang + math.pi / 2) * 2400; y2 = math.sin(ang + math.pi / 2) * 2400
            rd.polygon([(W * .85, -50), (x2 - 120, y2), (x2 + 120, y2)], fill=int(26 + 14 * math.sin(t * 1.3 + i)))
        rl = rl.filter(ImageFilter.GaussianBlur(30)); ray = Image.new('RGBA', (W, H), (255, 236, 190, 0)); ray.putalpha(rl)
        lay.alpha_composite(ray)
    return lay

def sweep(layer, t):
    """light sweep over an RGBA layer, t in 0..1"""
    w, h = layer.size; m = Image.new('L', (w, h)); md = ImageDraw.Draw(m)
    cx = -w * .3 + t * w * 1.6
    md.polygon([(cx - 40, 0), (cx + 40, 0), (cx + 40 - h * .5, h), (cx - 40 - h * .5, h)], fill=200)
    m = m.filter(ImageFilter.GaussianBlur(14))
    a = np.minimum(np.asarray(m), np.asarray(layer.split()[3]))
    s = Image.new('RGBA', (w, h), (255, 250, 235, 0)); s.putalpha(Image.fromarray(a.astype(np.uint8)))
    o = layer.copy(); o.alpha_composite(s); return o

# ---------- product ----------
def product_layer(items):
    """items: list of (PIL RGBA cutout, cx, bottom, h) -> layer with shadow+reflection on transparent canvas"""
    c = Image.new('RGBA', (W, H))
    for p, cx, bottom, h in items:
        p = p.crop(p.getbbox())
        p = p.resize((int(p.width * h / p.height), h), Image.LANCZOS)
        x = int(cx - p.width / 2); y = int(bottom - p.height)
        sh = Image.new('L', (W, H)); ImageDraw.Draw(sh).ellipse([x + p.width * .08, bottom - 14, x + p.width * .92, bottom + 18], fill=110)
        bl = Image.new('RGBA', (W, H), (70, 50, 20, 255)); bl.putalpha(sh.filter(ImageFilter.GaussianBlur(16))); c.alpha_composite(bl)
        ref = p.transpose(Image.FLIP_TOP_BOTTOM); ra = np.asarray(ref.split()[3]).astype(float)
        ref.putalpha(Image.fromarray((ra * np.linspace(.22, 0, ref.height)[:, None]).astype(np.uint8)))
        c.alpha_composite(ref.filter(ImageFilter.GaussianBlur(2)), (x, bottom + 2)); c.alpha_composite(p, (x, y))
    return c

# ---------- render ----------
import cv2
def clean_plate(base, L, R):
    sm = base.convert('RGB').resize((W // 4, H // 4))
    m = np.maximum(np.asarray(L.resize(sm.size)), np.asarray(R.resize(sm.size)))
    m = (m > 40).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    inp = cv2.inpaint(np.asarray(sm), m, 25, cv2.INPAINT_TELEA)
    return Image.fromarray(inp).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(28)).convert('RGBA')

def frame_path(inset=46):
    x0, y0, x1, y1 = inset, inset, W - inset, H - inset
    pts = [(W / 2, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0), (W / 2, y0)]
    seg = [math.dist(pts[k], pts[k + 1]) for k in range(5)]
    return pts, seg, sum(seg)

def render(bg, out, name, sub=None, items=None, fx=None, parallax=True, seed=1, show_wm=True, ty=None, style='classic', cycle=None, dur=None):
    fx = fx or {}
    base, top = to_story(bg)
    base = base.convert('RGBA')
    yy = np.arange(H)[:, None].astype(float)
    a_top = np.clip((820 - yy) / 620, 0, 1) ** 1.2 * 0.62
    a_bot = np.clip((yy - 1560) / 300, 0, 1) * 0.5
    a = np.repeat(np.maximum(a_top, a_bot), W, axis=1)
    mist = Image.new('RGBA', (W, H), (250, 242, 228, 0)); mist.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    base.alpha_composite(mist)
    L, R = edge_masks(base)
    propL = base.copy(); propL.putalpha(L); propR = base.copy(); propR.putalpha(R)
    soft = base.filter(ImageFilter.GaussianBlur(3))
    if style == 'enter':
        soft = clean_plate(base, L, R); soft.alpha_composite(mist)
    P = make_particles(fx, seed)
    f_small = ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Medium.ttf', 36)
    f_big = ImageFont.truetype(F + 'opentype/inter/InterDisplay-Bold.otf', 150 if len(name) <= 9 else int(150 * 9 / len(name)) + 10)
    f_mid = ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Medium.ttf', 44)
    f_h = ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Medium.ttf', 34)
    T1 = gold_layer('NEW ARRIVAL', f_small, 14); T2 = gold_layer(name, f_big); T3 = gold_layer(sub, f_mid, 10) if sub else None
    typed = {}
    if style == 'cinematic':
        full = T2.size
        for k in range(1, len(name) + 1):
            l = gold_layer(name[:k], f_big); c = Image.new('RGBA', full); c.alpha_composite(l, (0, 0)); typed[k] = c
    pill, _ = pill_layer(); handle = gold_layer('@rax3d.sa', f_h, 2)
    wm = WM.resize((340, int(WM.height * 340 / WM.width)), Image.LANCZOS)
    prod = product_layer(items) if items else None
    cyc = [product_layer(it) for it in cycle] if cycle else None
    ty = ty or (470 if top else 560)
    D = {'classic': 0, 'enter': 1.2, 'spotlight': 2.0, 'cinematic': 1.0, 'frame': 1.6}[style]
    if style == 'frame': pts, seg, tot = frame_path()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    DD = dur or DUR
    N = int(FPS * DD)
    for i in range(N):
        t = i / FPS; u = t / DD; tt = t - D
        s = 1.0 + 0.06 * u
        fr = zoom(soft if parallax else base, s)
        if parallax:
            sway = math.sin(t * 1.1)
            off = 0
            if style == 'enter': off = 650 * (1 - ease(t / 1.3))
            fr.alpha_composite(zoom(propL, s + .035 * u + .01, dx=14 * sway - 18 * u + off, dy=-6 * u))
            fr.alpha_composite(zoom(propR, s + .035 * u + .01, dx=-14 * sway + 18 * u - off, dy=-6 * u))
        if style == 'cinematic' and t < 2.0:
            k = 1 - ease(t / 1.8)
            fr = fr.filter(ImageFilter.GaussianBlur(26 * k))
            wh = Image.new('RGBA', (W, H), (255, 248, 235, int(200 * k))); fr.alpha_composite(wh)
        fr.alpha_composite(draw_particles(P, t, fx))
        if style == 'cinematic':  # moving light leak
            lk = Image.new('L', (W, H)); ld = ImageDraw.Draw(lk)
            cx = -300 + (t / DUR) * (W + 600)
            ld.ellipse([cx - 420, -200, cx + 420, 900], fill=70)
            lk = lk.filter(ImageFilter.GaussianBlur(120)); lo = Image.new('RGBA', (W, H), (255, 190, 110, 0)); lo.putalpha(lk); fr.alpha_composite(lo)
        if style == 'spotlight':
            if t < 2.2:
                p = ease(t / 2.0); sx = 150 + (W / 2 - 150) * p; sy = 500 + (1300 - 500) * p; rad = 260 + 40 * math.sin(t * 3)
                dark = 0.62
            else:
                sx, sy = W / 2, 1300; e = ease((t - 2.2) / 1.0); rad = 300 + 700 * e; dark = 0.62 * (1 - e) + 0.12 * e
            m = Image.new('L', (W, H), int(255 * dark)); md = ImageDraw.Draw(m)
            md.ellipse([sx - rad, sy - rad * 1.25, sx + rad, sy + rad * 1.25], fill=0)
            m = m.filter(ImageFilter.GaussianBlur(90)); dk = Image.new('RGBA', (W, H), (25, 15, 5, 0)); dk.putalpha(m); fr.alpha_composite(dk)
            gl = Image.new('L', (W, H)); gd = ImageDraw.Draw(gl)
            gd.ellipse([sx - rad * .9, sy + rad * .6, sx + rad * .9, sy + rad * 1.1], fill=110)
            gl = gl.filter(ImageFilter.GaussianBlur(50)); go = Image.new('RGBA', (W, H), (255, 225, 160, 0)); go.putalpha(gl); fr.alpha_composite(go)
        if style == 'frame':
            fp = ease(t / 1.6) * tot; fl = Image.new('RGBA', (W, H)); fd = ImageDraw.Draw(fl); acc = 0; head = pts[0]
            for k in range(5):
                if acc >= fp: break
                a0, a1_ = pts[k], pts[k + 1]; L_ = seg[k]; r = min(1, (fp - acc) / L_)
                e_ = (a0[0] + (a1_[0] - a0[0]) * r, a0[1] + (a1_[1] - a0[1]) * r)
                fd.line([a0, e_], fill=(214, 172, 86, 255), width=5); head = e_; acc += L_
            fd.line([(70, 70), (W - 70, 70)], fill=(0, 0, 0, 0))
            glow = fl.filter(ImageFilter.GaussianBlur(8)); fr.alpha_composite(glow); fr.alpha_composite(fl)
            if t < 1.7:
                hx, hy = head; hl = Image.new('RGBA', (W, H)); ImageDraw.Draw(hl).ellipse([hx - 22, hy - 22, hx + 22, hy + 22], fill=(255, 245, 210, 230))
                fr.alpha_composite(hl.filter(ImageFilter.GaussianBlur(9)))
        # wordmark
        if show_wm:
            if style == 'frame':
                st = (t - 1.2) / .5
                if st > 0:
                    w2 = sweep(wm, (t - 1.8) / .8) if 1.8 < t < 2.6 else wm
                    put(fr, w2, W / 2, 175, min(1, st * 1.5) * .95, 1 + .8 * (1 - ease_back(min(1, st))) if st < 1 else 1)
            else:
                put(fr, wm, W / 2, 175, alpha=ease((t - .1 - (D if style == 'spotlight' else 0)) / .8) * .9)
        a1 = ease((tt - .35) / .6); put(fr, T1, W / 2, ty - 110 + 30 * (1 - a1), a1)
        if style == 'cinematic':
            k = int(min(len(name), max(0, (t - 1.0) / 0.09)))
            if k > 0:
                lay = typed[k]
                if k == len(name) and 2.4 < t < 3.4: lay = sweep(lay, (t - 2.4) / 1.0)
                put(fr, lay, W / 2, ty, 1.0)
        else:
            a2 = ease((tt - .65) / .7)
            t2 = sweep(T2, (tt - 2.0) / 1.0) if 2.0 < tt < 3.0 else T2
            put(fr, t2, W / 2, ty, a2, .85 + .15 * ease_back((tt - .65) / .7))
        if T3: a3 = ease((tt - 1.0) / .6); put(fr, T3, W / 2, ty + 115, a3)
        if cyc:
            t0 = tt - .8
            if t0 > 0:
                seg = (DD - D - .8) / len(cyc); k = min(len(cyc) - 1, int(t0 / seg)); lt = t0 - k * seg
                a_in = ease(lt / .6); a_out = 1 - ease((lt - (seg - .5)) / .5) if k < len(cyc) - 1 else 1
                ap = max(0, min(a_in, a_out)); bob = 8 * math.sin(t * 1.6)
                pl = cyc[k].copy(); pl.putalpha(cyc[k].split()[3].point(lambda v: int(v * ap)))
                fr.alpha_composite(pl, (0, int(50 * (1 - a_in) + bob)))
        if prod:
            ap = ease((tt - .8) / 1.0); bob = 8 * math.sin(t * 1.6) * ap
            pl = prod
            if ap < .999:
                pl = prod.copy(); pl.putalpha(prod.split()[3].point(lambda v: int(v * ap)))
            fr.alpha_composite(pl, (0, int(60 * (1 - ap) + bob)))
        dp = min(D, 1.0) if style != 'classic' else 0
        ab = (t - 1.6 - dp * 1.6) / .5
        if ab > 0:
            t0 = 2.1 + dp * 1.6
            pulse = 1 + .03 * math.sin((t - t0) * 4) if t > t0 else 1
            pp = sweep(pill, ((t - t0 - 1.1) % 2.2) / 1.0) if t > t0 + 1.1 else pill
            put(fr, pp, W / 2, 1680, min(1, ab * 2), ease_back(ab) * pulse)
        put(fr, handle, W / 2, 1790, ease((t - 2.0 - dp * 1.6) / .6))
        arr = np.asarray(fr.convert('RGB'))
        ff.stdin.write(arr.tobytes())
    ff.stdin.close(); ff.wait()
