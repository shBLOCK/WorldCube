mod mediapipe;

use crate::mediapipe::FaceLandmarkerResult;
use pymeta::pymeta;
use rerun::components::ViewCoordinates;
use rerun::external::glam::{vec2, vec3, Vec2, Vec3Swizzles};
use rerun::external::re_sdk_types::view_coordinates::ViewDir;
use rerun::{Pinhole, Points2D, Points3D, Transform3D};
use std::sync::LazyLock;

static REC: LazyLock<rerun::RecordingStream> = LazyLock::new(|| {
    rerun::RecordingStreamBuilder::new("tauri-media-pipe-face")
        .spawn()
        .unwrap()
});

const HALF_FOV_Y: f32 = pymeta! {
    $from math import *;
    $fov_diag = 87;
    $ar = 1920 / 1080;
    $half_diag_length = tan(radians(fov_diag / 2));
    $half_vert_length = sin(atan(ar)) * half_diag_length;
    $atan(half_vert_length)$
};

#[tauri::command]
async fn handle_face_landmarker_result(result: FaceLandmarkerResult) {
    let cam_half_size = vec2(HALF_FOV_Y.tan() * result.aspect_ratio, HALF_FOV_Y.tan());

    REC.log(
        "camera",
        &Pinhole::from_focal_length_and_resolution(Vec2::ONE, cam_half_size * 2.0)
            .with_camera_xyz(ViewCoordinates::RUB)
            .with_image_plane_distance(1.0), // .with_image_from_camera(),
    )
    .unwrap();

    const LEFT_EYE_POINTS: [usize; 16] = [
        362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382,
    ];
    const RIGHT_EYE_POINTS: [usize; 16] = [
        33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7,
    ];

    let get_eye_p_2d = |points: &[usize], name: &str, color: rerun::Color| -> Vec2 {
        let p_scale = vec2(HALF_FOV_Y.tan() * result.aspect_ratio, HALF_FOV_Y.tan()) * 2.0;
        let points = points
            .iter()
            .map(|&i| (result.face_landmarks[i].pos.xy() - 0.5) * p_scale)
            .collect::<Vec<Vec2>>();

        REC.log(
            "camera/2d",
            &Transform3D::from_translation(cam_half_size.extend(0.0)),
        )
        .unwrap();

        REC.log(
            format!("camera/2d/{name}/points"),
            &Points2D::new(points.iter().copied())
                .with_colors([color])
                .with_radii([0.003]),
        )
        .unwrap();

        let point = points.iter().sum::<Vec2>() / points.len() as f32;

        REC.log(
            format!("camera/2d/{name}/point"),
            &Points2D::new([point])
                .with_colors([color])
                .with_radii([0.01]),
        )
        .unwrap();

        point
    };

    let left_eye_p_2d = get_eye_p_2d(&LEFT_EYE_POINTS, "left", rerun::Color::from_rgb(255, 0, 0));
    let right_eye_p_2d = get_eye_p_2d(
        &RIGHT_EYE_POINTS,
        "right",
        rerun::Color::from_rgb(0, 255, 0),
    );
}

pub fn run() {
    LazyLock::force(&REC);
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![handle_face_landmarker_result])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
