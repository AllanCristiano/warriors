@tool
class_name Enemy
extends CharacterBody2D
## Inimigo generico com varias IAs (goblins, general, minotauro, cerbero).
## No editor mostra o sprite para facilitar o level design.

signal defeated(enemy: Enemy)

const GRAVITY := 2200.0

const TYPES := {
	"goblin_guerreiro": {"name": "Goblin Guerreiro", "hp": 50, "speed": 130.0, "damage": 12, "ai": "melee",
		"reach": Vector2(100, 90), "hit_frame": 6, "attack_cd": 1.3, "sight": 520.0, "size": Vector2(50, 95), "gold": 2},
	"goblin_lanca": {"name": "Goblin Lanceiro", "hp": 65, "speed": 105.0, "damage": 15, "ai": "melee",
		"reach": Vector2(150, 80), "hit_frame": 4, "attack_cd": 1.6, "sight": 520.0, "size": Vector2(50, 100), "gold": 2, "block": 0.35},
	"goblin_boleadeira": {"name": "Goblin Boleadeiro", "hp": 35, "speed": 0.0, "damage": 12, "ai": "thrower",
		"hit_frame": 4, "attack_cd": 2.4, "sight": 720.0, "size": Vector2(44, 76), "gold": 2},
	"goblin_mago": {"name": "Goblin Xamã", "hp": 50, "speed": 80.0, "damage": 14, "ai": "caster",
		"hit_frame": 7, "attack_cd": 2.6, "sight": 760.0, "size": Vector2(46, 100), "gold": 3},
	"goblin_general": {"name": "Grukk, o General Goblin", "hp": 420, "speed": 170.0, "damage": 20, "ai": "general",
		"reach": Vector2(160, 140), "hit_frame": 6, "attack_cd": 1.0, "sight": 1000.0, "size": Vector2(70, 150), "gold": 15, "boss": true},
	"minotauro": {"name": "Tauron, o Minotauro", "hp": 650, "speed": 120.0, "damage": 24, "ai": "minotaur",
		"reach": Vector2(170, 170), "hit_frame": 7, "attack_cd": 1.2, "sight": 1100.0, "size": Vector2(90, 180), "gold": 25, "boss": true},
	"cerberus": {"name": "Cérbero, Guardião do Abismo", "hp": 950, "speed": 0.0, "damage": 26, "ai": "cerberus",
		"hit_frame": 8, "attack_cd": 1.6, "sight": 1300.0, "size": Vector2(250, 200), "gold": 40, "boss": true},
}

@export_enum("goblin_guerreiro", "goblin_lanca", "goblin_boleadeira", "goblin_mago", "goblin_general", "minotauro", "cerberus")
var kind: String = "goblin_guerreiro":
	set(v):
		kind = v
		if is_inside_tree():
			_build()
@export var patrol_range := 180.0
@export var start_facing_left := true
## Chefes comecam adormecidos ate o jogador entrar na arena.
@export var dormant := false

var cfg: Dictionary
var hp := 1
var max_hp := 1
var facing := -1.0
var state := "patrol"  # patrol, chase, attack, hurt, dead, special, idle
var state_time := 0.0
var cooldown := 1.0
var special_cd := 4.0
var home_x := 0.0
var sprite: CharSprite
var shape: CollisionShape2D
var _phase2 := false
var _summoned := false
var _contact_cd := 0.0
var _rolling := false
var _pounce := false
var _pounce_hit := false


func _ready() -> void:
	_build()
	if Engine.is_editor_hint():
		return
	home_x = global_position.x
	add_to_group("enemies")
	add_to_group("damageable")
	collision_layer = 4
	collision_mask = 1
	floor_snap_length = 12.0
	cooldown = randf_range(0.6, 1.4)
	if cfg.get("boss", false):
		add_to_group("bosses")


func _build() -> void:
	cfg = TYPES[kind]
	for c in get_children():
		if c.has_meta("gen"):
			c.free()
	sprite = SpriteLib.make_sprite(kind)
	sprite.set_meta("gen", true)
	add_child(sprite)
	sprite.play("idle")
	if not Engine.is_editor_hint():
		sprite.frame_changed.connect(_on_frame)
		sprite.animation_finished.connect(_on_anim_finished)
	shape = CollisionShape2D.new()
	shape.set_meta("gen", true)
	var rs := RectangleShape2D.new()
	rs.size = cfg["size"]
	shape.shape = rs
	shape.position = Vector2(0, -cfg["size"].y / 2)
	add_child(shape)
	max_hp = cfg["hp"]
	hp = max_hp
	_set_facing(-1.0 if start_facing_left else 1.0)


func _set_facing(f: float) -> void:
	facing = f
	if sprite:
		sprite.set_facing(f)


func is_boss() -> bool:
	return cfg.get("boss", false)


func activate() -> void:
	dormant = false
	state = "chase"
	cooldown = 1.0
	special_cd = 2.5


func _hero() -> Hero:
	var p := get_tree().get_nodes_in_group("player")
	return p[0] if p.size() > 0 else null


# ------------------------------------------------------------------ loop

func _physics_process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	state_time -= delta
	cooldown -= delta
	special_cd -= delta
	_contact_cd -= delta
	if not is_on_floor():
		velocity.y = minf(velocity.y + GRAVITY * delta, 1400.0)

	var hero := _hero()
	if state == "dead":
		velocity.x = move_toward(velocity.x, 0, 1200 * delta)
		move_and_slide()
		return
	if dormant or hero == null or hero.state == "dead":
		velocity.x = move_toward(velocity.x, 0, 1200 * delta)
		if sprite.animation != "idle" and state != "hurt":
			sprite.play("idle")
		move_and_slide()
		return

	var to_hero := hero.global_position - global_position
	var dist := absf(to_hero.x)
	var sees: bool = dist < cfg["sight"] and absf(to_hero.y) < 260

	match cfg["ai"]:
		"melee": _ai_melee(delta, hero, to_hero, dist, sees)
		"thrower": _ai_thrower(delta, hero, to_hero, dist, sees)
		"caster": _ai_caster(delta, hero, to_hero, dist, sees)
		"general": _ai_general(delta, hero, to_hero, dist)
		"minotaur": _ai_minotaur(delta, hero, to_hero, dist)
		"cerberus": _ai_cerberus(delta, hero, to_hero, dist)

	move_and_slide()

	# dano por contato (chefes e investidas)
	if (is_boss() or _rolling) and _contact_cd <= 0 and state != "dead":
		if get_hurt_rect().grow(-10).intersects(hero.get_hurt_rect()):
			var dmg := int(cfg["damage"] * (1.0 if _rolling or _pounce else 0.5))
			if hero.take_damage(dmg, global_position):
				_contact_cd = 0.8

	if global_position.y > 3000:
		queue_free()


func _walk(speed: float, delta: float) -> void:
	velocity.x = move_toward(velocity.x, facing * speed, 900 * delta)
	if absf(velocity.x) > 10:
		if sprite.animation != "walk":
			sprite.play("walk")
	elif sprite.animation != "idle":
		sprite.play("idle")


func _stop(delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0, 1400 * delta)
	if sprite.animation == "walk":
		sprite.play("idle")


func _face(x: float) -> void:
	var f := signf(x)
	if f != 0 and f != facing:
		_set_facing(f)


func _ground_ahead() -> bool:
	var space := get_world_2d().direct_space_state
	var from := global_position + Vector2(facing * (cfg["size"].x * 0.5 + 12), -10)
	var q := PhysicsRayQueryParameters2D.create(from, from + Vector2(0, 60), 1)
	return not space.intersect_ray(q).is_empty()


func _patrol(delta: float) -> void:
	if cfg["speed"] <= 0:
		_stop(delta)
		return
	if is_on_floor() and (not _ground_ahead() or is_on_wall()
			or (global_position.x - home_x) * facing > patrol_range):
		_set_facing(-facing)
	_walk(cfg["speed"] * 0.5, delta)


# ------------------------------------------------------------------ IAs

func _ai_melee(delta: float, hero: Hero, to_hero: Vector2, dist: float, sees: bool) -> void:
	match state:
		"patrol":
			_patrol(delta)
			if (sees and signf(to_hero.x) == facing) or (dist < 200 and absf(to_hero.y) < 150):
				state = "chase"
				FX.text(get_parent(), global_position + Vector2(0, -cfg["size"].y - 30), "!", Color(1, 0.3, 0.2), 34)
		"chase":
			_face(to_hero.x)
			if dist > cfg["sight"] * 1.3:
				state = "patrol"
			elif dist < cfg["reach"].x * 0.85 and absf(to_hero.y) < 120:
				_stop(delta)
				if cooldown <= 0:
					_begin_attack("attack")
			elif is_on_floor() and not _ground_ahead():
				_stop(delta)
			else:
				_walk(cfg["speed"], delta)
		"attack":
			_stop(delta)
		"hurt":
			velocity.x = move_toward(velocity.x, 0, 900 * delta)
			if state_time <= 0:
				state = "chase"


func _ai_thrower(delta: float, hero: Hero, to_hero: Vector2, dist: float, sees: bool) -> void:
	_stop(delta)
	match state:
		"patrol", "chase":
			if sees:
				_face(to_hero.x)
				if cooldown <= 0:
					_begin_attack("attack")
		"hurt":
			if state_time <= 0:
				state = "chase"


func _ai_caster(delta: float, hero: Hero, to_hero: Vector2, dist: float, sees: bool) -> void:
	match state:
		"patrol":
			_patrol(delta)
			if sees:
				state = "chase"
		"chase":
			_face(to_hero.x)
			if dist < 280 and is_on_floor():
				# recua mantendo distancia
				var back := -signf(to_hero.x)
				_set_facing(back)
				if _ground_ahead() and not is_on_wall():
					_walk(cfg["speed"], delta)
				else:
					_stop(delta)
				_face(to_hero.x)
			elif dist > 560:
				_walk(cfg["speed"], delta)
			else:
				_stop(delta)
			if cooldown <= 0 and dist < cfg["sight"]:
				_begin_attack("attack")
		"attack":
			_stop(delta)
		"hurt":
			velocity.x = move_toward(velocity.x, 0, 900 * delta)
			if state_time <= 0:
				state = "chase"


func _ai_general(delta: float, hero: Hero, to_hero: Vector2, dist: float) -> void:
	if not _phase2 and hp < max_hp * 0.5:
		_phase2 = true
		_summon(2)
		FX.text(get_parent(), global_position + Vector2(0, -190), "A MIM, GOBLINS!", Color(1, 0.5, 0.2), 30)
	match state:
		"patrol", "chase", "idle":
			_face(to_hero.x)
			if special_cd <= 0 and dist > 220 and is_on_floor():
				# salto em direcao ao heroi
				special_cd = randf_range(3.5, 5.0) * (0.7 if _phase2 else 1.0)
				velocity = Vector2(clampf(to_hero.x * 1.4, -700, 700), -900)
				_pounce = true
				state = "special"
				Audio.play("jump", 2, 0.0)
			elif dist < cfg["reach"].x * 0.8:
				_stop(delta)
				if cooldown <= 0:
					_begin_attack("attack")
			else:
				_walk(cfg["speed"] * (1.25 if _phase2 else 1.0), delta)
		"special":
			if is_on_floor() and velocity.y >= 0:
				_land_shock(0.8)
				_pounce = false
				state = "chase"
		"attack":
			_stop(delta)


func _ai_minotaur(delta: float, hero: Hero, to_hero: Vector2, dist: float) -> void:
	if not _phase2 and hp < max_hp * 0.5:
		_phase2 = true
		sprite.speed_scale = 1.25
		FX.text(get_parent(), global_position + Vector2(0, -220), "FÚRIA!", Color(1, 0.3, 0.2), 38)
	match state:
		"patrol", "chase", "idle":
			_face(to_hero.x)
			if special_cd <= 0:
				special_cd = randf_range(3.0, 4.5) * (0.7 if _phase2 else 1.0)
				if randf() < 0.55 or dist > 500:
					state = "special"
					_rolling = false
					sprite.play("roll")
					Audio.play("roar", -4, 0.15)
				else:
					_begin_attack("attack")
			elif dist > 140:
				_walk(cfg["speed"] * (1.3 if _phase2 else 1.0), delta)
			else:
				_stop(delta)
				if cooldown <= 0:
					_begin_attack("attack")
		"special":
			if _rolling:
				velocity.x = facing * (720.0 if _phase2 else 600.0)
				if is_on_wall():
					_rolling = false
					velocity.x = -facing * 200
					_get_level_hero_shake(10)
					Audio.play("slam")
			else:
				velocity.x = move_toward(velocity.x, 0, 2000 * delta)
		"attack":
			_stop(delta)


func _ai_cerberus(delta: float, hero: Hero, to_hero: Vector2, dist: float) -> void:
	if not _phase2 and hp < max_hp * 0.5:
		_phase2 = true
		sprite.speed_scale = 1.3
		_summon(2)
	match state:
		"patrol", "chase", "idle":
			_face(to_hero.x)
			velocity.x = move_toward(velocity.x, 0, 1400 * delta)
			if sprite.animation != "idle":
				sprite.play("idle")
			if cooldown <= 0:
				var r := randf()
				if r < 0.4:
					_begin_attack("howl")  # sopro de fogo / chuva de fogo
					_play_cerberus_howl()
				else:
					# bote: salta ate o heroi
					state = "special"
					_pounce = true
					_pounce_hit = false
					var tx := clampf(to_hero.x, -650, 650)
					velocity = Vector2(tx * 1.25, -1050)
					sprite.play("leap")
					Audio.play("roar", -2, 0.1)
				cooldown = cfg["attack_cd"] * (0.65 if _phase2 else 1.0) + 1.0
		"special":
			if is_on_floor() and velocity.y >= 0:
				_pounce = false
				_land_shock(1.2)
				state = "chase"
				sprite.play("idle")
		"attack":
			_stop(delta)


func _play_cerberus_howl() -> void:
	Audio.play("cerberus_howl", 2, 0.0)


func _get_level_hero_shake(a: float) -> void:
	var h := _hero()
	if h:
		h.add_shake(a)


func _land_shock(scale_: float) -> void:
	Audio.play("slam")
	_get_level_hero_shake(12)
	FX.spawn(get_parent(), "shock", global_position, 1, Color(1, 0.6, 0.3), scale_)
	FX.spawn(get_parent(), "dust", global_position, 1, Color(0.5, 0.4, 0.35, 0.8), 1.5)
	for d in [-1.0, 1.0]:
		Projectile.spawn(get_parent(), "shock", global_position + Vector2(d * 60, -14), Vector2(d * 520, 0), int(cfg["damage"] * 0.6), "player")


func _summon(n: int) -> void:
	for i in n:
		var e := Enemy.new()
		e.kind = "goblin_guerreiro" if i % 2 == 0 else "goblin_lanca"
		e.position = position + Vector2((-1 if i % 2 == 0 else 1) * 260, -200)
		e.patrol_range = 400
		get_parent().add_child.call_deferred(e)
		e.set_deferred("state", "chase")
		FX.spawn(get_parent(), "dust", global_position + Vector2((-1 if i % 2 == 0 else 1) * 260, 0), 1, Color(0.4, 0.8, 0.3, 0.8), 1.4)


func _begin_attack(anim: String) -> void:
	state = "attack"
	cooldown = cfg["attack_cd"] * randf_range(0.9, 1.3) * (0.7 if _phase2 else 1.0)
	velocity.x = 0
	sprite.play(anim)


func _on_frame() -> void:
	if state == "attack" and sprite.frame == cfg["hit_frame"]:
		var hero := _hero()
		if hero == null:
			return
		match cfg["ai"]:
			"melee", "general":
				Audio.play("swing", -3)
				_melee_hit(hero)
			"minotaur":
				# rugido + golpe no chao gera ondas de choque
				_land_shock(1.0)
				_melee_hit(hero)
			"thrower":
				Audio.play("throw")
				var to := hero.global_position + Vector2(0, -50) - (global_position + Vector2(facing * 20, -60))
				var T := clampf(absf(to.x) / 480.0, 0.55, 1.4)
				var g := 1200.0
				var v := Vector2(to.x / T, (to.y - 0.5 * g * T * T) / T)
				var p := Projectile.spawn(get_parent(), "bola", global_position + Vector2(facing * 20, -60), v, cfg["damage"], "player")
				p.grav = g
			"caster":
				Audio.play("magic")
				var from := global_position + Vector2(facing * 40, -80)
				var dir := (hero.global_position + Vector2(0, -55) - from).normalized()
				Projectile.spawn(get_parent(), "orb", from, dir * 360, cfg["damage"], "player")
			"cerberus":
				var mouth := global_position + Vector2(facing * 150, -150)
				Audio.play("fire")
				if randf() < 0.5 or not _phase2:
					for a in [-0.18, 0.0, 0.18]:
						var dir := (hero.global_position + Vector2(0, -50) - mouth).normalized().rotated(a)
						Projectile.spawn(get_parent(), "fireball", mouth, dir * 480, int(cfg["damage"] * 0.7), "player")
				if _phase2 or randf() < 0.4:
					for i in 5:
						var x := hero.global_position.x + (i - 2) * 140 + randf_range(-30, 30)
						var p := Projectile.spawn(get_parent(), "fireball", Vector2(x, hero.global_position.y - 650 - i * 60), Vector2(0, 420), int(cfg["damage"] * 0.6), "player")
						p.grav = 300
	elif state == "special" and kind == "minotauro":
		if sprite.frame == 3:
			_rolling = true
			Audio.play("swing", 0, 0.0)
		elif sprite.frame == 12:
			_rolling = false


func _melee_hit(hero: Hero) -> void:
	var reach: Vector2 = cfg["reach"]
	var x := global_position.x + (-10.0 if facing > 0 else 10.0 - reach.x)
	var r := Rect2(x, global_position.y - reach.y, reach.x, reach.y)
	if r.intersects(hero.get_hurt_rect()):
		hero.take_damage(cfg["damage"], global_position)


func _on_anim_finished() -> void:
	if state == "dead":
		return
	if state in ["attack", "hurt"] or (state == "special" and kind == "minotauro"):
		_rolling = false
		state = "chase"
		sprite.play("idle")


# ------------------------------------------------------------------ dano

func get_hurt_rect() -> Rect2:
	var s: Vector2 = cfg["size"]
	return Rect2(global_position.x - s.x / 2, global_position.y - s.y, s.x, s.y)


func take_damage(amount: int, from_pos: Vector2, knock := Vector2.ZERO) -> bool:
	if state == "dead":
		return false
	if dormant:
		activate()
	var from_dir := signf(from_pos.x - global_position.x)
	# lanceiro pode bloquear golpes frontais
	if cfg.has("block") and state != "attack" and from_dir == facing and randf() < cfg["block"]:
		Audio.play("clang")
		FX.spawn(get_parent(), "spark", global_position + Vector2(facing * 30, -60), 1, Color(1, 0.9, 0.5))
		FX.text(get_parent(), global_position + Vector2(0, -cfg["size"].y - 20), "Bloqueou!", Color(0.8, 0.85, 1.0), 22)
		sprite.play("attack")
		state = "attack"
		return true
	hp -= amount
	FX.text(get_parent(), global_position + Vector2(0, -cfg["size"].y - 10), str(amount))
	FX.spawn(get_parent(), "spark", global_position + Vector2(0, -cfg["size"].y * 0.55), 1, Color(1, 0.85, 0.4))
	sprite.modulate = Color(1, 0.35, 0.35)
	create_tween().tween_property(sprite, "modulate", Color.WHITE, 0.25)
	if hp <= 0:
		_die()
		return true
	if not is_boss():
		state = "hurt"
		state_time = 0.35
		_rolling = false
		if knock != Vector2.ZERO:
			velocity = knock
		if sprite.sprite_frames.has_animation("hurt"):
			sprite.play("hurt")
		_face(from_pos.x - global_position.x)
	return true


func _die() -> void:
	state = "dead"
	_rolling = false
	_pounce = false
	remove_from_group("damageable")
	remove_from_group("enemies")
	set_deferred("collision_layer", 0)
	Audio.play("enemy_die")
	if is_boss():
		Audio.play("roar", 0, 0.0)
		_get_level_hero_shake(18)
		Game.flash(Color(1, 1, 1, 0.6))
	# saque
	for i in cfg["gold"]:
		Pickup.drop(get_parent(), "coin", global_position + Vector2(0, -40))
	if randf() < (1.0 if is_boss() else 0.15):
		Pickup.drop(get_parent(), "potion", global_position + Vector2(0, -40))
	defeated.emit(self)
	var tw := create_tween()
	if sprite.sprite_frames.has_animation("die"):
		sprite.play("die")
		tw.tween_interval(1.0)
	else:
		sprite.pause()
		tw.set_parallel(true)
		tw.tween_property(sprite, "rotation", -facing * PI / 2.2, 0.45).set_trans(Tween.TRANS_BACK)
		tw.tween_property(sprite, "position:y", 10.0, 0.45)
		tw.chain().tween_interval(0.6 if not is_boss() else 1.5)
	tw.chain().tween_property(self, "modulate:a", 0.0, 0.6)
	tw.chain().tween_callback(queue_free)
