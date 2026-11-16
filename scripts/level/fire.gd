@tool
class_name Fire
extends Node2D
## Fogueira/incendio: chamas, fumaca e luz tremeluzente. Origem = base do fogo.

@export var size := 1.0:
	set(v):
		size = v
		if is_inside_tree():
			_build()
@export var smoke := true

var _light: PointLight2D
var _t := 0.0


func _ready() -> void:
	_build()


func _build() -> void:
	for c in get_children():
		c.free()
	if smoke:
		var sm := _particles(18, 2.4, Color(0.12, 0.1, 0.1, 0.55), Color(0.05, 0.05, 0.06, 0.0), 40.0, 80.0, 30.0, 60.0)
		sm.position = Vector2(0, -40 * size)
		sm.gravity = Vector2(14, -20)
		sm.material = null
		add_child(sm)
	var fl := _particles(34, 0.7, Color(1, 0.62, 0.22, 0.5), Color(0.8, 0.12, 0.02, 0.0), 60.0, 140.0, 14.0, 26.0)
	fl.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	fl.emission_rect_extents = Vector2(26 * size, 6)
	add_child(fl)
	var em := _particles(10, 1.6, Color(1, 0.6, 0.2, 1), Color(1, 0.3, 0.05, 0), 80.0, 180.0, 2.0, 4.0)
	em.spread = 40
	add_child(em)
	_light = PointLight2D.new()
	_light.texture = Torch.light_texture()
	_light.color = Color(1, 0.5, 0.2)
	_light.energy = 1.3
	_light.texture_scale = 3.2 * size
	_light.position = Vector2(0, -40 * size)
	add_child(_light)


func _particles(amount: int, life: float, c0: Color, c1: Color, vmin: float, vmax: float, smin: float, smax: float) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = amount
	p.lifetime = life
	p.direction = Vector2(0, -1)
	p.spread = 18
	p.initial_velocity_min = vmin * size
	p.initial_velocity_max = vmax * size
	p.gravity = Vector2(0, -40)
	p.texture = Torch.soft_dot()
	p.scale_amount_min = smin * size / 16.0
	p.scale_amount_max = smax * size / 16.0
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.6))
	curve.add_point(Vector2(0.3, 1))
	curve.add_point(Vector2(1, 0.1))
	p.scale_amount_curve = curve
	var g := Gradient.new()
	g.set_color(0, c0)
	g.set_color(1, c1)
	p.color_ramp = g
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	p.material = mat
	p.preprocess = life
	return p


func _process(delta: float) -> void:
	if Engine.is_editor_hint() or _light == null:
		return
	_t += delta
	_light.energy = 1.3 * (0.8 + 0.2 * sin(_t * 11.0) * sin(_t * 5.3 + 1.0))
