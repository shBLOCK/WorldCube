@tool
class_name Utils extends Node

static func read_line_from(stream: StreamPeerTCP) -> String:
	var partial_string = ""
	stream.poll()
	var c = String.chr(stream.get_u8())
	while c != "\n":
		partial_string += c
		stream.poll()
		c = String.chr(stream.get_u8())
	return partial_string

static func parse_json_vector3(data: Dictionary) -> Vector3:
	return Vector3(data["x"], data["y"], data["z"])
