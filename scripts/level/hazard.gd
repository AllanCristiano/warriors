@tool
class_name Hazard
extends Area2D
## Perigos: espinhos (dano + quique), agua (fosso) e lava. Origem = canto sup. esquerdo.

@export_enum("espinhos", "agua", "lava") var kind: String = "espinhos":
	set(v):
		kind = v
		_refresh()
@export var width := 192.0:
	set(v):
		width = v
		_refresh()
@export var depth := 120.0:
	set(v):
		depth = v
		_refresh()

var _tex: Texture2D
var _shape: CollisionShape2D
var _t := 0.0


func _ready() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	_refresh()
	if Engine.is_editor_hint():
		return
	collision_layer = 0
	collision_mask = 2
	if kind == "lava":
		var l := PointLight2D.new()
		l.texture = Torch.light_texture()
		l.color = Color(1, 0.45, 0.1)
		l.energy = 1.2
		l.texture_scale = maxf(1.0, width / 200.0)
		l.position = Vector2(width / 2, 0)
		add_child(l)


func _refresh() -> void:
	if not is_inside_tree():
		return
	var tex_name: String = {"espinhos": "spikes", "agua": "tile_water", "lava": "tile_lava"}[kind]
	_tex = load("res://assets/kingdom/%s.png" % tex_name)
	if _shape == null:
		_shape = CollisionShape2D.new()
		add_child(_shape)
	var rs := RectangleShape2D.new()
	var h := 26.0 if kind == "espinhos" else depth
	rs.size = Vector2(width, h)
	_shape.shape = rs
	_shape.position = Vector2(width / 2, h / 2 + (10.0 if kind == "espinhos" else 20.0))
	queue_redraw()


func _process(delta: float) -> void:
	if kind != "espinhos":
		_t += delta
		queue_redraw()


func _physics_process(_delta: float) -> void:
	if Engine.is_editor_hint():
		return
	for b in get_overlapping_bodies():
		if b is Hero and b.state != "dead":
			if kind == "espinhos":
				if b.take_damage(20, b.global_position + Vector2(0, 50)):
					b.velocity.y = -700
			else:
				Audio.play("fire" if kind == "lava" else "break", -4)
				b.fall_in_pit()


func _draw() -> void:
	if _tex == null:
		return
	if kind == "espinhos":
		draw_texture_rect(_tex, Rect2(0, 0, width, 36), true)
	else:
		var off := Vector2(fmod(_t * 20.0, 128.0), 0)
		draw_texture_rect_region(_tex, Rect2(0, 0, width, depth), Rect2(off, Vector2(width, depth)))
		var wave := Color(1, 0.85, 0.4, 0.8) if kind == "lava" else Color(0.75, 0.9, 1, 0.7)
		var pts := PackedVector2Array()
		for i in int(width / 8) + 1:
			var x := i * 8.0
			pts.append(Vector2(x, sin(x * 0.05 + _t * 3.0) * 3.0))
		draw_polyline(pts, wave, 3.0)
