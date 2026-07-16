"""Live-site screenshot capture via Playwright (runs in GitHub Actions / locally).

Captures pursuitai.net at desktop resolution, crops platform-sized frames,
and drops a subtle brand footer so raw screenshots are post-ready.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "screenshots")

SECTIONS = [
    # (name, url, selector-or-None, scroll_y fallback)
    ("hero", "https://pursuitai.net/", None, 0),
    ("how-it-works", "https://pursuitai.net/", None, 1400),
    ("pipeline-board", "https://pursuitai.net/", None, 3000),
    ("features", "https://pursuitai.net/#features", None, 0),
    ("pricing", "https://pursuitai.net/#pricing", None, 0),
    ("why", "https://pursuitai.net/why-pursuitai", None, 0),
]

def _footer(img, text="pursuitai.net · free 14-day trial"):
    d = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    bar = int(h * 0.055)
    d.rectangle([0, h - bar, w, h], fill=(23, 12, 46, 255))
    try:
        f = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(bar * 0.45))
    except OSError:
        f = ImageFont.load_default()
    d.text((int(w * 0.03), h - bar + int(bar * 0.24)), text, font=f,
           fill=(196, 181, 253))
    return img

def capture_all(out_dir=OUT):
    from playwright.sync_api import sync_playwright
    os.makedirs(out_dir, exist_ok=True)
    made = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1000},
                                device_scale_factor=2)
        for name, url, selector, scroll_y in SECTIONS:
            try:
                page.goto(url, wait_until="load", timeout=45000)
                page.wait_for_timeout(3500)  # let animations settle
                if scroll_y:
                    page.mouse.wheel(0, scroll_y)
                    page.wait_for_timeout(1500)
                raw = os.path.join(out_dir, f"{name}_raw.png")
                if selector:
                    page.locator(selector).first.screenshot(path=raw)
                else:
                    page.screenshot(path=raw)
                made.append(_postprocess(raw, name, out_dir))
            except Exception as e:  # keep going; screenshots are best-effort
                print(f"[screenshots] {name} failed: {e}")
        browser.close()
    return [m for m in made if m]

def _postprocess(raw_path, name, out_dir):
    img = Image.open(raw_path).convert("RGB")
    outs = []
    # X: 16:9
    x_img = _center_crop(img, 16 / 9).resize((1600, 900), Image.LANCZOS)
    xp = os.path.join(out_dir, f"{name}_x.png")
    _footer(x_img).save(xp, quality=92)
    outs.append(xp)
    # IG: 4:5
    ig_img = _center_crop(img, 4 / 5).resize((1080, 1350), Image.LANCZOS)
    igp = os.path.join(out_dir, f"{name}_ig.png")
    _footer(ig_img).save(igp, quality=92)
    outs.append(igp)
    os.remove(raw_path)
    return outs

def _center_crop(img, ratio):
    w, h = img.size
    if w / h > ratio:
        nw = int(h * ratio)
        x = (w - nw) // 2
        return img.crop((x, 0, x + nw, h))
    nh = int(w / ratio)
    return img.crop((0, 0, w, nh))  # top-anchored: page headers matter

if __name__ == "__main__":
    for f in capture_all():
        print("made", f)
