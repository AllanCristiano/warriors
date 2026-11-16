@tool
class_name BossArena
extends Area2D
## Ao entrar, tranca a camera entre "arena_left" e "arena_right" e acorda o chefe.

@export var boss_path: NodePath
@export var arena_width := 1400.0:
	set(v):
		arena_width = v
		queue_redraw()
@export var trigger_offset := 260.0

var _triggered := false


func _ready() -> void:
	if Engine.is_editor_hint():
		return
	collision_layer = 0
	collision_mask = 2
	var cs := CollisionShape2D.new()
	var rs := RectangleShape2D.new()
	rs.size = Vector2(arena_width - trigger_offset, 2000)
	cs.shape = rs
	cs.position = Vector2(trigger_offset + rs.size.x / 2, -900)
	add_child(cs)
	body_entered.connect(_on_body)


func _draw() -> void:
	if Engine.is_editor_hint():
		draw_rect(Rect2(0, -720, arena_width, 720), Color(1, 0.2, 0.2, 0.12))
		draw_rect(Rect2(0, -720, arena_width, 720), Color(1, 0.2, 0.2, 0.8), false, 4)
		draw_line(Vector2(trigger_offset, -720), Vector2(trigger_offset, 0), Color(1, 1, 0, 0.8), 3)
		draw_string(ThemeDB.fallback_font, Vector2(20, -680), "ARENA DO CHEFE", HORIZONTAL_ALIGNMENT_LEFT, -1, 32, Color(1, 0.3, 0.3))


func _on_body(b: Node) -> void:
	if _triggered or not b is Hero:
		return
	var boss := get_node_or_null(boss_path) as Enemy
	if boss == null or boss.state == "dead":
		return
	_triggered = true
	var level := get_tree().current_scene
	if level.has_method("start_boss"):
		level.start_boss(boss, global_position.x, global_position.x + arena_width)
