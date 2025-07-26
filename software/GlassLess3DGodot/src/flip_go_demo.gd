extends Node

var left_eye_3d := Vector3.ZERO
var right_eye_3d := Vector3.ZERO
var fg_quaternion := Quaternion.from_euler(Vector3(-PI / 2, 0, 0))
var wand_transform := Transform3D.IDENTITY
var handheld_display_transform := Transform3D.IDENTITY
var joystick_input := Vector2.ZERO
var joystick_down := false
signal joystick_pressed
signal joystick_released
signal rotary_encoder(dir: int)

func _ready() -> void:
	Utils.tcp_json_client("127.0.0.1", 30001, func(pkt): # Eye Positioning
		left_eye_3d = Utils.parse_json_vector3(pkt["left_eye_3d"])
		right_eye_3d = Utils.parse_json_vector3(pkt["right_eye_3d"])
	)
	Utils.tcp_json_client("127.0.0.1", 30002, func(pkt): # IMU
		fg_quaternion = Quaternion(pkt["x"], pkt["y"], pkt["z"], pkt["w"])
	)
	Utils.tcp_json_client("127.0.0.1", 30003, func(pkt): # Wand Interaction
		if pkt["type"] == "rot":
			rotary_encoder.emit(pkt["dir"])
		elif pkt["type"] == "btn_pressed":
			joystick_pressed.emit()
			joystick_down = true
		elif pkt["type"] == "btn_released":
			joystick_released.emit()
			joystick_down = false
		elif pkt["type"] == "joystick":
			joystick_input = Vector2(pkt["x"], pkt["y"])
	)
	Utils.tcp_json_client("127.0.0.1", 30004, func(pkt): # Tag tracking
		if pkt["name"] == "handhold screen":
			handheld_display_transform = Utils.parse_json_transform3d(pkt["transform"])
		elif pkt["name"] == "wand":
			wand_transform = Utils.parse_json_transform3d(pkt["transform"])
	)

@onready var FG_A_VP := %FG_A_VP
@onready var FG_B_VP := %FG_B_VP
@onready var HH_VP := %HH_VP

func _process(delta: float) -> void:
	const FG_SCALE := 1.0
	const FG_SIZE := Vector2(34.5, 21.5)
	const FG_INNER_EDGE := 0.6
	const FG_TOP_CAM_LOCAL_OFFSET_FROM_TOP_SCREEN_CENTER := Vector3(0, FG_SIZE.y / 2 + 1.8, -1.0)
	var fg_angle := PI - fg_quaternion.normalized().get_euler(EULER_ORDER_ZYX).z
	
	FG_A_VP.real_size = FG_SIZE
	FG_B_VP.real_size = FG_SIZE
	
	FG_A_VP.real_position = Vector3.ZERO
	FG_A_VP.real_quaternion = Quaternion.from_euler(Vector3(-PI / 2, 0, 0))
	
	var fg_b_transform := Transform3D()\
		.translated(Vector3.UP * (FG_SIZE.y / 2 + FG_INNER_EDGE))\
		.rotated(Vector3.RIGHT, PI / 2 - fg_angle)\
		.translated(Vector3(0, 0, -1) * (FG_SIZE.y / 2 + FG_INNER_EDGE))
	
	FG_B_VP.real_position = fg_b_transform * Vector3.ZERO
	FG_B_VP.real_quaternion = Quaternion.from_euler(Vector3(PI / 2 - fg_angle, 0, 0))
	
	var eye_pos := FG_TOP_CAM_LOCAL_OFFSET_FROM_TOP_SCREEN_CENTER\
		+ (left_eye_3d + right_eye_3d) / 2 * Vector3(-1, 1, -1)
	eye_pos = fg_b_transform * eye_pos
	%GlassLess3DCameraController.eye_pos_raw = eye_pos
	
	FG_A_VP.position = FG_A_VP.real_position * FG_SCALE
	FG_A_VP.size = FG_A_VP.real_size * FG_SCALE
	FG_A_VP.quaternion = FG_A_VP.real_quaternion
	FG_B_VP.position = FG_B_VP.real_position * FG_SCALE
	FG_B_VP.size = FG_B_VP.real_size * FG_SCALE
	FG_B_VP.quaternion = FG_B_VP.real_quaternion
	
	#FG_A_VP.position += $PlayerCenter.position
	#FG_B_VP.position += $PlayerCenter.position
	
	const HH_SIZE := Vector2(15.4, 8.55) # Handheld Display
	const HH_OFFSET_FROM_TAG_PATTERN := Vector3(0.0, 0.25, 2.2)
	var global_hh_transform := fg_b_transform * handheld_display_transform.translated_local(HH_OFFSET_FROM_TAG_PATTERN).translated(FG_TOP_CAM_LOCAL_OFFSET_FROM_TOP_SCREEN_CENTER)
	HH_VP.real_position = global_hh_transform.origin
	HH_VP.real_quaternion = global_hh_transform.basis.rotated(global_hh_transform.basis.z, PI).get_rotation_quaternion()

	HH_VP.real_size = HH_SIZE
	HH_VP.position = HH_VP.real_position
	HH_VP.size = HH_VP.real_size
	HH_VP.quaternion = HH_VP.real_quaternion
	
	%Wand.transform = fg_b_transform * wand_transform.translated(FG_TOP_CAM_LOCAL_OFFSET_FROM_TOP_SCREEN_CENTER)

func _on_perspective_snap_target_perspective_snapped() -> void:
	$World/PerspectiveSplicingContainer/PerspectiveSplicingPart2.depth = $World/PerspectiveSplicingContainer/PerspectiveSplicingPart.depth
	$World/PerspectiveSplicingContainer/PerspectiveSnapTarget.hide()

func _on_prj_surf_perspective_snap_target_perspective_snapped() -> void:
	$World/ProjectSurface/ProjectSurfaceProjector.enabled = false
	$World/ProjectSurface/ProjectSurfaceProjector/RenderLayerModifier.layers = 0b11
