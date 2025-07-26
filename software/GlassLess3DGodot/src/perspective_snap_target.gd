@tool
class_name PerspectiveSnapTarget extends Marker3D

@export var range_xy := 1.0
@export var range_z := 2.0
var range: Vector3:
	get():
		return Vector3(range_xy, range_xy, range_z)

@export var margin_xy := 1.0
@export var margin_z := 1.0
var margin: Vector3:
	get():
		return Vector3(margin_xy, margin_xy, margin_z)

signal perspective_snapped

func _process(_delta: float) -> void:
	if visible:
		if Engine.is_editor_hint():
			DebugDraw3D.draw_sphere_xf(
				Transform3D(Basis(global_basis.get_rotation_quaternion()), global_position)
					.scaled_local(range * 2),
				Color(Color.GREEN, 0.5)
			)
			DebugDraw3D.draw_sphere_xf(
				Transform3D(Basis(global_basis.get_rotation_quaternion()), global_position)
					.scaled_local((range + margin) * 2),
				Color(Color.RED, 0.5)
			)
