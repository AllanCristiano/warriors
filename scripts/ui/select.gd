extends Control
## Tela de escolha do guerreiro.

const ORDER := ["cavaleiro", "barbaro", "sabio"]

var _index := 0
var _cards: Array[Control] = []
var _sprites: Array[AnimatedSprite2D] = []
var _locked := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	Audio.music("music_title")
	Menu.full_texture(self, "res://assets/kingdom/bg_dungeon_back.png", Color(0.8, 0.7, 0.75))
	var shade := ColorRect.new()
	shade.color = Color(0.05, 0.02, 0.02, 0.35)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(shade)

	var vb := VBoxContainer.new()
	vb.set_anchors_preset(Control.PRESET_FULL_RECT)
	vb.add_theme_constant_override("separation", 10)
	add_child(vb)
	var top := Control.new()
	top.custom_minimum_size.y = 8
	vb.add_child(top)
	vb.add_child(Menu.title_label("Escolha seu Guerreiro", 64))
	var info := Menu.title_label("<  >  para escolher     ENTER / clique para confirmar", 20, Color(1, 0.95, 0.85))
	info.add_theme_font_override("font", Game.font_body)
	vb.add_child(info)

	var center := CenterContainer.new()
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vb.add_child(center)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 26)
	center.add_child(row)
	for i in ORDER.size():
		row.add_child(_make_card(ORDER[i], i))
	var bottom := Control.new()
	bottom.custom_minimum_size.y = 20
	vb.add_child(bottom)

	var back := Menu.wood_button("Voltar", 20)
	back.custom_minimum_size = Vector2(150, 44)
	back.position = Vector2(20, 20)
	back.focus_mode = Control.FOCUS_NONE
	back.pressed.connect(func(): Game.change_scene("res://scenes/title.tscn"))
	add_child(back)
	_select(0, false)


func _make_card(id: String, i: int) -> Control:
	var d: Dictionary = Game.HEROES[id]
	var card := HUD.parchment_panel()
	card.custom_minimum_size = Vector2(370, 500)
	card.pivot_offset = Vector2(185, 250)
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.mouse_entered.connect(func(): _select(i))
	card.gui_input.connect(func(ev: InputEvent):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			_select(i)
			_confirm())
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 4)
	vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(vb)

	var stage := Control.new()
	stage.custom_minimum_size = Vector2(330, 200)
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vb.add_child(stage)
	var glow := TextureRect.new()
	glow.texture = Torch.light_texture()
	glow.modulate = Color(d["color"].r, d["color"].g, d["color"].b, 0.55)
	glow.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	glow.size = Vector2(260, 130)
	glow.position = Vector2(35, 120)
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stage.add_child(glow)
	var s := SpriteLib.make_sprite(d["sprite"])
	s.position = Vector2(165, 190)
	s.scale = Vector2(1.35, 1.35)
	s.play("idle")
	stage.add_child(s)
	_sprites.append(s)

	var name_l := HUD.style_label(Label.new(), 36, Color(0.96, 0.7, 0.32), Game.font_title)
	name_l.text = d["name"]
	name_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(name_l)
	var title_l := HUD.style_label(Label.new(), 18, Color(0.82, 0.72, 0.58))
	title_l.text = d["title"]
	title_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(title_l)

	for stat in d["stats"]:
		var r := HBoxContainer.new()
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := HUD.style_label(Label.new(), 17, Color(0.9, 0.82, 0.66))
		l.text = stat
		l.custom_minimum_size.x = 100
		r.add_child(l)
		for k in 5:
			var pip := ColorRect.new()
			pip.custom_minimum_size = Vector2(36, 14)
			pip.color = Color(0.75, 0.15, 0.12) if k < d["stats"][stat] else Color(0.3, 0.24, 0.22, 0.8)
			r.add_child(pip)
		r.add_theme_constant_override("separation", 5)
		vb.add_child(r)

	var desc := HUD.style_label(Label.new(), 14, Color(0.78, 0.72, 0.62))
	desc.text = d["desc"]
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.custom_minimum_size = Vector2(330, 90)
	vb.add_child(desc)
	_cards.append(card)
	return card


func _select(i: int, sound := true) -> void:
	if _locked:
		return
	if sound and i != _index:
		Audio.play("select", -4, 0.0)
	_index = i
	for k in _cards.size():
		var on := k == _index
		var tw := create_tween().set_parallel(true)
		tw.tween_property(_cards[k], "scale", Vector2.ONE * (1.06 if on else 0.94), 0.15)
		tw.tween_property(_cards[k], "modulate", Color.WHITE if on else Color(0.6, 0.55, 0.55), 0.15)
		_sprites[k].speed_scale = 1.0 if on else 0.4


func _unhandled_input(event: InputEvent) -> void:
	if _locked:
		return
	if event.is_action_pressed("left"):
		_select((_index + ORDER.size() - 1) % ORDER.size())
	elif event.is_action_pressed("right"):
		_select((_index + 1) % ORDER.size())
	elif event.is_action_pressed("confirm"):
		_confirm()


func _confirm() -> void:
	if _locked:
		return
	_locked = true
	Audio.play("confirm")
	Audio.play("swing", 0, 0.0)
	var s := _sprites[_index]
	if s.sprite_frames.has_animation("attack"):
		s.play("attack")
	else:
		s.play("walk")
	var card := _cards[_index]
	var tw := create_tween()
	tw.tween_property(card, "scale", Vector2.ONE * 1.12, 0.12)
	tw.tween_property(card, "scale", Vector2.ONE * 1.06, 0.2)
	tw.tween_interval(0.6)
	tw.tween_callback(func(): Game.new_game(ORDER[_index]))
