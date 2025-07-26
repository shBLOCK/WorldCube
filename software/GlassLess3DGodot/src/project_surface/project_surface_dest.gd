@tool
extends Node3D

@export var projectors: Array[ProjectSurfaceProjector] = []
var _projector_overlay_materials: Array[ShaderMaterial] = []
var _linked_overlay_material = null
var _geometry_instances: Array[GeometryInstance3D] = []

@export_tool_button("Update")
var _update_button = func():
	rebuild_geometry_instances_list()
	apply()

func rebuild_geometry_instances_list():
	_geometry_instances.clear()
	for node in find_children("*"):
		if node is GeometryInstance3D:
			_geometry_instances.append(node)

func apply():
	_projector_overlay_materials.clear()
	for projector in projectors:
		var material := ShaderMaterial.new()
		material.shader = preload("res://src/project_surface/dest_overlay.gdshader")
		_projector_overlay_materials.append(material)
	
	if not _projector_overlay_materials.is_empty():
		_linked_overlay_material = _projector_overlay_materials[0]
		for i in range(1, len(_projector_overlay_materials)):
			_projector_overlay_materials[i - 1].next_pass = _projector_overlay_materials[i]
	
	for gi in _geometry_instances:
		gi.material_overlay = _linked_overlay_material

func _enter_tree() -> void:
	rebuild_geometry_instances_list()
	apply()

func _process(delta: float) -> void:
	for i in len(projectors):
		var projector := projectors[i]
		var material := _projector_overlay_materials[i]
		projector._update_dest_shader_uniforms(material)
