@tool
class_name ProjectSurfaceProjector extends SubViewport

@export_flags_3d_render var layers := 0

@onready var texture: ViewportTexture = get_texture()
@export var updating := false
@export var enabled := true
var is_first_frame := true

func _process(delta: float) -> void:
	own_world_3d = false
	transparent_bg = true
	
	%Camera3D.cull_mask = layers
	
	if is_first_frame or updating or Engine.is_editor_hint():
		render_target_update_mode = SubViewport.UPDATE_ONCE
	else:
		render_target_update_mode = SubViewport.UPDATE_DISABLED
	
	is_first_frame = false

func _update_dest_shader_uniforms(material: ShaderMaterial):
	material.set_shader_parameter("projector_enabled", enabled)
	if enabled:
		material.set_shader_parameter("projector_texture", texture)
		var cam_inv_transform: Transform3D = %Camera3D.global_transform.inverse()
		material.set_shader_parameter("camera_inv_matrix_x", cam_inv_transform.basis.x)
		material.set_shader_parameter("camera_inv_matrix_y", cam_inv_transform.basis.y)
		material.set_shader_parameter("camera_inv_matrix_z", cam_inv_transform.basis.z)
		material.set_shader_parameter("camera_inv_matrix_o", cam_inv_transform.origin)
		var half_size_y := tan(deg_to_rad(%Camera3D.fov / 2.0))
		var half_size_x: float = half_size_y * (size.x / size.y)
		material.set_shader_parameter("camera_half_size", Vector2(half_size_x, half_size_y))
