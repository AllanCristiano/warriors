"""Gerador procedural dos assets do Reino (tematica medieval).
Uso: python tools/gen_kingdom.py   (na raiz do projeto)
Gera tudo em assets/kingdom/
"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "kingdom")
os.makedirs(OUT, exist_ok=True)
SS = 2  # supersampling
OUTLINE = (32, 22, 18, 255)
rng = np.random.default_rng(7)
random.seed(7)

# ---------------------------------------------------------------- helpers

def tnoise(w, h, cx, cy, octaves=3, seed=None):
    """Value noise tileavel (wrap nos dois eixos), retorna array 0..1."""
    r = np.random.default_rng(seed if seed is not None else rng.integers(1 << 30))
    out = np.zeros((h, w)); amp = 1.0; tot = 0
    for o in range(octaves):
        gx, gy = cx * (2 ** o), cy * (2 ** o)
        G = r.random((gy, gx))
        x = np.arange(w) / w * gx; y = np.arange(h) / h * gy
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
        fx = x - x0; fy = y - y0
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
        x1 = (x0 + 1) % gx; y1 = (y0 + 1) % gy; x0 %= gx; y0 %= gy
        a = G[np.ix_(y0, x0)]; b = G[np.ix_(y0, x1)]
        c = G[np.ix_(y1, x0)]; d = G[np.ix_(y1, x1)]
        top = a + (b - a) * fx[None, :]; bot = c + (d - c) * fx[None, :]
        out += amp * (top + (bot - top) * fy[:, None]); tot += amp; amp *= 0.5
    return out / tot

def canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))

def S(v):
    if isinstance(v, (list, tuple)):
        return [S(x) for x in v]
    return v * SS

def lerpc(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(len(c1)))

def grad_layer(size, c1, c2, vertical=True):
    w, h = size
    t = np.linspace(0, 1, h if vertical else w)
    arr = np.zeros((h, w, 4), np.uint8)
    cols = np.array([lerpc(c1 + (255,) if len(c1) == 3 else c1, c2 + (255,) if len(c2) == 3 else c2, x) for x in t], np.uint8)
    if vertical: arr[:] = cols[:, None, :]
    else: arr[:] = cols[None, :, :]
    return Image.fromarray(arr, "RGBA")

def fill_mask(img, mask, c1, c2=None, vertical=True, grain=0.12, box=None):
    """Preenche img onde mask (L) com gradiente c1->c2 + granulado."""
    c2 = c2 or c1
    if box is None:
        box = mask.getbbox()
        if box is None: return
    x0, y0, x1, y1 = box
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    g = grad_layer((w, h), c1, c2, vertical)
    if grain:
        n = tnoise(w, h, max(2, w // 40), max(2, h // 40), 4)
        a = np.array(g).astype(np.float32)
        a[:, :, :3] *= (1 + grain * (n[:, :, None] - 0.5) * 2)
        g = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    full = Image.new("RGBA", img.size, (0, 0, 0, 0))
    full.paste(g, (x0, y0))
    img.paste(full, (0, 0), mask)

def poly(img, pts, c1, c2=None, vertical=True, grain=0.12):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    fill_mask(img, m, c1, c2, vertical, grain)
    return m

def rect(img, x0, y0, x1, y1, c1, c2=None, vertical=True, grain=0.12, radius=0):
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    if radius: d.rounded_rectangle(S([x0, y0, x1, y1]), radius=radius * SS, fill=255)
    else: d.rectangle(S([x0, y0, x1, y1]), fill=255)
    fill_mask(img, m, c1, c2, vertical, grain)
    return m

def ellipse(img, x0, y0, x1, y1, c1, c2=None, vertical=True, grain=0.12):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse(S([x0, y0, x1, y1]), fill=255)
    fill_mask(img, m, c1, c2, vertical, grain)
    return m

def line(img, pts, color, width=2):
    ImageDraw.Draw(img).line([(x * SS, y * SS) for x, y in pts], fill=color, width=int(width * SS), joint="curve")

def outline(img, thick=2, color=OUTLINE):
    a = img.split()[3]
    k = thick * SS * 2 + 1
    dil = a.filter(ImageFilter.MaxFilter(k if k % 2 else k + 1))
    base = Image.new("RGBA", img.size, color)
    base.putalpha(dil)
    base.alpha_composite(img)
    return base

def shade_bottom(img, strength=0.35):
    """Escurece a parte de baixo (oclusao ambiente simples)."""
    a = np.array(img).astype(np.float32)
    h = a.shape[0]
    t = np.linspace(0, 1, h)[:, None, None]
    a[:, :, :3] *= (1 - strength * t ** 2)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")

def grade(img, desat=0.22, mul=0.9):
    a = np.array(img).astype(np.float32)
    rgb = a[:, :, :3]
    lum = rgb.mean(2, keepdims=True)
    rgb = rgb * (1 - desat) + lum * desat
    shadow = np.clip(1 - lum / 140.0, 0, 1)
    rgb = rgb * mul + shadow * np.array([2, 0, 10], np.float32)
    a[:, :, :3] = rgb
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def save(img, name, outline_px=2, downsample=True):
    img = grade(img)
    if outline_px: img = outline(img, outline_px, (14, 10, 12, 255))
    if downsample and SS > 1:
        img = img.resize((img.width // SS, img.height // SS), Image.LANCZOS)
    img.save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name, img.size)
    return img

def save_raw(img, name, do_grade=True):
    if do_grade:
        img = grade(img.convert("RGBA"))
    img.save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name, img.size)

def colorize(n, c_dark, c_light):
    n = n[..., None]
    a = np.array(c_dark, np.float32) * (1 - n) + np.array(c_light, np.float32) * n
    return a

# ---------------------------------------------------------------- palette
# tema sombrio: cores dessaturadas e escuras
WOOD = (88, 60, 40); WOOD_L = (120, 86, 56); WOOD_D = (48, 32, 22)
PLASTER = (146, 136, 118); PLASTER_D = (100, 92, 80)
THATCH = (130, 102, 58); THATCH_D = (80, 58, 32)
STONE = (100, 97, 96); STONE_D = (54, 52, 56); STONE_L = (134, 130, 127)
SLATE = (50, 54, 66); SLATE_D = (28, 30, 40)
RED = (118, 18, 26); RED_D = (66, 10, 15)
BLUE = (32, 40, 78); BLUE_D = (16, 20, 44)
GOLD = (186, 140, 52); GOLD_D = (116, 82, 28)
GRASS = (56, 74, 42); GRASS_D = (30, 44, 26); GRASS_L = (84, 104, 56)
DIRT = (66, 50, 38); DIRT_D = (36, 27, 22)
IRON = (84, 86, 92); IRON_D = (46, 48, 54)

# ================================================================ TILES

def tile_fill(name, w, h, dark, light, stones=0, seed=1, bricks=None, mortar=None):
    n = tnoise(w, h, 4, 4, 5, seed)
    arr = colorize(n, dark, light)
    img = Image.fromarray(np.concatenate([arr, np.full((h, w, 1), 255)], 2).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    r = random.Random(seed)
    if bricks:
        bw, bh = bricks
        rows = h // bh
        for ry in range(rows):
            off = (bw // 2) * (ry % 2)
            for bx in range(-1, w // bw + 1):
                x0 = bx * bw + off; y0 = ry * bh
                shade = r.uniform(0.82, 1.12)
                col = tuple(int(min(255, c * shade)) for c in light)
                for xx in (x0, x0 - w, x0 + w):
                    d.rectangle([xx + 1, y0 + 1, xx + bw - 2, y0 + bh - 2], fill=None)
                # pinta tijolo com ruido
                for xx in (x0 - w, x0, x0 + w):
                    box = [max(0, xx + 1), y0 + 1, min(w, xx + bw - 1), y0 + bh - 1]
                    if box[2] <= box[0]: continue
                    sub = img.crop(box)
                    sa = np.array(sub).astype(np.float32); sa[:, :, :3] *= shade
                    img.paste(Image.fromarray(np.clip(sa, 0, 255).astype(np.uint8)), box[:2])
                    d.line([box[0], box[1], box[2] - 1, box[1]], fill=tuple(min(255, int(c * 1.25)) for c in col) + (120,))
                    d.line([box[0], box[3] - 1, box[2] - 1, box[3] - 1], fill=(0, 0, 0, 90))
            d.line([0, ry * bh, w, ry * bh], fill=mortar, width=2)
            for bx in range(-1, w // bw + 2):
                x = (bx * bw + off) % w
                d.line([x, ry * bh, x, ry * bh + bh], fill=mortar, width=2)
    for _ in range(stones):
        x, y = r.randrange(w), r.randrange(h)
        rr = r.randint(2, 5)
        c = tuple(int(c * r.uniform(1.1, 1.4)) for c in dark)
        for xx in (x - w, x, x + w):
            d.ellipse([xx - rr, y - rr * 0.7, xx + rr, y + rr * 0.7], fill=c + (255,), outline=(0, 0, 0, 80))
    save_raw(img, name)
    return img

def grass_top():
    w, h = 128, 48
    img = canvas(w, h)
    # faixa de terra com grama
    n = tnoise(w * SS, h * SS, 8, 2, 4, 11)
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m)
    d.rectangle(S([0, 14, w, h]), fill=255)
    fill_mask(img, m, GRASS_L, GRASS_D, True, 0.25)
    # tufos sobressaindo no topo e franja caindo
    dr = ImageDraw.Draw(img)
    r = random.Random(3)
    for i in range(170):
        x = r.uniform(0, w); hgt = r.uniform(5, 15)
        c = lerpc(GRASS_D, GRASS_L, r.random())
        for xx in (x, x - w, x + w):
            dr.polygon(S([(xx - 2, 16), (xx + r.uniform(-3, 3), 16 - hgt), (xx + 2, 16)]), fill=c + (255,))
    for i in range(60):
        x = r.uniform(0, w); hgt = r.uniform(6, 16)
        c = lerpc(GRASS_D, GRASS, r.random())
        for xx in (x, x - w, x + w):
            dr.polygon(S([(xx - 3, 40), (xx, 40 + hgt * 0.5), (xx + 3, 40)]), fill=c + (255,))
    # florzinhas
    for i in range(10):
        x = r.uniform(4, w - 4); y = r.uniform(6, 14)
        col = r.choice([(240, 230, 120), (240, 240, 240), (200, 90, 160)])
        dr.ellipse(S([x - 1.5, y - 1.5, x + 1.5, y + 1.5]), fill=col + (255,))
    img = img.resize((w, h), Image.LANCZOS)
    save_raw(img, "tile_grass_top")

def cobble_top():
    w, h = 128, 36
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = random.Random(5)
    # meio-fio de pedra lavrada
    x = 0
    while x < w:
        bw = 32
        c = lerpc(STONE_D, STONE_L, r.uniform(0.35, 0.8))
        d.rounded_rectangle([x + 1, 2, x + bw - 1, 20], radius=3, fill=c + (255,), outline=OUTLINE)
        d.line([x + 3, 4, x + bw - 4, 4], fill=lerpc(c, (255, 255, 255), 0.35) + (255,), width=2)
        x += bw
    x = -16
    while x < w + 16:
        c = lerpc(STONE_D, STONE, r.uniform(0.3, 0.9))
        d.rounded_rectangle([x + 1, 20, x + 31, 35], radius=2, fill=c + (255,), outline=OUTLINE)
        x += 32
    a = np.array(img).astype(np.float32)
    n = tnoise(w, h, 8, 2, 4, 5)
    a[:, :, :3] *= (0.88 + 0.24 * n[:, :, None])
    save_raw(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), "tile_cobble_top")

def dungeon_top():
    w, h = 128, 30
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = random.Random(9)
    x = 0
    while x < w:
        bw = 64
        c = lerpc((50, 48, 58), (100, 96, 108), r.uniform(0.4, 0.9))
        d.rectangle([x, 2, x + bw - 1, 22], fill=c + (255,), outline=(18, 14, 20, 255))
        d.line([x + 2, 4, x + bw - 3, 4], fill=lerpc(c, (200, 200, 220), 0.35) + (255,), width=2)
        for k in range(3):
            cx = x + r.uniform(6, bw - 6)
            d.line([cx, 6, cx + r.uniform(-6, 6), 18], fill=(25, 22, 30, 200), width=1)
        x += bw
    d.rectangle([0, 22, w, 30], fill=(36, 32, 42, 255))
    a = np.array(img).astype(np.float32)
    n = tnoise(w, h, 8, 2, 4, 8)
    a[:, :, :3] *= (0.85 + 0.3 * n[:, :, None])
    save_raw(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), "tile_dungeon_top")

def plank_tile():
    w, h = 64, 22
    img = canvas(w, h)
    rect(img, 0, 2, w, 14, WOOD_L, WOOD, grain=0.3)
    rect(img, 0, 14, w, 20, WOOD_D, (50, 30, 18), grain=0.2)
    dr = ImageDraw.Draw(img)
    for x in (0, 32):
        line(img, [(x, 2), (x, 20)], OUTLINE, 1.5)
        dr.ellipse(S([x + 4, 6, x + 7, 9]), fill=IRON + (255,))
        dr.ellipse(S([x + 25, 6, x + 28, 9]), fill=IRON + (255,))
    for y in (6, 10):
        line(img, [(0, y), (w, y + 0.5)], WOOD_D + (110,), 0.7)
    line(img, [(0, 2), (w, 2)], OUTLINE, 1.5)
    line(img, [(0, 20), (w, 20)], OUTLINE, 1.5)
    img = img.resize((w, h), Image.LANCZOS)
    save_raw(img, "tile_plank")

def stone_ledge_tile():
    w, h = 64, 28
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1, w - 1, 18], fill=STONE + (255,), outline=OUTLINE)
    d.line([0, 3, w, 3], fill=STONE_L + (255,), width=2)
    d.line([32, 1, 32, 18], fill=OUTLINE, width=1)
    d.rectangle([0, 18, w - 1, 27], fill=STONE_D + (255,), outline=OUTLINE)
    for x in range(4, w, 16):
        d.polygon([(x, 18), (x + 8, 18), (x + 4, 26)], fill=(70, 66, 64, 255))
    a = np.array(img).astype(np.float32)
    n = tnoise(w, h, 4, 2, 4, 21)
    a[:, :, :3] *= (0.85 + 0.3 * n[:, :, None])
    save_raw(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), "tile_stone_ledge")

# ================================================================ PROPS

def thatch_roof(img, pts, seed=1):
    m = poly(img, pts, THATCH, THATCH_D, True, 0.2)
    r = random.Random(seed)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    for i in range(int((max(xs) - min(xs)) * (max(ys) - min(ys)) / 30)):
        x = r.uniform(min(xs), max(xs)); y = r.uniform(min(ys), max(ys))
        c = lerpc(THATCH_D, (235, 200, 120), r.random())
        dl.line(S([x, y, x + r.uniform(-2, 2), y + r.uniform(6, 12)]), fill=c + (255,), width=SS)
    img.paste(layer, (0, 0), ImageChops.multiply(m, layer.split()[3]))
    # rows
    for y in np.arange(min(ys) + 14, max(ys), 16):
        rowm = Image.new("L", img.size, 0)
        ImageDraw.Draw(rowm).rectangle(S([min(xs), y, max(xs), y + 3]), fill=110)
        sh = Image.new("RGBA", img.size, (60, 40, 15, 255))
        img.paste(sh, (0, 0), ImageChops.multiply(m, rowm))

def window(img, x, y, w, h, lit=True, arch=False):
    rect(img, x - 3, y - 3, x + w + 3, y + h + 3, WOOD_D, grain=0.2)
    glass = (250, 205, 110) if lit else (40, 50, 70)
    glass2 = (230, 150, 60) if lit else (25, 30, 45)
    if arch:
        m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m)
        d.rectangle(S([x, y + w / 2, x + w, y + h]), fill=255); d.ellipse(S([x, y, x + w, y + w]), fill=255)
        fill_mask(img, m, glass, glass2)
    else:
        rect(img, x, y, x + w, y + h, glass, glass2)
    line(img, [(x + w / 2, y), (x + w / 2, y + h)], WOOD_D, 2)
    line(img, [(x, y + h / 2), (x + w, y + h / 2)], WOOD_D, 2)
    rect(img, x - 5, y + h + 2, x + w + 5, y + h + 6, WOOD, WOOD_D)

def door(img, x, y, w, h):
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m)
    d.rectangle(S([x, y + w / 2, x + w, y + h]), fill=255); d.ellipse(S([x, y, x + w, y + w]), fill=255)
    fill_mask(img, m, WOOD, WOOD_D, False, 0.3)
    for k in range(1, 4):
        line(img, [(x + w * k / 4, y + 4), (x + w * k / 4, y + h)], WOOD_D, 1.5)
    rect(img, x + 2, y + h * 0.3, x + w - 2, y + h * 0.3 + 4, IRON, IRON_D)
    rect(img, x + 2, y + h * 0.75, x + w - 2, y + h * 0.75 + 4, IRON, IRON_D)
    ImageDraw.Draw(img).ellipse(S([x + w - 9, y + h * 0.55, x + w - 4, y + h * 0.55 + 5]), fill=GOLD + (255,))

def house_a():
    W, H = 300, 290
    img = canvas(W, H)
    # parede de pedra base
    rect(img, 30, 170, 270, 290, STONE, STONE_D, grain=0.25)
    d = ImageDraw.Draw(img); r = random.Random(2)
    for y in range(176, 288, 16):
        for x in range(30 + (8 if (y // 16) % 2 else 0), 270, 26):
            d.rounded_rectangle(S([x + 1, y + 1, min(269, x + 24), y + 14]), radius=3 * SS,
                                outline=(70, 66, 62, 255), width=SS)
    # andar superior enxaimel
    rect(img, 22, 95, 278, 175, PLASTER, PLASTER_D, grain=0.15)
    for x in (22, 85, 150, 215, 272):
        rect(img, x, 95, x + 7, 175, WOOD, WOOD_D)
    line(img, [(29, 100), (85, 170)], WOOD_D, 6); line(img, [(150, 100), (92, 170)], WOOD_D, 6)
    line(img, [(222, 100), (272, 170)], WOOD_D, 6)
    rect(img, 18, 168, 282, 177, WOOD, WOOD_D)
    rect(img, 18, 92, 282, 100, WOOD, WOOD_D)
    window(img, 165, 115, 36, 40)
    window(img, 60, 205, 34, 40)
    window(img, 205, 205, 34, 40)
    door(img, 125, 215, 44, 75)
    # telhado de palha
    thatch_roof(img, [(150, 2), (296, 100), (4, 100)], 4)
    # chamine
    rect(img, 210, 10, 236, 60, STONE, STONE_D)
    rect(img, 206, 6, 240, 14, STONE_L, STONE)
    img = shade_bottom(img, 0.2)
    save(img, "house_a")

def house_b():
    W, H = 260, 340
    img = canvas(W, H)
    rect(img, 20, 110, 240, 340, PLASTER, PLASTER_D, grain=0.15)
    for x in (20, 90, 165, 233):
        rect(img, x, 110, x + 7, 340, WOOD, WOOD_D)
    for y in (110, 220, 333):
        rect(img, 16, y, 244, y + 8, WOOD, WOOD_D)
    line(img, [(27, 120), (90, 220)], WOOD_D, 6); line(img, [(240, 120), (172, 220)], WOOD_D, 6)
    window(img, 108, 140, 40, 50, arch=True)
    window(img, 40, 245, 34, 40)
    door(img, 175, 255, 46, 78)
    # placa de taverna
    rect(img, 96, 236, 100, 290, IRON_D)
    line(img, [(98, 238), (150, 238)], IRON_D, 3)
    rect(img, 108, 242, 150, 272, WOOD_L, WOOD, radius=4)
    d = ImageDraw.Draw(img)
    d.polygon(S([(121, 249), (137, 249), (134, 266), (124, 266)]), fill=GOLD + (255,))  # caneca
    d.arc(S([132, 252, 142, 262]), -90, 90, fill=GOLD + (255,), width=2 * SS)
    # telhado de ardosia
    m = poly(img, [(130, 0), (256, 116), (4, 116)], SLATE, SLATE_D, True, 0.2)
    for y in range(18, 116, 10):
        half = (y / 116) * 126
        for x in np.arange(130 - half, 130 + half, 14):
            xx = x + (7 if (y // 10) % 2 else 0)
            if xx < 130 + half - 4:
                line(img, [(xx, y), (xx, y + 9)], SLATE_D, 1.2)
        line(img, [(130 - half, y), (130 + half, y)], SLATE_D, 1.2)
    img = shade_bottom(img, 0.2)
    save(img, "house_b")

def tree():
    W, H = 280, 340
    img = canvas(W, H)
    # tronco
    poly(img, [(122, 340), (128, 200), (112, 150), (130, 150), (140, 190), (155, 150), (168, 150), (152, 210), (160, 340)],
         WOOD, WOOD_D, False, 0.35)
    r = random.Random(12)
    blobs = []
    for i in range(26):
        a = r.uniform(0, math.tau); rad = r.uniform(0, 90)
        cx = 140 + math.cos(a) * rad * 0.8; cy = 120 + math.sin(a) * rad * 0.75
        s = r.uniform(38, 62)
        blobs.append((cy, cx, s))
    blobs.sort()
    for cy, cx, s in blobs:
        t = (cy - 40) / 160
        ellipse(img, cx - s, cy - s * 0.85, cx + s, cy + s * 0.85,
                lerpc(GRASS_L, GRASS, min(1, max(0, t))), lerpc(GRASS, (22, 36, 22), min(1, max(0, t))), True, 0.35)
    # folhagem detalhe
    d = ImageDraw.Draw(img)
    a = np.array(img.split()[3])
    for i in range(500):
        x = r.uniform(30, 250); y = r.uniform(20, 220)
        if a[int(y * SS), int(x * SS)] > 0 and r.random() < 0.8:
            c = lerpc((30, 46, 28), (96, 118, 64), (220 - y) / 220 * r.random())
            d.ellipse(S([x - 3, y - 2, x + 3, y + 2]), fill=c + (255,))
    save(img, "tree_oak")

def pine():
    W, H = 160, 320
    img = canvas(W, H)
    rect(img, 72, 250, 88, 320, WOOD, WOOD_D)
    for i, (y, w) in enumerate([(20, 30), (70, 50), (120, 65), (170, 78), (215, 80)]):
        poly(img, [(80, y - 25), (80 + w, y + 55), (80 - w, y + 55)], (40, 66, 48), (18, 34, 26), True, 0.3)
    save(img, "tree_pine")

def bush():
    W, H = 140, 80
    img = canvas(W, H)
    for cx, cy, s in [(40, 55, 30), (100, 55, 30), (70, 40, 36), (30, 65, 20), (115, 65, 22)]:
        ellipse(img, cx - s, cy - s * 0.8, cx + s, cy + s * 0.8, GRASS_L, GRASS_D, True, 0.35)
    d = ImageDraw.Draw(img); r = random.Random(4)
    for i in range(8):
        x = r.uniform(25, 115); y = r.uniform(30, 60)
        d.ellipse(S([x - 2.5, y - 2.5, x + 2.5, y + 2.5]), fill=(200, 40, 50, 255))
    save(img, "bush")

def fence():
    W, H = 128, 64
    img = canvas(W, H)
    for x in (8, 72):
        poly(img, [(x, 64), (x, 8), (x + 6, 2), (x + 12, 8), (x + 12, 64)], WOOD_L, WOOD_D, False, 0.3)
    rect(img, 0, 18, 128, 27, WOOD_L, WOOD, grain=0.35)
    rect(img, 0, 40, 128, 49, WOOD, WOOD_D, grain=0.35)
    save(img, "fence", 1)

def haystack():
    W, H = 150, 110
    img = canvas(W, H)
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m)
    d.pieslice(S([5, 10, 145, 210]), 180, 360, fill=255)
    d.rectangle(S([5, 108, 145, 110]), fill=255)
    fill_mask(img, m, (238, 205, 110), THATCH_D, True, 0.3)
    r = random.Random(8); layer = Image.new("RGBA", img.size); dl = ImageDraw.Draw(layer)
    for i in range(400):
        x = r.uniform(10, 140); y = r.uniform(15, 108)
        c = lerpc(THATCH_D, (250, 220, 140), r.random())
        dl.line(S([x, y, x + r.uniform(-5, 5), y + r.uniform(4, 9)]), fill=c + (255,), width=SS)
    img.paste(layer, (0, 0), ImageChops.multiply(m, layer.split()[3]))
    line(img, [(40, 108), (60, 20)], WOOD_D, 3)  # forcado
    save(img, "haystack")

def barrel():
    W, H = 64, 80
    img = canvas(W, H)
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m)
    d.rounded_rectangle(S([6, 4, 58, 78]), radius=16 * SS, fill=255)
    fill_mask(img, m, WOOD_L, WOOD_D, False, 0.3)
    for x in (18, 32, 46):
        line(img, [(x, 6), (x, 76)], WOOD_D + (160,), 1)
    for y in (14, 66):
        rect(img, 5, y, 59, y + 6, IRON, IRON_D)
    rect(img, 4, 37, 60, 43, IRON, IRON_D)
    save(img, "barrel")

def crate():
    W, H = 70, 70
    img = canvas(W, H)
    rect(img, 2, 2, 68, 68, WOOD_L, WOOD, grain=0.3)
    for y in (2, 60):
        rect(img, 2, y, 68, y + 8, WOOD, WOOD_D)
    for x in (2, 60):
        rect(img, x, 2, x + 8, 68, WOOD, WOOD_D)
    line(img, [(10, 12), (60, 58)], WOOD_D, 7)
    line(img, [(10, 12), (60, 58)], WOOD, 4)
    d = ImageDraw.Draw(img)
    for x, y in [(6, 6), (64, 6), (6, 64), (64, 64)]:
        d.ellipse(S([x - 2, y - 2, x + 2, y + 2]), fill=IRON + (255,))
    save(img, "crate")

def well():
    W, H = 170, 200
    img = canvas(W, H)
    rect(img, 15, 120, 155, 200, STONE, STONE_D, grain=0.3)
    d = ImageDraw.Draw(img)
    for y in range(124, 198, 18):
        for x in range(15 + (12 if (y // 18) % 2 else 0), 155, 28):
            d.rounded_rectangle(S([x + 1, y, min(154, x + 26), y + 16]), radius=3 * SS, outline=(70, 66, 62, 255), width=SS)
    rect(img, 10, 112, 160, 124, STONE_L, STONE)
    rect(img, 24, 40, 32, 116, WOOD, WOOD_D); rect(img, 138, 40, 146, 116, WOOD, WOOD_D)
    poly(img, [(85, 0), (168, 48), (2, 48)], RED, RED_D, True, 0.2)
    rect(img, 28, 66, 142, 72, WOOD_D)
    line(img, [(85, 72), (85, 96)], (190, 170, 120), 1.5)
    rect(img, 74, 94, 96, 112, WOOD, WOOD_D)
    rect(img, 72, 96, 98, 99, IRON)
    save(img, "well")

def cart():
    W, H = 220, 130
    img = canvas(W, H)
    rect(img, 20, 40, 190, 90, WOOD_L, WOOD, grain=0.3)
    for x in range(20, 190, 34):
        line(img, [(x, 40), (x, 90)], WOOD_D, 2)
    line(img, [(190, 80), (220, 92)], WOOD_D, 6)
    # carga de feno + abobora
    ellipse(img, 30, 14, 120, 56, (235, 200, 110), THATCH_D)
    ellipse(img, 110, 22, 150, 52, (225, 130, 40), (170, 80, 20))
    rect(img, 128, 18, 132, 26, GRASS_D)
    for cx in (60, 160):
        m = ellipse(img, cx - 32, 70, cx + 32, 130, WOOD, WOOD_D)
        d = ImageDraw.Draw(img)
        for k in range(8):
            a = k * math.pi / 4
            d.line(S([cx, 100, cx + math.cos(a) * 28, 100 + math.sin(a) * 28]), fill=WOOD_D + (255,), width=3 * SS)
        d.ellipse(S([cx - 26, 74, cx + 26, 126]), outline=IRON_D + (255,), width=3 * SS)
        d.ellipse(S([cx - 6, 94, cx + 6, 106]), fill=IRON + (255,))
    save(img, "cart")

def market_stall():
    W, H = 230, 210
    img = canvas(W, H)
    rect(img, 20, 60, 28, 210, WOOD, WOOD_D); rect(img, 202, 60, 210, 210, WOOD, WOOD_D)
    rect(img, 10, 140, 220, 160, WOOD_L, WOOD)
    rect(img, 20, 160, 210, 210, WOOD, WOOD_D)
    # toldo listrado
    for i in range(8):
        c = RED if i % 2 == 0 else (235, 225, 200)
        cd = RED_D if i % 2 == 0 else (190, 180, 150)
        x0 = 5 + i * 27.5
        poly(img, [(x0 + 8, 20), (x0 + 35.5, 20), (x0 + 27.5, 64), (x0, 64)], c, cd, True, 0.15)
    for i in range(8):
        x0 = 5 + i * 27.5
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).pieslice(S([x0, 52, x0 + 27.5, 76]), 0, 180, fill=255)
        c = RED if i % 2 == 0 else (235, 225, 200)
        fill_mask(img, m, c, lerpc(c, (0, 0, 0), 0.3))
    # mercadorias
    for x, c in [(40, (220, 60, 50)), (62, (230, 120, 40)), (84, (210, 190, 60)), (150, (120, 170, 60)), (172, (220, 60, 50))]:
        ellipse(img, x - 10, 122, x + 10, 142, c, lerpc(c, (0, 0, 0), 0.35))
    rect(img, 105, 112, 135, 140, WOOD_L, WOOD)
    save(img, "market_stall")

def signpost():
    W, H = 110, 160
    img = canvas(W, H)
    rect(img, 50, 30, 60, 160, WOOD, WOOD_D)
    poly(img, [(8, 30), (88, 30), (104, 46), (88, 62), (8, 62)], WOOD_L, WOOD)
    poly(img, [(100, 72), (22, 72), (6, 86), (22, 100), (100, 100)], WOOD_L, WOOD)
    line(img, [(20, 46), (80, 46)], WOOD_D, 2); line(img, [(30, 86), (90, 86)], WOOD_D, 2)
    save(img, "signpost")

def torch():
    W, H = 40, 90
    img = canvas(W, H)
    rect(img, 4, 60, 36, 66, IRON, IRON_D)
    rect(img, 16, 40, 24, 88, WOOD, WOOD_D)
    poly(img, [(8, 28), (32, 28), (26, 44), (14, 44)], IRON, IRON_D)
    ellipse(img, 10, 22, 30, 34, (60, 30, 20), (30, 15, 10))
    save(img, "torch")

def banner(name, col, cold, emblem="lion"):
    W, H = 80, 200
    img = canvas(W, H)
    rect(img, 0, 0, 80, 10, WOOD, WOOD_D)
    ellipse(img, -4, -2, 8, 12, GOLD, GOLD_D); ellipse(img, 72, -2, 84, 12, GOLD, GOLD_D)
    poly(img, [(6, 8), (74, 8), (74, 190), (40, 165), (6, 190)], col, cold, True, 0.2)
    line(img, [(10, 12), (10, 180)], GOLD, 2); line(img, [(70, 12), (70, 180)], GOLD, 2)
    # escudo/emblema
    poly(img, [(22, 50), (58, 50), (58, 90), (40, 112), (22, 90)], GOLD, GOLD_D, True, 0.1)
    if emblem == "lion":
        d = ImageDraw.Draw(img)
        d.polygon(S([(30, 70), (40, 58), (50, 70), (46, 96), (34, 96)]), fill=col + (255,))
        d.ellipse(S([34, 60, 46, 72]), fill=cold + (255,))
    else:
        line(img, [(40, 56), (40, 104)], col, 4); line(img, [(28, 72), (52, 72)], col, 4)
    rect(img, 18, 128, 62, 132, GOLD, GOLD_D)
    save(img, name)

def flag(name, col, cold, up=True):
    W, H = 90, 200
    img = canvas(W, H)
    rect(img, 8, 10, 16, 200, WOOD_L, WOOD_D, False)
    ellipse(img, 4, 0, 20, 14, GOLD, GOLD_D)
    rect(img, 0, 188, 26, 200, STONE, STONE_D)
    y0 = 18 if up else 130
    poly(img, [(16, y0), (88, y0 + 10), (70, y0 + 28), (88, y0 + 46), (16, y0 + 50)], col, cold, False, 0.2)
    if up:
        ImageDraw.Draw(img).regular_polygon((S(42), S(y0 + 25), S(11)), 5, rotation=0, fill=GOLD + (255,))
    save(img, name)

def tower():
    W, H = 220, 520
    img = canvas(W, H)
    rect(img, 30, 110, 190, 520, STONE, STONE_D, False, 0.25)
    d = ImageDraw.Draw(img)
    for y in range(116, 520, 22):
        for x in range(30 + (18 if (y // 22) % 2 else 0), 190, 36):
            d.rectangle(S([x, y, min(190, x + 36), y + 22]), outline=(80, 76, 72, 255), width=SS)
    rect(img, 20, 96, 200, 116, STONE_L, STONE)
    for x in range(20, 200, 30):
        rect(img, x, 76, x + 18, 98, STONE_L, STONE)
    poly(img, [(110, 0), (205, 82), (15, 82)], BLUE, BLUE_D, True, 0.2)
    rect(img, 108, -20, 112, 4, IRON_D)
    window(img, 96, 170, 28, 52, lit=True, arch=True)
    window(img, 96, 320, 28, 52, lit=False, arch=True)
    img = shade_bottom(img, 0.25)
    save(img, "tower")

def castle_gate():
    W, H = 340, 380
    img = canvas(W, H)
    rect(img, 0, 60, 340, 380, STONE, STONE_D, False, 0.25)
    d = ImageDraw.Draw(img)
    for y in range(66, 380, 24):
        for x in range((20 if (y // 24) % 2 else 0), 340, 40):
            d.rectangle(S([x, y, min(340, x + 40), y + 24]), outline=(80, 76, 72, 255), width=SS)
    for x in range(0, 340, 40):
        rect(img, x, 30, x + 26, 62, STONE_L, STONE)
    rect(img, -2, 56, 342, 66, STONE_L, STONE)
    # arco
    m = Image.new("L", img.size, 0); dm = ImageDraw.Draw(m)
    dm.rectangle(S([90, 200, 250, 380]), fill=255); dm.ellipse(S([90, 120, 250, 280]), fill=255)
    fill_mask(img, m, (30, 24, 22), (12, 10, 10), True, 0.1)
    # portcullis
    for x in range(98, 250, 18):
        line(img, [(x, 130), (x, 360)], IRON, 4)
    for y in range(160, 360, 26):
        line(img, [(92, y), (248, y)], IRON, 4)
    for x in range(98, 250, 18):
        d.polygon(S([(x - 4, 360), (x + 4, 360), (x, 372)]), fill=IRON + (255,))
    # pedras do arco
    for k in range(13):
        a = math.pi + k * math.pi / 12
        x = 170 + math.cos(a) * 88; y = 200 + math.sin(a) * 88
        d.ellipse(S([x - 10, y - 10, x + 10, y + 10]), fill=STONE_L + (255,), outline=OUTLINE)
    # brasoes
    for bx in (30, 270):
        poly(img, [(bx, 120), (bx + 40, 120), (bx + 40, 170), (bx + 20, 192), (bx, 170)], RED, RED_D)
        ImageDraw.Draw(img).regular_polygon((S(bx + 20), S(150), S(11)), 5, fill=GOLD + (255,))
    save(img, "castle_gate")

def pillar():
    W, H = 100, 420
    img = canvas(W, H)
    rect(img, 18, 40, 82, 380, (110, 104, 118), (60, 56, 70), False, 0.25)
    for x in (30, 50, 70):
        line(img, [(x, 44), (x, 376)], (50, 46, 58, 200), 2)
    rect(img, 6, 20, 94, 44, (140, 134, 146), (90, 86, 100))
    rect(img, 0, 0, 100, 22, (120, 114, 128), (80, 76, 90))
    rect(img, 6, 376, 94, 400, (140, 134, 146), (90, 86, 100))
    rect(img, 0, 398, 100, 420, (120, 114, 128), (80, 76, 90))
    save(img, "pillar")

def chain():
    W, H = 30, 220
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    for i, y in enumerate(range(0, 210, 14)):
        if i % 2 == 0:
            d.ellipse(S([7, y, 23, y + 20]), outline=IRON + (255,), width=4 * SS)
        else:
            d.rectangle(S([13, y, 17, y + 20]), fill=IRON_D + (255,))
    rect(img, 4, 200, 26, 220, IRON, IRON_D)
    save(img, "chain", 1)

def throne():
    W, H = 220, 300
    img = canvas(W, H)
    rect(img, 20, 250, 200, 300, STONE, STONE_D)
    poly(img, [(40, 20), (110, 0), (180, 20), (180, 200), (40, 200)], RED_D, (60, 10, 14), True, 0.2)
    rect(img, 30, 20, 50, 250, GOLD, GOLD_D, False); rect(img, 170, 20, 190, 250, GOLD, GOLD_D, False)
    ellipse(img, 24, 6, 56, 38, GOLD, GOLD_D); ellipse(img, 164, 6, 196, 38, GOLD, GOLD_D)
    rect(img, 30, 190, 190, 222, RED, RED_D)
    rect(img, 40, 222, 180, 250, GOLD_D, (120, 80, 20))
    ImageDraw.Draw(img).regular_polygon((S(110), S(80), S(26)), 5, fill=GOLD + (255,))
    poly(img, [(90, 0), (100, -0), (110, 0)], GOLD)
    save(img, "throne")

def skulls():
    W, H = 120, 60
    img = canvas(W, H)
    for cx, cy, s in [(30, 40, 18), (70, 42, 16), (50, 24, 17), (95, 44, 14)]:
        ellipse(img, cx - s, cy - s, cx + s, cy + s * 0.9, (225, 215, 190), (150, 140, 120))
        d = ImageDraw.Draw(img)
        d.ellipse(S([cx - s * 0.55, cy - s * 0.2, cx - s * 0.1, cy + s * 0.3]), fill=(30, 20, 20, 255))
        d.ellipse(S([cx + s * 0.1, cy - s * 0.2, cx + s * 0.55, cy + s * 0.3]), fill=(30, 20, 20, 255))
    save(img, "skulls")

def weapon_rack():
    W, H = 140, 170
    img = canvas(W, H)
    rect(img, 10, 40, 130, 50, WOOD, WOOD_D); rect(img, 10, 120, 130, 130, WOOD, WOOD_D)
    rect(img, 10, 40, 18, 170, WOOD, WOOD_D); rect(img, 122, 40, 130, 170, WOOD, WOOD_D)
    # espada
    poly(img, [(40, 0), (46, 0), (46, 130), (43, 140), (40, 130)], (210, 214, 222), IRON)
    rect(img, 32, 128, 54, 134, GOLD, GOLD_D)
    # lança
    line(img, [(72, 10), (72, 160)], WOOD_D, 4)
    poly(img, [(72, 0), (78, 16), (66, 16)], (210, 214, 222), IRON)
    # machado
    line(img, [(100, 20), (100, 160)], WOOD_D, 4)
    poly(img, [(100, 24), (120, 14), (124, 44), (100, 38)], (200, 204, 212), IRON)
    save(img, "weapon_rack")

def knight_statue():
    W, H = 140, 330
    img = canvas(W, H)
    rect(img, 15, 270, 125, 330, STONE, STONE_D)
    rect(img, 8, 262, 132, 274, STONE_L, STONE)
    c1, c2 = (170, 168, 160), (100, 98, 96)
    poly(img, [(50, 120), (90, 120), (100, 262), (40, 262)], c1, c2)
    ellipse(img, 52, 70, 88, 118, c1, c2)
    rect(img, 50, 90, 90, 96, (60, 58, 56))
    poly(img, [(40, 120), (100, 120), (110, 150), (30, 150)], c1, c2)
    line(img, [(70, 30), (70, 250)], (150, 148, 142), 6)
    rect(img, 50, 130, 90, 138, c1, c2)
    poly(img, [(20, 150), (50, 150), (50, 210), (35, 228), (20, 210)], c1, c2)
    save(img, "knight_statue")

def windmill():
    W, H = 260, 400
    img = canvas(W, H)
    poly(img, [(95, 140), (165, 140), (185, 400), (75, 400)], PLASTER, PLASTER_D, False)
    poly(img, [(130, 90), (175, 145), (85, 145)], WOOD, WOOD_D)
    rect(img, 118, 330, 142, 400, WOOD, WOOD_D)
    window(img, 122, 220, 16, 22)
    cx, cy = 130, 140
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        ex, ey = cx + math.cos(a) * 125, cy + math.sin(a) * 125
        line(img, [(cx, cy), (ex, ey)], WOOD_D, 5)
        px, py = -math.sin(a) * 22, math.cos(a) * 22
        m1x, m1y = cx + math.cos(a) * 30, cy + math.sin(a) * 30
        poly(img, [(m1x, m1y), (ex, ey), (ex + px, ey + py), (m1x + px, m1y + py)], (230, 220, 190), (190, 175, 140), True, 0.15)
    ellipse(img, cx - 9, cy - 9, cx + 9, cy + 9, WOOD_D)
    save(img, "windmill")

def coin():
    W, H = 32, 32
    img = canvas(W, H)
    ellipse(img, 1, 1, 31, 31, GOLD_D, (110, 75, 20))
    ellipse(img, 3, 3, 29, 29, (255, 220, 110), GOLD)
    ImageDraw.Draw(img).regular_polygon((S(16), S(16), S(7)), 5, fill=GOLD_D + (255,))
    ImageDraw.Draw(img).ellipse(S([7, 6, 13, 11]), fill=(255, 250, 220, 220))
    save(img, "coin", 1)

def potion():
    W, H = 34, 44
    img = canvas(W, H)
    ellipse(img, 2, 12, 32, 42, (230, 50, 60), (130, 15, 25))
    rect(img, 12, 2, 22, 16, (200, 220, 230), (150, 170, 185))
    rect(img, 10, 0, 24, 6, WOOD, WOOD_D)
    ImageDraw.Draw(img).ellipse(S([8, 18, 14, 26]), fill=(255, 220, 220, 220))
    save(img, "potion", 1)

def heart():
    W, H = 40, 36
    img = canvas(W, H)
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m)
    d.ellipse(S([2, 2, 22, 22]), fill=255); d.ellipse(S([18, 2, 38, 22]), fill=255)
    d.polygon(S([(3, 15), (37, 15), (20, 34)]), fill=255)
    fill_mask(img, m, (240, 60, 70), (140, 15, 25))
    ImageDraw.Draw(img).ellipse(S([8, 7, 14, 13]), fill=(255, 220, 220, 230))
    save(img, "heart", 1)

def bola():
    W, H = 44, 28
    img = canvas(W, H)
    line(img, [(8, 14), (36, 14)], (150, 120, 80), 2)
    ellipse(img, 0, 6, 16, 22, STONE_L, STONE_D)
    ellipse(img, 28, 6, 44, 22, STONE_L, STONE_D)
    save(img, "proj_bola", 1)

def dart():
    W, H = 46, 12
    img = canvas(W, H)
    poly(img, [(0, 6), (10, 2), (40, 4), (46, 6), (40, 8), (10, 10)], (220, 225, 235), IRON)
    poly(img, [(0, 6), (6, 0), (10, 6), (6, 12)], RED, RED_D)
    save(img, "proj_dart", 1)

def fireball():
    W, H = 64, 40
    img = Image.new("RGBA", (W * SS, H * SS))
    for i, (r, c) in enumerate([(20, (255, 90, 20, 140)), (15, (255, 150, 40, 220)), (9, (255, 230, 150, 255))]):
        d = ImageDraw.Draw(img)
        d.ellipse(S([44 - r, 20 - r * 0.8, 44 + r, 20 + r * 0.8]), fill=c)
        d.polygon(S([(44, 20 - r * 0.8), (44 - r * 2.2, 20), (44, 20 + r * 0.8)]), fill=c)
    img = img.filter(ImageFilter.GaussianBlur(SS))
    save(img, "proj_fireball", 0)

def magic_orb():
    W, H = 36, 36
    img = Image.new("RGBA", (W * SS, H * SS))
    d = ImageDraw.Draw(img)
    for r, c in [(17, (120, 255, 120, 90)), (12, (150, 255, 140, 200)), (6, (235, 255, 220, 255))]:
        d.ellipse(S([18 - r, 18 - r, 18 + r, 18 + r]), fill=c)
    img = img.filter(ImageFilter.GaussianBlur(SS))
    save(img, "proj_orb", 0)

def spikes():
    W, H = 64, 36
    img = canvas(W, H)
    rect(img, 0, 28, 64, 36, IRON_D, (30, 30, 34))
    for x in range(0, 64, 16):
        poly(img, [(x + 1, 30), (x + 8, 0), (x + 15, 30)], (190, 192, 200), IRON_D, False, 0.1)
    save(img, "spikes", 1)

def lava_tile():
    w, h = 128, 64
    n = tnoise(w, h, 6, 3, 4, 33)
    arr = colorize(n ** 1.5, (150, 20, 5), (255, 200, 60))
    img = Image.fromarray(np.concatenate([arr, np.full((h, w, 1), 255)], 2).astype(np.uint8), "RGBA")
    save_raw(img, "tile_lava")

def water_tile():
    w, h = 128, 64
    n = tnoise(w, h, 6, 3, 4, 34)
    arr = colorize(n, (20, 50, 90), (70, 130, 170))
    img = Image.fromarray(np.concatenate([arr, np.full((h, w, 1), 230)], 2).astype(np.uint8), "RGBA")
    save_raw(img, "tile_water")

# ================================================================ UI

def parchment():
    W, H = 192, 192
    n = tnoise(W, H, 6, 6, 5, 41)
    arr = colorize(n, (24, 18, 18), (58, 44, 38))
    img = Image.fromarray(np.concatenate([arr, np.full((H, W, 1), 255)], 2).astype(np.uint8), "RGBA")
    a = np.array(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy)) / 30.0
    a[:, :, :3] *= np.clip(0.55 + edge[:, :, None] * 0.45, 0, 1)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=(10, 6, 6, 255), width=4)
    d.rectangle([8, 8, W - 9, H - 9], outline=(150, 110, 45, 255), width=2)
    for x, y in [(8, 8), (W - 9, 8), (8, H - 9), (W - 9, H - 9)]:
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=GOLD + (255,), outline=(90, 55, 25, 255), width=2)
    save_raw(img, "ui_parchment", False)

def wood_button(name, light, dark):
    W, H = 96, 48
    img = Image.new("RGBA", (W, H))
    n = tnoise(W, H, 2, 6, 4, 50)
    arr = colorize(n, dark, light)
    base = Image.fromarray(np.concatenate([arr, np.full((H, W, 1), 255)], 2).astype(np.uint8), "RGBA")
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], 10, fill=255)
    img.paste(base, (0, 0), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], 10, outline=(40, 25, 15, 255), width=3)
    d.rounded_rectangle([5, 5, W - 6, H - 6], 7, outline=GOLD_D + (255,), width=2)
    for x, y in [(10, 10), (W - 11, 10), (10, H - 11), (W - 11, H - 11)]:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=IRON + (255,))
    save_raw(img, name, False)

def crest():
    W, H = 220, 260
    img = canvas(W, H)
    # espadas cruzadas
    for s in (1, -1):
        cx = 110
        pts = [(cx - s * 100, 20), (cx - s * 92, 12), (cx + s * 90, 220), (cx + s * 84, 226)]
        poly(img, pts, (225, 228, 236), IRON, True, 0.05)
        line(img, [(cx + s * 60, 190), (cx + s * 100, 170)], GOLD_D, 8)
    poly(img, [(40, 40), (180, 40), (180, 150), (110, 240), (40, 150)], RED, RED_D, True, 0.2)
    poly(img, [(52, 52), (168, 52), (168, 146), (110, 224), (52, 146)], RED, (130, 25, 30), True, 0.2)
    line(img, [(40, 40), (180, 40), (180, 150), (110, 240), (40, 150), (40, 40)], GOLD, 6)
    # coroa
    poly(img, [(70, 130), (70, 90), (88, 110), (110, 80), (132, 110), (150, 90), (150, 130)], GOLD, GOLD_D)
    for x in (70, 110, 150):
        ellipse(img, x - 6, 78 + (0 if x == 110 else 8), x + 6, 90 + (0 if x == 110 else 8), (240, 240, 250), (170, 180, 200))
    rect(img, 68, 130, 152, 142, GOLD, GOLD_D)
    save(img, "crest", 3)

# ================================================================ BACKGROUNDS

def sky(name, top, bottom, sun=None, stars=False, clouds=0, cloud_col=(255, 255, 255), horizon=None):
    W, H = 1280, 720
    img = grad_layer((W, H), top, bottom)
    if horizon:
        ramp = (np.clip((np.arange(H) - H * 0.45) / (H * 0.55), 0, 1) ** 1.6 * 255).astype(np.uint8)
        m = Image.fromarray(np.repeat(ramp[:, None], W, 1), "L")
        img.paste(Image.new("RGBA", (W, H), horizon + (255,)), (0, 0), m)
    d = ImageDraw.Draw(img)
    r = random.Random(hash(name) & 0xffff)
    if stars:
        for i in range(260):
            x, y = r.uniform(0, W), r.uniform(0, H * 0.7)
            b = r.randint(140, 255); s = r.choice([0.6, 0.8, 1.2, 1.6])
            d.ellipse([x - s, y - s, x + s, y + s], fill=(b, b, min(255, b + 20), 255))
    if sun:
        sx, sy, sr, sc = sun
        glow = Image.new("RGBA", (W, H))
        gd = ImageDraw.Draw(glow)
        for k in range(12, 0, -1):
            rr = sr * (1 + k * 0.5)
            gd.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=sc + (int(10 + 4 * (12 - k)),))
        glow = glow.filter(ImageFilter.GaussianBlur(25))
        img.alpha_composite(glow)
        d = ImageDraw.Draw(img)
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=lerpc(sc, (255, 255, 255), 0.6) + (255,))
    if clouds:
        cl = Image.new("RGBA", (W, H))
        cd = ImageDraw.Draw(cl)
        for i in range(clouds):
            cx = r.uniform(0, W); cy = r.uniform(60, 330); s = r.uniform(40, 90)
            for k in range(7):
                ox = r.uniform(-s * 1.4, s * 1.4); oy = r.uniform(-s * 0.3, s * 0.2)
                rr = r.uniform(s * 0.4, s * 0.8)
                for xx in (cx + ox, cx + ox - W, cx + ox + W):
                    cd.ellipse([xx - rr, cy + oy - rr * 0.6, xx + rr, cy + oy + rr * 0.6], fill=cloud_col + (190,))
                    cd.ellipse([xx - rr * 0.8, cy + oy - rr * 0.1, xx + rr * 0.8, cy + oy + rr * 0.55], fill=lerpc(cloud_col, (255, 90, 50), 0.12) + (90,))
        cl = cl.filter(ImageFilter.GaussianBlur(9))
        img.alpha_composite(cl)
    img.convert("RGB").save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name)

def ridge(W, H, base_y, amp, freq, seed):
    r = np.random.default_rng(seed)
    xs = np.arange(W)
    y = np.full(W, float(base_y))
    for k in range(1, 6):
        ph = r.uniform(0, math.tau)
        y += amp / k * np.sin(xs / W * math.tau * freq * k + ph)
    return y

def hills_layer(name, col_top, col_bot, base_y, amp, freq, seed, castle=None, trees=0, houses=0, tree_col=None, haze=None):
    W, H = 1280, 720
    img = Image.new("RGBA", (W, H))
    y = ridge(W, H, base_y, amp, freq, seed)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(0, H)] + [(x, y[x]) for x in range(W)] + [(W, H)], fill=255)
    g = grad_layer((W, H), col_top, col_bot)
    n = tnoise(W, H, 16, 9, 4, seed)
    ga = np.array(g).astype(np.float32); ga[:, :, :3] *= (0.92 + 0.16 * n[:, :, None])
    g = Image.fromarray(np.clip(ga, 0, 255).astype(np.uint8))
    img.paste(g, (0, 0), m)
    d = ImageDraw.Draw(img)
    r = random.Random(seed)
    tc = tree_col or lerpc(col_top, (0, 0, 0), 0.25)
    if castle:
        cx, ccol, scale = castle
        gy = y[int(cx)] + 10
        def tw(x, w, h, roof=True):
            d.rectangle([x - w / 2, gy - h, x + w / 2, gy], fill=ccol)
            for k in range(int(w // 10)):
                if k % 2 == 0:
                    d.rectangle([x - w / 2 + k * 10, gy - h - 7, x - w / 2 + k * 10 + 6, gy - h], fill=ccol)
            if roof:
                d.polygon([(x - w / 2 - 4, gy - h), (x, gy - h - w * 1.3), (x + w / 2 + 4, gy - h)], fill=ccol)
                d.line([x, gy - h - w * 1.3, x, gy - h - w * 1.3 - 14], fill=ccol, width=2)
                d.polygon([(x, gy - h - w * 1.3 - 14), (x + 12, gy - h - w * 1.3 - 10), (x, gy - h - w * 1.3 - 6)], fill=ccol)
            for k in range(2):
                wy = gy - h * (0.4 + 0.3 * k)
                d.rectangle([x - 2, wy, x + 2, wy + 7], fill=(255, 210, 120, 220))
        s = scale
        d.rectangle([cx - 110 * s, gy - 70 * s, cx + 110 * s, gy], fill=ccol)
        for k in range(int(22 * s)):
            if k % 2 == 0:
                d.rectangle([cx - 110 * s + k * 10, gy - 70 * s - 7, cx - 110 * s + k * 10 + 6, gy - 70 * s], fill=ccol)
        tw(cx - 110 * s, 30 * s, 120 * s); tw(cx + 110 * s, 30 * s, 120 * s)
        tw(cx - 40 * s, 36 * s, 170 * s); tw(cx + 45 * s, 28 * s, 140 * s); tw(cx, 46 * s, 220 * s)
    for i in range(trees):
        x = r.uniform(0, W); s = r.uniform(10, 22)
        yy = y[int(x) % W] + 6
        for xx in (x, x - W, x + W):
            if r.random() < 0.5:
                d.polygon([(xx, yy - s * 3), (xx - s, yy), (xx + s, yy)], fill=tc)
            else:
                d.ellipse([xx - s, yy - s * 2, xx + s, yy], fill=tc)
                d.rectangle([xx - 2, yy - 4, xx + 2, yy + 4], fill=tc)
    for i in range(houses):
        x = r.uniform(30, W - 30); yy = y[int(x)] + 8
        hw = r.uniform(26, 40); hh = r.uniform(18, 28)
        c = lerpc(tc, (0, 0, 0), 0.1)
        d.rectangle([x - hw / 2, yy - hh, x + hw / 2, yy], fill=c)
        d.polygon([(x - hw / 2 - 5, yy - hh), (x, yy - hh - hw * 0.6), (x + hw / 2 + 5, yy - hh)], fill=lerpc(c, (0, 0, 0), 0.2))
        d.rectangle([x - 3, yy - hh * 0.7, x + 3, yy - hh * 0.4], fill=(255, 205, 110, 230))
    if haze:
        hz = grad_layer((W, H), haze + (0,), haze + (110,))
        hm = img.split()[3]
        hz2 = Image.new("RGBA", (W, H)); hz2.paste(hz, (0, 0), hm)
        img.alpha_composite(hz2)
    img.save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name)

def castle_wall_layer(name, col, col_d, lit_col, base_y=330, seed=3):
    W, H = 1280, 720
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    r = random.Random(seed)
    # muralha continua
    d.rectangle([0, base_y, W, H], fill=col)
    for k in range(0, W, 28):
        d.rectangle([k, base_y - 22, k + 17, base_y], fill=col)
    # torres a cada 320 px
    for tx in range(160, W, 427):
        tw, th = 120, 240
        d.rectangle([tx - tw / 2, base_y - th, tx + tw / 2, H], fill=col_d)
        for k in range(0, tw, 22):
            d.rectangle([tx - tw / 2 + k, base_y - th - 20, tx - tw / 2 + k + 13, base_y - th], fill=col_d)
        d.polygon([(tx - tw / 2 - 8, base_y - th - 20), (tx, base_y - th - 150), (tx + tw / 2 + 8, base_y - th - 20)],
                  fill=lerpc(col_d, (40, 20, 60), 0.3))
        d.line([tx, base_y - th - 150, tx, base_y - th - 185], fill=col_d, width=3)
        d.polygon([(tx, base_y - th - 185), (tx + 30, base_y - th - 175), (tx, base_y - th - 165)], fill=(150, 30, 40))
        for wy in (base_y - th + 50, base_y - th + 130):
            d.rectangle([tx - 7, wy, tx + 7, wy + 26], fill=lit_col)
            d.ellipse([tx - 7, wy - 7, tx + 7, wy + 7], fill=lit_col)
    # textura de pedra
    a = np.array(img).astype(np.float32)
    n = tnoise(W, H, 40, 22, 3, seed)
    a[:, :, :3] *= (0.85 + 0.3 * n[:, :, None])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for y in range(base_y + 10, H, 26):
        d.line([0, y, W, y], fill=lerpc(col, (0, 0, 0), 0.3) + (120,), width=1)
        for x in range((0 if (y // 26) % 2 else 22), W, 44):
            d.line([x, y, x, y + 26], fill=lerpc(col, (0, 0, 0), 0.3) + (120,), width=1)
    # estandartes nas muralhas
    for bx in range(373, W, 427):
        d.rectangle([bx - 20, base_y + 20, bx + 20, base_y + 130], fill=(140, 28, 36))
        d.polygon([(bx - 20, base_y + 130), (bx, base_y + 112), (bx + 20, base_y + 130)], fill=(0, 0, 0, 0))
        d.regular_polygon((bx, base_y + 60, 10), 5, fill=(220, 170, 60))
    img.save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name)

def dungeon_bg(name):
    W, H = 1280, 720
    img = tile_like_bricks(W, H, (20, 18, 26), (42, 38, 50), 80, 40, 77)
    d = ImageDraw.Draw(img)
    # arcos com janelas de luar
    for ax in range(160, W, 320):
        d.rectangle([ax - 60, 160, ax + 60, 460], fill=(14, 12, 20))
        d.ellipse([ax - 60, 100, ax + 60, 220], fill=(14, 12, 20))
        win = Image.new("RGBA", (W, H)); wd = ImageDraw.Draw(win)
        wd.rectangle([ax - 26, 190, ax + 26, 330], fill=(60, 80, 130, 255))
        wd.ellipse([ax - 26, 164, ax + 26, 216], fill=(60, 80, 130, 255))
        img.alpha_composite(win)
        d = ImageDraw.Draw(img)
        d.line([ax, 166, ax, 330], fill=(20, 18, 26), width=4)
        d.line([ax - 26, 250, ax + 26, 250], fill=(20, 18, 26), width=4)
        for k in range(9):
            a = math.pi + k * math.pi / 8
            x = ax + math.cos(a) * 68; y = 160 + math.sin(a) * 68
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(80, 74, 92), outline=(20, 18, 26))
    # raios de luar
    rays = Image.new("RGBA", (W, H)); rd = ImageDraw.Draw(rays)
    for ax in range(160, W, 320):
        rd.polygon([(ax - 26, 200), (ax + 26, 200), (ax + 140, 720), (ax + 20, 720)], fill=(110, 140, 210, 26))
    rays = rays.filter(ImageFilter.GaussianBlur(12))
    img.alpha_composite(rays)
    img.convert("RGB").save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name)

def tile_like_bricks(W, H, dark, light, bw, bh, seed):
    n = tnoise(W, H, 32, 18, 4, seed)
    arr = colorize(n, dark, light)
    img = Image.fromarray(np.concatenate([arr, np.full((H, W, 1), 255)], 2).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    r = random.Random(seed)
    for ry in range(H // bh + 1):
        off = (bw // 2) * (ry % 2)
        for bx in range(-1, W // bw + 1):
            x0 = bx * bw + off; y0 = ry * bh
            s = r.uniform(-18, 10)
            d.rectangle([x0 + 2, y0 + 2, x0 + bw - 2, y0 + bh - 2], fill=None, outline=(int(dark[0] * 0.6), int(dark[1] * 0.6), int(dark[2] * 0.6)), width=2)
            if s < -10:
                d.rectangle([x0 + 4, y0 + 4, x0 + bw - 4, y0 + bh - 4], fill=lerpc(dark, (0, 0, 0), 0.15) + (120,))
    return img

def dungeon_mid(name):
    W, H = 1280, 720
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for px in range(0, W, 427):
        x = px + 213
        d.rectangle([x - 40, 0, x + 40, H], fill=(18, 16, 24))
        d.rectangle([x - 52, 0, x + 52, 40], fill=(26, 23, 32))
        d.rectangle([x - 52, 560, x + 52, H], fill=(26, 23, 32))
        for k in (-20, 0, 20):
            d.line([x + k, 40, x + k, 560], fill=(22, 20, 28), width=3)
        # estandarte rasgado
        d.rectangle([x + 70, 80, x + 120, 300], fill=(62, 10, 16))
        d.polygon([(x + 70, 300), (x + 85, 280), (x + 95, 310), (x + 108, 285), (x + 120, 300)], fill=(0, 0, 0, 0))
        d.regular_polygon((x + 95, 150, 13), 5, fill=(120, 90, 36))
    a = np.array(img).astype(np.float32)
    n = tnoise(W, H, 40, 22, 3, 5)
    a[:, :, :3] *= (0.85 + 0.3 * n[:, :, None])
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name)

def village_mid(name):
    """Silhuetas de casas e arvores em tom azulado (plano medio)."""
    W, H = 1280, 720
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    r = random.Random(17)
    base = 520
    col = (34, 34, 42); col_d = (24, 24, 32)
    x = 0
    while x < W:
        kind = r.random()
        if kind < 0.45:
            hw = r.uniform(90, 140); hh = r.uniform(70, 110)
            d.rectangle([x, base - hh, x + hw, H], fill=col)
            d.polygon([(x - 10, base - hh), (x + hw / 2, base - hh - hw * 0.55), (x + hw + 10, base - hh)], fill=col_d)
            for k in range(r.randint(1, 3)):
                wx = x + 15 + k * 32
                if wx + 14 < x + hw:
                    d.rectangle([wx, base - hh + 20, wx + 14, base - hh + 40], fill=(255, 140, 60, 255))
            d.rectangle([x + hw * 0.7, base - hh - hw * 0.45, x + hw * 0.7 + 12, base - hh - 10], fill=col_d)
            x += hw + r.uniform(10, 40)
        elif kind < 0.8:
            s = r.uniform(40, 70)
            d.ellipse([x, base - s * 3.2, x + s * 2, base - s * 1.2], fill=(26, 32, 30))
            d.rectangle([x + s - 5, base - s * 1.4, x + s + 5, H], fill=(22, 24, 24))
            x += s * 2 + r.uniform(0, 30)
        else:
            # torre de igreja
            d.rectangle([x, base - 190, x + 60, H], fill=col)
            d.polygon([(x - 6, base - 190), (x + 30, base - 290), (x + 66, base - 190)], fill=col_d)
            d.line([x + 30, base - 290, x + 30, base - 320], fill=col_d, width=4)
            d.line([x + 18, base - 308, x + 42, base - 308], fill=col_d, width=4)
            d.ellipse([x + 20, base - 160, x + 40, base - 140], fill=(255, 140, 60))
            x += 90
    d.rectangle([0, base, W, H], fill=(20, 22, 22))
    glow = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(glow)
    for gx in (200, 700, 1100):
        gd.ellipse([gx - 160, base - 260, gx + 160, base + 40], fill=(255, 90, 30, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    out = Image.new("RGBA", (W, H)); out.alpha_composite(glow); out.alpha_composite(img)
    img = out
    img.save(os.path.join(OUT, name + ".png"), optimize=True)
    print("ok", name)

def title_bg():
    W, H = 1280, 720
    img = grad_layer((W, H), (8, 6, 12), (120, 30, 22))
    glow = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(glow)
    gd.ellipse([440, 300, 840, 700], fill=(255, 90, 40, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(60)); img.alpha_composite(glow)
    img.convert("RGB").save(os.path.join(OUT, "bg_title_sky.png"))
    print("ok bg_title_sky")


if __name__ == "__main__":
    # tiles
    tile_fill("tile_dirt", 128, 128, DIRT_D, DIRT, stones=26, seed=2)
    tile_fill("tile_castle_wall", 128, 128, (90, 86, 80), (150, 145, 135), seed=4, bricks=(64, 32), mortar=(60, 56, 52, 255))
    tile_fill("tile_dungeon_wall", 128, 128, (34, 30, 40), (78, 72, 88), seed=6, bricks=(64, 32), mortar=(20, 18, 24, 255))
    grass_top(); cobble_top(); dungeon_top(); plank_tile(); stone_ledge_tile(); lava_tile(); water_tile()
    # props
    house_a(); house_b(); tree(); pine(); bush(); fence(); haystack(); barrel(); crate(); well(); cart()
    market_stall(); signpost(); torch(); banner("banner_red", RED, RED_D, "lion"); banner("banner_blue", BLUE, BLUE_D, "cross")
    flag("flag_on", RED, RED_D, True); flag("flag_off", (120, 115, 105), (80, 76, 70), False)
    tower(); castle_gate(); pillar(); chain(); throne(); skulls(); weapon_rack(); knight_statue(); windmill()
    coin(); potion(); heart(); bola(); dart(); fireball(); magic_orb(); spikes()
    parchment(); wood_button("ui_button", (70, 48, 34), (30, 20, 16)); wood_button("ui_button_hover", (118, 72, 40), (50, 30, 20)); crest()
    # fundos (tema sombrio)
    sky("bg_sky_day", (8, 6, 16), (60, 22, 26), sun=(1000, 150, 46, (210, 70, 50)), stars=True, clouds=16,
        cloud_col=(26, 18, 24), horizon=(150, 45, 22))
    sky("bg_sky_sunset", (6, 5, 10), (54, 14, 20), sun=None, clouds=22, cloud_col=(20, 14, 20), horizon=(110, 20, 24))
    sky("bg_sky_night", (3, 4, 10), (18, 16, 32), sun=(1050, 120, 40, (170, 185, 220)), stars=True)
    hills_layer("bg_day_far", (30, 24, 38), (18, 15, 26), 380, 40, 2, 10, castle=(830, (14, 12, 22), 1.2), trees=50, tree_col=(22, 18, 30))
    hills_layer("bg_day_near", (24, 28, 28), (14, 17, 18), 460, 30, 3, 11, trees=70, houses=6, tree_col=(18, 22, 22))
    village_mid("bg_day_mid")
    hills_layer("bg_sunset_far", (34, 20, 30), (20, 12, 20), 400, 50, 2, 12, trees=40, tree_col=(24, 14, 22), haze=(110, 24, 26))
    castle_wall_layer("bg_sunset_wall", (52, 44, 52), (38, 32, 42), (255, 140, 60), 430, 3)
    dungeon_bg("bg_dungeon_back"); dungeon_mid("bg_dungeon_mid")
    hills_layer("bg_night_far", (18, 18, 34), (10, 10, 22), 420, 40, 2, 14, castle=(640, (10, 10, 20), 1.6), trees=40, tree_col=(14, 14, 28))
    title_bg()


def fog():
    W, H = 1280, 320
    n = tnoise(W, H, 10, 3, 5, 99)
    ramp = np.sin(np.linspace(0, np.pi, H))[:, None] ** 1.5
    a = (np.clip((n - 0.35) * 2.2, 0, 1) * ramp * 150).astype(np.uint8)
    img = np.zeros((H, W, 4), np.uint8); img[:, :, :3] = (170, 160, 175); img[:, :, 3] = a
    Image.fromarray(img).save(os.path.join(OUT, "fog.png"))
    print("ok fog")


if __name__ == "__main__":
    fog()
