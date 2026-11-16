class_name Atmosphere
extends CanvasLayer
## Clima e pos-processamento da fase: brasas, chuva com relampagos, poeira e vinheta.

var weather := ""
var _flash: ColorRect
var _next_bolt := 4.0


func _init(w: String) -> void:
	weather = w


func _ready() -> void:
	layer = 3
	var vp := Vector2(1280, 720)
	match weather:
		"brasas":
			var p := _p(90, 5.0, Vector2(vp.x * 0.6, 10), Vector2(vp.x / 2, vp.y + 20))
			p.direction = Vector2(0.3, -1)
			p.spread = 25
			p.initial_velocity_min = 40
			p.initial_velocity_max = 110
			p.gravity = Vector2(10, -6)
			p.texture = Torch.soft_dot()
			p.scale_amount_min = 0.12
			p.scale_amount_max = 0.3
			p.color_ramp = _grad(Color(1, 0.75, 0.3, 1), Color(1, 0.25, 0.05, 0))
			_add(p)
			var ash := _p(50, 9.0, Vector2(vp.x * 0.7, 10), Vector2(vp.x / 2, -20))
			ash.direction = Vector2(-0.2, 1)
			ash.initial_velocity_min = 15
			ash.initial_velocity_max = 40
			ash.gravity = Vector2(-4, 6)
			ash.scale_amount_min = 1.5
			ash.scale_amount_max = 3
			ash.color = Color(0.6, 0.58, 0.6, 0.6)
			ash.material = null
			add_child(ash)
		"chuva":
			var r := _p(420, 0.9, Vector2(vp.x * 0.75, 10), Vector2(vp.x / 2 + 150, -30))
			r.direction = Vector2(-0.25, 1)
			r.spread = 2
			r.initial_velocity_min = 900
			r.initial_velocity_max = 1150
			r.gravity = Vector2.ZERO
			r.scale_amount_min = 1
			r.scale_amount_max = 1
			r.texture = _streak()
			r.color = Color(0.7, 0.75, 0.9, 0.35)
			r.material = null
			r.particle_flag_align_y = true
			add_child(r)
			_flash = ColorRect.new()
			_flash.color = Color(0.8, 0.85, 1.0, 0.0)
			_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
			_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
			add_child(_flash)
		"poeira":
			var d := _p(60, 10.0, Vector2(vp.x / 2, vp.y / 2), vp / 2)
			d.direction = Vector2(1, -0.2)
			d.spread = 180
			d.initial_velocity_min = 4
			d.initial_velocity_max = 18
			d.gravity = Vector2.ZERO
			d.texture = Torch.soft_dot()
			d.scale_amount_min = 0.1
			d.scale_amount_max = 0.25
			d.color_ramp = _grad(Color(0.7, 0.75, 1.0, 0.0), Color(0.7, 0.75, 1.0, 0.0), Color(0.7, 0.8, 1.0, 0.5))
			_add(d)
	# vinheta
	var v := ColorRect.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/vignette.gdshader")
	v.material = mat
	add_child(v)


func _p(amount: int, life: float, extents: Vector2, pos: Vector2) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = amount
	p.lifetime = life
	p.preprocess = life
	p.position = pos
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = extents
	return p


func _add(p: CPUParticles2D) -> void:
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	p.material = mat
	add_child(p)


func _grad(a: Color, b: Color, mid = null) -> Gradient:
	var g := Gradient.new()
	g.set_color(0, a)
	g.set_color(1, b)
	if mid != null:
		g.add_point(0.5, mid)
	return g


func _streak() -> Texture2D:
	var img := Image.create(2, 26, false, Image.FORMAT_RGBA8)
	for y in 26:
		img.set_pixel(0, y, Color(1, 1, 1, y / 26.0))
		img.set_pixel(1, y, Color(1, 1, 1, y / 40.0))
	return ImageTexture.create_from_image(img)


func _process(delta: float) -> void:
	if _flash == null:
		return
	_next_bolt -= delta
	if _next_bolt <= 0:
		_next_bolt = randf_range(5.0, 11.0)
		var tw := create_tween()
		tw.tween_property(_flash, "color:a", 0.45, 0.04)
		tw.tween_property(_flash, "color:a", 0.05, 0.08)
		tw.tween_property(_flash, "color:a", 0.35, 0.04)
		tw.tween_property(_flash, "color:a", 0.0, 0.5)
		get_tree().create_timer(randf_range(0.3, 0.9)).timeout.connect(func(): Audio.play("thunder", -2, 0.15))
