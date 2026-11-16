class_name SpriteLib
extends RefCounted
## Monta SpriteFrames a partir das spritesheets processadas (assets/sprites).
## Cada entrada: animacao -> [arquivo, frame_inicial, frame_final(-1=ultimo), fps, loop]
## Arquivos "gen_*" sao animacoes geradas por tools/gen_anims.py.

const BASE := "res://assets/sprites/"

const ANIMS := {
	"cavaleiro": {
		"idle": ["idle", 0, -1, 12, true],
		"walk": ["walk", 0, -1, 26, true],
		"attack": ["gen_attack", 0, -1, 28, false],
		"attack2": ["gen_attack2", 0, -1, 28, false],
		"dash": ["gen_dash", 0, -1, 24, true],
		"jump": ["gen_jump", 0, -1, 14, false],
		"fall": ["gen_fall", 0, -1, 8, true],
		"hurt": ["gen_hurt", 0, -1, 16, false],
		"die": ["gen_die", 0, -1, 16, false],
	},
	"barbaro": {
		"idle": ["idle", 0, -1, 20, true],
		"walk": ["walk", 0, -1, 30, true],
		"attack": ["attack", 0, 12, 28, false],
		"special": ["attack", 36, 54, 24, false],
		"jump": ["gen_jump", 0, -1, 14, false],
		"fall": ["gen_fall", 0, -1, 8, true],
		"hurt": ["gen_hurt", 0, -1, 16, false],
		"die": ["die", 0, -1, 20, false],
	},
	"sabio": {
		"idle": ["idle", 0, -1, 12, true],
		"walk": ["gen_walk", 0, -1, 18, true],
		"attack": ["attack", 0, -1, 26, false],
		"jump": ["gen_jump", 0, -1, 14, false],
		"fall": ["gen_fall", 0, -1, 8, true],
		"hurt": ["gen_hurt", 0, -1, 16, false],
		"die": ["gen_die", 0, -1, 16, false],
	},
	"goblin_guerreiro": {
		"idle": ["gen_idle", 0, -1, 10, true],
		"walk": ["walk", 0, -1, 18, true],
		"attack": ["attack", 0, -1, 20, false],
		"jump": ["jump", 0, -1, 18, false],
		"hurt": ["gen_hurt", 0, -1, 14, false],
		"die": ["gen_die", 0, -1, 16, false],
	},
	"goblin_lanca": {
		"idle": ["gen_idle", 0, -1, 10, true],
		"walk": ["walk", 0, -1, 24, true],
		"attack": ["defense", 0, -1, 16, false],
		"hurt": ["hurt", 0, -1, 22, false],
		"die": ["gen_die", 0, -1, 16, false],
	},
	"goblin_boleadeira": {
		"idle": ["idle", 0, -1, 14, true],
		"walk": ["idle", 0, -1, 14, true],
		"attack": ["attack", 0, -1, 18, false],
		"hurt": ["gen_hurt", 0, -1, 14, false],
		"die": ["gen_die", 0, -1, 16, false],
	},
	"goblin_mago": {
		"idle": ["idle", 0, -1, 16, true],
		"walk": ["walk", 0, -1, 24, true],
		"attack": ["attack", 0, -1, 18, false],
		"hurt": ["hurt", 0, -1, 18, false],
		"die": ["die", 0, -1, 16, false],
	},
	"goblin_general": {
		"idle": ["idle", 0, -1, 12, true],
		"walk": ["gen_walk", 0, -1, 18, true],
		"attack": ["attack", 0, -1, 18, false],
		"hurt": ["hurt", 0, -1, 18, false],
		"die": ["gen_die", 0, -1, 14, false],
	},
	"minotauro": {
		"idle": ["gen_idle", 0, -1, 10, true],
		"walk": ["walk", 0, -1, 14, true],
		"attack": ["attack", 0, -1, 14, false],
		"roll": ["roll", 0, -1, 16, false],
		"hurt": ["gen_hurt", 0, -1, 14, false],
		"die": ["gen_die", 0, -1, 12, false],
	},
	"cerberus": {
		"idle": ["idle", 0, -1, 16, true],
		"walk": ["idle", 0, -1, 24, true],
		"howl": ["howl", 0, -1, 14, false],
		"leap": ["gen_leap", 0, -1, 10, false],
		"hurt": ["gen_hurt", 0, -1, 14, false],
		"die": ["gen_die", 0, -1, 10, false],
	},
}

static var _cache := {}
static var _offsets := {}


static func frames(char_name: String) -> SpriteFrames:
	if _cache.has(char_name):
		return _cache[char_name]
	var meta: Dictionary = SpriteMeta.DATA[char_name]
	var sf := SpriteFrames.new()
	if sf.has_animation("default"):
		sf.remove_animation("default")
	var offs := {}
	var anims: Dictionary = ANIMS[char_name]
	for anim in anims:
		var cfg: Array = anims[anim]
		var sheet: String = cfg[0]
		var am: Dictionary = meta["anims"][sheet]
		var cell: Array = am.get("cell", meta["cell"])
		var anchor: Array = am.get("anchor", meta["anchor"])
		var cw := int(cell[0])
		var ch := int(cell[1])
		offs[anim] = Vector2(cw * 0.5 - float(anchor[0]), ch * 0.5 - float(anchor[1]))
		var tex: Texture2D = load(BASE + char_name + "/" + sheet + ".png")
		var cols := int(am["cols"])
		var last: int = cfg[2] if cfg[2] >= 0 else int(am["frames"]) - 1
		sf.add_animation(anim)
		sf.set_animation_speed(anim, cfg[3])
		sf.set_animation_loop(anim, cfg[4])
		for i in range(cfg[1], last + 1):
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2((i % cols) * cw, (i / cols) * ch, cw, ch)
			sf.add_frame(anim, at)
	_cache[char_name] = sf
	_offsets[char_name] = offs
	return sf


## Offsets (pes na origem) de cada animacao.
static func offsets(char_name: String) -> Dictionary:
	frames(char_name)
	return _offsets[char_name]


static func make_sprite(char_name: String) -> CharSprite:
	var s := CharSprite.new()
	s.setup(char_name)
	return s


static func portrait(char_name: String) -> Texture2D:
	return frames(char_name).get_frame_texture("idle", 0)
