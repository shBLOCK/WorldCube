@tool
extends Marker3D

@export var viewports: Array[Viewport3D] = []
var snap_target = null
var _snap_target_point := Vector3()
var _snap_animation_progress := 0.0
var _snapped_event_emitted := true

var eye_pos_raw := Vector3()
var eye_pos := Vector3()

func _process(delta: float) -> void:
	var old_snap_target = snap_target
	if snap_target != null:
		if not snap_target.visible:
			snap_target = null
		else:
			var offset: Vector3 = snap_target.to_local(eye_pos_raw)
			if (offset / (snap_target.range + snap_target.margin)).length() > 1.0:
				snap_target = null
	else:
		for node in get_tree().get_nodes_in_group("PerspectiveSnapTargets"):
			var target := node as PerspectiveSnapTarget
			if not target.visible:
				continue
			var offset := target.to_local(eye_pos_raw)
			if (offset / target.range).length() <= 1.0:
				snap_target = target
				break
	
	if snap_target != old_snap_target:
		if snap_target != null:
			_snap_target_point = snap_target.global_position
		_snapped_event_emitted = false
	
	_snap_animation_progress = clamp(_snap_animation_progress + delta * 2.0 * (1 if snap_target != null else -1), 0.0, 1.0)
	if snap_target != null and not _snapped_event_emitted and _snap_animation_progress == 1.0:
		snap_target.perspective_snapped.emit()
		_snapped_event_emitted = true
	
	eye_pos = lerp(
		eye_pos_raw, _snap_target_point,
		Tween.interpolate_value(0.0, 1.0, _snap_animation_progress, 1.0, Tween.TRANS_SINE, Tween.EASE_OUT)
	)
	
	for viewport in viewports:
		viewport.real_camera_pos = eye_pos
