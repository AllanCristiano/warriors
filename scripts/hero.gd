class_name Hero
extends CharacterBody2D
## Heroi controlado pelo jogador (Cavaleiro, Barbaro ou Sabio).

signal hp_changed(hp: int, max_hp: int)
signal died

const GRAVITY := 2200.0
const MAX_FALL := 1400.0

var id := "cavaleiro"
var data: Dictionary
var max_hp := 100
var hp := 100
var facing := 1.0
var state := "normal"  # normal, attack, special, dash, hurt, dead, frozen
var state_time := 0.0
var attack_timer := 0.0
var special_timer := 0.0
var invuln := 0.0
var jumps_left := 1
var max_jumps := 1
var coyote := 0.0
var jump_buffer := 0.0
var combo := 0
var dash_hit: Array = []
var shake := 0.0
var sprite: AnimatedSprite2D
var camera: Camera2D
var _base_offset := Vector2.ZERO
var _bob := 0.0
var level: Node = null


func setup(hero_id: String) -> void:
	id = hero_id
	data = Game.HEROES[id]


func _ready() -> void:
	if data.is_empty():
		setup(id)
	add_to_group("player")
	collision_layer = 2
	collision_mask = 1
	floor_snap_length = 10.0
	var cs := CollisionShape2D.new()
	var rs := RectangleShape2D.new()
	rs.size = Vector2(42, 100)
	cs.shape = rs
	cs.position = Vector2(0, -50)
	add_child(cs)

	sprite = SpriteLib.make_sprite(data["sprite"])
	_base_offset = sprite.offset
	add_child(sprite)
	sprite.play("idle")
	sprite.frame_changed.connect(_on_frame)
	sprite.animation_finished.connect(_on_anim_finished)

	camera = Camera2D.new()
	camera.position = Vector2(0, -110)
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 6.0
	camera.drag_vertical_enabled = true
	camera.drag_top_margin = 0.25
	camera.drag_bottom_margin = 0.2
	add_child(camera)
	camera.make_current()

	max_jumps = 2 if id == "sabio" else 1
	max_hp = data["hp"]
	hp = Game.hero_hp if Game.hero_hp > 0 else max_hp
	hp_changed.emit.call_deferred(hp, max_hp)


func set_camera_limits(l: float, r: float, t: float, b: float) -> void:
	camera.limit_left = int(l)
	camera.limit_right = int(r)
	camera.limit_top = int(t)
	camera.limit_bottom = int(b)


# ------------------------------------------------------------------ loop

func _physics_process(delta: float) -> void:
	attack_timer -= delta
	special_timer -= delta
	invuln -= delta
	state_time -= delta
	jump_buffer -= delta
	_update_shake(delta)
	sprite.visible = invuln <= 0 or state == "dead" or int(invuln * 20) % 2 == 0

	if not is_on_floor():
		if state != "dash":
			velocity.y = minf(velocity.y + GRAVITY * delta, MAX_FALL)
		coyote -= delta
	else:
		coyote = 0.12
		jumps_left = max_jumps

	var dir := 0.0
	if state != "dead" and state != "frozen":
		dir = Input.get_axis("left", "right")
		if Input.is_action_just_pressed("jump"):
			jump_buffer = 0.14

	match state:
		"normal":
			var spd: float = data["speed"]
			velocity.x = move_toward(velocity.x, dir * spd, (2600.0 if is_on_floor() else 1800.0) * delta)
			if dir != 0:
				_set_facing(signf(dir))
			_try_jump()
			if Input.is_action_just_released("jump") and velocity.y < -200:
				velocity.y *= 0.55
			if Input.is_action_just_pressed("attack") and attack_timer <= 0:
				_start_attack()
			elif Input.is_action_just_pressed("special"):
				if special_timer <= 0:
					_start_special()
		"attack", "special":
			var air_ctrl := 0.4 if not is_on_floor() else 0.0
			velocity.x = move_toward(velocity.x, dir * data["speed"] * air_ctrl, 2400.0 * delta)
			if state_time <= 0 and id == "cavaleiro":
				state = "normal"
		"dash":
			velocity.x = facing * 980.0
			velocity.y = 0
			if Engine.get_physics_frames() % 2 == 0 and level:
				FX.ghost(level, sprite)
			_dash_hits()
			if state_time <= 0 or is_on_wall():
				state = "normal"
				velocity.x = facing * 250.0
		"hurt":
			velocity.x = move_toward(velocity.x, 0, 1400.0 * delta)
			if state_time <= 0:
				state = "normal"
		"dead", "frozen":
			velocity.x = move_toward(velocity.x, 0, 2000.0 * delta)

	move_and_slide()
	_update_anim(dir, delta)

	if level and global_position.y > level.kill_y and state != "dead":
		fall_in_pit()


func _try_jump() -> void:
	if jump_buffer <= 0:
		return
	if is_on_floor() or coyote > 0:
		velocity.y = -data["jump"]
		jumps_left = max_jumps - 1
	elif jumps_left > 0 and max_jumps > 1:
		velocity.y = -data["jump"] * 0.9
		jumps_left -= 1
		if level:
			FX.spawn(level, "dust", global_position, 1, Color(0.9, 0.9, 1, 0.7), 0.6)
	else:
		return
	jump_buffer = 0
	coyote = 0
	Audio.play("jump", -4)


func _set_facing(f: float) -> void:
	facing = f
	sprite.flip_h = f < 0
	sprite.offset.x = _base_offset.x * f


func _update_anim(dir: float, delta: float) -> void:
	if state in ["attack", "special", "dead"] and sprite.animation != "idle" and sprite.animation != "walk":
		return
	if state == "dead" or state == "attack":
		return
	var has_walk := sprite.sprite_frames.has_animation("walk")
	if not is_on_floor():
		if has_walk:
			sprite.play("walk")
			sprite.pause()
			sprite.frame = 3
		else:
			sprite.play("idle")
			sprite.pause()
		sprite.position.y = 0
		return
	if absf(velocity.x) > 30:
		if has_walk:
			sprite.play("walk")
			sprite.speed_scale = clampf(absf(velocity.x) / data["speed"], 0.5, 1.3)
		else:
			sprite.play("idle")
			sprite.speed_scale = 2.0
			_bob += delta * 14.0
			sprite.position.y = -absf(sin(_bob)) * 5.0
			return
	else:
		sprite.play("idle")
		sprite.speed_scale = 1.0
	sprite.position.y = 0


# ------------------------------------------------------------------ ataques

func _start_attack() -> void:
	attack_timer = data["attack_cd"]
	match id:
		"cavaleiro":
			state = "attack"
			state_time = 0.26
			combo = (combo + 1) % 2
			sprite.play("walk")
			sprite.pause()
			sprite.frame = 5 if combo == 0 else 12
			var tw := create_tween()
			tw.tween_property(sprite, "rotation", facing * 0.12, 0.06)
			tw.tween_property(sprite, "rotation", 0.0, 0.18)
			Audio.play("swing", -2)
			velocity.x = facing * 160.0
			FX.spawn(self, "slash" if combo == 0 else "slash_up", Vector2(facing * 40, -60), facing, Color(0.9, 0.95, 1.0), 1.0)
			get_tree().create_timer(0.06).timeout.connect(func():
				if state != "dead": _melee(data["damage"], data["reach"]))
		"barbaro":
			state = "attack"
			sprite.speed_scale = 1.0
			sprite.position.y = 0
			sprite.play("attack")
		"sabio":
			state = "attack"
			sprite.speed_scale = 1.4
			sprite.position.y = 0
			sprite.play("attack")


func _start_special() -> void:
	special_timer = data["special_cd"]
	attack_timer = 0.3
	match id:
		"cavaleiro":
			state = "dash"
			state_time = 0.3
			invuln = maxf(invuln, 0.45)
			dash_hit.clear()
			sprite.play("walk")
			Audio.play("swing", 2, 0.0)
		"barbaro":
			state = "special"
			sprite.speed_scale = 1.0
			sprite.play("special")
			Audio.play("swing", 0, 0.0)
		"sabio":
			state = "special"
			sprite.speed_scale = 1.8
			sprite.play("attack")


func _on_frame() -> void:
	if state == "attack":
		if id == "barbaro" and sprite.animation == "attack" and sprite.frame == 6:
			Audio.play("swing")
			FX.spawn(self, "slash", Vector2(facing * 50, -60), facing, Color(0.8, 0.7, 0.5), 1.3)
			_melee(data["damage"], data["reach"])
		elif id == "sabio" and sprite.frame == 6:
			_throw_dart(0.0)
	elif state == "special":
		if id == "barbaro" and sprite.frame == 7:
			_slam()
		elif id == "sabio" and sprite.frame == 6:
			for a in [-0.35, -0.17, 0.0, 0.17, 0.35]:
				_throw_dart(a)
			Audio.play("magic", -4)


func _on_anim_finished() -> void:
	if state in ["attack", "special"]:
		state = "normal"
		sprite.speed_scale = 1.0


func _attack_rect(reach: Vector2) -> Rect2:
	var x := global_position.x + (-10.0 if facing > 0 else 10.0 - reach.x)
	return Rect2(x, global_position.y - reach.y, reach.x, reach.y)


func _melee(dmg: int, reach: Vector2) -> void:
	var r := _attack_rect(reach)
	var hits := 0
	for n in get_tree().get_nodes_in_group("damageable"):
		if n.has_method("get_hurt_rect") and r.intersects(n.get_hurt_rect()):
			if n.take_damage(dmg, global_position, Vector2(facing * 280, -160)):
				hits += 1
	if hits > 0:
		Audio.play("hit")
		_hitstop(0.05)
		add_shake(4)


func _dash_hits() -> void:
	var r := Rect2(global_position.x - 50, global_position.y - 110, 100, 110)
	for n in get_tree().get_nodes_in_group("damageable"):
		if n in dash_hit:
			continue
		if n.has_method("get_hurt_rect") and r.intersects(n.get_hurt_rect()):
			dash_hit.append(n)
			n.take_damage(int(data["damage"] * 1.5), global_position, Vector2(facing * 400, -250))
			Audio.play("hit")
			add_shake(5)


func _slam() -> void:
	Audio.play("slam")
	add_shake(16)
	if level:
		FX.spawn(level, "shock", global_position + Vector2(facing * 70, 0), 1, Color(1, 0.6, 0.2), 1.0)
		FX.spawn(level, "dust", global_position + Vector2(facing * 70, 0), 1, Color(0.6, 0.45, 0.3, 0.8), 1.5)
	var center := global_position + Vector2(facing * 60, 0)
	var r := Rect2(center.x - 240, center.y - 140, 480, 160)
	for n in get_tree().get_nodes_in_group("damageable"):
		if n.has_method("get_hurt_rect") and r.intersects(n.get_hurt_rect()):
			var d := signf(n.global_position.x - center.x)
			n.take_damage(int(data["damage"] * 1.6), center, Vector2(d * 350, -450))


func _throw_dart(angle: float) -> void:
	if not level:
		return
	Audio.play("throw", -2)
	var v := Vector2(facing * 900, 0).rotated(angle * facing)
	Projectile.spawn(level, "dart", global_position + Vector2(facing * 50, -78), v, data["damage"], "enemies")


func _hitstop(sec: float) -> void:
	Engine.time_scale = 0.05
	get_tree().create_timer(sec, true, false, true).timeout.connect(func(): Engine.time_scale = 1.0)


# ------------------------------------------------------------------ vida

func get_hurt_rect() -> Rect2:
	return Rect2(global_position.x - 21, global_position.y - 100, 42, 100)


func take_damage(amount: int, from_pos: Vector2, knock := Vector2.ZERO) -> bool:
	if invuln > 0 or state == "dead":
		return false
	hp = maxi(0, hp - amount)
	hp_changed.emit(hp, max_hp)
	Audio.play("hurt")
	add_shake(8)
	if level:
		FX.text(level, global_position + Vector2(0, -120), "-%d" % amount, Color(1, 0.35, 0.3))
	var tw := create_tween()
	sprite.modulate = Color(1, 0.3, 0.3)
	tw.tween_property(sprite, "modulate", Color.WHITE, 0.3)
	if hp <= 0:
		_die()
		return true
	invuln = 1.0
	if state != "dash":
		state = "hurt"
		state_time = 0.3
		var d := signf(global_position.x - from_pos.x)
		if d == 0: d = -facing
		velocity = Vector2(d * 380, -380) if knock == Vector2.ZERO else Vector2(d * absf(knock.x), knock.y)
		sprite.rotation = 0
	return true


func heal(amount: int) -> void:
	hp = mini(max_hp, hp + amount)
	hp_changed.emit(hp, max_hp)
	if level:
		FX.spawn(self, "heal", Vector2(0, -60))
		FX.text(level, global_position + Vector2(0, -130), "+%d" % amount, Color(0.5, 1, 0.5))


func fall_in_pit() -> void:
	hp = maxi(0, hp - 30)
	hp_changed.emit(hp, max_hp)
	Audio.play("hurt")
	if hp <= 0:
		_die()
		return
	velocity = Vector2.ZERO
	global_position = level.respawn_point()
	camera.reset_smoothing()
	invuln = 1.5


func _die() -> void:
	state = "dead"
	invuln = 99
	velocity.x = 0
	Audio.play("gameover", -6)
	if sprite.sprite_frames.has_animation("die"):
		sprite.speed_scale = 1.0
		sprite.play("die")
	else:
		sprite.pause()
		var tw := create_tween()
		tw.tween_property(sprite, "rotation", -facing * PI / 2, 0.5).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	sprite.visible = true
	died.emit()


func freeze(on: bool) -> void:
	if state == "dead":
		return
	state = "frozen" if on else "normal"
	if on:
		sprite.play("idle")
		sprite.position.y = 0


# ------------------------------------------------------------------ camera

func add_shake(amount: float) -> void:
	shake = maxf(shake, amount)


func _update_shake(delta: float) -> void:
	if shake > 0.1:
		camera.offset = Vector2(randf_range(-shake, shake), randf_range(-shake, shake))
		shake = move_toward(shake, 0, 40.0 * delta)
	else:
		camera.offset = Vector2.ZERO
