class_name Pickup
extends Area2D
## Moedas de ouro e pocoes de cura.

var kind := "coin"
var vel := Vector2.ZERO
var _landed := false
var _t := 0.0
var _sprite: Sprite2D
var _base_y := 0.0


static func drop(parent: Node, k: String, pos: Vector2) -> Pickup:
	var p := Pickup.new()
	p.kind = k
	p.position = pos
	p.vel = Vector2(randf_range(-180, 180), randf_range(-520, -320))
	parent.add_child.call_deferred(p)
	return p


func _ready() -> void:
	z_index = 8
	collision_layer = 0
	collision_mask = 2
	var cs := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = 20
	cs.shape = c
	add_child(cs)
	_sprite = Sprite2D.new()
	_sprite.texture = load("res://assets/kingdom/%s.png" % kind)
	add_child(_sprite)
	body_entered.connect(_on_body)
	_t = randf() * 3.0
	if vel == Vector2.ZERO:
		_landed = true
		_base_y = position.y


func _physics_process(delta: float) -> void:
	_t += delta
	if not _landed:
		vel.y += 1500 * delta
		var space := get_world_2d().direct_space_state
		var step := vel * delta
		if vel.y > 0:
			var q := PhysicsRayQueryParameters2D.create(global_position, global_position + Vector2(0, step.y + 18), 1)
			var hit := space.intersect_ray(q)
			if not hit.is_empty():
				global_position.y = hit.position.y - 20
				_landed = true
				_base_y = position.y
				return
		position += step
		if position.y > 3000:
			queue_free()
	else:
		position.y = _base_y + sin(_t * 3.0) * 4.0
	if kind == "coin":
		_sprite.scale.x = absf(cos(_t * 3.0))


func _on_body(b: Node) -> void:
	if not b is Hero or b.state == "dead":
		return
	match kind:
		"coin":
			Game.gold += 1
			Audio.play("coin", -4)
		"potion":
			b.heal(45)
			Audio.play("potion")
	queue_free()
