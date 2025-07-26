shader_type spatial;

uniform sampler2D image

void vertex() {
	// Called for every vertex the material is visible on.
}

void fragment() {
	ivec3 fc = ivec3(VERTEX.xyz * 10.0);
	int fcs = fc.x + fc.y + fc.z;
	ALBEDO = vec3(1.0, 0.0, 0.0);
	ALPHA = float(fcs % 2);
}

//void light() {
//	// Called for every pixel for every light affecting the material.
//	// Uncomment to replace the default light processing function with this one.
//}
