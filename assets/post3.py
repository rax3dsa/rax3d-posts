"""RAX3D approved post look: themed background 1080x1350 + mist top + wordmark + floor spotlight + product."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
W, H = 1080, 1350
WM = Image.open('/home/claude/p1/wordmark.png').convert('RGBA')

def post_bg(path):
    b = Image.open(path).convert('RGB')
    s = H / b.height; b = b.resize((int(b.width * s), H), Image.LANCZOS)
    x = (b.width - W) // 2; b = b.crop((x, 0, x + W, H)).convert('RGBA')
    yy = np.arange(H)[:, None].astype(float)
    a = np.repeat(np.clip((330 - yy) / 330, 0, 1) ** 1.3 * 0.55, W, axis=1)
    mist = Image.new('RGBA', (W, H), (250, 242, 228, 0)); mist.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    b.alpha_composite(mist)
    wm = WM.resize((330, int(WM.height * 330 / WM.width)), Image.LANCZOS)
    wa = wm.split()[3].point(lambda v: int(v * .92)); wm.putalpha(wa)
    b.alpha_composite(wm, ((W - wm.width) // 2, 40))
    return b

def spot(c, cx, floor_y, rx=360):
    g = Image.new('L', (W, H)); d = ImageDraw.Draw(g)
    d.ellipse([cx - rx, floor_y - rx * .28, cx + rx, floor_y + rx * .28], fill=120)
    d.ellipse([cx - rx * .55, floor_y - 900, cx + rx * .55, floor_y], fill=35)
    g = g.filter(ImageFilter.GaussianBlur(60))
    l = Image.new('RGBA', (W, H), (255, 236, 195, 0)); l.putalpha(g); c.alpha_composite(l)

def place(c, p, cx, bottom, h=None, w=None):
    p = p.crop(p.getbbox())
    if h: p = p.resize((int(p.width * h / p.height), h), Image.LANCZOS)
    if w: p = p.resize((w, int(p.height * w / p.width)), Image.LANCZOS)
    x = int(cx - p.width / 2); y = int(bottom - p.height)
    sh = Image.new('L', (W, H)); ImageDraw.Draw(sh).ellipse([x + p.width * .06, bottom - 16, x + p.width * .94, bottom + 20], fill=150)
    bl = Image.new('RGBA', (W, H), (60, 40, 15, 255)); bl.putalpha(sh.filter(ImageFilter.GaussianBlur(18))); c.alpha_composite(bl)
    ref = p.transpose(Image.FLIP_TOP_BOTTOM); ra = np.asarray(ref.split()[3]).astype(float)
    ref.putalpha(Image.fromarray((ra * np.linspace(.25, 0, ref.height)[:, None]).astype(np.uint8)))
    c.alpha_composite(ref.filter(ImageFilter.GaussianBlur(2)), (x, bottom + 2)); c.alpha_composite(p, (x, y))
    return c
