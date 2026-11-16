"""Corta e normaliza as spritesheets originais para o jogo.
Uso: python tools/process_sprites.py   (rodar na raiz do projeto)
Gera assets/sprites/<personagem>/<anim>.png + assets/sprites/sprites.json
"""
import os, json, glob
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "sprites")

# personagem -> (pasta original, escala, {anim: (arquivo, cell_w, cell_h)})
CHARS = {
    "cavaleiro": ("cavaleiro", 0.55, {
        "idle": ("idle.png", 300, 400), "walk": ("walk.png", 300, 400)}),
    "barbaro": ("barbaro", 0.55, {
        "idle": ("idle_1.png", 711, 400), "walk": ("walk_1.png", 711, 400),
        "attack": ("attack_7.png", 711, 400), "die": ("die_1.png", 711, 400)}),
    "sabio": ("sabio marcial", 0.55, {
        "idle": ("idle (1).png", 400, 400), "attack": ("attack_1.png", 400, 400)}),
    "goblin_guerreiro": ("goblin guerreiro", 0.55, {
        "walk": ("walk_1 (1).png", 400, 400), "attack": ("attack_1 (3).png", 400, 400),
        "jump": ("jump_small.png", 400, 400)}),
    "goblin_lanca": ("goblin de lanca", 0.55, {
        "walk": ("walk_1 (3).png", 400, 400), "defense": ("defense_1.png", 400, 400),
        "hurt": ("hurt_front.png", 400, 400)}),
    "goblin_boleadeira": ("goblin boleadeira", 0.55, {
        "idle": ("idle_1 (1).png", 400, 400), "attack": ("attack_1 (2).png", 400, 400)}),
    "goblin_mago": ("goblin mago", 0.55, {
        "idle": ("idle_1 (2).png", 400, 400), "walk": ("walk_1 (2).png", 400, 400),
        "attack": ("attack_2.png", 400, 400), "hurt": ("hurt_top.png", 400, 400),
        "die": ("die_1 (1).png", 400, 400)}),
    "goblin_general": ("goblin general", 0.65, {
        "idle": ("idle_4.png", 400, 400), "attack": ("attack_1 (1).png", 400, 400),
        "hurt": ("hurt_1.png", 400, 400)}),
    "minotauro": ("minotauro", 0.75, {
        "walk": ("walk (1).png", 300, 300), "roll": ("roll.png", 400, 300),
        "attack": ("other_1.png", 400, 300)}),
    "cerberus": ("cerberus", 0.7, {
        "idle": ("idle.png", 800, 800), "howl": ("howl.png", 800, 800)}),
}

def slice_frames(img, cw, ch):
    a = np.array(img)
    h, w = a.shape[:2]
    cols, rows = w // cw, h // ch
    frames = []
    for r in range(rows):
        for c in range(cols):
            f = a[r*ch:(r+1)*ch, c*cw:(c+1)*cw]
            if (f[:, :, 3] > 10).sum() > 50:
                frames.append(f)
    return frames

def anchor(frames):
    xs, ys = [], []
    for f in frames:
        al = f[:, :, 3].astype(np.float64)
        cols = al.sum(0)
        xs.append((cols * np.arange(len(cols))).sum() / cols.sum())
        rows = np.where((f[:, :, 3] > 10).any(1))[0]
        ys.append(rows.max())
    return float(np.median(xs)), float(np.percentile(ys, 90))

def main():
    meta = {}
    for name, (folder, scale, anims) in CHARS.items():
        data = {}
        ext = [0, 0, 0, 0]  # left, right, up, down relativos a ancora
        for anim, (fn, cw, ch) in anims.items():
            img = Image.open(os.path.join(ROOT, folder, fn)).convert("RGBA")
            frames = slice_frames(img, cw, ch)
            ax, ay = anchor(frames)
            for f in frames:
                m = f[:, :, 3] > 10
                ys = np.where(m.any(1))[0]; xs = np.where(m.any(0))[0]
                ext[0] = max(ext[0], ax - xs.min()); ext[1] = max(ext[1], xs.max() + 1 - ax)
                ext[2] = max(ext[2], ay - ys.min()); ext[3] = max(ext[3], ys.max() + 1 - ay)
            data[anim] = (frames, ax, ay)
        L, R, U, D = [int(np.ceil(e)) + 2 for e in ext]
        W, H = L + R, U + D
        sw, sh = int(round(W * scale)), int(round(H * scale))
        os.makedirs(os.path.join(OUT, name), exist_ok=True)
        cm = {"cell": [sw, sh], "anchor": [round(L * scale, 1), round(U * scale, 1)], "anims": {}}
        for anim, (frames, ax, ay) in data.items():
            n = len(frames)
            cols = min(n, max(1, 8192 // sw))
            rows = (n + cols - 1) // cols
            sheet = Image.new("RGBA", (cols * sw, rows * sh), (0, 0, 0, 0))
            for i, f in enumerate(frames):
                canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                canvas.paste(Image.fromarray(f), (int(round(L - ax)), int(round(U - ay))))
                small = canvas.resize((sw, sh), Image.LANCZOS)
                sheet.paste(small, ((i % cols) * sw, (i // cols) * sh))
            sheet.save(os.path.join(OUT, name, anim + ".png"), optimize=True)
            cm["anims"][anim] = {"frames": n, "cols": cols}
            print(name, anim, n, "frames", sheet.size)
        meta[name] = cm
    with open(os.path.join(OUT, "sprites.json"), "w") as fp:
        json.dump(meta, fp, indent=1)

if __name__ == "__main__":
    main()
