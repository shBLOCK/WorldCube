use nalgebra_glm::{DMat4, DVec3, Mat4};
use pymeta::pymeta;
use serde::{Deserialize, Deserializer};

#[derive(Copy, Clone, Debug)]
struct NormalizedLandmark {
    pos: DVec3,
    visibility: f64,
}

impl<'de> Deserialize<'de> for NormalizedLandmark {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(serde::Deserialize)]
        struct _NormalizedLandmark {
            x: f64,
            y: f64,
            z: f64,
            visibility: f64,
        }

        let _NormalizedLandmark {
            x,
            y,
            z,
            visibility,
        } = _NormalizedLandmark::deserialize(deserializer)?;

        Ok(Self {
            pos: DVec3::new(x, y, z),
            visibility,
        })
    }
}

fn _deserialize_mat4<'de, D: Deserializer<'de>>(deserializer: D) -> Result<DMat4, D::Error> {
    #[derive(serde::Deserialize)]
    struct _Matrix {
        data: [f64; 4 * 4]
    }
    let mat = _Matrix::deserialize(deserializer)?;
    pymeta!(Ok(DMat4::new(
        $import itertools;
        $for col, row in itertools.product(range(4), range(4)):{
            mat.data[$col + row * 4$],
        }
    )))
}

const FACE_LANDMARK_N: usize = 478;

#[serde_with::serde_as]
#[derive(Clone, serde::Deserialize, Debug)]
#[serde(rename_all = "camelCase")]
struct FaceLandmarkerResult {
    #[serde_as(as = "[_; FACE_LANDMARK_N]")]
    face_landmarks: [NormalizedLandmark; FACE_LANDMARK_N],
    #[serde(deserialize_with = "_deserialize_mat4")]
    facial_transformation_matrix: DMat4,
}

#[tauri::command]
fn handle_face_landmarker_result(result: FaceLandmarkerResult) {
    // println!("{:#?}", result);
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![handle_face_landmarker_result])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
