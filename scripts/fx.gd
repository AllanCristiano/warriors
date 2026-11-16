class_name FX
extends Node2D
## Efeitos visuais simples desenhados por codigo (cortes, ondas, faiscas, poeira).

var kind := ""
var t := 0.0
var dur := 0.3
var dir := 1.0
var color := Color.WHITE
var size := 1.0
var _parts: Array = []


static func spawn(parent: Node, k: String, pos: Vector2, d := 1.0, c := Color.WHITE, s := 1.0) -> FX:
	var f := FX.new()
	f.kind = k
	f.dir = d
	f.color = c
	f.size = s
	f.global_position = pos
	f.z_index = 20
	parent.add_child(f)
	return f


static func text(parent: Node, pos: Vector2, msg: String, c := Color(1, 0.95, 0.6), font_size := 26) -> void:
	var l := Label.new()
	l.text = msg
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", c)
	l.add_theme_color_override("font_outline_color", Color(0.1, 0.05, 0.02))
	l.add_theme_constant_override("outline_size", 6)
	l.z_index = 30
	l.position = pos + Vector2(-40 + randf_range(-10, 10), -20)
	parent.add_child(l)
	var tw := l.create_tween()
	tw.set_parallel(true)
	tw.tween_property(l, "position:y", l.position.y - 60, 0.8).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(l, "modulate:a", 0.0, 0.4).set_delay(0.45)
	tw.chain().tween_callback(l.queue_free)


static func ghost(parent: Node, sprite: AnimatedSprite2D) -> void:
	var s := Sprite2D.new()
	s.texture = sprite.sprite_frames.get_frame_texture(sprite.animation, sprite.frame)
	s.flip_h = sprite.flip_h
	s.offset = sprite.offset
	s.global_position = sprite.global_position
	s.modulate = Color(0.6, 0.8, 1.0, 0.6)
	s.z_index = 4
	parent.add_child(s)
	var tw := s.create_tween()
	tw.tween_property(s, "modulate:a", 0.0, 0.25)
	tw.tween_callback(s.queue_free)


func _ready() -> void:
	match kind:
		"slash", "slash_up": dur = 0.18
		"shock": dur = 0.5
		"spark":
			dur = 0.25
			for i in 8:
				_parts.append(Vector2.from_angle(randf() * TAU) * randf_range(60, 160))
		"dust", "debris":
			dur = 0.5 if kind == "dust" else 0.7
			for i in (10 if kind == "dust" else 12):
				_parts.append([Vector2(randf_range(-30, 30), randf_range(-10, 0)) * size,
					Vector2(randf_range(-160, 160), randf_range(-320, -60)) * size, randf_range(3, 8) * size])
		"boom": dur = 0.35
		"heal": dur = 0.6


func _process(delta: float) -> void:
	t += delta
	for p in _parts:
		if p is Array:
			p[0] += p[1] * delta
			p[1].y += 900 * delta
	queue_redraw()
	if t >= dur:
		queue_free()


func _draw() -> void:
	var k := t / dur
	match kind:
		"slash", "slash_up":
			var a := 1.0 - k
			var start := -1.2 if kind == "slash" else 1.0
			var end := 1.0 if kind == "slash" else -1.2
			for i in 3:
				var r := (70.0 + i * 8.0) * size
				var w := (10.0 - i * 3.0) * size
				var a0 := start
				var a1 := lerpf(start, end, minf(1.0, k * 2.5))
				if dir < 0:
					a0 = PI - a0
					a1 = PI - a1
				draw_arc(Vector2.ZERO, r, minf(a0, a1), maxf(a0, a1), 20, Color(color.r, color.g, color.b, a * (0.9 - i * 0.25)), w, true)
		"shock":
			var r := lerpf(20, 230 * size, k)
			var c := Color(color.r, color.g, color.b, 1.0 - k)
			draw_arc(Vector2.ZERO, r, PI, TAU, 32, c, 10 * (1.0 - k) + 2, true)
			draw_line(Vector2(-r, 0), Vector2(r, 0), c, 6 * (1.0 - k) + 1)
		"spark":
			for v in _parts:
				var p: Vector2 = v * k
				draw_line(p, p + v.normalized() * 14 * (1.0 - k), Color(color.r, color.g, color.b, 1.0 - k), 3)
		"dust", "debris":
			for p in _parts:
				var c := color
				c.a = 1.0 - k
				if kind == "dust":
					draw_circle(p[0], p[2] * (1.0 + k), c)
				else:
					draw_rect(Rect2(p[0], Vector2(p[2], p[2] * 0.6)), c)
		"boom":
			draw_circle(Vector2.ZERO, lerpf(10, 50 * size, k), Color(1, 0.6, 0.2, 1.0 - k))
			draw_circle(Vector2.ZERO, lerpf(5, 30 * size, k), Color(1, 0.95, 0.6, 1.0 - k))
		"heal":
			for i in 6:
				var p := Vector2(cos(i * 1.7) * 30, -k * 80 - i * 12)
				draw_string(ThemeDB.fallback_font, p, "+", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, Color(0.5, 1, 0.5, 1.0 - k))
