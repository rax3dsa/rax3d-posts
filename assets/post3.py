"""RAX3D approved post look: themed background 1080x1350 + mist top + wordmark + floor spotlight + product."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
W, H = 1080, 1350
WM = Image.open('/home/claude/p1/wordmark_neutral.png').convert('RGBA')

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

# ---- approved header/footer text (matches older feed posts) ----
from PIL import ImageFont
_F = '/usr/share/fonts/'
INK = (58, 52, 46, 255)

def _ctext(c, y, text, font, fill, track=0):
    d = ImageDraw.Draw(c)
    ws = [font.getlength(ch) for ch in text]; tw = sum(ws) + track * (len(text) - 1); x = (W - tw) / 2
    for ch, w in zip(text, ws): d.text((x, y), ch, font=font, fill=fill, anchor='lm'); x += w + track

def post_text_bg(path):
    """Background with mist, text header 'RAX3D / @rax3d.sa' (no image wordmark)."""
    b = Image.open(path).convert('RGB')
    s = H / b.height; b = b.resize((int(b.width * s), H), Image.LANCZOS)
    x = (b.width - W) // 2; b = b.crop((x, 0, x + W, H)).convert('RGBA')
    yy = np.arange(H)[:, None].astype(float)
    a = np.maximum(np.clip((300 - yy) / 300, 0, 1) ** 1.2 * .6, np.clip((yy - 1130) / 110, 0, 1) * .8)
    mist = Image.new('RGBA', (W, H), (250, 244, 234, 0)); mist.putalpha(Image.fromarray((np.repeat(a, W, 1) * 255).astype(np.uint8)))
    b.alpha_composite(mist)
    _ctext(b, 100, 'RAX3D', ImageFont.truetype(_F + 'opentype/inter/InterDisplay-Bold.otf', 64), INK, 1)
    _ctext(b, 150, '@rax3d.sa', ImageFont.truetype(_F + 'opentype/inter/Inter-Regular.otf', 24) if __import__('os').path.exists(_F + 'opentype/inter/Inter-Regular.otf') else ImageFont.truetype(_F + 'truetype/google-fonts/Poppins-Regular.ttf', 24), (95, 88, 80, 255))
    return b

def post_footer(c, title, sub='Printed in the color you choose — DM to order'):
    _ctext(c, 1222, title, ImageFont.truetype(_F + 'opentype/inter/InterDisplay-Medium.otf', 32) if __import__('os').path.exists(_F + 'opentype/inter/InterDisplay-Medium.otf') else ImageFont.truetype(_F + 'truetype/google-fonts/Poppins-Medium.ttf', 30), INK)
    _ctext(c, 1266, sub, ImageFont.truetype(_F + 'truetype/google-fonts/Poppins-Regular.ttf', 21), (110, 102, 94, 255))
    return c
