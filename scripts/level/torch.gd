@tool
class_name Torch
extends Node2D
## Tocha de parede com chama em particulas e luz tremeluzente.

static var _light_tex: Texture2D

@export var light_energy := 1.0
@export var light_scale := 2.2

var _light: PointLight2D
var _t := 0.0


static func light_texture() -> Texture2D:
	if _light_tex == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		var gt := GradientTexture2D.new()
		gt.gradient = g
		gt.fill = GradientTexture2D.FILL_RADIAL
		gt.fill_from = Vector2(0.5, 0.5)
		gt.fill_to = Vector2(1.0, 0.5)
		gt.width = 256
		gt.height = 256
		_light_tex = gt
	return _light_tex


func _ready() -> void:
	var s := Sprite2D.new()
	s.texture = load("res://assets/kingdom/torch.png")
	s.offset = Vector2(0, 0)
	add_child(s)
	var p := CPUParticles2D.new()
	p.position = Vector2(0, -24)
	p.amount = 26
	p.lifetime = 0.5
	p.direction = Vector2(0, -1)
	p.spread = 14
	p.initial_velocity_min = 40
	p.initial_velocity_max = 80
	p.gravity = Vector2(0, -60)
	p.scale_amount_min = 5
	p.scale_amount_max = 9
	var curve := Curve.new()
	curve.add_point(Vector2(0, 1))
	curve.add_point(Vector2(1, 0.1))
	p.scale_amount_curve = curve
	var g := Gradient.new()
	g.set_color(0, Color(1, 0.95, 0.6, 1))
	g.set_color(1, Color(1, 0.25, 0.05, 0))
	g.add_point(0.4, Color(1, 0.6, 0.15, 0.9))
	p.color_ramp = g
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	p.material = mat
	add_child(p)
	_light = PointLight2D.new()
	_light.texture = light_texture()
	_light.color = Color(1, 0.7, 0.35)
	_light.energy = light_energy
	_light.texture_scale = light_scale
	_light.position = Vector2(0, -30)
	add_child(_light)
	_t = randf() * 10.0


func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	_t += delta
	_light.energy = light_energy * (0.85 + 0.15 * sin(_t * 13.0) * sin(_t * 7.3))
