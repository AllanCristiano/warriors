extends Node
## Estado global do jogo: heroi escolhido, fases, vidas, ouro, transicoes.

const HEROES := {
	"cavaleiro": {
		"name": "Sir Aldric",
		"title": "O Cavaleiro de Ferro",
		"sprite": "cavaleiro",
		"desc": "Guardião juramentado da Coroa. Armadura pesada e espada longa. Especial: Investida Real — avança atravessando inimigos.",
		"hp": 150, "speed": 280.0, "jump": 800.0, "damage": 26,
		"attack_cd": 0.36, "special_cd": 2.2, "reach": Vector2(120, 110),
		"stats": {"Vida": 4, "Força": 3, "Agilidade": 3},
		"color": Color(0.75, 0.78, 0.85),
	},
	"barbaro": {
		"name": "Brakka",
		"title": "O Bárbaro das Montanhas",
		"sprite": "barbaro",
		"desc": "Fera das terras geladas. Lento, mas cada golpe da sua clava esmaga goblins. Especial: Terremoto — esmaga o chão ao redor.",
		"hp": 200, "speed": 240.0, "jump": 760.0, "damage": 40,
		"attack_cd": 0.15, "special_cd": 3.5, "reach": Vector2(150, 120),
		"stats": {"Vida": 5, "Força": 5, "Agilidade": 2},
		"color": Color(0.85, 0.6, 0.35),
	},
	"sabio": {
		"name": "Mestre Liang",
		"title": "O Sábio Marcial",
		"sprite": "sabio",
		"desc": "Andarilho do Oriente que serve ao Rei. Ataca à distância com dardos e salta duas vezes. Especial: Leque de Dardos.",
		"hp": 110, "speed": 310.0, "jump": 780.0, "damage": 18,
		"attack_cd": 0.1, "special_cd": 2.0, "reach": Vector2(0, 0),
		"stats": {"Vida": 2, "Força": 3, "Agilidade": 5},
		"color": Color(0.85, 0.75, 0.4),
	},
}

const LEVELS := [
	{"scene": "res://scenes/levels/level_1.tscn", "name": "Aldeia de Vale Dourado"},
	{"scene": "res://scenes/levels/level_2.tscn", "name": "Muralhas de Pedraforte"},
	{"scene": "res://scenes/levels/level_3.tscn", "name": "Masmorras do Trono"},
]

const START_LIVES := 3

var hero_id := "cavaleiro"
var level_index := 0
var lives := START_LIVES
var gold := 0
var checkpoint := Vector2.INF
var hero_hp := -1  # hp carregado entre fases (-1 = cheio)

var font_title: Font
var font_body: Font
var _fade: ColorRect
var _fade_layer: CanvasLayer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_input()
	_setup_fonts()
	_fade_layer = CanvasLayer.new()
	_fade_layer.layer = 100
	add_child(_fade_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade_layer.add_child(_fade)
	_debug_args()


# Debug: godot --path . <cena> -- --hero=barbaro --x=3000 --shot=arquivo.png --frames=90
var _shots: Array = []
var _frame := 0

func _debug_args() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=")
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	if args.is_empty():
		return
	if args.has("hero"):
		hero_id = args["hero"]
	if args.has("x"):
		checkpoint = Vector2(float(args["x"]), float(args.get("y", "540")))
	if args.has("shot"):
		var frames := int(args.get("frames", "90"))
		for i in int(args.get("count", "1")):
			_shots.append([frames * (i + 1), args["shot"].replace(".png", "_%d.png" % i)])
	set_meta("debug_args", args)


func _process(_delta: float) -> void:
	if _shots.is_empty():
		return
	_frame += 1
	var act: Dictionary = get_meta("debug_args", {})
	if act.has("walk"):
		Input.action_press("right")
	if act.has("attack") and _frame % 30 == 0:
		Input.action_press("attack")
	elif act.has("attack") and _frame % 30 == 2:
		Input.action_release("attack")
	if _frame >= _shots[0][0]:
		var img := get_viewport().get_texture().get_image()
		img.save_png(_shots[0][1])
		_shots.pop_front()
		if _shots.is_empty():
			get_tree().quit()


func _setup_fonts() -> void:
	var t := SystemFont.new()
	t.font_names = PackedStringArray(["Old English Text MT", "Blackadder ITC", "Cambria", "Georgia", "Times New Roman", "serif"])
	font_title = t
	var b := SystemFont.new()
	b.font_names = PackedStringArray(["Georgia", "Cambria", "Times New Roman", "serif"])
	b.font_weight = 600
	font_body = b
	var theme := Theme.new()
	theme.default_font = font_body
	theme.default_font_size = 20
	get_tree().root.theme = theme
	ThemeDB.fallback_font = font_body


func _add_action(action: String, keys: Array, joy_buttons: Array = []) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	for k in keys:
		var e := InputEventKey.new()
		e.physical_keycode = k
		InputMap.action_add_event(action, e)
	for b in joy_buttons:
		var j := InputEventJoypadButton.new()
		j.button_index = b
		InputMap.action_add_event(action, j)


func _setup_input() -> void:
	_add_action("left", [KEY_A, KEY_LEFT], [JOY_BUTTON_DPAD_LEFT])
	_add_action("right", [KEY_D, KEY_RIGHT], [JOY_BUTTON_DPAD_RIGHT])
	_add_action("up", [KEY_W, KEY_UP], [JOY_BUTTON_DPAD_UP])
	_add_action("down", [KEY_S, KEY_DOWN], [JOY_BUTTON_DPAD_DOWN])
	_add_action("jump", [KEY_SPACE, KEY_K], [JOY_BUTTON_A])
	_add_action("attack", [KEY_J, KEY_Z], [JOY_BUTTON_X])
	_add_action("special", [KEY_L, KEY_X], [JOY_BUTTON_Y])
	_add_action("pause", [KEY_ESCAPE, KEY_P], [JOY_BUTTON_START])
	_add_action("confirm", [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_J], [JOY_BUTTON_A])
	for a in ["left", "right"]:
		var m := InputEventJoypadMotion.new()
		m.axis = JOY_AXIS_LEFT_X
		m.axis_value = -1.0 if a == "left" else 1.0
		InputMap.action_add_event(a, m)


# ------------------------------------------------------------------ fluxo

func new_game(id: String) -> void:
	hero_id = id
	level_index = 0
	lives = START_LIVES
	gold = 0
	hero_hp = -1
	checkpoint = Vector2.INF
	goto_level(0)


func goto_level(i: int) -> void:
	level_index = i
	checkpoint = Vector2.INF
	change_scene(LEVELS[i]["scene"])


func next_level() -> void:
	if level_index + 1 >= LEVELS.size():
		hero_hp = -1
		change_scene("res://scenes/victory.tscn")
	else:
		goto_level(level_index + 1)


func lose_life() -> void:
	lives -= 1
	hero_hp = -1
	if lives < 0:
		change_scene("res://scenes/game_over.tscn")
	else:
		change_scene(LEVELS[level_index]["scene"])


func change_scene(path: String) -> void:
	get_tree().paused = false
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, 0.35)
	tw.tween_callback(func(): get_tree().change_scene_to_file(path))
	tw.tween_interval(0.05)
	tw.tween_property(_fade, "color:a", 0.0, 0.4)


func hero_data() -> Dictionary:
	return HEROES[hero_id]


func flash(color := Color(1, 1, 1, 0.5)) -> void:
	_fade.color = color
	create_tween().tween_property(_fade, "color:a", 0.0, 0.25)
