@tool
extends EditorScript

func _run() -> void:
	var root := get_scene().get_node("World/Matrix")
	for child in root.get_children():
		root.remove_child(child)
	const N := 5
	for x in range(-N, N+1):
		for y in range(-N, N+1):
			for z in range(-N, N+1):
				var element = preload("res://src/tmp/matrix_element.tscn").instantiate()
				element.position = Vector3(x, y, z)
				root.add_child(element)
				element.owner = get_scene()
