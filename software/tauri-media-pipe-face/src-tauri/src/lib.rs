mod mediapipe;

use crate::mediapipe::FaceLandmarkerResult;
use pymeta::pymeta;
use rerun::components::ViewCoordinates;
use rerun::external::glam::{vec2, vec3, Vec2, Vec3, Vec3Swizzles, Vec4Swizzles};
use rerun::{Arrows3D, LineStrips3D, Pinhole, Points2D, Points3D, SpawnOptions, Transform3D};
use serde::ser::SerializeStruct;
use serde::Serializer;
use std::net::UdpSocket;
use std::sync::LazyLock;
// use tokio::net::UdpSocket;

static REC: LazyLock<rerun::RecordingStream> = LazyLock::new(|| {
    rerun::RecordingStreamBuilder::new("tauri-media-pipe-face")
        .spawn_opts(&SpawnOptions {
            extra_args: vec!["--renderer".into(), "vulkan".into()], // for some reason rerun viewer doesn't work without this
            ..Default::default()
        })
        .unwrap()
});

static SOCKET: LazyLock<UdpSocket> = LazyLock::new(|| {
    let sock = UdpSocket::bind(("0.0.0.0", 8888)).unwrap();
    sock.connect(("127.0.0.1", 30001)).unwrap();
    sock
});

const HALF_FOV_Y: f32 = pymeta! {
    $from math import *;

    // $fov_diag = 87;

    // $fov_diag = 110;
    // $ar = 1920 / 1080;
    // $half_diag_length = tan(radians(fov_diag / 2));
    // $half_vert_length = sin(atan(ar)) * half_diag_length;
    // $atan(half_vert_length)$

    $radians(70 / 2)$
};
const STD_EYE_DISTANCE: f32 = 6.2;

#[tauri::command]
async fn handle_face_landmarker_result(result: FaceLandmarkerResult) {
    let cam_half_size = vec2(HALF_FOV_Y.tan() * result.aspect_ratio, HALF_FOV_Y.tan());

    REC.log(
        "camera/camera",
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
        let p_scale = vec2(-HALF_FOV_Y.tan() * result.aspect_ratio, -HALF_FOV_Y.tan()) * 2.0;
        let points = points
            .iter()
            .map(|&i| (result.face_landmarks[i].pos.xy() - 0.5) * p_scale)
            .collect::<Vec<Vec2>>();

        REC.log(
            "camera/camera/2d",
            &Transform3D::from_translation(cam_half_size.extend(0.0)).with_scale([1.0, -1.0, 1.0]),
        )
        .unwrap();

        REC.log(
            format!("camera/camera/2d/{name}/points"),
            &Points2D::new(points.iter().copied())
                .with_colors([color])
                .with_radii([0.003]),
        )
        .unwrap();

        let point = points.iter().sum::<Vec2>() / points.len() as f32;

        REC.log(
            format!("camera/camera/2d/{name}/point"),
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

    let left_eye_p = left_eye_p_2d.extend(-1.0);
    let right_eye_p = right_eye_p_2d.extend(-1.0);
    let head_right_dir = result.facial_transformation_matrix.x_axis.xyz();

    REC.log(
        "camera/head_right_dir",
        &Arrows3D::from_vectors([head_right_dir.normalize()]).with_radii([0.01]),
    )
    .unwrap();

    // normal vector of the q plane (plane formed by origin, left_eye_p and right_eye_p)
    let q_normal = left_eye_p.cross(right_eye_p).normalize();
    // head_right_dir, projected into the p plane
    let head_right_dir_q = (head_right_dir - q_normal * (head_right_dir.dot(q_normal))).normalize();
    let head_forward = (head_right_dir_q.cross(q_normal)).normalize();

    REC.log(
        "camera/head_forward",
        &Arrows3D::from_vectors([head_forward])
            .with_colors([rerun::Color::from_rgb(0, 0, 255)])
            .with_radii([0.01]),
    )
    .unwrap();

    // left_eye_p & right_eye_p with standard depth (has projection length of one when projected onto head_forward)
    let left_eye_p_std_depth = left_eye_p / (left_eye_p.dot(head_forward));
    let right_eye_p_std_depth = right_eye_p / (right_eye_p.dot(head_forward));

    REC.log(
        "camera/eye_p_std_depth",
        &Arrows3D::from_vectors([left_eye_p_std_depth, right_eye_p_std_depth])
            .with_colors([
                rerun::Color::from_rgb(255, 0, 0),
                rerun::Color::from_rgb(0, 255, 0),
            ])
            .with_radii([0.01]),
    )
    .unwrap();

    let eyes_p_distance_at_std_depth = left_eye_p_std_depth.distance(right_eye_p_std_depth);
    REC.log(
        "camera/eyes_p_distance_at_std_depth",
        &LineStrips3D::new([[left_eye_p_std_depth, right_eye_p_std_depth]])
            .with_radii([0.01])
            .with_labels([format!("{eyes_p_distance_at_std_depth}")])
            .with_colors([rerun::Color::from_rgb(255, 255, 255)]),
    )
    .unwrap();
    let eye_depth_scale = STD_EYE_DISTANCE / eyes_p_distance_at_std_depth;

    let left_eye_3d = left_eye_p_std_depth * eye_depth_scale;
    let right_eye_3d = right_eye_p_std_depth * eye_depth_scale;

    REC.log(
        "camera/eye_3d_arrow",
        &Arrows3D::from_vectors([left_eye_3d, right_eye_3d])
            .with_colors([
                rerun::Color::from_rgb(255, 0, 0),
                rerun::Color::from_rgb(0, 255, 0),
            ])
            .with_radii([0.03]),
    )
    .unwrap();

    REC.log(
        "camera/eye_3d",
        &Points3D::new([left_eye_3d, right_eye_3d])
            .with_colors([
                rerun::Color::from_rgb(255, 0, 0),
                rerun::Color::from_rgb(0, 255, 0),
            ])
            .with_radii([0.25]),
    )
    .unwrap();

    fn _serialize_vec3_obj<S: Serializer>(vec: &Vec3, serializer: S) -> Result<S::Ok, S::Error> {
        let mut s = serializer.serialize_struct("Vec3", 3)?;
        s.serialize_field("x", &vec.x)?;
        s.serialize_field("y", &vec.y)?;
        s.serialize_field("z", &vec.z)?;
        s.end()
    }

    #[derive(serde::Serialize)]
    struct Packet {
        #[serde(serialize_with = "_serialize_vec3_obj")]
        left_eye_3d: Vec3,
        #[serde(serialize_with = "_serialize_vec3_obj")]
        right_eye_3d: Vec3,
    }

    let pkt = serde_json::to_string(&Packet {
        left_eye_3d,
        right_eye_3d,
    }).unwrap();

    // println!("{}", pkt);
    SOCKET.send(pkt.as_bytes()).unwrap();
}

pub fn run() {
    LazyLock::force(&REC);
    LazyLock::force(&SOCKET);

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![handle_face_landmarker_result])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
