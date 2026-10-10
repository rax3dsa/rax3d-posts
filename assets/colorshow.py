"""Color-change segment: product recolored through several filament colors (for stories)."""
import sys, math, subprocess
sys.path.insert(0, '/home/claude/p1')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from anim import W, H, FPS, ease, ease_back, put, to_story, WM, gold_layer, pill_layer, sweep, make_particles, draw_particles, product_layer

COLORS = [('BLACK', None), ('RED', (210, 32, 38)), ('BLUE', (20, 100, 215)), ('WHITE', (238, 236, 230)),
          ('GREEN', (34, 150, 70)), ('ORANGE', (240, 120, 20)), ('PINK', (236, 92, 150)), ('GOLD', (205, 160, 60))]

def recolor(img, rgb, dark_max=None):
    """Recolor a dark (black) printed part, keeping metal ring/highlights."""
    if rgb is None: return img.copy()
    a = np.asarray(img).astype(float); L = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255
    m = a[..., 3] > 10
    hi = dark_max or np.percentile(L[m & (L < .42)], 92)
    s = np.clip(L / hi, 0, 1.25) ** .85
    w = np.clip((.44 - L) / .12, 0, 1)[..., None]  # keep bright metal ring as is
    c = np.array(rgb, float)
    if sum(rgb) > 600:  # white/light filament: lighter base
        col = c * (.62 + .38 * np.minimum(s, 1))[..., None]
    else:
        col = c * (.32 + .95 * np.minimum(s, 1))[..., None] + 255 * np.clip(s - 1, 0, .25)[..., None] * 1.5
    out = a.copy(); out[..., :3] = a[..., :3] * (1 - w) + np.clip(col, 0, 255) * w
    return Image.fromarray(out.astype(np.uint8), 'RGBA')

def swatch_row(active_idx, prog):
    row = Image.new('RGBA', (W, 120)); d = ImageDraw.Draw(row)
    n = len(COLORS); gap = 104; x0 = W / 2 - gap * (n - 1) / 2
    for i, (_, rgb) in enumerate(COLORS):
        c = rgb or (25, 25, 28); r = 30
        if i == active_idx: r = 30 + 12 * ease_back(min(1, prog / .4))
        x = x0 + i * gap; y = 60
        if i == active_idx: d.ellipse([x - r - 7, y - r - 7, x + r + 7, y + r + 7], outline=(205, 160, 80, 255), width=5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c + (255,), outline=(255, 255, 255, 230), width=3)
    return row

def color_clip(bg, out, name, product_png, prod_w=960, bottom=1430, per=.75, seed=41, sub='IN ANY COLOR YOU CHOOSE'):
    base, top = to_story(Image.open(bg)); base = base.convert('RGBA')
    yy = np.arange(H)[:, None].astype(float)
    a = np.repeat(np.maximum(np.clip((820 - yy) / 620, 0, 1) ** 1.2 * .62, np.clip((yy - 1560) / 300, 0, 1) * .5), W, axis=1)
    mist = Image.new('RGBA', (W, H), (250, 242, 228, 0)); mist.putalpha(Image.fromarray((a * 255).astype(np.uint8))); base.alpha_composite(mist)
    soft = base.filter(ImageFilter.GaussianBlur(3))
    # spotlight already landed (matches end of spotlight story)
    m = Image.new('L', (W, H), int(255 * .12)); ImageDraw.Draw(m).ellipse([W / 2 - 1000, 1300 - 1250, W / 2 + 1000, 1300 + 1250], fill=0)
    dk = Image.new('RGBA', (W, H), (25, 15, 5, 0)); dk.putalpha(m.filter(ImageFilter.GaussianBlur(90))); soft.alpha_composite(dk)
    P = make_particles({}, seed)
    F = '/usr/share/fonts/'
    T1 = gold_layer('NEW ARRIVAL', ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Medium.ttf', 36), 14)
    T2 = gold_layer(name, ImageFont.truetype(F + 'opentype/inter/InterDisplay-Bold.otf', 150 if len(name) <= 9 else int(150 * 9 / len(name)) + 10))
    T3 = gold_layer(sub, ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Medium.ttf', 44), 10)
    wm = WM.resize((340, int(WM.height * 340 / WM.width)), Image.LANCZOS)
    pill, _ = pill_layer(); hd = gold_layer('@rax3d.sa', ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Medium.ttf', 34), 2)
    prod = Image.open(product_png).convert('RGBA'); prod = prod.crop(prod.getbbox())
    ph = int(prod.height * prod_w / prod.width); prod = prod.resize((prod_w, ph), Image.LANCZOS)
    layers = [product_layer([(recolor(prod, rgb), W // 2, bottom, ph)]) for _, rgb in COLORS]
    lf = ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Bold.ttf', 40)
    dur = per * len(COLORS) + .8; ty = 470 if top else 560
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', out], stdin=subprocess.PIPE)
    for i in range(int(FPS * dur)):
        t = i / FPS; fr = soft.copy(); fr.alpha_composite(draw_particles(P, t + 11, {}))
        put(fr, wm, W / 2, 175, .9); put(fr, T1, W / 2, ty - 110); put(fr, T2, W / 2, ty)
        a3 = ease(t / .5); put(fr, T3, W / 2, ty + 115, a3)
        k = min(len(COLORS) - 1, int(t / per)); lt = t - k * per
        cur = layers[k]
        if k > 0 and lt < .3:  # crossfade from previous color
            prev = layers[k - 1].copy(); mix = Image.blend(prev, cur, ease(lt / .3)); cur = mix
        bob = 6 * math.sin(t * 1.6)
        fr.alpha_composite(cur, (0, int(bob)))
        sw = swatch_row(k, lt); fr.alpha_composite(sw, (0, bottom + 60))
        lab = gold_layer(COLORS[k][0], lf, 8); put(fr, lab, W / 2, bottom + 200, ease(lt / .25))
        put(fr, pill, W / 2, 1680, 1, 1 + .03 * math.sin(t * 4)); put(fr, hd, W / 2, 1790)
        ff.stdin.write(np.asarray(fr.convert('RGB')).tobytes())
    ff.stdin.close(); ff.wait(); return dur
