"""Branded feature-card image generator for PursuitAI social posts.

Renders 1080x1350 (Instagram feed) and 1600x900 (X) cards with the
brand's violet gradient, feature headline, body copy, stat chip, and CTA.
Pure PIL - no network required.
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BRAND_VIOLET = (124, 58, 237)      # #7c3aed
BRAND_DEEP = (23, 12, 46)          # dark backdrop
BRAND_DEEP2 = (44, 21, 84)
WHITE = (255, 255, 255)
MUTED = (196, 181, 253)            # violet-200
GREEN = (74, 222, 128)

def _font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def _gradient(w, h):
    img = Image.new("RGB", (w, h), BRAND_DEEP)
    top = Image.new("RGB", (w, h), BRAND_DEEP2)
    mask = Image.new("L", (w, h))
    md = ImageDraw.Draw(mask)
    for y in range(h):
        md.line([(0, y), (w, y)], fill=int(255 * (1 - y / h) * 0.9))
    img = Image.composite(top, img, mask)
    # violet glow, upper right
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * 0.45, -h * 0.35, w * 1.25, h * 0.45], fill=(88, 38, 178))
    glow = glow.filter(ImageFilter.GaussianBlur(w // 9))
    img = Image.blend(img, Image.blend(img, glow, 0.55), 0.8)
    # subtle grid
    d = ImageDraw.Draw(img, "RGBA")
    step = w // 14
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(255, 255, 255, 8))
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(255, 255, 255, 8))
    return img

def render_card(topic, brand, size=(1080, 1350), out_path=None):
    w, h = size
    s = w / 1080.0  # scale factor
    img = _gradient(w, h)
    d = ImageDraw.Draw(img, "RGBA")
    pad = int(84 * s)

    # top brand row
    logo_f = _font(int(46 * s))
    d.text((pad, pad), "PursuitAI", font=logo_f, fill=WHITE)
    lw = d.textlength("PursuitAI", font=logo_f)
    tag_f = _font(int(26 * s), bold=False)
    d.text((pad + lw + int(24 * s), pad + int(14 * s)), brand["tagline"],
           font=tag_f, fill=MUTED)

    # feature eyebrow chip
    y = pad + int(150 * s) if h > w else pad + int(120 * s)
    chip_f = _font(int(30 * s))
    chip_txt = topic["feature"].upper()
    cw = d.textlength(chip_txt, font=chip_f)
    d.rounded_rectangle([pad, y, pad + cw + int(48 * s), y + int(62 * s)],
                        radius=int(31 * s), fill=(124, 58, 237, 235))
    d.text((pad + int(24 * s), y + int(13 * s)), chip_txt, font=chip_f, fill=WHITE)

    # headline
    y += int(120 * s)
    head_f = _font(int(84 * s) if h > w else int(72 * s))
    for line in _wrap(d, topic["headline"], head_f, w - 2 * pad):
        d.text((pad, y), line, font=head_f, fill=WHITE)
        y += int((head_f.size) * 1.16)

    # body
    y += int(36 * s)
    body_f = _font(int(40 * s) if h > w else int(34 * s), bold=False)
    for line in _wrap(d, topic["body"], body_f, w - 2 * pad):
        d.text((pad, y), line, font=body_f, fill=(226, 219, 250))
        y += int(body_f.size * 1.42)

    # stat chip
    y += int(48 * s)
    stat_f = _font(int(36 * s))
    stat = "  " + topic["stat"] + "  "
    sw = d.textlength(stat, font=stat_f)
    d.rounded_rectangle([pad, y, pad + sw + int(70 * s), y + int(84 * s)],
                        radius=int(18 * s), outline=GREEN, width=max(2, int(3 * s)))
    d.ellipse([pad + int(26 * s), y + int(32 * s), pad + int(46 * s),
               y + int(52 * s)], fill=GREEN)
    d.text((pad + int(56 * s), y + int(20 * s)), stat, font=stat_f, fill=GREEN)

    # bottom CTA bar
    bar_h = int(150 * s)
    d.rectangle([0, h - bar_h, w, h], fill=(12, 6, 26, 255))
    cta_f = _font(int(40 * s))
    d.text((pad, h - bar_h + int(30 * s)), "Start your free 14-day trial",
           font=cta_f, fill=WHITE)
    url_f = _font(int(32 * s), bold=False)
    d.text((pad, h - bar_h + int(86 * s)), brand["url"].replace("https://", "")
           + "  ·  no credit card", font=url_f, fill=MUTED)
    # arrow button
    bx = w - pad - int(96 * s)
    d.ellipse([bx, h - bar_h + int(28 * s), bx + int(94 * s),
               h - bar_h + int(122 * s)], fill=BRAND_VIOLET)
    ar_f = _font(int(52 * s))
    d.text((bx + int(28 * s), h - bar_h + int(40 * s)), "→", font=ar_f, fill=WHITE)

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        img.save(out_path, quality=92)
    return img

def render_all(calendar_path=None, out_dir=None):
    calendar_path = calendar_path or os.path.join(ROOT, "content", "calendar.json")
    out_dir = out_dir or os.path.join(ROOT, "assets", "cards")
    with open(calendar_path) as f:
        cal = json.load(f)
    made = []
    for t in cal["topics"]:
        for suffix, size in (("ig", (1080, 1350)), ("x", (1600, 900))):
            p = os.path.join(out_dir, f"{t['id']}_{suffix}.png")
            render_card(t, cal["brand"], size=size, out_path=p)
            made.append(p)
    return made

if __name__ == "__main__":
    for p in render_all():
        print("made", p)
