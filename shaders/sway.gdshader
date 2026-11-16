shader_type canvas_item;
// Balanco suave para estandartes e bandeiras (mais forte na ponta de baixo).
uniform float strength = 6.0;
uniform float speed = 2.0;

void vertex() {
	float w = sin(TIME * speed + VERTEX.y * 0.04 + VERTEX.x * 0.01);
	VERTEX.x += w * strength * UV.y;
}
