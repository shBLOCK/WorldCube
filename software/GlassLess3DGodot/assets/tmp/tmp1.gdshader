shader_type spatial;
render_mode unshaded;
//render_mode world_vertex_coords;

void fragment() {
	ivec3 fc = ivec3(VERTEX.xyz * 5.0);
	int fcs = fc.x + fc.y + fc.z;
	ALPHA = float(fcs % 2);
}

//void light() {
//	// Called for every pixel for every light affecting the material.
//	// Uncomment to replace the default light processing function with this one.
//}
