@tool
extends Node3D

@export var std_depth := 1.0
@export var fov := 75.0

@onready var Camera := %Camera3D
@onready var RotScaleMarker := %RotScaleMarker
@onready var SnapTarget := %PerspectiveSnapTarget

func _process(_delta: float) -> void:
	Camera.position = Vector3(0, 0, std_depth)
	SnapTarget.position = Camera.position
	Camera.fov = fov
	for part in get_children():
		if part is not PerspectiveSplicingPart:
			continue
		part.quaternion = RotScaleMarker.quaternion
		part.scale = RotScaleMarker.scale * (part.depth / std_depth)
		part.position = Vector3(0, 0, -(part.depth - std_depth))
