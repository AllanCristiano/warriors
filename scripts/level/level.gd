class_name Level
extends Node2D
## Controlador de fase: cria heroi, HUD, camera, chefe e saida.

@export var level_name := "Fase"
@export var subtitle := ""
@export var music := "music_village"
@export var level_width := 8000.0
@export var top_limit := -500.0
@export var kill_y := 900.0
@export var ambient := Color(1, 1, 1)

var hero: Hero
var hud: HUD
var boss: Enemy
var _walls: Array[StaticBody2D] = []
var _completed := false


func _ready() -> void:
	if ambient != Color(1, 1, 1):
		var cm := CanvasModulate.new()
		cm.color = ambient
		add_child(cm)
	hero = Hero.new()
	hero.setup(Game.hero_id)
	hero.level = self
	hero.position = respawn_point()
	hero.z_index = 5
	add_child(hero)
	hero.set_camera_limits(0, level_width, top_limit, 720)
	hero.died.connect(_on_hero_died)
	hud = HUD.new()
	add_child(hud)
	hud.bind_hero(hero)
	hud.show_title(level_name, subtitle)
	Audio.music(music)


func respawn_point() -> Vector2:
	if Game.checkpoint != Vector2.INF:
		return Game.checkpoint + Vector2(0, -10)
	var start := get_node_or_null("PlayerStart")
	return start.global_position if start else Vector2(120, 400)


func start_boss(b: Enemy, left: float, right: float) -> void:
	boss = b
	hero.set_camera_limits(left, right, top_limit, 720)
	for x in [left - 20, right + 20]:
		var w := StaticBody2D.new()
		var cs := CollisionShape2D.new()
		var rs := RectangleShape2D.new()
		rs.size = Vector2(40, 3000)
		cs.shape = rs
		w.add_child(cs)
		w.position = Vector2(x, -800)
		add_child(w)
		_walls.append(w)
	Audio.music("music_boss")
	Audio.play("roar")
	hero.add_shake(10)
	b.activate()
	hud.show_boss(b)
	b.defeated.connect(_on_boss_defeated, CONNECT_ONE_SHOT)


func _on_boss_defeated(_b: Enemy) -> void:
	for w in _walls:
		w.queue_free()
	_walls.clear()
	hero.set_camera_limits(0, level_width, top_limit, 720)
	Audio.music(music)
	Audio.play("victory")
	hud.hide_boss()
	hud.message("%s foi derrotado!" % boss.cfg["name"], 3.0)


func complete() -> void:
	if _completed:
		return
	_completed = true
	hero.freeze(true)
	Audio.music("")
	Audio.play("victory")
	hud.message("Fase concluida!  +%d de ouro" % Game.gold, 3.0)
	Game.hero_hp = hero.hp
	get_tree().create_timer(3.0).timeout.connect(Game.next_level)


func _on_hero_died() -> void:
	hud.message("Voce caiu em batalha...", 2.5)
	get_tree().create_timer(2.8).timeout.connect(Game.lose_life)
