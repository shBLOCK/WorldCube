shader_type spatial;
render_mode unshaded;

uniform bool projector_enabled;
uniform sampler2D projector_texture : source_color, repeat_disable, filter_linear;
uniform vec3 camera_inv_matrix_x;
uniform vec3 camera_inv_matrix_y;
uniform vec3 camera_inv_matrix_z;
uniform vec3 camera_inv_matrix_o;
uniform vec2 camera_half_size;

varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = MODEL_NORMAL_MATRIX * NORMAL;
}

void fragment() {
	mat4 camera_inv_matrix = mat4(
		vec4(camera_inv_matrix_x, 0.0),
		vec4(camera_inv_matrix_y, 0.0),
		vec4(camera_inv_matrix_z, 0.0),
		vec4(camera_inv_matrix_o, 1.0)
	);
	vec3 local_pos = (camera_inv_matrix * vec4(world_pos, 1.0)).xyz * vec3(1, 1, -1);
	vec3 local_normal = mat3(camera_inv_matrix) * world_normal * vec3(1, 1, -1);
	vec2 pos_on_proj_plane = local_pos.xy / local_pos.z;
	vec2 uv = (pos_on_proj_plane / camera_half_size) * vec2(0.5, -0.5) + 0.5;
	vec4 color = vec4(0.0);
	if (projector_enabled
		&& dot(local_pos, local_normal) <= 0.0
		&& uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {
			color = texture(projector_texture, uv);
	}

	ALBEDO = color.rgb;
	ALPHA = color.a;
}
