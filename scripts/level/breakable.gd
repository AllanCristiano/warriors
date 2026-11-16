@tool
class_name Breakable
extends StaticBody2D
## Barril ou caixote que quebra com golpes e solta saque. Origem = base.

@export_enum("barrel", "crate") var kind: String = "crate":
	set(v):
		kind = v
		_build()
@export_enum("aleatorio", "moedas", "pocao", "nada") var loot: String = "aleatorio"

var hp := 2
var _sprite: Sprite2D
var _size := Vector2(64, 64)


func _ready() -> void:
	_build()
	if Engine.is_editor_hint():
		return
	add_to_group("damageable")
	add_to_group("breakable")
	collision_layer = 1
	collision_mask = 0


func _build() -> void:
	if not is_inside_tree():
		return
	for c in get_children():
		c.free()
	_sprite = Sprite2D.new()
	_sprite.texture = load("res://assets/kingdom/%s.png" % kind)
	_size = _sprite.texture.get_size()
	_sprite.offset = Vector2(0, -_size.y / 2)
	add_child(_sprite)
	var cs := CollisionShape2D.new()
	var rs := RectangleShape2D.new()
	rs.size = _size - Vector2(8, 4)
	cs.shape = rs
	cs.position = Vector2(0, -rs.size.y / 2)
	add_child(cs)


func get_hurt_rect() -> Rect2:
	return Rect2(global_position.x - _size.x / 2, global_position.y - _size.y, _size.x, _size.y)


func take_damage(_amount: int, _from: Vector2, _knock := Vector2.ZERO) -> bool:
	hp -= 1
	var tw := create_tween()
	tw.tween_property(_sprite, "rotation", 0.12, 0.05)
	tw.tween_property(_sprite, "rotation", 0.0, 0.08)
	if hp > 0:
		Audio.play("hit", -6)
		return true
	Audio.play("break")
	FX.spawn(get_parent(), "debris", global_position + Vector2(0, -_size.y / 2), 1, Color(0.5, 0.33, 0.18), 1.2)
	var l := loot
	if l == "aleatorio":
		l = ["moedas", "moedas", "pocao", "nada"][randi() % 4]
	match l:
		"moedas":
			for i in randi_range(2, 4):
				Pickup.drop(get_parent(), "coin", global_position + Vector2(0, -30))
		"pocao":
			Pickup.drop(get_parent(), "potion", global_position + Vector2(0, -30))
	remove_from_group("damageable")
	queue_free()
	return true
