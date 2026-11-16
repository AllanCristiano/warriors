@tool
class_name Checkpoint
extends Area2D
## Bandeira do Reino: ao tocar vira ponto de renascimento e cura um pouco.

var active := false
var _sprite: Sprite2D


func _ready() -> void:
	_sprite = Sprite2D.new()
	_sprite.texture = load("res://assets/kingdom/flag_off.png")
	_sprite.offset = Vector2(20, -100)
	add_child(_sprite)
	var cs := CollisionShape2D.new()
	var rs := RectangleShape2D.new()
	rs.size = Vector2(80, 200)
	cs.shape = rs
	cs.position = Vector2(0, -100)
	add_child(cs)
	if Engine.is_editor_hint():
		return
	collision_layer = 0
	collision_mask = 2
	body_entered.connect(_on_body)
	if Game.checkpoint.distance_to(global_position) < 5:
		_set_active(false)


func _on_body(b: Node) -> void:
	if active or not b is Hero:
		return
	_set_active(true)
	Game.checkpoint = global_position
	b.heal(25)


func _set_active(with_fx: bool) -> void:
	active = true
	_sprite.texture = load("res://assets/kingdom/flag_on.png")
	if with_fx:
		Audio.play("checkpoint")
		FX.text(get_parent(), global_position + Vector2(-60, -220), "Bandeira erguida!", Color(1, 0.85, 0.4), 26)
		var tw := create_tween()
		_sprite.scale = Vector2(1.2, 0.8)
		tw.tween_property(_sprite, "scale", Vector2.ONE, 0.4).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
