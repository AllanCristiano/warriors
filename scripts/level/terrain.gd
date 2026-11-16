@tool
class_name Terrain
extends StaticBody2D
## Bloco de terreno/plataforma redimensionavel. Ajuste "size" e "style" no inspetor.
## A origem e o canto superior esquerdo (a superficie onde se pisa).

const STYLES := {
	# estilo: [textura topo, deslocamento y do topo, textura de preenchimento, one_way padrao]
	"grama": ["tile_grass_top", -14, "tile_dirt"],
	"castelo": ["tile_cobble_top", -2, "tile_castle_wall"],
	"masmorra": ["tile_dungeon_top", -2, "tile_dungeon_wall"],
	"tabuas": ["tile_plank", -2, ""],
	"pedra": ["tile_stone_ledge", -1, ""],
}

@export var size := Vector2(512, 200):
	set(v):
		size = v
		_refresh()
@export_enum("grama", "castelo", "masmorra", "tabuas", "pedra") var style: String = "grama":
	set(v):
		style = v
		_refresh()
## Plataforma atravessavel por baixo.
@export var one_way := false:
	set(v):
		one_way = v
		_refresh()

var _shape: CollisionShape2D
var _top: Texture2D
var _fill: Texture2D
var _top_y := 0


func _ready() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	collision_layer = 1
	collision_mask = 0
	_refresh()


func _refresh() -> void:
	if not is_inside_tree():
		return
	var st: Array = STYLES[style]
	_top = load("res://assets/kingdom/%s.png" % st[0])
	_top_y = st[1]
	_fill = load("res://assets/kingdom/%s.png" % st[2]) if st[2] != "" else null
	if _shape == null:
		_shape = CollisionShape2D.new()
		add_child(_shape)
	var rs := RectangleShape2D.new()
	var h := size.y if _fill else 18.0
	rs.size = Vector2(size.x, h)
	_shape.shape = rs
	_shape.position = Vector2(size.x / 2, h / 2)
	_shape.one_way_collision = one_way
	queue_redraw()


func _draw() -> void:
	if _top == null:
		return
	if _fill:
		var fill_top := 10.0
		draw_texture_rect(_fill, Rect2(0, fill_top, size.x, size.y - fill_top), true)
		# sombra suave abaixo da borda e laterais escuras
		for i in 6:
			draw_rect(Rect2(0, fill_top + i * 4, size.x, 4), Color(0, 0, 0, 0.25 - i * 0.04))
		draw_rect(Rect2(0, fill_top, 4, size.y - fill_top), Color(0, 0, 0, 0.35))
		draw_rect(Rect2(size.x - 4, fill_top, 4, size.y - fill_top), Color(0, 0, 0, 0.35))
	else:
		# vigas de apoio sob plataformas
		var beam := Color(0.3, 0.2, 0.12) if style == "tabuas" else Color(0.32, 0.31, 0.33)
		for x in [12.0, size.x - 24.0]:
			draw_rect(Rect2(x, 16, 12, 26), beam)
			draw_rect(Rect2(x, 16, 12, 26), Color(0.12, 0.08, 0.06), false, 2)
	var th := float(_top.get_height())
	draw_texture_rect(_top, Rect2(0, _top_y, size.x, th), true)
