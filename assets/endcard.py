"""RAX3D slogan end card (brand rule: every ad/promo ends with it) + concat helper."""
import sys, subprocess, math
sys.path.insert(0, '/home/claude/p1')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from anim import W, H, FPS, ease, ease_back, put, to_story, WM, gold_layer, sweep, make_particles, draw_particles

F = '/usr/share/fonts/'

def plain(text, font, color):
    bb = font.getbbox(text); im = Image.new('RGBA', (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20))
    ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), text, font=font, fill=color); return im

def make_endcard(bg, out, dur=3.0, seed=2):
    base, _ = to_story(Image.open(bg)); base = base.convert('RGBA').filter(ImageFilter.GaussianBlur(14))
    veil = Image.new('RGBA', (W, H), (250, 243, 230, 175)); base.alpha_composite(veil)
    P = make_particles({}, seed)
    wm = WM.resize((420, int(WM.height * 420 / WM.width)), Image.LANCZOS)
    big = ImageFont.truetype(F + 'opentype/inter/InterDisplay-Bold.otf', 92)
    L1 = gold_layer('Turn Your Idea', big); L2 = gold_layer('Into 3D', big)
    L3 = gold_layer('In The Color You Choose', ImageFont.truetype(F + 'opentype/inter/InterDisplay-Bold.otf', 64))
    L4 = plain('DM us on Instagram', ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Medium.ttf', 44), (95, 70, 30, 255))
    L5 = gold_layer('@rax3d.sa', ImageFont.truetype(F + 'truetype/google-fonts/Poppins-Bold.ttf', 66), 2)
    line = Image.new('RGBA', (360, 4), (205, 160, 80, 255))
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', out], stdin=subprocess.PIPE)
    for i in range(int(FPS * dur)):
        t = i / FPS; fr = base.copy(); fr.alpha_composite(draw_particles(P, t + 5, {}))
        put(fr, wm, W / 2, 470, ease(t / .6), .9 + .1 * ease_back(min(1, t / .6)))
        for k, (L, y, d) in enumerate([(L1, 760, .25), (L2, 870, .4), (L3, 990, .6)]):
            a = ease((t - d) / .5); lay = sweep(L, (t - 1.4 - k * .1) / .9) if 1.4 + k * .1 < t < 2.3 + k * .1 else L
            put(fr, lay, W / 2, y + 30 * (1 - a), a)
        put(fr, line, W / 2, 1090, ease((t - .8) / .4), max(.01, ease((t - .8) / .4)))
        put(fr, L4, W / 2, 1180, ease((t - 1.0) / .5)); put(fr, L5, W / 2, 1270, ease((t - 1.15) / .5), .9 + .1 * ease_back(min(1, max(0, (t - 1.15) / .5))))
        ff.stdin.write(np.asarray(fr.convert('RGB')).tobytes())
    ff.stdin.close(); ff.wait()

def concat(main, card, out, main_dur, fade=.5):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', main, '-i', card, '-filter_complex',
                    f'[0:v][1:v]xfade=transition=fade:duration={fade}:offset={main_dur - fade},format=yuv420p[v]',
                    '-map', '[v]', '-c:v', 'libx264', '-crf', '19', '-preset', 'medium', out], check=True)
