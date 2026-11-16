class_name Projectile
extends Area2D
## Projeteis: dardo do sabio, boleadeira, orbe magico, bola de fogo, onda de choque.

const TEX := {
	"dart": "res://assets/kingdom/proj_dart.png",
	"bola": "res://assets/kingdom/proj_bola.png",
	"orb": "res://assets/kingdom/proj_orb.png",
	"fireball": "res://assets/kingdom/proj_fireball.png",
}

var kind := "dart"
var vel := Vector2.ZERO
var grav := 0.0
var damage := 10
var target := "player"
var life := 3.5
var _sprite: Sprite2D
var _t := 0.0


static func spawn(parent: Node, k: String, pos: Vector2, v: Vector2, dmg: int, tgt: String) -> Projectile:
	var p := Projectile.new()
	p.kind = k
	p.vel = v
	p.damage = dmg
	p.target = tgt
	p.position = pos
	parent.add_child(p)
	return p


func _ready() -> void:
	z_index = 10
	collision_layer = 0
	var world := 0 if kind == "shock" else 1
	collision_mask = world | (2 if target == "player" else 4)
	var cs := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = {"dart": 8.0, "bola": 12.0, "orb": 13.0, "fireball": 16.0, "shock": 20.0}.get(kind, 10.0)
	cs.shape = c
	add_child(cs)
	if TEX.has(kind):
		_sprite = Sprite2D.new()
		_sprite.texture = load(TEX[kind])
		add_child(_sprite)
	if kind == "shock":
		life = 1.3
	if kind in ["orb", "fireball"]:
		var l := PointLight2D.new()
		l.texture = Torch.light_texture()
		l.color = Color(0.5, 1, 0.5) if kind == "orb" else Color(1, 0.6, 0.2)
		l.energy = 0.9
		l.texture_scale = 0.6
		add_child(l)
	body_entered.connect(_on_body)


func _physics_process(delta: float) -> void:
	_t += delta
	vel.y += grav * delta
	position += vel * delta
	if kind == "bola":
		rotation += 14.0 * delta
	elif kind != "shock":
		rotation = vel.angle()
	if kind == "shock":
		queue_redraw()
	life -= delta
	if life <= 0:
		queue_free()


func _draw() -> void:
	if kind == "shock":
		var a := clampf(life, 0, 1)
		for i in 3:
			draw_arc(Vector2(0, 12), 22 - i * 6, PI, TAU, 12, Color(1, 0.65 - i * 0.15, 0.2, a), 5, true)
		draw_circle(Vector2(-signf(vel.x) * 14, 8), 6, Color(0.6, 0.45, 0.3, a * 0.7))


func _on_body(b: Node) -> void:
	if b.is_in_group(target) and b.has_method("take_damage"):
		b.take_damage(damage, global_position - vel.normalized() * 30)
		_explode()
	elif target == "enemies" and b.is_in_group("breakable"):
		b.take_damage(damage, global_position)
		_explode()
	elif b is Terrain and b.one_way:
		return
	elif collision_mask & 1 and (b is StaticBody2D):
		_explode()


func _explode() -> void:
	var parent := get_parent()
	if parent:
		match kind:
			"fireball":
				FX.spawn(parent, "boom", global_position, 1, Color.WHITE, 1.0)
				Audio.play("fire", -6)
			"orb":
				FX.spawn(parent, "spark", global_position, 1, Color(0.6, 1, 0.5))
			"shock":
				pass
			_:
				FX.spawn(parent, "spark", global_position, 1, Color(1, 0.9, 0.6))
	queue_free()
