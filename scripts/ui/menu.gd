class_name Menu
extends Control
## Utilitarios de UI com estilo medieval (botoes de madeira, fundos).

static func wood_button(text: String, font_size := 26) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(300, 56)
	b.focus_mode = Control.FOCUS_ALL
	var states := {"normal": "ui_button", "hover": "ui_button_hover", "pressed": "ui_button", "focus": "ui_button_hover"}
	for st in states:
		var sb := StyleBoxTexture.new()
		sb.texture = load("res://assets/kingdom/%s.png" % states[st])
		sb.set_texture_margin_all(14)
		sb.set_content_margin_all(10)
		if st == "focus":
			sb.modulate_color = Color(1.15, 1.05, 0.85)
		b.add_theme_stylebox_override(st, sb)
	b.add_theme_font_override("font", Game.font_title)
	b.add_theme_font_size_override("font_size", font_size)
	for c in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color"]:
		b.add_theme_color_override(c, Color(1, 0.9, 0.6) if c != "font_color" else Color(0.98, 0.86, 0.6))
	b.add_theme_color_override("font_outline_color", Color(0.15, 0.07, 0.03))
	b.add_theme_constant_override("outline_size", 6)
	b.mouse_entered.connect(func(): b.grab_focus())
	b.focus_entered.connect(func(): Audio.play("select", -8, 0.0))
	return b


static func full_texture(parent: Control, path: String, mod := Color.WHITE) -> TextureRect:
	var t := TextureRect.new()
	t.texture = load(path)
	t.set_anchors_preset(Control.PRESET_FULL_RECT)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	t.modulate = mod
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(t)
	return t


static func title_label(text: String, size: int, c := Color(1, 0.86, 0.45)) -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	HUD.style_label(l, size, c, Game.font_title, 14, Color(0.2, 0.06, 0.02))
	return l
