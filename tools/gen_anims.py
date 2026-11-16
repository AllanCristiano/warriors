"""Gera as animacoes que faltam nas spritesheets originais (ataque do cavaleiro,
andar do sabio, pulo, dano e morte de todos) deformando/compondo frames existentes.
Uso (depois de process_sprites.py): python tools/gen_anims.py
Cria assets/sprites/<personagem>/gen_<anim>.png e atualiza sprites.json/sprite_meta.gd
"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPR = os.path.join(ROOT, "assets", "sprites")
META_PATH = os.path.join(SPR, "sprites.json")
meta = json.load(open(META_PATH))

# remove geracoes anteriores
for c in meta.values():
    for k in [k for k in c["anims"] if k.startswith("gen_")]:
        del c["anims"][k]

S = 900          # lado do canvas de trabalho
PX, PY = S // 2, int(S * 0.7)  # ponto do pe (pivo) no canvas


def frames_of(char, sheet):
    c = meta[char]; cw, ch = c["cell"]; ax, ay = c["anchor"]
    a = c["anims"][sheet]
    img = Image.open(os.path.join(SPR, char, sheet + ".png")).convert("RGBA")
    out = []
    for i in range(a["frames"]):
        col, row = i % a["cols"], i // a["cols"]
        f = img.crop((col * cw, row * ch, (col + 1) * cw, (row + 1) * ch))
        cv = Image.new("RGBA", (S, S))
        cv.paste(f, (int(round(PX - ax)), int(round(PY - ay))))
        out.append(cv)
    return out


def body_height(img):
    a = np.array(img)[:, :, 3]
    ys = np.where(a.max(1) > 20)[0]
    return PY - ys.min() if len(ys) else 100


def affine(img, A, t=(0, 0), pivot=(PX, PY)):
    """Aplica x' = A (x - p) + p + t. PIL quer o inverso (saida -> entrada)."""
    A = np.array(A, float)
    inv = np.linalg.inv(A)
    p = np.array(pivot, float); t = np.array(t, float)
    # x = inv (x' - p - t) + p
    c = p - inv @ (p + t)
    data = (inv[0, 0], inv[0, 1], c[0], inv[1, 0], inv[1, 1], c[1])
    return img.transform(img.size, Image.AFFINE, data, resample=Image.BICUBIC)


def xf(img, shear=0.0, sx=1.0, sy=1.0, rot=0.0, dx=0, dy=0, pivot=(PX, PY)):
    """shear>0 inclina o topo para frente; rot em graus (>0 cai para tras)."""
    th = math.radians(rot)
    R = np.array([[math.cos(th), math.sin(th)], [-math.sin(th), math.cos(th)]])
    Sh = np.array([[1, -shear], [0, 1]])
    Sc = np.array([[sx, 0], [0, sy]])
    return affine(img, R @ Sh @ Sc, (dx, dy), pivot)


def tint(img, color, amt):
    a = np.array(img).astype(np.float32)
    a[:, :, :3] = a[:, :, :3] * (1 - amt) + np.array(color, np.float32) * amt
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def darken(img, amt):
    a = np.array(img).astype(np.float32)
    a[:, :, :3] *= (1 - amt)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def fade(img, alpha):
    a = np.array(img).astype(np.float32)
    a[:, :, 3] *= alpha
    return Image.fromarray(a.astype(np.uint8))


def sway_lower(img, amp, waist_frac=0.5):
    """Balanca a metade de baixo (manto/pernas) horizontalmente."""
    a = np.array(img).astype(np.float32)
    h = body_height(img)
    waist = PY - h * waist_frac
    out = a.copy()
    for y in range(int(waist), min(S, PY + 4)):
        t = (y - waist) / max(1, PY - waist)
        s = amp * t
        i = int(math.floor(s)); f = s - i
        r = np.roll(a[y], i, axis=0) * (1 - f) + np.roll(a[y], i + 1, axis=0) * f
        out[y] = r
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def trail(img, dist, n=2, alpha=0.35):
    base = Image.new("RGBA", img.size)
    for k in range(n, 0, -1):
        ghost = fade(tint(img, (150, 180, 230), 0.5), alpha / k)
        base.alpha_composite(xf(ghost, dx=-dist * k))
    base.alpha_composite(img)
    return base


def slash(img, start, end, center, radius, alpha=1.0, color=(220, 235, 255)):
    """Desenha um arco de corte (sentido horario de start a end, graus)."""
    up = 2
    lay = Image.new("RGBA", (S * up, S * up))
    d = ImageDraw.Draw(lay)
    cx, cy = center
    for w, a in [(26, 60), (16, 120), (8, 230)]:
        r = radius * up
        d.arc([(cx * up - r), (cy * up - r), (cx * up + r), (cy * up + r)], start, end,
              fill=color + (int(a * alpha),), width=w)
    lay = lay.filter(ImageFilter.GaussianBlur(3)).resize((S, S), Image.LANCZOS)
    out = img.copy()
    out.alpha_composite(lay)
    return out


def ease(t):
    return t * t


# ------------------------------------------------------------------ geradores

def gen_hurt(base):
    return [xf(tint(base, (255, 60, 50), 0.28), shear=-0.12, dx=-4),
            xf(tint(base, (255, 80, 70), 0.2), shear=-0.16, dx=-6),
            xf(base, shear=-0.09, dx=-4),
            xf(base, shear=-0.03, dx=-1)]


def gen_die(base, frames=16):
    out = [xf(tint(base, (255, 60, 50), 0.25), shear=-0.12, dx=-4),
           xf(tint(base, (255, 80, 60), 0.2), shear=-0.2, dx=-8),
           xf(base, shear=-0.22, sy=0.95, dx=-10),
           xf(base, shear=-0.18, sy=0.9, dx=-12)]
    n_fall = 7
    for i in range(n_fall):
        t = ease((i + 1) / n_fall)
        out.append(xf(base, shear=-0.12 * (1 - t), sy=0.9 + 0.1 * t, rot=88 * t, dx=-12 - 10 * t))
    for r in (82, 88, 90):
        out.append(xf(base, sy=1.0, rot=r, dx=-22))
    while len(out) < frames:
        k = (len(out) - 13) / 4
        out.append(darken(xf(base, rot=90, dx=-22), 0.15 + 0.2 * k))
    return out


def gen_collapse(base, frames=14):
    """Morte de quadrupede: dobra as patas e deita."""
    out = [xf(tint(base, (255, 60, 50), 0.25), shear=-0.06),
           xf(tint(base, (255, 90, 70), 0.2), shear=-0.1)]
    for i in range(frames - 4):
        t = ease((i + 1) / (frames - 4))
        out.append(xf(base, sx=1 + 0.12 * t, sy=1 - 0.45 * t, rot=-6 * t, shear=0.04 * t))
    for k in range(2):
        out.append(darken(xf(base, sx=1.12, sy=0.55, rot=-6, shear=0.04), 0.2 + 0.15 * k))
    return out


def gen_idle_breath(base, n=12):
    out = []
    for i in range(n):
        s = math.sin(i / n * math.tau)
        out.append(xf(base, sx=1 - 0.008 * s, sy=1 + 0.018 * s, shear=0.01 * s))
    return out


def gen_jump(base):
    return [xf(base, sx=1.08, sy=0.9), xf(base, sx=0.94, sy=1.08, shear=0.03),
            xf(base, sx=0.97, sy=1.04, shear=0.04)]


def gen_fall(base):
    return [xf(base, sx=1.0, sy=1.02, shear=-0.02), xf(base, sx=1.02, sy=1.0, shear=-0.04)]


def gen_glide_walk(bases, n=16, bob=5, lean=0.05, amp=7, waist=0.5):
    out = []
    for i in range(n):
        ph = i / n * math.tau
        b = bases[i % len(bases)]
        f = sway_lower(b, amp * math.sin(ph), waist)
        out.append(xf(f, shear=lean, dy=-abs(math.sin(ph)) * bob))
    return out


def gen_knight_attack(base):
    h = body_height(base)
    c = (PX + 10, PY - h * 0.55)
    r = h * 0.62
    seq = [
        (xf(base, shear=-0.07, sy=1.02), None),
        (xf(base, shear=-0.14, sy=1.03, dx=-4), None),
        (xf(base, shear=0.10, sy=0.97, dx=10), (-130, -30, 1.0)),
        (xf(base, shear=0.20, sy=0.95, dx=18), (-130, 50, 1.0)),
        (xf(base, shear=0.17, sy=0.95, dx=18), (-40, 55, 0.6)),
        (xf(base, shear=0.10, sy=0.97, dx=12), (10, 55, 0.25)),
        (xf(base, shear=0.04, dx=5), None),
        (xf(base, shear=0.0), None),
    ]
    out = []
    for img, arc in seq:
        if arc:
            img = slash(img, arc[0], arc[1], (c[0] + 10, c[1]), r, arc[2])
        out.append(img)
    return out


def gen_knight_attack2(base):
    h = body_height(base)
    c = (PX + 20, PY - h * 0.5)
    r = h * 0.6
    seq = [
        (xf(base, sy=0.95, shear=0.05), None),
        (xf(base, sy=0.9, shear=0.1, dx=4), None),
        (xf(base, sy=1.03, shear=-0.02, dx=12), (5, 60, 1.0)),
        (xf(base, sy=1.05, shear=-0.08, dx=16), (-90, 60, 1.0)),
        (xf(base, sy=1.03, shear=-0.06, dx=16), (-90, 0, 0.6)),
        (xf(base, sy=1.0, shear=-0.03, dx=10), (-90, -40, 0.25)),
        (xf(base, shear=0.0, dx=4), None),
        (xf(base), None),
    ]
    out = []
    for img, arc in seq:
        if arc:
            img = slash(img, arc[0], arc[1], c, r, arc[2], (255, 225, 190))
        out.append(img)
    return out


def gen_dash(walk):
    out = []
    for i in range(6):
        b = walk[(i * 3) % len(walk)]
        out.append(trail(xf(b, shear=0.24, sy=0.96), 22, 3, 0.45))
    return out


def gen_leap(howl):
    b = howl[10]
    return [xf(b, sx=1.06, sy=0.88), xf(b, sx=1.1, sy=0.96, rot=-12),
            xf(b, sx=1.06, sy=1.0, rot=-6), xf(b, sx=1.02, sy=1.0, rot=8)]


def gen_march(bases, n=16):
    out = []
    for i in range(n):
        ph = i / n * math.tau
        b = bases[i % len(bases)]
        f = sway_lower(b, 6 * math.sin(ph), 0.45)
        out.append(xf(f, shear=0.03 * math.sin(ph) + 0.03, dy=-abs(math.sin(ph)) * 5))
    return out


# ------------------------------------------------------------------ saida

def save(char, name, frames):
    alpha = np.zeros((S, S), np.uint8)
    for f in frames:
        alpha = np.maximum(alpha, np.array(f)[:, :, 3])
    ys = np.where(alpha.max(1) > 8)[0]; xs = np.where(alpha.max(0) > 8)[0]
    x0, x1 = max(0, xs.min() - 2), min(S, xs.max() + 3)
    y0, y1 = max(0, ys.min() - 2), min(S, max(ys.max() + 3, PY + 2))
    cw, ch = int(x1 - x0), int(y1 - y0)
    n = len(frames)
    cols = min(n, max(1, 8192 // cw))
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cw, rows * ch))
    for i, f in enumerate(frames):
        sheet.paste(f.crop((x0, y0, x1, y1)), ((i % cols) * cw, (i // cols) * ch))
    key = "gen_" + name
    sheet.save(os.path.join(SPR, char, key + ".png"), optimize=True)
    meta[char]["anims"][key] = {"frames": n, "cols": cols, "cell": [int(cw), int(ch)], "anchor": [int(PX - x0), int(PY - y0)]}
    print(char, key, n, "frames", sheet.size)


def main():
    # Cavaleiro: ataque x2, investida, pulo, queda, dano, morte
    idle = frames_of("cavaleiro", "idle"); walk = frames_of("cavaleiro", "walk")
    save("cavaleiro", "attack", gen_knight_attack(idle[0]))
    save("cavaleiro", "attack2", gen_knight_attack2(idle[0]))
    save("cavaleiro", "dash", gen_dash(walk))
    save("cavaleiro", "jump", gen_jump(walk[3]))
    save("cavaleiro", "fall", gen_fall(walk[3]))
    save("cavaleiro", "hurt", gen_hurt(idle[0]))
    save("cavaleiro", "die", gen_die(idle[0]))

    # Barbaro: pulo, queda, dano
    bi = frames_of("barbaro", "idle"); bw = frames_of("barbaro", "walk")
    save("barbaro", "jump", gen_jump(bw[10]))
    save("barbaro", "fall", gen_fall(bw[10]))
    save("barbaro", "hurt", gen_hurt(bi[0]))

    # Sabio: andar, pulo, queda, dano, morte
    si = frames_of("sabio", "idle")
    save("sabio", "walk", gen_glide_walk(si))
    save("sabio", "jump", [sway_lower(f, -6) for f in gen_jump(si[0])])
    save("sabio", "fall", [sway_lower(f, 5) for f in gen_fall(si[0])])
    save("sabio", "hurt", gen_hurt(si[0]))
    save("sabio", "die", gen_die(si[0]))

    # Goblins
    gw = frames_of("goblin_guerreiro", "walk")
    save("goblin_guerreiro", "idle", gen_idle_breath(gw[0]))
    save("goblin_guerreiro", "hurt", gen_hurt(gw[0]))
    save("goblin_guerreiro", "die", gen_die(gw[0], 14))
    lw = frames_of("goblin_lanca", "walk")
    save("goblin_lanca", "idle", gen_idle_breath(lw[0]))
    save("goblin_lanca", "die", gen_die(lw[0], 14))
    bo = frames_of("goblin_boleadeira", "idle")
    save("goblin_boleadeira", "hurt", gen_hurt(bo[0]))
    save("goblin_boleadeira", "die", gen_die(bo[0], 14))
    ge = frames_of("goblin_general", "idle")
    save("goblin_general", "walk", gen_march(ge))
    save("goblin_general", "die", gen_die(ge[0], 16))

    # Minotauro
    mw = frames_of("minotauro", "walk")
    save("minotauro", "idle", gen_idle_breath(mw[0], 14))
    save("minotauro", "hurt", gen_hurt(mw[0]))
    save("minotauro", "die", gen_die(mw[0], 16))

    # Cerbero
    ci = frames_of("cerberus", "idle"); ch = frames_of("cerberus", "howl")
    save("cerberus", "leap", gen_leap(ch))
    save("cerberus", "hurt", [xf(tint(ci[0], (255, 60, 50), 0.25), shear=-0.05), xf(ci[0], shear=-0.07, dx=-6),
                              xf(ci[0], shear=-0.04, dx=-3), xf(ci[0])])
    save("cerberus", "die", gen_collapse(ci[0], 16))

    json.dump(meta, open(META_PATH, "w"), indent=1)
    import process_sprites
    process_sprites.write_gd(meta)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
