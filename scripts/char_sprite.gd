class_name CharSprite
extends AnimatedSprite2D
## Sprite de personagem: mantem os pes na origem em todas as animacoes e
## cuida do espelhamento (todas as spritesheets olham para a direita).

var char_name := ""
var facing := 1.0
var _offs := {}


func setup(n: String) -> void:
	char_name = n
	sprite_frames = SpriteLib.frames(n)
	_offs = SpriteLib.offsets(n)
	animation_changed.connect(_apply)
	_apply()


func set_facing(f: float) -> void:
	facing = f
	flip_h = f < 0
	_apply()


func _apply() -> void:
	var o: Vector2 = _offs.get(animation, Vector2.ZERO)
	offset = Vector2(o.x * facing, o.y)


func has(anim: String) -> bool:
	return sprite_frames.has_animation(anim)
