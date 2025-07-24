@tool
extends TextureRect

## Sync the resolution of the viewport with this node
@export var sync_resolution := true

func _get_configuration_warnings() -> PackedStringArray:
	return PackedStringArray([] if get_child_count() > 0 and get_child(0) is Viewport3D else ["The first child must be a Viewport3D isntance."])

func _process(delta: float) -> void:
	var first_child = get_child(0) if get_child_count() > 0 else null
	if first_child is not Viewport3D:
		return
	
	var viewport := get_child(0) as Viewport3D
	self.texture.viewport_path = NodePath(viewport.name + "/SubViewport")
	if sync_resolution:
		viewport.resolution = size
		stretch_mode = TextureRect.STRETCH_KEEP
	else:
		stretch_mode = TextureRect.STRETCH_SCALE
