@tool
extends Node

func read_line_from(stream: StreamPeerTCP) -> Variant:
	var buffer := PackedByteArray()
	while true:
		while stream.get_available_bytes() == 0:
			if stream.poll() != OK:
				return null
			if stream.get_status() != StreamPeerTCP.STATUS_CONNECTED:
				return null
		var byte := stream.get_u8()
		if byte == 0x0A:
			return buffer.get_string_from_ascii()
		buffer.append(byte)
	return null

func parse_json_vector3(data: Array) -> Vector3:
	return Vector3(data[0], data[1], data[2])

func parse_json_transform3d(data: Array) -> Transform3D:
	return Transform3D(
		parse_json_vector3(data[0]),
		parse_json_vector3(data[1]),
		parse_json_vector3(data[2]),
		parse_json_vector3(data[3])
	)

func tcp_json_client(host: String, port: int, callback: Callable) -> Thread:
	var thread_main := func():
		var json := JSON.new()
		while true:
			var conn := StreamPeerTCP.new()
			print("Trying to connect to %s:%d." % [host, port])
			if conn.connect_to_host(host, port) == OK and conn.poll() == OK and conn.get_status() == StreamPeerTCP.Status.STATUS_CONNECTED:
				print("Connected to %s:%d." % [host, port])
				while conn.get_status() == StreamPeerTCP.Status.STATUS_CONNECTED:
					var line = Utils.read_line_from(conn)
					if line == null:
						continue
					var pkt = json.parse_string(line)
					if pkt == null:
						continue
					callback.call(pkt)
				print("Connection to %s:%d closed." % [host, port])
			await get_tree().create_timer(2).timeout
	
	var thread := Thread.new()
	thread.start(thread_main)
	return thread
