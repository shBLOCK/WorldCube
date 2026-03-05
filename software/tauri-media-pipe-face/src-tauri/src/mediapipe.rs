use rerun::external::glam::{Mat4, Vec3};
use pymeta::pymeta;
use serde::{Deserialize, Deserializer};

#[derive(Copy, Clone, Debug)]
pub struct NormalizedLandmark {
    pub pos: Vec3,
    pub visibility: f32,
}

impl<'de> Deserialize<'de> for NormalizedLandmark {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(serde::Deserialize)]
        struct _NormalizedLandmark {
            x: f32,
            y: f32,
            z: f32,
            visibility: f32,
        }

        let _NormalizedLandmark {
            x,
            y,
            z,
            visibility,
        } = _NormalizedLandmark::deserialize(deserializer)?;

        Ok(Self {
            pos: Vec3::new(x, y, z),
            visibility,
        })
    }
}

fn _deserialize_mat4<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Mat4, D::Error> {
    #[derive(serde::Deserialize)]
    struct _Matrix {
        data: [f32; 4 * 4],
    }
    let mat = _Matrix::deserialize(deserializer)?;
    pymeta!(Ok(Mat4::from_cols_array(
        $import itertools;
        &[
            $for col, row in itertools.product(range(4), range(4)):{
                mat.data[$col + row * 4$],
            }
        ]
    )))
}

#[serde_with::serde_as]
#[derive(Clone, serde::Deserialize, Debug)]
#[serde(rename_all = "camelCase")]
pub struct FaceLandmarkerResult {
    pub aspect_ratio: f32,
    #[serde_as(as = "[_; FaceLandmarkerResult::FACE_LANDMARK_N]")]
    pub face_landmarks: [NormalizedLandmark; Self::FACE_LANDMARK_N],
    #[serde(deserialize_with = "_deserialize_mat4")]
    pub facial_transformation_matrix: Mat4,
}

impl FaceLandmarkerResult {
    const FACE_LANDMARK_N: usize = 478;
}
