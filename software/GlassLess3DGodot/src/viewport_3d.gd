@tool
class_name Viewport3D extends Node3D

# position
# quaternion
@export var size := Vector2(1, 1)
var camera_pos: Vector3:
	get():
		return %Camera3D.position
	set(value):
		%Camera3D.position = value
@export var real_position := Vector3.ZERO
@export var real_quaternion := Quaternion.IDENTITY
@export var real_size := Vector2(1, 1)
@export var real_camera_pos := Vector3(0, 0, 1)

@export var z_near := 0.05
@export var z_far := 4000.0
@export var clip_at_screen_plane := false

@export var resolution := Vector2i(512, 512)

@export_node_path("Node3D") var world: NodePath

func _ready() -> void:
	if not Engine.is_editor_hint():
		$_EditorTools.visible = false
	update_projection()

func _process(delta: float) -> void:
	scale = Vector3.ONE
	update_projection()
	%SubViewport.size = resolution
	if Engine.is_editor_hint():
		_update_editor_tools()

func update_projection():
	var local_real_camera_pos := real_quaternion.inverse() * (real_camera_pos - real_position)
	var screen_scale := size / real_size
	var screen_scale_3d := Vector3(screen_scale.x, screen_scale.y, (screen_scale.x + screen_scale.y) / 2.0)
	var local_camera_pos := local_real_camera_pos * screen_scale_3d
	camera_pos = quaternion * local_camera_pos + position
	
	if clip_at_screen_plane:
		z_near = local_camera_pos.z
	
	%Camera3D.near = z_near
	%Camera3D.far = z_far
	%Camera3D.quaternion = quaternion
	%Camera3D.size = size.y / local_camera_pos.z * z_near
	%Camera3D.frustum_offset = -Vector2(local_camera_pos.x, local_camera_pos.y) / local_camera_pos.z * z_near

func _update_editor_tools():
	$_EditorTools.get_node("VirtualScreen").mesh.size = size
