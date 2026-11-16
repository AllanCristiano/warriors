"""Gera as cenas das fases (scenes/levels/level_N.tscn) a partir do design abaixo.
Depois de gerado, tudo pode ser editado normalmente no editor do Godot
(blocos de terreno, props, inimigos, bandeiras etc. sao nos comuns).
Uso: python tools/build_levels.py
ATENCAO: rodar de novo sobrescreve edicoes feitas no editor.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KING = os.path.join(ROOT, "assets", "kingdom")
GY = 560  # altura padrao do chao


def tex_size(name):
    return Image.open(os.path.join(KING, name + ".png")).size


def v2(x, y):
    return "Vector2(%s, %s)" % (round(x, 2), round(y, 2))


class Scene:
    def __init__(self, root_name, script):
        self.ext = {}
        self.nodes = []
        self.counts = {}
        self.root = root_name
        self.root_props = {"script": self.res("Script", script)}

    def res(self, typ, path):
        if path not in self.ext:
            self.ext[path] = (typ, "r%d" % (len(self.ext) + 1))
        return 'ExtResource("%s")' % self.ext[path][1]

    def name(self, base):
        self.counts[base] = self.counts.get(base, 0) + 1
        n = self.counts[base]
        return base if n == 1 and base[0].isupper() and base in ("Boss",) else "%s%d" % (base, n)

    def node(self, name, typ, parent=".", props=None):
        self.nodes.append((name, typ, parent, props or {}))
        return name if parent == "." else parent + "/" + name

    def save(self, path):
        out = ['[gd_scene format=3]', '']
        for p, (typ, i) in self.ext.items():
            out.append('[ext_resource type="%s" path="%s" id="%s"]' % (typ, p, i))
        out.append('')
        out.append('[node name="%s" type="Node2D"]' % self.root)
        for k, v in self.root_props.items():
            out.append("%s = %s" % (k, v))
        out.append('')
        for name, typ, parent, props in self.nodes:
            out.append('[node name="%s" type="%s" parent="%s"]' % (name, typ, parent))
            # script primeiro para que as propriedades exportadas sejam aplicadas
            if "script" in props:
                out.append("script = %s" % props["script"])
            for k, v in props.items():
                if k != "script":
                    out.append("%s = %s" % (k, v))
            out.append('')
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        print("ok", path)


def q(s):
    return '"%s"' % s


class LevelBuilder:
    def __init__(self, root, name, subtitle, music, width, ambient=None, kill_y=900):
        s = self.s = Scene(root, "res://scripts/level/level.gd")
        s.root_props.update({"level_name": q(name), "subtitle": q(subtitle), "music": q(music),
                             "level_width": float(width), "kill_y": float(kill_y)})
        if ambient:
            s.root_props["ambient"] = "Color(%s, %s, %s, 1)" % ambient
        self.width = width

    # ----- fundos
    def sky(self, tex):
        s = self.s
        s.node("Sky", "CanvasLayer", ".", {"layer": -100})
        s.node("SkyTexture", "TextureRect", "Sky", {
            "anchors_preset": 15, "anchor_right": 1.0, "anchor_bottom": 1.0,
            "grow_horizontal": 2, "grow_vertical": 2,
            "texture": s.res("Texture2D", "res://assets/kingdom/%s.png" % tex),
            "expand_mode": 1, "stretch_mode": 6})

    def parallax(self, name, tex, scroll, y=0, modulate=None):
        s = self.s
        props = {"scroll_scale": v2(scroll, 1), "repeat_size": v2(1280, 0), "repeat_times": 4}
        s.node(name, "Parallax2D", ".", props)
        sp = {"texture": s.res("Texture2D", "res://assets/kingdom/%s.png" % tex), "centered": "false",
              "position": v2(0, y)}
        if modulate:
            sp["modulate"] = "Color(%s, %s, %s, 1)" % modulate
        s.node("Layer", "Sprite2D", name, sp)

    def groups(self):
        for g in ["Decor", "Terrain", "Hazards", "Items", "Checkpoints", "Enemies", "Foreground"]:
            props = {}
            if g == "Decor":
                props["z_index"] = -1
            if g == "Foreground":
                props["z_index"] = 10
            self.s.node(g, "Node2D", ".", props)

    # ----- elementos
    def prop(self, tex, x, y=GY, sink=6, flip=False, scale=1.0, mod=None, sway=False, parent="Decor", z=None):
        s = self.s
        w, h = tex_size(tex)
        props = {"position": v2(x, y + sink), "texture": s.res("Texture2D", "res://assets/kingdom/%s.png" % tex),
                 "offset": v2(0, -h / 2)}
        if flip:
            props["flip_h"] = "true"
        if scale != 1.0:
            props["scale"] = v2(scale, scale)
        if mod:
            props["modulate"] = "Color(%s, %s, %s, %s)" % (mod + (1,) if len(mod) == 3 else mod)
        if sway:
            props["material"] = s.res("Material", "res://shaders/sway.tres")
        if z is not None:
            props["z_index"] = z
        s.node(s.name(tex.title().replace("_", "")), "Sprite2D", parent, props)

    def ground(self, x0, x1, y=GY, style="grama", depth=None, safe=True):
        d = depth if depth else (1100 - y)
        props = {"position": v2(x0, y), "script": self.s.res("Script", "res://scripts/level/terrain.gd"),
                 "size": v2(x1 - x0, d), "style": q(style)}
        if not safe:
            props["safe"] = "false"
        self.s.node(self.s.name("Ground"), "StaticBody2D", "Terrain", props)

    def platform(self, x, y, w, style="tabuas", one_way=True):
        self.s.node(self.s.name("Platform"), "StaticBody2D", "Terrain", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/level/terrain.gd"),
            "size": v2(w, 24), "style": q(style), "one_way": "true" if one_way else "false"})

    def hazard(self, kind, x, y, w, depth=200):
        self.s.node(self.s.name("Hazard"), "Area2D", "Hazards", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/level/hazard.gd"),
            "kind": q(kind), "width": float(w), "depth": float(depth)})

    def enemy(self, kind, x, y=GY, patrol=180, left=True, name=None, dormant=False):
        n = name or self.s.name("Enemy")
        props = {"position": v2(x, y), "script": self.s.res("Script", "res://scripts/enemy.gd"),
                 "kind": q(kind), "patrol_range": float(patrol), "start_facing_left": "true" if left else "false"}
        if dormant:
            props["dormant"] = "true"
        self.s.node(n, "CharacterBody2D", "Enemies", props)
        return "Enemies/" + n

    def crate(self, x, y=GY, kind="crate", loot="aleatorio"):
        self.s.node(self.s.name("Breakable"), "StaticBody2D", "Items", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/level/breakable.gd"),
            "kind": q(kind), "loot": q(loot)})

    def coin(self, x, y):
        self.s.node(self.s.name("Coin"), "Area2D", "Items", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/pickup.gd"), "kind": q("coin")})

    def coin_arc(self, x0, x1, y, h=80, n=5):
        for i in range(n):
            t = i / (n - 1)
            self.coin(x0 + (x1 - x0) * t, y - h * 4 * t * (1 - t))

    def coin_row(self, x0, y, n=4, gap=44):
        for i in range(n):
            self.coin(x0 + i * gap, y)

    def potion(self, x, y):
        self.s.node(self.s.name("Potion"), "Area2D", "Items", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/pickup.gd"), "kind": q("potion")})

    def checkpoint(self, x, y=GY):
        self.s.node(self.s.name("Checkpoint"), "Area2D", "Checkpoints", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/level/checkpoint.gd")})

    def torch(self, x, y, energy=1.0, scale=2.2):
        self.s.node(self.s.name("Torch"), "Node2D", "Decor", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/level/torch.gd"),
            "light_energy": energy, "light_scale": scale})

    def start(self, x, y=GY):
        self.s.node("PlayerStart", "Marker2D", ".", {"position": v2(x, y - 4)})

    def arena(self, x, width, boss_path, y=GY):
        self.s.node("BossArena", "Area2D", ".", {
            "position": v2(x, y), "script": self.s.res("Script", "res://scripts/level/boss_arena.gd"),
            "boss_path": 'NodePath("../%s")' % boss_path, "arena_width": float(width)})

    def goal(self, x, y=GY, tex="castle_gate"):
        self.s.node("Goal", "Area2D", ".", {
            "position": v2(x, y + 4), "script": self.s.res("Script", "res://scripts/level/goal.gd"),
            "texture_name": q(tex)})

    def save(self, n):
        self.s.save(os.path.join(ROOT, "scenes", "levels", "level_%d.tscn" % n))


# =====================================================================
# FASE 1 - Aldeia de Vale Dourado (dia, grama, casas, moinho, praca)
# =====================================================================
def level1():
    L = LevelBuilder("Level1", "Aldeia de Vale Dourado", "Os goblins invadiram a aldeia! Defenda o povo do Rei.",
                     "music_village", 8700)
    L.sky("bg_sky_day")
    L.parallax("FarHills", "bg_day_far", 0.15)
    L.parallax("NearHills", "bg_day_near", 0.3, 40)
    L.parallax("Village", "bg_day_mid", 0.5, 60)
    L.groups()
    L.start(160)

    # --- trecho 1: entrada da aldeia
    L.ground(-200, 1400)
    L.prop("signpost", 330)
    L.prop("tree_oak", 80)
    L.prop("house_a", 640)
    L.prop("fence", 860); L.prop("fence", 988)
    L.prop("tree_oak", 1150, flip=True)
    L.prop("haystack", 1290)
    L.prop("bush", 470, parent="Foreground", mod=(0.75, 0.8, 0.75), sink=30)
    L.crate(900); L.crate(960, loot="moedas")
    L.enemy("goblin_guerreiro", 1100, patrol=160)
    L.coin_row(500, GY - 40, 4)

    # --- fosso com agua e ponte de tabuas
    L.hazard("agua", 1400, GY + 60, 340, 200)
    L.platform(1470, GY - 70, 90)
    L.platform(1600, GY - 120, 90)
    L.coin_arc(1430, 1720, GY - 150, 90, 6)

    # --- trecho 2: mercado
    L.ground(1740, 3300)
    L.prop("market_stall", 1900)
    L.prop("house_b", 2250)
    L.prop("banner_red", 2180, GY - 240, sink=0, sway=True)
    L.prop("well", 2620)
    L.prop("cart", 3000)
    L.prop("tree_pine", 3200)
    L.platform(2080, GY - 140, 200)
    L.platform(2330, GY - 260, 220)
    L.crate(2440, GY - 260, loot="pocao")
    L.coin_row(2110, GY - 180, 4)
    L.enemy("goblin_lanca", 2150, patrol=200)
    L.enemy("goblin_boleadeira", 2380, GY - 260, patrol=0)
    L.enemy("goblin_guerreiro", 2800, patrol=200)
    L.crate(2700, kind="barrel")
    L.checkpoint(3150)

    # --- trecho 3: colina do moinho (terreno elevado)
    L.ground(3300, 4600, GY - 100)
    L.prop("windmill", 3750, GY - 100)
    L.prop("haystack", 3500, GY - 100)
    L.prop("tree_oak", 4250, GY - 100)
    L.prop("fence", 4000, GY - 100); L.prop("fence", 4128, GY - 100)
    L.enemy("goblin_guerreiro", 3700, GY - 100, patrol=200)
    L.enemy("goblin_guerreiro", 4100, GY - 100, patrol=200)
    L.enemy("goblin_boleadeira", 4500, GY - 100, patrol=0)
    L.platform(3900, GY - 290, 160)
    L.coin_row(3910, GY - 330, 4)
    L.crate(4400, GY - 100, kind="barrel")

    # --- abismo com espinhos
    L.hazard("espinhos", 4600, GY + 100, 320)
    L.ground(4600, 4920, GY + 130, depth=600, safe=False)
    L.platform(4680, GY - 140, 140)
    L.coin_arc(4620, 4900, GY - 170, 70, 5)

    # --- trecho 4: rua das casas
    L.ground(4920, 6300)
    L.prop("house_a", 5150, flip=True)
    L.prop("house_b", 5650)
    L.prop("banner_blue", 5470, GY - 230, sink=0, sway=True)
    L.prop("tree_pine", 5950)
    L.prop("market_stall", 6150)
    L.platform(5400, GY - 170, 200, "pedra")
    L.potion(5500, GY - 210)
    L.enemy("goblin_mago", 5350, patrol=150)
    L.enemy("goblin_lanca", 5750, patrol=180)
    L.enemy("goblin_guerreiro", 6050, patrol=150)
    L.crate(5880); L.crate(5880, GY - 66, loot="moedas")
    L.checkpoint(6250)

    # --- arena: praca da aldeia (chefe: General Goblin)
    L.ground(6300, 8700)
    L.prop("well", 7000)
    L.prop("banner_red", 6700, GY - 250, sink=0, sway=True)
    L.prop("banner_red", 7500, GY - 250, sink=0, sway=True)
    L.prop("house_b", 7250, mod=(0.85, 0.85, 0.9))
    L.prop("market_stall", 6600)
    L.prop("tree_oak", 7700)
    boss = L.enemy("goblin_general", 7400, name="Boss", dormant=True)
    L.arena(6400, 1500, boss)
    L.goal(8350)
    L.prop("signpost", 8100)
    L.save(1)


# =====================================================================
# FASE 2 - Muralhas de Pedraforte (por do sol, muralhas, fosso, torres)
# =====================================================================
def level2():
    L = LevelBuilder("Level2", "Muralhas de Pedraforte", "As hordas cercam o castelo. Abra caminho pelas muralhas!",
                     "music_castle", 9400, ambient=(1.0, 0.9, 0.85))
    L.sky("bg_sky_sunset")
    L.parallax("FarHills", "bg_sunset_far", 0.15)
    L.parallax("Walls", "bg_sunset_wall", 0.4, 40)
    L.groups()
    L.start(160)

    # --- ponte levadica sobre o fosso
    L.ground(-200, 900, style="castelo")
    L.prop("tower", 120)
    L.prop("banner_red", 360, GY - 260, sink=0, sway=True)
    L.prop("knight_statue", 560)
    L.torch(300, GY - 140); L.torch(760, GY - 140)
    L.crate(700, kind="barrel")
    L.enemy("goblin_lanca", 800, patrol=100)
    L.hazard("agua", 900, GY + 70, 520, 200)
    L.platform(900, GY, 520, "tabuas", one_way=False)  # ponte levadica
    L.enemy("goblin_guerreiro", 1200, GY, patrol=150)
    L.coin_row(1000, GY - 60, 7, 50)

    # --- patio externo com escadarias de pedra
    L.ground(1420, 3200, style="castelo")
    L.prop("weapon_rack", 1600)
    L.prop("tower", 1950)
    L.torch(1820, GY - 150); L.torch(2080, GY - 150)
    L.platform(2200, GY - 120, 160, "pedra")
    L.platform(2420, GY - 240, 160, "pedra")
    L.platform(2650, GY - 360, 200, "pedra")
    L.enemy("goblin_boleadeira", 2740, GY - 360, patrol=0)
    L.coin_row(2440, GY - 280, 3)
    L.crate(2700, GY - 360, loot="pocao")
    L.enemy("goblin_mago", 2500, patrol=180)
    L.enemy("goblin_guerreiro", 3000, patrol=150)
    L.prop("banner_blue", 3050, GY - 250, sink=0, sway=True)
    L.checkpoint(3120)

    # --- caminho da muralha (terreno alto) com buracos
    L.ground(3200, 4000, GY - 120, "castelo")
    L.prop("knight_statue", 3450, GY - 120)
    L.torch(3650, GY - 270)
    L.enemy("goblin_lanca", 3700, GY - 120, patrol=200)
    L.hazard("espinhos", 4000, GY + 80, 260)
    L.ground(4000, 4260, GY + 110, "castelo", depth=600, safe=False)
    L.platform(4070, GY - 180, 120, "pedra")
    L.ground(4260, 5200, GY - 120, "castelo")
    L.prop("tower", 4600, GY - 120)
    L.enemy("goblin_mago", 4500, GY - 120, patrol=120)
    L.enemy("goblin_boleadeira", 5100, GY - 120, patrol=0)
    L.crate(4850, GY - 120); L.crate(4920, GY - 120, kind="barrel")
    L.coin_arc(4020, 4240, GY - 220, 60, 5)

    # --- descida e fosso interno
    L.ground(5200, 5700, GY, "castelo")
    L.hazard("agua", 5700, GY + 70, 380, 200)
    L.platform(5760, GY - 80, 100, "tabuas")
    L.platform(5940, GY - 150, 100, "tabuas")
    L.coin_arc(5720, 6070, GY - 200, 80, 6)
    L.ground(6080, 7400, GY, "castelo")
    L.prop("weapon_rack", 6200)
    L.prop("banner_red", 6450, GY - 250, sink=0, sway=True)
    L.torch(6650, GY - 150)
    L.enemy("goblin_guerreiro", 6400, patrol=150)
    L.enemy("goblin_lanca", 6800, patrol=150)
    L.enemy("goblin_mago", 7150, patrol=120)
    L.platform(6550, GY - 170, 180, "pedra")
    L.potion(6640, GY - 210)
    L.checkpoint(7350)

    # --- arena: patio interno (chefe: Minotauro)
    L.ground(7400, 9400, GY, "castelo")
    L.prop("tower", 7600)
    L.prop("tower", 8800)
    L.prop("knight_statue", 8000); L.prop("knight_statue", 8400, flip=True)
    L.prop("banner_red", 8200, GY - 300, sink=0, sway=True)
    L.torch(7800, GY - 160); L.torch(8600, GY - 160)
    boss = L.enemy("minotauro", 8500, name="Boss", dormant=True)
    L.arena(7500, 1500, boss)
    L.goal(9150)
    L.save(2)


# =====================================================================
# FASE 3 - Masmorras do Trono (escuro, tochas, lava, sala do trono)
# =====================================================================
def level3():
    L = LevelBuilder("Level3", "Masmorras do Trono", "Cerbero guarda o trono roubado. Desca as masmorras e liberte o reino!",
                     "music_dungeon", 9000, ambient=(0.38, 0.36, 0.5))
    L.sky("bg_sky_night")
    L.parallax("DungeonBack", "bg_dungeon_back", 0.25, -40)
    L.parallax("DungeonMid", "bg_dungeon_mid", 0.5, 0)
    L.groups()
    L.start(160)

    # --- entrada
    L.ground(-200, 1300, style="masmorra")
    L.prop("pillar", 260); L.prop("pillar", 900)
    L.prop("chain", 560, GY - 330, sink=0)
    L.prop("skulls", 700)
    L.torch(420, GY - 160); L.torch(1100, GY - 160)
    L.enemy("goblin_guerreiro", 950, patrol=180)
    L.crate(1200, kind="barrel")

    # --- rio de lava com plataformas de pedra
    L.hazard("lava", 1300, GY + 60, 700, 200)
    L.platform(1360, GY - 60, 110, "pedra")
    L.platform(1540, GY - 140, 110, "pedra")
    L.platform(1720, GY - 80, 110, "pedra")
    L.platform(1880, GY - 150, 100, "pedra")
    L.coin_arc(1360, 1980, GY - 220, 60, 8)
    L.ground(2000, 3300, style="masmorra")
    L.prop("pillar", 2200); L.prop("pillar", 2900)
    L.prop("weapon_rack", 2500)
    L.torch(2350, GY - 160); L.torch(3050, GY - 160)
    L.enemy("goblin_mago", 2450, patrol=150)
    L.enemy("goblin_lanca", 2750, patrol=150)
    L.enemy("goblin_guerreiro", 3100, patrol=150)
    L.platform(2550, GY - 170, 180, "pedra")
    L.crate(2620, GY - 170, loot="pocao")
    L.checkpoint(3230)

    # --- corredor de espinhos com teto baixo
    L.ground(3300, 3500, style="masmorra")
    L.hazard("espinhos", 3500, GY + 70, 640)
    L.ground(3500, 4140, GY + 100, "masmorra", depth=600, safe=False)
    L.platform(3560, GY - 70, 100, "pedra")
    L.platform(3740, GY - 140, 100, "pedra")
    L.platform(3920, GY - 70, 100, "pedra")
    L.enemy("goblin_boleadeira", 3790, GY - 140, patrol=0)
    L.coin_row(3580, GY - 110, 2); L.coin_row(3940, GY - 110, 2)
    L.ground(4140, 5400, style="masmorra")
    L.prop("chain", 4300, GY - 330, sink=0); L.prop("chain", 4900, GY - 330, sink=0)
    L.prop("skulls", 4600)
    L.torch(4450, GY - 160); L.torch(5150, GY - 160)
    L.enemy("goblin_mago", 4700, patrol=120)
    L.enemy("goblin_guerreiro", 5000, patrol=150)
    L.enemy("goblin_lanca", 5300, patrol=100)
    L.crate(4500); L.crate(4560, kind="barrel")

    # --- poco de lava e subida
    L.hazard("lava", 5400, GY + 60, 400, 200)
    L.platform(5470, GY - 90, 120, "pedra")
    L.platform(5650, GY - 170, 120, "pedra")
    L.ground(5800, 6900, GY - 120, "masmorra")
    L.prop("pillar", 6000, GY - 120); L.prop("pillar", 6700, GY - 120)
    L.torch(6200, GY - 280); L.torch(6500, GY - 280)
    L.enemy("goblin_mago", 6300, GY - 120, patrol=120)
    L.enemy("goblin_guerreiro", 6600, GY - 120, patrol=120)
    L.potion(6450, GY - 170)
    L.checkpoint(6850, GY - 120)

    # --- sala do trono (chefe final: Cerbero)
    L.ground(6900, 9000, GY, "masmorra")
    L.prop("throne", 8000, GY)
    L.prop("banner_red", 7750, GY - 330, sink=0, sway=True)
    L.prop("banner_red", 8250, GY - 330, sink=0, sway=True)
    L.prop("pillar", 7300); L.prop("pillar", 8700)
    L.prop("skulls", 7500); L.prop("skulls", 8500)
    L.torch(7150, GY - 170, 1.3, 2.8); L.torch(7650, GY - 200, 1.3, 2.8)
    L.torch(8350, GY - 200, 1.3, 2.8); L.torch(8850, GY - 170, 1.3, 2.8)
    boss = L.enemy("cerberus", 8300, name="Boss", dormant=True)
    L.arena(6950, 1700, boss)
    L.goal(8880)
    L.save(3)


if __name__ == "__main__":
    level1(); level2(); level3()
