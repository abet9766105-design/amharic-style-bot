"""Text-style renderer: text + style name -> PNG bytes."""
import io
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os
CATEGORIES = {
    "normal": "መደበኛ"
}

STYLES = {
    "default": "Default"
}

def render(text, style="default"):
    return b""
W, H = 1080, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
# Put NotoSansEthiopic-Bold.ttf next to this file (free from Google Fonts).
FONT_CANDIDATES = [
    os.path.join(HERE, "font.ttf"),
    "C:/Windows/Fonts/nyala.ttf",  # Windows has Nyala (Ethiopic)
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",  # Linux fallback (has Ethiopic)
]


def _font_path():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Put an Ethiopic font at font.ttf")


def _wrap(text, font, max_w):
    d = ImageDraw.Draw(Image.new("L", (10, 10)))
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _text_mask(text, top=320):
    """Return (mask, bottom_y). Auto-sizes and wraps the text."""
    path = _font_path()
    size = 260
    while True:
        font = ImageFont.truetype(path, size)
        lines = _wrap(text, font, W - 160)
        line_h = int(size * 1.15)
        widest = max(ImageDraw.Draw(Image.new("L", (10, 10))).textlength(l, font=font) for l in lines)
        if (widest <= W - 120 and line_h * len(lines) <= 560) or size <= 70:
            break
        size -= 10
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    total_h = line_h * len(lines)
    y = max(120, (H - total_h) // 2 - 80)
    for l in lines:
        w = d.textlength(l, font=font)
        d.text(((W - w) / 2, y), l, font=font, fill=255, stroke_width=3, stroke_fill=255)
        y += line_h
    return mask


def _dark_bg(tint=(30, 10, 12)):
    vig = Image.radial_gradient("L").resize((W, H)).point(lambda v: min(255, int(v * 1.2)))
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), Image.new("RGB", (W, H), tint), vig)


def _vgrad(stops):
    """Vertical gradient over the full image. stops = [(pos0-1, (r,g,b)), ...]"""
    g = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(g)
    for y in range(H):
        t = y / (H - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                k = (t - p0) / (p1 - p0) if p1 > p0 else 0
                gd.line([(0, y), (W, y)], fill=tuple(int(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)))
                break
    return g


def _paste_color(bg, color, mask, opacity=1.0):
    m = mask.point(lambda v: int(v * opacity))
    bg.paste(Image.new("RGB", (W, H), color), (0, 0), m)


def blood(text):
    rnd = random.Random()
    mask = _text_mask(text)
    px = mask.load()
    drips = Image.new("L", (W, H), 0)
    dd = ImageDraw.Draw(drips)
    cols = {}
    for x in range(W):
        ys = [y for y in range(0, H, 2) if px[x, y] > 200]
        if ys:
            cols[x] = max(ys)
    x = min(cols) if cols else 0
    xmax = max(cols) if cols else 0
    while x < xmax:
        if x in cols and rnd.random() < 0.9:
            w = rnd.randint(10, 20)
            length = rnd.randint(40, 230)
            yb = cols[x] - 6
            dd.rectangle([x, yb, x + w, yb + length], fill=255)
            dd.ellipse([x - 1, yb + length - w // 2 - 2, x + w + 1, yb + length + w // 2 + 8], fill=255)
            x += w + rnd.randint(18, 60)
        else:
            x += 6
    shape = ImageChops.lighter(mask, drips).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 120 else 0)
    shape = shape.filter(ImageFilter.GaussianBlur(1.0))
    bg = _dark_bg()
    _paste_color(bg, (170, 0, 0), shape.filter(ImageFilter.GaussianBlur(28)), 0.8)
    _paste_color(bg, (35, 0, 0), shape.filter(ImageFilter.MaxFilter(9)))
    bg.paste(_vgrad([(0, (240, 20, 25)), (0.5, (190, 0, 10)), (1, (90, 0, 0))]), (0, 0), shape)
    hi = ImageChops.subtract(shape, ImageChops.offset(shape, 5, 8)).filter(ImageFilter.GaussianBlur(2))
    _paste_color(bg, (255, 150, 150), hi, 0.7)
    return bg


def _neon(text, color, core=(255, 255, 255)):
    mask = _text_mask(text)
    bg = _dark_bg((8, 8, 18))
    for radius, op in [(60, 0.55), (30, 0.7), (14, 0.9)]:
        _paste_color(bg, color, mask.filter(ImageFilter.GaussianBlur(radius)), op)
    _paste_color(bg, color, mask.filter(ImageFilter.MaxFilter(5)))
    _paste_color(bg, core, mask.filter(ImageFilter.MinFilter(5)))
    return bg


def neon_blue(text):
    return _neon(text, (0, 170, 255))


def neon_pink(text):
    return _neon(text, (255, 40, 170))


def neon_green(text):
    return _neon(text, (40, 255, 90))


def gold(text):
    mask = _text_mask(text)
    bg = _dark_bg((20, 14, 4))
    _paste_color(bg, (255, 190, 40), mask.filter(ImageFilter.GaussianBlur(26)), 0.35)
    _paste_color(bg, (60, 35, 0), mask.filter(ImageFilter.MaxFilter(9)))
    fill = _vgrad([(0.2, (255, 244, 170)), (0.45, (240, 180, 40)), (0.6, (150, 90, 10)), (0.8, (255, 215, 90)), (1, (200, 140, 30))])
    bg.paste(fill, (0, 0), mask)
    hi = ImageChops.subtract(mask, ImageChops.offset(mask, 3, 5)).filter(ImageFilter.GaussianBlur(1.5))
    _paste_color(bg, (255, 255, 230), hi, 0.8)
    return bg


def fire(text):
    mask = _text_mask(text)
    bg = _dark_bg((25, 6, 0))
    _paste_color(bg, (255, 90, 0), mask.filter(ImageFilter.GaussianBlur(40)), 0.7)
    _paste_color(bg, (255, 140, 0), mask.filter(ImageFilter.GaussianBlur(16)), 0.6)
    _paste_color(bg, (60, 5, 0), mask.filter(ImageFilter.MaxFilter(7)))
    fill = _vgrad([(0.2, (255, 250, 150)), (0.45, (255, 170, 20)), (0.65, (240, 60, 0)), (1, (140, 10, 0))])
    bg.paste(fill, (0, 0), mask)
    return bg


def glow(text):
    mask = _text_mask(text)
    bg = _dark_bg((14, 14, 14))
    for radius, op in [(50, 0.5), (22, 0.7), (8, 0.9)]:
        _paste_color(bg, (255, 255, 255), mask.filter(ImageFilter.GaussianBlur(radius)), op)
    _paste_color(bg, (255, 255, 255), mask)
    return bg


STYLES = {
    "blood": ("🩸 ደም", blood),
    "neon_blue": ("💙 ኒዮን ሰማያዊ", neon_blue),
    "neon_pink": ("💗 ኒዮን ሮዝ", neon_pink),
    "neon_green": ("💚 ኒዮን አረንጓዴ", neon_green),
    "gold": ("🥇 ወርቅ", gold),
    "fire": ("🔥 እሳት", fire),
    "glow": ("⚪ ነጭ ብርሃን", glow),
}


def render(text, style):
    img = STYLES[style][1](text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
