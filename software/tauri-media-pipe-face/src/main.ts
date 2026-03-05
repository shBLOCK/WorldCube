// import {invoke} from "@tauri-apps/api/core";
import {DrawingUtils, FaceLandmarker, FaceLandmarkerResult, FilesetResolver} from "@mediapipe/tasks-vision";
import {invoke} from "@tauri-apps/api/core";

const canvas = document.getElementById("canvas") as HTMLCanvasElement;

async function loadFaceLandmarker() {
    return await FaceLandmarker.createFromOptions(
        await FilesetResolver.forVisionTasks("node_modules/@mediapipe/tasks-vision/wasm"),
        {
            baseOptions: {
                modelAssetPath: "src/assets/face_landmarker.task",
                delegate: "GPU"
            },
            runningMode: "VIDEO",
            outputFacialTransformationMatrixes: true,
            numFaces: 1
        }
    );
}

let faceLandmarker = await loadFaceLandmarker();

const camera = document.getElementById("camera") as HTMLVideoElement;

navigator.mediaDevices.getUserMedia({video: true}).then(stream => {
    camera.srcObject = stream;
    camera.addEventListener("loadeddata", handleCameraFrame)
});

const drawingUtils = new DrawingUtils(canvas.getContext("2d") as CanvasRenderingContext2D);

let lastCameraTime = -1;
let faceLandmarkerResult: FaceLandmarkerResult | null = null;

async function handleCameraFrame() {
    const aspectRatio = camera.videoWidth / camera.videoHeight;
    const visualWidth = 720;
    const visualHeight = visualWidth / aspectRatio;
    camera.style.width = canvas.style.width = `${visualWidth}px`;
    camera.style.height = canvas.style.height = `${visualHeight}px`;
    canvas.width = visualWidth;
    canvas.height = visualHeight

    const startMs = performance.now();
    if (lastCameraTime !== camera.currentTime) {
        lastCameraTime = camera.currentTime;
        faceLandmarkerResult = faceLandmarker.detectForVideo(camera, startMs);

        if (faceLandmarkerResult.faceLandmarks.length >= 1) {
            //TODO: optimize, don't serialize to json
            const _ = invoke("handle_face_landmarker_result", {
                result: {
                    aspectRatio: aspectRatio,
                    faceLandmarks: faceLandmarkerResult.faceLandmarks[0],
                    facialTransformationMatrix: faceLandmarkerResult.facialTransformationMatrixes[0]
                }
            });
        }
    }

    if (faceLandmarkerResult !== null && faceLandmarkerResult.faceLandmarks) {
        for (const landmarks of faceLandmarkerResult.faceLandmarks) {
            // drawingUtils.drawConnectors(
            //     landmarks,
            //     FaceLandmarker.FACE_LANDMARKS_TESSELATION,
            //     {color: "#C0C0C070", lineWidth: 1}
            // );
            drawingUtils.drawConnectors(
                landmarks,
                FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE,
                {color: "#FF3030"}
            );
            // drawingUtils.drawConnectors(
            //     landmarks,
            //     FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW,
            //     {color: "#FF3030"}
            // );
            drawingUtils.drawConnectors(
                landmarks,
                FaceLandmarker.FACE_LANDMARKS_LEFT_EYE,
                {color: "#30FF30"}
            );
            // drawingUtils.drawConnectors(
            //     landmarks,
            //     FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW,
            //     {color: "#30FF30"}
            // );
            // drawingUtils.drawConnectors(
            //     landmarks,
            //     FaceLandmarker.FACE_LANDMARKS_FACE_OVAL,
            //     {color: "#E0E0E0"}
            // );
            // drawingUtils.drawConnectors(
            //     landmarks,
            //     FaceLandmarker.FACE_LANDMARKS_LIPS,
            //     {color: "#E0E0E0"}
            // );
            // drawingUtils.drawConnectors(
            //     landmarks,
            //     FaceLandmarker.FACE_LANDMARKS_RIGHT_IRIS,
            //     {color: "#FF3030"}
            // );
            // drawingUtils.drawConnectors(
            //     landmarks,
            //     FaceLandmarker.FACE_LANDMARKS_LEFT_IRIS,
            //     {color: "#30FF30"}
            // );
        }
    }

    window.requestAnimationFrame(handleCameraFrame);
}
