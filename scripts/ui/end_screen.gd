extends Control
## Tela final: vitoria (reino salvo) ou derrota (fim de jornada).

@export var victory := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if victory:
		Audio.music("music_title")
		Audio.play("victory")
		Menu.full_texture(self, "res://assets/kingdom/bg_sky_day.png")
		Menu.full_texture(self, "res://assets/kingdom/bg_day_far.png")
		Menu.full_texture(self, "res://assets/kingdom/bg_day_mid.png")
	else:
		Audio.music("music_dungeon")
		Menu.full_texture(self, "res://assets/kingdom/bg_sky_night.png", Color(0.7, 0.5, 0.5))
		Menu.full_texture(self, "res://assets/kingdom/bg_night_far.png", Color(0.6, 0.4, 0.4))

	var stage := Node2D.new()
	add_child(stage)
	var d := Game.hero_data()
	var s := SpriteLib.make_sprite(d["sprite"])
	s.scale = Vector2(1.5, 1.5)
	s.play("idle")
	stage.add_child(s)
	if not victory:
		s.modulate = Color(0.5, 0.45, 0.5)
		s.rotation = -PI / 2
	var place_hero := func(): s.position = Vector2(size.x / 2, size.y - 80 if victory else size.y - 40)
	place_hero.call()
	resized.connect(place_hero)

	var vb := VBoxContainer.new()
	vb.set_anchors_preset(Control.PRESET_CENTER_TOP)
	vb.offset_left = -500
	vb.offset_right = 500
	vb.offset_top = 40
	vb.add_theme_constant_override("separation", 10)
	add_child(vb)
	if victory:
		var crest := TextureRect.new()
		crest.texture = load("res://assets/kingdom/crest.png")
		crest.custom_minimum_size = Vector2(120, 140)
		crest.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		crest.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		vb.add_child(crest)
		vb.add_child(Menu.title_label("O Reino esta salvo!", 76))
		var l := Menu.title_label("%s derrotou Cerbero e as hordas goblins.\nO Rei ergue sua taca em sua honra!\nOuro coletado: %d" % [d["name"], Game.gold], 24, Color(1, 0.97, 0.88))
		l.add_theme_font_override("font", Game.font_body)
		vb.add_child(l)
	else:
		vb.add_child(Menu.title_label("Fim da Jornada", 84, Color(0.95, 0.4, 0.3)))
		var l := Menu.title_label("As trevas tomaram o reino... mas a lenda pode continuar.\nOuro coletado: %d" % Game.gold, 24, Color(1, 0.92, 0.85))
		l.add_theme_font_override("font", Game.font_body)
		vb.add_child(l)
	var bc := CenterContainer.new()
	var buttons := VBoxContainer.new()
	buttons.add_theme_constant_override("separation", 10)
	bc.add_child(buttons)
	vb.add_child(bc)
	if not victory:
		var retry := Menu.wood_button("Tentar novamente")
		retry.pressed.connect(func():
			Game.lives = Game.START_LIVES
			Game.hero_hp = -1
			Game.goto_level(Game.level_index))
		buttons.add_child(retry)
	var other := Menu.wood_button("Outro guerreiro")
	other.pressed.connect(func(): Game.change_scene("res://scenes/select.tscn"))
	buttons.add_child(other)
	var menu := Menu.wood_button("Menu principal")
	menu.pressed.connect(func(): Game.change_scene("res://scenes/title.tscn"))
	buttons.add_child(menu)
	(buttons.get_child(0) as Button).grab_focus.call_deferred()
