class_name SpriteLib
extends RefCounted
## Monta SpriteFrames a partir das spritesheets processadas (assets/sprites).
## Cada entrada: animacao -> [arquivo, frame_inicial, frame_final(-1=ultimo), fps, loop]

const BASE := "res://assets/sprites/"

const ANIMS := {
	"cavaleiro": {
		"idle": ["idle", 0, -1, 12, true],
		"walk": ["walk", 0, -1, 26, true],
	},
	"barbaro": {
		"idle": ["idle", 0, -1, 20, true],
		"walk": ["walk", 0, -1, 30, true],
		"attack": ["attack", 0, 12, 28, false],
		"special": ["attack", 36, 54, 24, false],
		"die": ["die", 0, -1, 20, false],
	},
	"sabio": {
		"idle": ["idle", 0, -1, 12, true],
		"attack": ["attack", 0, -1, 26, false],
	},
	"goblin_guerreiro": {
		"idle": ["walk", 0, 0, 1, true],
		"walk": ["walk", 0, -1, 18, true],
		"attack": ["attack", 0, -1, 20, false],
		"hurt": ["jump", 0, 6, 20, false],
	},
	"goblin_lanca": {
		"idle": ["defense", 0, 0, 1, true],
		"walk": ["walk", 0, -1, 24, true],
		"attack": ["defense", 0, -1, 16, false],
		"hurt": ["hurt", 0, -1, 22, false],
	},
	"goblin_boleadeira": {
		"idle": ["idle", 0, -1, 14, true],
		"walk": ["idle", 0, -1, 14, true],
		"attack": ["attack", 0, -1, 18, false],
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
		"walk": ["idle", 0, -1, 18, true],
		"attack": ["attack", 0, -1, 18, false],
		"hurt": ["hurt", 0, -1, 18, false],
	},
	"minotauro": {
		"idle": ["walk", 0, 0, 1, true],
		"walk": ["walk", 0, -1, 14, true],
		"attack": ["attack", 0, -1, 14, false],
		"roll": ["roll", 0, -1, 16, false],
	},
	"cerberus": {
		"idle": ["idle", 0, -1, 16, true],
		"walk": ["idle", 0, -1, 24, true],
		"howl": ["howl", 0, -1, 14, false],
	},
}

static var _cache := {}


static func frames(char_name: String) -> SpriteFrames:
	if _cache.has(char_name):
		return _cache[char_name]
	var meta: Dictionary = SpriteMeta.DATA[char_name]
	var cw := int(meta["cell"][0])
	var ch := int(meta["cell"][1])
	var sf := SpriteFrames.new()
	if sf.has_animation("default"):
		sf.remove_animation("default")
	var anims: Dictionary = ANIMS[char_name]
	for anim in anims:
		var cfg: Array = anims[anim]
		var sheet: String = cfg[0]
		var am: Dictionary = meta["anims"][sheet]
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
	return sf


## Offset para um AnimatedSprite2D centralizado ficar com os pes na origem.
static func foot_offset(char_name: String) -> Vector2:
	var meta: Dictionary = SpriteMeta.DATA[char_name]
	return Vector2(meta["cell"][0] * 0.5 - meta["anchor"][0], meta["cell"][1] * 0.5 - meta["anchor"][1])


static func make_sprite(char_name: String) -> AnimatedSprite2D:
	var s := AnimatedSprite2D.new()
	s.sprite_frames = frames(char_name)
	s.offset = foot_offset(char_name)
	return s


static func portrait(char_name: String) -> Texture2D:
	var sf := frames(char_name)
	return sf.get_frame_texture("idle", 0)
