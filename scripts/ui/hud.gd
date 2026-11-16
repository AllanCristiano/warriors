class_name HUD
extends CanvasLayer
## Interface em jogo: vida, especial, vidas, ouro, barra do chefe, mensagens e pausa.

var hero: Hero
var _hp_bar: ProgressBar
var _hp_label: Label
var _sp_bar: ProgressBar
var _gold_label: Label
var _lives_box: HBoxContainer
var _boss_box: Control
var _boss_bar: ProgressBar
var _boss_name: Label
var _boss: Enemy
var _msg: Label
var _title: Label
var _subtitle: Label
var _pause: Control


static func bar_style(c: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(4)
	return s


static func make_bar(fill: Color, w: float, h: float) -> ProgressBar:
	var b := ProgressBar.new()
	b.custom_minimum_size = Vector2(w, h)
	b.show_percentage = false
	var bg := bar_style(Color(0.12, 0.07, 0.05, 0.9))
	bg.border_color = Color(0.85, 0.65, 0.25)
	bg.set_border_width_all(2)
	b.add_theme_stylebox_override("background", bg)
	b.add_theme_stylebox_override("fill", bar_style(fill))
	return b


static func place(c: Control, off: Vector2) -> void:
	c.offset_left = off.x
	c.offset_top = off.y
	c.offset_right = off.x
	c.offset_bottom = off.y


static func parchment_panel() -> PanelContainer:
	var p := PanelContainer.new()
	var sb := StyleBoxTexture.new()
	sb.texture = load("res://assets/kingdom/ui_parchment.png")
	sb.set_texture_margin_all(24)
	sb.set_content_margin_all(18)
	p.add_theme_stylebox_override("panel", sb)
	return p


static func style_label(l: Label, size: int, c := Color(0.25, 0.13, 0.05), font: Font = null, outline := 0, oc := Color.BLACK) -> Label:
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", c)
	if font:
		l.add_theme_font_override("font", font)
	if outline > 0:
		l.add_theme_constant_override("outline_size", outline)
		l.add_theme_color_override("font_outline_color", oc)
	return l


func _ready() -> void:
	layer = 10
	process_mode = Node.PROCESS_MODE_ALWAYS
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = get_tree().root.theme
	add_child(root)

	# painel do heroi
	var panel := parchment_panel()
	panel.position = Vector2(16, 12)
	root.add_child(panel)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 12)
	panel.add_child(hb)
	var portrait_box := Control.new()
	portrait_box.custom_minimum_size = Vector2(70, 70)
	portrait_box.clip_contents = true
	hb.add_child(portrait_box)
	var pr := TextureRect.new()
	pr.name = "Portrait"
	pr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	pr.size = Vector2(110, 110)
	pr.position = Vector2(-20, -6)
	portrait_box.add_child(pr)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 4)
	hb.add_child(vb)
	var name_l := style_label(Label.new(), 22, Color(0.35, 0.1, 0.05), Game.font_title)
	name_l.name = "HeroName"
	vb.add_child(name_l)
	var hp_row := HBoxContainer.new()
	vb.add_child(hp_row)
	_hp_bar = make_bar(Color(0.78, 0.12, 0.12), 220, 20)
	hp_row.add_child(_hp_bar)
	_hp_label = style_label(Label.new(), 16)
	_hp_label.custom_minimum_size.x = 80
	hp_row.add_child(_hp_label)
	_sp_bar = make_bar(Color(0.95, 0.75, 0.2), 220, 10)
	vb.add_child(_sp_bar)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	vb.add_child(row)
	_lives_box = HBoxContainer.new()
	row.add_child(_lives_box)
	var sp := Control.new()
	sp.custom_minimum_size.x = 20
	row.add_child(sp)
	var coin := TextureRect.new()
	coin.texture = load("res://assets/kingdom/coin.png")
	coin.custom_minimum_size = Vector2(24, 24)
	coin.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	row.add_child(coin)
	_gold_label = style_label(Label.new(), 20)
	row.add_child(_gold_label)

	# controles
	var help := style_label(Label.new(), 15, Color(1, 0.95, 0.8, 0.85), null, 5, Color(0.1, 0.05, 0.02))
	help.text = "A/D mover   ESPAÇO pular   J atacar   L especial   ESC pausa"
	help.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	place(help, Vector2(-560, -34))
	root.add_child(help)

	# barra do chefe
	_boss_box = VBoxContainer.new()
	_boss_box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	place(_boss_box, Vector2(-330, -96))
	_boss_box.visible = false
	root.add_child(_boss_box)
	_boss_name = style_label(Label.new(), 28, Color(1, 0.85, 0.5), Game.font_title, 8, Color(0.15, 0.03, 0.02))
	_boss_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_boss_name.custom_minimum_size.x = 660
	_boss_box.add_child(_boss_name)
	_boss_bar = make_bar(Color(0.6, 0.08, 0.12), 660, 22)
	_boss_box.add_child(_boss_bar)

	# mensagens
	_msg = style_label(Label.new(), 34, Color(1, 0.9, 0.55), Game.font_title, 10, Color(0.15, 0.06, 0.02))
	_msg.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg.custom_minimum_size.x = 1000
	place(_msg, Vector2(-500, 190))
	_msg.modulate.a = 0
	root.add_child(_msg)
	_title = style_label(Label.new(), 64, Color(1, 0.88, 0.5), Game.font_title, 14, Color(0.18, 0.06, 0.02))
	_title.set_anchors_preset(Control.PRESET_CENTER)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.custom_minimum_size.x = 1200
	place(_title, Vector2(-600, -150))
	_title.modulate.a = 0
	root.add_child(_title)
	_subtitle = style_label(Label.new(), 24, Color(1, 0.96, 0.85), null, 8, Color(0.1, 0.05, 0.02))
	_subtitle.set_anchors_preset(Control.PRESET_CENTER)
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_subtitle.custom_minimum_size.x = 1200
	place(_subtitle, Vector2(-600, -60))
	_subtitle.modulate.a = 0
	root.add_child(_subtitle)

	_build_pause(root)


func _build_pause(root: Control) -> void:
	_pause = ColorRect.new()
	(_pause as ColorRect).color = Color(0, 0, 0, 0.55)
	_pause.set_anchors_preset(Control.PRESET_FULL_RECT)
	_pause.visible = false
	root.add_child(_pause)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_pause.add_child(center)
	var p := parchment_panel()
	center.add_child(p)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 12)
	p.add_child(vb)
	var t := style_label(Label.new(), 48, Color(0.4, 0.1, 0.05), Game.font_title)
	t.text = "Pausa"
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(t)
	for item in [["Continuar", _toggle_pause], ["Reiniciar fase", _restart], ["Menu principal", _to_menu]]:
		var b := Menu.wood_button(item[0])
		b.pressed.connect(item[1])
		vb.add_child(b)


func bind_hero(h: Hero) -> void:
	hero = h
	h.hp_changed.connect(_on_hp)
	var d := Game.hero_data()
	(find_child("HeroName", true, false) as Label).text = d["name"]
	(find_child("Portrait", true, false) as TextureRect).texture = SpriteLib.portrait(d["sprite"])
	_on_hp(h.hp, h.max_hp)
	for c in _lives_box.get_children():
		c.queue_free()
	for i in maxi(0, Game.lives):
		var hr := TextureRect.new()
		hr.texture = load("res://assets/kingdom/heart.png")
		hr.custom_minimum_size = Vector2(26, 24)
		hr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_lives_box.add_child(hr)


func _on_hp(hp: int, max_hp: int) -> void:
	_hp_bar.max_value = max_hp
	var tw := create_tween()
	tw.tween_property(_hp_bar, "value", float(hp), 0.2)
	_hp_label.text = " %d/%d" % [hp, max_hp]


func _process(_delta: float) -> void:
	_gold_label.text = str(Game.gold)
	if hero:
		var cd: float = hero.data["special_cd"]
		_sp_bar.max_value = cd
		_sp_bar.value = cd - maxf(0.0, hero.special_timer)
		_sp_bar.modulate = Color(1, 1, 1) if hero.special_timer <= 0 else Color(0.6, 0.6, 0.6)
	if _boss and is_instance_valid(_boss):
		_boss_bar.value = lerpf(_boss_bar.value, float(maxi(0, _boss.hp)), 0.2)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		_toggle_pause()


func _toggle_pause() -> void:
	var p := not get_tree().paused
	get_tree().paused = p
	_pause.visible = p
	if p:
		Audio.play("select")
		var first := _pause.find_children("*", "Button", true, false)
		if first.size() > 0:
			(first[0] as Button).grab_focus()


func _restart() -> void:
	get_tree().paused = false
	Game.hero_hp = -1
	Game.change_scene(Game.LEVELS[Game.level_index]["scene"])


func _to_menu() -> void:
	get_tree().paused = false
	Game.change_scene("res://scenes/title.tscn")


func show_boss(b: Enemy) -> void:
	_boss = b
	_boss_name.text = b.cfg["name"]
	_boss_bar.max_value = b.max_hp
	_boss_bar.value = 0
	_boss_box.visible = true
	_boss_box.modulate.a = 0
	create_tween().tween_property(_boss_box, "modulate:a", 1.0, 0.6)


func hide_boss() -> void:
	var tw := create_tween()
	tw.tween_property(_boss_box, "modulate:a", 0.0, 1.0)
	tw.tween_callback(func(): _boss_box.visible = false)


func message(text: String, time := 2.0) -> void:
	_msg.text = text
	var tw := create_tween()
	tw.tween_property(_msg, "modulate:a", 1.0, 0.3)
	tw.tween_interval(time)
	tw.tween_property(_msg, "modulate:a", 0.0, 0.5)


func show_title(t: String, sub: String) -> void:
	_title.text = t
	_subtitle.text = sub
	for l in [_title, _subtitle]:
		var tw := create_tween()
		tw.tween_interval(0.3)
		tw.tween_property(l, "modulate:a", 1.0, 0.8)
		tw.tween_interval(2.0)
		tw.tween_property(l, "modulate:a", 0.0, 0.8)
