@tool
extends Node3D

@export_flags_3d_render var layers: int = 0:
	set(value):
		layers = value
		_update_layer_mask()

var _visual_instances: Array[VisualInstance3D] = []

func _rebuild():
	_visual_instances.clear()
	for child in find_children("*"):
		if child is VisualInstance3D:
			_visual_instances.append(child)

func _update_layer_mask():
	for instance in _visual_instances:
		instance.layers = layers

func _enter_tree() -> void:
	_rebuild()
	_update_layer_mask()

func _on_child_entered_tree(node: Node) -> void:
	if node is VisualInstance3D:
		node.layers = layers
		_visual_instances.append(node)

func _on_child_exiting_tree(node: Node) -> void:
	if node is VisualInstance3D:
		_visual_instances.erase(node)
