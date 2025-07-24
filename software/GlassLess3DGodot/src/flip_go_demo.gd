extends Node

var _eye_tracking_conn_thread := Thread.new()
var left_eye_3d := Vector3.ZERO
var right_eye_3d := Vector3.ZERO

func _eye_tracking_conn_thread_main():
	var json := JSON.new()
	while true:
		var conn := StreamPeerTCP.new()
		conn.connect_to_host("127.0.0.1", 30001)
		conn.poll()
		print("Connected to eye tracking server.")
		while conn.get_status() == StreamPeerTCP.Status.STATUS_CONNECTED:
			var line := Utils.read_line_from(conn)
			var pkt = json.parse_string(line)
			if pkt == null:
				continue
			left_eye_3d = Utils.parse_json_vector3(pkt["left_eye_3d"])
			right_eye_3d = Utils.parse_json_vector3(pkt["right_eye_3d"])
		print("Connection closed!")
		await get_tree().create_timer(1).timeout

func _ready() -> void:
	_eye_tracking_conn_thread.start(_eye_tracking_conn_thread_main)

@onready var FG_A_VP := %FG_A_VP
@onready var FG_B_VP := %FG_B_VP

func _process(delta: float) -> void:
	const FG_SCALE := 1.0
	const FG_SIZE := Vector2(34.5, 21.5)
	const FG_INNER_EDGE := 0.5
	const FG_TOP_CAM_LOCAL_OFFSET_FROM_TOP_SCREEN_CENTER := Vector3(0, FG_SIZE.y / 2 + 1.8, -1.0)
	var fg_angle := deg_to_rad(90)
	
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
	FG_A_VP.real_camera_pos = eye_pos
	FG_B_VP.real_camera_pos = eye_pos
	
	FG_A_VP.position = FG_A_VP.real_position * FG_SCALE
	FG_A_VP.size = FG_A_VP.real_size * FG_SCALE
	FG_A_VP.quaternion = FG_A_VP.real_quaternion
	FG_B_VP.position = FG_B_VP.real_position * FG_SCALE
	FG_B_VP.size = FG_B_VP.real_size * FG_SCALE
	FG_B_VP.quaternion = FG_B_VP.real_quaternion
