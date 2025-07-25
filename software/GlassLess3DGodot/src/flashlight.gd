# 手电筒
@tool
extends Node3D

@export_group("Properties")
@export var brightness := 2.0:
	set(value):
		brightness = value
		_update_light()

@export var focus := 45:
	set(value):
		focus = clamp(value, 10.0, 90.0)
		_update_light()

@export var colour := Color.WHITE:
	set(value):
		colour = value
		_update_light()

@export var range := 20.0:
	set(value):
		range = value
		_update_light()

@onready var spotlight := $SpotLight3D
@onready var light_cone := $SpotLight3D/LightCone
@onready var raycast := $RayCast3D

signal object_illuminated(object: Node3D)

func _ready() -> void:
	_setup_light()
	_update_light()

func _setup_light():
	spotlight.light_energy = brightness
	spotlight.spot_angle = focus
	spotlight.light_color = colour
	spotlight.spot_range = range
	
	if light_cone and light_cone.get_surface_override_material(0) == null:
		var cone_material = StandardMaterial3D.new()
		cone_material.emission = colour * 0.1
		cone_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		cone_material.albedo_color.a = 0.1

		light_cone.set_surface_override_material(0, cone_material)

func _update_light():
	if not is_node_ready(): return
	
	spotlight.light_energy = brightness
	spotlight.spot_angle = focus
	spotlight.light_color = colour
	spotlight.spot_range = range
	
	if light_cone:
		var cone_mesh = light_cone.mesh as CylinderMesh
		if cone_mesh == null:
			cone_mesh = CylinderMesh.new()
			light_cone.mesh = cone_mesh

		cone_mesh.top_radius = 0.0
		cone_mesh.bottom_radius = range * tan(deg_to_rad(focus))
		cone_mesh.height = range
