@tool
class_name Goal
extends Area2D
## Saida da fase (portao do castelo). Fica trancada ate o chefe da fase cair.

@export var texture_name := "castle_gate":
	set(v):
		texture_name = v
		_build()
@export var requires_boss := true

var _done := false
var _arrow: Label


func _ready() -> void:
	_build()
	if Engine.is_editor_hint():
		return
	collision_layer = 0
	collision_mask = 2
	body_entered.connect(_on_body)
	_arrow = Label.new()
	_arrow.text = "SAÍDA  >>"
	_arrow.add_theme_font_size_override("font_size", 30)
	_arrow.add_theme_font_override("font", Game.font_title)
	_arrow.add_theme_color_override("font_color", Color(1, 0.85, 0.3))
	_arrow.add_theme_color_override("font_outline_color", Color(0.15, 0.08, 0.02))
	_arrow.add_theme_constant_override("outline_size", 8)
	_arrow.position = Vector2(-70, -440)
	_arrow.visible = false
	add_child(_arrow)


func _build() -> void:
	if not is_inside_tree():
		return
	for c in get_children():
		c.free()
	var s := Sprite2D.new()
	s.texture = load("res://assets/kingdom/%s.png" % texture_name)
	s.offset = Vector2(0, -s.texture.get_height() / 2.0)
	s.z_index = -1
	add_child(s)
	var cs := CollisionShape2D.new()
	var rs := RectangleShape2D.new()
	rs.size = Vector2(120, 200)
	cs.shape = rs
	cs.position = Vector2(0, -100)
	add_child(cs)


func _process(_delta: float) -> void:
	if Engine.is_editor_hint() or _arrow == null:
		return
	var open := _is_open()
	_arrow.visible = open and not _done
	if open:
		_arrow.position.y = -440 + sin(Time.get_ticks_msec() * 0.006) * 8


func _is_open() -> bool:
	if not requires_boss:
		return true
	return get_tree().get_nodes_in_group("bosses").filter(func(b): return b.state != "dead").is_empty()


func _on_body(b: Node) -> void:
	if _done or not b is Hero:
		return
	if not _is_open():
		FX.text(get_parent(), global_position + Vector2(-120, -260), "Derrote o chefe primeiro!", Color(1, 0.5, 0.4), 24)
		return
	_done = true
	var level := get_tree().current_scene
	if level.has_method("complete"):
		level.complete()
