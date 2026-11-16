"""Sintetiza efeitos sonoros e musicas de tema medieval.
Uso: python tools/gen_audio.py  -> assets/audio/*.wav
"""
import os, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
os.makedirs(OUT, exist_ok=True)
SR = 22050
rng = np.random.default_rng(3)

def write(name, x, vol=0.8):
    x = np.asarray(x, np.float64)
    peak = np.max(np.abs(x)) or 1
    x = x / peak * vol
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())
    print("ok", name, round(len(x) / SR, 2), "s")

def t(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, decay=6.0):
    tt = np.arange(n) / SR
    e = np.exp(-tt * decay)
    na = max(1, int(a * SR)); e[:na] *= np.linspace(0, 1, na)
    return e
def noise(d): return rng.uniform(-1, 1, int(SR * d))
def lowpass(x, a):
    y = np.zeros_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y
def sweep(f0, f1, d, wave_="sine"):
    tt = t(d); f = np.linspace(f0, f1, len(tt)); ph = np.cumsum(f) / SR * 2 * np.pi
    return np.sin(ph) if wave_ == "sine" else np.sign(np.sin(ph))

def pluck(freq, d, decay=0.996, bright=0.5):
    """Karplus-Strong: som de alaude."""
    n = int(SR * d); p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p) * bright + (1 - bright) * np.sin(np.linspace(0, 2 * np.pi, p))
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = decay * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out

def note_freq(n):  # n = semitons a partir de A4
    return 440.0 * 2 ** (n / 12)

# ------------------------------------------------------------ SFX
def sfx():
    # golpe de espada (whoosh)
    n = noise(0.25); write("swing", lowpass(n, 0.25) * env(len(n), 0.03, 14) , 0.6)
    # impacto
    n = noise(0.18) * env(int(SR * 0.18), 0.001, 30) + sweep(180, 60, 0.18) * env(int(SR * 0.18), 0.001, 18)
    write("hit", n, 0.8)
    # metal (espada contra escudo)
    tt = t(0.4); m = sum(np.sin(2 * np.pi * f * tt) for f in (1200, 1830, 2650, 3400)) * env(len(tt), 0.001, 9)
    write("clang", m + noise(0.4) * env(len(tt), 0.001, 40) * 0.6, 0.6)
    # dano no heroi
    write("hurt", sweep(420, 160, 0.25, "square") * env(int(SR * 0.25), 0.005, 8) * 0.5 + lowpass(noise(0.25), 0.3) * env(int(SR * 0.25), 0.001, 12), 0.6)
    # pulo
    write("jump", sweep(220, 520, 0.16) * env(int(SR * 0.16), 0.005, 10), 0.4)
    # moeda
    tt = t(0.3); c = np.sin(2 * np.pi * 988 * tt) * (tt < 0.07) + np.sin(2 * np.pi * 1319 * tt) * (tt >= 0.07)
    write("coin", c * env(len(tt), 0.002, 9), 0.45)
    # pocao
    tt = t(0.5); write("potion", np.sin(2 * np.pi * (500 + 300 * np.sin(tt * 30)) * tt) * env(len(tt), 0.01, 5), 0.4)
    # morte inimigo
    write("enemy_die", sweep(300, 60, 0.45, "square") * env(int(SR * 0.45), 0.005, 5) * 0.4 + lowpass(noise(0.45), 0.1) * env(int(SR * 0.45), 0.001, 6), 0.6)
    # bola de fogo / magia
    n = lowpass(noise(0.6), 0.15) * env(int(SR * 0.6), 0.05, 4); write("fire", n, 0.6)
    tt = t(0.4); write("magic", np.sin(2 * np.pi * (600 + 500 * tt) * tt) * np.sin(2 * np.pi * 9 * tt) * env(len(tt), 0.01, 6), 0.4)
    # arremesso
    write("throw", lowpass(noise(0.2), 0.4) * env(int(SR * 0.2), 0.05, 12), 0.4)
    # pancada no chao
    tt = t(0.7); write("slam", (np.sin(2 * np.pi * 55 * tt) + lowpass(noise(0.7), 0.06) * 2) * env(len(tt), 0.001, 5), 0.9)
    # caixa quebrando
    write("break", lowpass(noise(0.3), 0.5) * env(int(SR * 0.3), 0.001, 16) + sweep(300, 100, 0.3) * env(int(SR * 0.3), 0.001, 20) * 0.5, 0.6)
    # bandeira / checkpoint: fanfarra curta
    seq = [(0, 0.12), (4, 0.12), (7, 0.12), (12, 0.35)]
    write("checkpoint", np.concatenate([pluck(note_freq(n + 3), d, 0.997) for n, d in seq]), 0.6)
    # selecionar menu
    write("select", pluck(note_freq(10), 0.18, 0.995), 0.5)
    write("confirm", np.concatenate([pluck(note_freq(3), 0.1), pluck(note_freq(10), 0.3)]), 0.6)
    # rugido de chefe
    tt = t(1.2)
    roar = lowpass(noise(1.2), 0.08) * (1 + np.sin(2 * np.pi * 30 * tt)) * env(len(tt), 0.1, 2) + sweep(110, 70, 1.2, "square") * 0.3 * env(len(tt), 0.1, 2)
    write("roar", roar, 0.9)
    # trombetas de vitoria
    def horn(f, d):
        tt = t(d); s = sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 7))
        e = np.minimum(1, tt * 30) * np.exp(-tt * 1.2); return s * e
    seq = [(-2, 0.18), (-2, 0.18), (-2, 0.18), (5, 0.6), (2, 0.3), (5, 0.9)]
    write("victory", np.concatenate([horn(note_freq(n), d) for n, d in seq]), 0.6)
    seq = [(3, 0.4), (2, 0.4), (1, 0.4), (0, 1.2)]
    write("gameover", np.concatenate([horn(note_freq(n - 12), d) for n, d in seq]), 0.6)

# ------------------------------------------------------------ MUSICA
def render_track(melody, bass, bpm, drum=None, lute_decay=0.996, drone=None, length_beats=None):
    beat = 60.0 / bpm
    total = length_beats or sum(d for _, d in melody)
    out = np.zeros(int(SR * beat * total) + SR)
    pos = 0.0
    for n, d in melody:
        if n is not None:
            s = pluck(note_freq(n), beat * d + 0.4, lute_decay, 0.6) * 0.5
            i = int(pos * beat * SR); out[i:i + len(s)] += s[:len(out) - i]
        pos += d
    pos = 0.0
    for n, d in bass:
        if n is not None:
            s = pluck(note_freq(n - 24), beat * d + 0.3, 0.998, 0.3) * 0.6
            i = int(pos * beat * SR); out[i:i + len(s)] += s[:len(out) - i]
        pos += d
    if drone is not None:
        tt = np.arange(len(out)) / SR
        f = note_freq(drone - 24)
        out += (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.5 * tt)) * 0.06
    if drum:
        for k in range(int(total)):
            for off, kind in drum:
                i = int((k + off) * beat * SR)
                if kind == "k":
                    s = np.sin(2 * np.pi * np.linspace(90, 45, int(0.25 * SR)).cumsum() / SR) * env(int(0.25 * SR), 0.001, 12)
                else:
                    s = lowpass(noise(0.12), 0.5) * env(int(0.12 * SR), 0.001, 30) * 0.5
                out[i:i + len(s)] += s[:max(0, len(out) - i)] * 0.6
    n = int(SR * beat * total)
    loop = out[:n].copy(); tail = out[n:]
    loop[:len(tail)] += tail  # costura o loop
    return loop

def music():
    # Dorico em D (D=-7): escala D E F G A B C
    D, E, F, G, A, B, C = -7, -5, -4, -2, 0, 2, 3
    D2, E2, F2 = 5, 7, 8
    mel = [(D, 1), (F, 0.5), (G, 0.5), (A, 1), (A, 0.5), (B, 0.5), (C, 1), (B, 0.5), (A, 0.5), (G, 2),
           (A, 1), (G, 0.5), (F, 0.5), (E, 1), (F, 0.5), (G, 0.5), (A, 1.5), (G, 0.5), (F, 1), (E, 1),
           (D, 1), (F, 0.5), (G, 0.5), (A, 1), (D2, 1), (C, 0.5), (B, 0.5), (A, 1), (G, 1), (A, 1),
           (F, 1), (G, 0.5), (F, 0.5), (E, 1), (C - 12, 1), (D, 3), (None, 1)]
    bass = [(D, 2), (A - 12, 2), (C - 12, 2), (G - 12, 2), (F - 12, 2), (C - 12, 2), (D, 2), (A - 12, 2)] * 2
    write("music_village", render_track(mel * 2, bass, 112, drum=[(0, "k"), (0.5, "s"), (1.5, "s")], drone=D), 0.55)

    # Castelo: marcha mais solene (menor harmonico)
    Cs = 4
    mel2 = [(A - 12, 1), (D, 1), (E, 1), (F, 1), (E, 1), (D, 0.5), (Cs - 12, 0.5), (D, 2),
            (F, 1), (G, 1), (A, 1.5), (G, 0.5), (F, 1), (E, 1), (D, 2),
            (A, 1), (B - 1, 1), (A, 1), (G, 1), (F, 1), (E, 1), (F, 1), (G, 1),
            (A, 1), (G, 0.5), (F, 0.5), (E, 1), (Cs - 12, 1), (D, 3), (None, 1)]
    bass2 = [(D, 2), (D, 2), (B - 13, 2), (A - 12, 2), (D, 2), (G - 12, 2), (A - 12, 2), (D, 2),
             (F - 12, 2), (G - 12, 2), (A - 12, 2), (D, 2), (B - 13, 2), (A - 12, 2), (D, 4)]
    write("music_castle", render_track(mel2 * 2, bass2 * 2, 100, drum=[(0, "k"), (1, "s"), (1.5, "s")], drone=D), 0.55)

    # Masmorra/chefe: rapido, tenso
    mel3 = [(D, 0.5), (D, 0.5), (F, 0.5), (D, 0.5), (G, 0.5), (D, 0.5), (Ab := -1, 0.5), (G, 0.5),
            (F, 0.5), (F, 0.5), (E, 0.5), (F, 0.5), (D, 1), (None, 1),
            (A, 0.5), (A, 0.5), (B - 1, 0.5), (A, 0.5), (G, 0.5), (F, 0.5), (E, 0.5), (F, 0.5),
            (D, 0.5), (E, 0.5), (F, 0.5), (E, 0.5), (Cs - 12, 1), (None, 1)]
    bass3 = [(D, 0.5), (None, 0.5)] * 16
    write("music_boss", render_track(mel3 * 4, bass3 * 4, 150, drum=[(0, "k"), (0.5, "k"), (1, "s"), (1.5, "k")], lute_decay=0.993), 0.6)

    # Masmorra (exploracao): lento, sombrio
    mel4 = [(D, 2), (None, 1), (F, 1), (E, 2), (Cs - 12, 2), (D, 1), (F, 1), (A, 2), (G, 2), (None, 2),
            (B - 1, 2), (A, 1), (G, 1), (F, 2), (E, 2), (D, 4), (None, 4)]
    write("music_dungeon", render_track(mel4 * 2, [(D, 8), (B - 13, 8), (G - 12, 8), (A - 12, 8)] * 2, 76, drum=[(0, "k")], drone=D, lute_decay=0.998), 0.55)

    # Titulo
    mel5 = [(D, 1), (A, 1), (G, 0.5), (F, 0.5), (G, 1), (A, 2), (C, 1), (D2, 1), (C, 0.5), (B, 0.5), (A, 1), (G, 2),
            (F, 1), (G, 1), (A, 1), (F, 1), (E, 1), (C - 12, 1), (D, 2), (None, 2)]
    write("music_title", render_track(mel5 * 2, [(D, 4), (C - 12, 4), (F - 12, 4), (G - 12, 2), (A - 12, 2), (D, 4)] * 2, 90, drone=D), 0.55)

if __name__ == "__main__":
    sfx()
    music()


def thunder():
    d = 2.6
    n = lowpass(noise(d), 0.04) * 3 + lowpass(noise(d), 0.15) * env(int(SR * d), 0.001, 9)
    tt = t(d)
    rumble = (0.6 + 0.4 * np.sin(tt * 7) * np.sin(tt * 3.1)) * env(len(tt), 0.02, 1.4)
    write("thunder", n * rumble, 0.9)


if __name__ == "__main__" and True:
    thunder()
