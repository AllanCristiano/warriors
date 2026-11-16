shader_type canvas_item;
// Vinheta escura + leve gradacao de cor para o clima sombrio.
uniform float strength = 0.85;
uniform vec4 tint : source_color = vec4(0.05, 0.02, 0.04, 1.0);

void fragment() {
	vec2 uv = SCREEN_UV - vec2(0.5);
	uv.x *= 1.25;
	float d = length(uv);
	float v = smoothstep(0.38, 0.95, d) * strength;
	COLOR = vec4(tint.rgb, v);
}
