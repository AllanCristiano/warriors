extends Control
## Tela de titulo.

var _t := 0.0
var _crest: TextureRect


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	Audio.music("music_title")
	Menu.full_texture(self, "res://assets/kingdom/bg_title_sky.png")
	Menu.full_texture(self, "res://assets/kingdom/bg_night_far.png", Color(0.55, 0.35, 0.45))
	Menu.full_texture(self, "res://assets/kingdom/bg_sunset_far.png", Color(0.7, 0.55, 0.6))

	# desfile de herois e monstros no chao
	var ground := ColorRect.new()
	ground.color = Color(0.12, 0.08, 0.08)
	ground.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	ground.offset_top = -110
	add_child(ground)
	var stage := Node2D.new()
	add_child(stage)
	var lineup := [["cavaleiro", 150, 1], ["barbaro", 290, 1], ["sabio", 410, 1],
		["goblin_guerreiro", 880, -1], ["minotauro", 1010, -1], ["goblin_mago", 1140, -1]]
	for e in lineup:
		var s := SpriteLib.make_sprite(e[0])
		s.position = Vector2(e[1], 626)
		if e[2] < 0:
			s.set_facing(-1)
		s.play("idle")
		s.frame = randi() % 5
		stage.add_child(s)
	get_viewport().size_changed.connect(func(): stage.position.x = (size.x - 1280) / 2)
	stage.position.x = (size.x - 1280) / 2

	var vb := VBoxContainer.new()
	vb.set_anchors_preset(Control.PRESET_CENTER_TOP)
	vb.offset_left = -400
	vb.offset_right = 400
	vb.offset_top = 20
	vb.alignment = BoxContainer.ALIGNMENT_BEGIN
	vb.add_theme_constant_override("separation", 6)
	add_child(vb)
	_crest = TextureRect.new()
	_crest.texture = load("res://assets/kingdom/crest.png")
	_crest.custom_minimum_size = Vector2(150, 176)
	_crest.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_crest.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	vb.add_child(_crest)
	vb.add_child(Menu.title_label("Guerreiros do Reino", 84))
	var sub := Menu.title_label("~ A Queda das Hordas Goblins ~", 28, Color(1, 0.95, 0.8))
	vb.add_child(sub)
	var sp := Control.new()
	sp.custom_minimum_size.y = 18
	vb.add_child(sp)
	var buttons := VBoxContainer.new()
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	buttons.add_theme_constant_override("separation", 10)
	var bc := CenterContainer.new()
	bc.add_child(buttons)
	vb.add_child(bc)
	var play := Menu.wood_button("Iniciar Jornada")
	play.pressed.connect(func():
		Audio.play("confirm")
		Game.change_scene("res://scenes/select.tscn"))
	buttons.add_child(play)
	var quit := Menu.wood_button("Sair")
	quit.pressed.connect(func(): get_tree().quit())
	buttons.add_child(quit)
	play.grab_focus.call_deferred()


func _process(delta: float) -> void:
	_t += delta
	_crest.pivot_offset = _crest.size / 2
	_crest.rotation = sin(_t * 1.5) * 0.03
