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

func _process(delta: float) -> void:
	var eye_pos := (left_eye_3d + right_eye_3d) / 2
	var window_screen = %Window.current_screen
	var window_pos = Vector2(%Window.position - DisplayServer.screen_get_position(window_screen))
	var screen_size = Vector2(DisplayServer.screen_get_size(window_screen))
	var window_a = window_pos / screen_size - Vector2(0.5, 0.5)
	var window_b = (window_pos + Vector2(%Window.size)) / screen_size - Vector2(0.5, 0.5)
	const SCREEN_SIZE := Vector2(34.5, 21.5)
	%Viewport3D.real_size = SCREEN_SIZE * (window_b - window_a)
	var real_position = Vector2(0, -%Viewport3D.real_size.y / 2 - 0.6) + (window_a + window_b) / 2 * Vector2(1, -1) * SCREEN_SIZE
	%Viewport3D.real_position = Vector3(real_position.x, real_position.y, 0)
	%Viewport3D.size = Vector2(SCREEN_SIZE * (5.0 / %Viewport3D.real_size.y))
	%Viewport3D.real_camera_pos = eye_pos * Vector3(-1, 1, -1)
