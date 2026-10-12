import cv2
import numpy as np
import mediapipe as mp
from fastapi import APIRouter,HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from fastapi import Query
import json
import io
from faster_whisper import WhisperModel
import numpy as np_audio
from classify import classify_gaze_binary


router=APIRouter(
    prefix="/face",
    tags=["face"]
)

calibration_store: dict = {}   # session_id -> list of blendshape dicts
session_thresholds: dict = {}  # session_id -> computed thresholds

def get_eye_state(result):

    if not result.face_landmarks:
        return {
            "eyes_detected": False
        }

    blendshapes = result.face_blendshapes[0]

    scores = {
        c.category_name: c.score
        for c in blendshapes
    }

    left_blink = scores.get("eyeBlinkLeft", 0)
    right_blink = scores.get("eyeBlinkRight", 0)

    look_down_left = scores.get("eyeLookDownLeft", 0)
    look_down_right = scores.get("eyeLookDownRight", 0)


    look_up_left = scores.get("eyeLookUpLeft", 0)
    look_up_right = scores.get("eyeLookUpRight", 0)

    look_down = (look_down_left + look_down_right) / 2
    look_up = (look_up_left + look_up_right) / 2

    blink = (left_blink + right_blink) / 2

    if blink > 0.5:
        eye_state = "CLOSED"

    elif look_down > 0.4:
        eye_state = "LOOKING_DOWN"

    elif look_up > 0.4:
        eye_state = "LOOKING_UP"

    else:
        eye_state = "CENTER"

    return {
        "eyes_detected": True,
        "eye_state": eye_state,
        "blink_score": blink,
        "look_down_score": look_down,
        "look_up_score": look_up,
        "look_down_left": look_down_left,
        "look_down_right": look_down_right,
        "look_up_left": look_up_left,
        "look_up_right": look_up_right
    }



print(" Loading MediaPipe model...")

base_options = python.BaseOptions(
    model_asset_path="face_landmarker.task"
)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
    num_faces=2
)

detector = vision.FaceLandmarker.create_from_options(
    options
)

print(" Loading Whisper model...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
print(" Whisper model loaded")


def compute_thresholds(samples: list) -> dict:
    """Derive per-user gaze thresholds from calibration blendshape samples."""
    import statistics

    keys = ['eyeLookDownLeft', 'eyeLookDownRight', 'eyeLookUpLeft', 'eyeLookUpRight',
            'eyeLookInLeft', 'eyeLookOutLeft', 'eyeLookInRight', 'eyeLookOutRight']

    avgs = {k: [s.get(k, 0.0) for s in samples] for k in keys}

    avg_down = [(avgs['eyeLookDownLeft'][i] + avgs['eyeLookDownRight'][i]) / 2 for i in range(len(samples))]
    avg_up   = [(avgs['eyeLookUpLeft'][i]   + avgs['eyeLookUpRight'][i])   / 2 for i in range(len(samples))]
    left_h   = [(avgs['eyeLookOutLeft'][i]  + avgs['eyeLookInRight'][i])   / 2 for i in range(len(samples))]
    right_h  = [(avgs['eyeLookOutRight'][i] + avgs['eyeLookInLeft'][i])    / 2 for i in range(len(samples))]
    horiz    = [max(left_h[i], right_h[i]) for i in range(len(samples))]

    down_baseline       = statistics.mean(avg_down)
    vertical_threshold  = statistics.mean(avg_up)   + statistics.stdev(avg_up)   if len(avg_up) > 1 else 0.20
    horizontal_threshold = statistics.mean(horiz)   + statistics.stdev(horiz)    if len(horiz) > 1 else 0.25

    return {
        "down_baseline":        round(down_baseline, 4),
        "vertical_threshold":   round(vertical_threshold, 4),
        "horizontal_threshold": round(horizontal_threshold, 4),
    }


@router.websocket("/ws/interview")
async def interview_websocket(websocket: WebSocket):
    print(" WebSocket endpoint called")
    await websocket.accept()
    print(" WebSocket accepted")
    
    session_id = int(websocket.query_params.get("session_id", 0))
    thresholds = session_thresholds.get(session_id)
    if thresholds:
        print(f" Using calibrated thresholds for session {session_id}: {thresholds}")
    else:
        print(f"  No calibration found for session_id={session_id}, using defaults")

    try:
        while True:
            # print("⏳ Waiting for frame...")
            data = await websocket.receive_bytes()
            # print("📦 Received:", len(data), "bytes")
            image_array = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if frame is None:
                print("Could not decode frame")
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = detector.detect(mp_image)
            face_count = len(result.face_landmarks)
            gaze = "UNKNOWN"
            if face_count > 0:
                blendshape_dict = {c.category_name: c.score for c in result.face_blendshapes[0]}
                gaze = classify_gaze_binary(blendshape_dict, thresholds=thresholds)
                print(f"Gaze: {gaze}")
            await websocket.send_json({
                "face_count": face_count,
                "face_detected": face_count > 0,
                "gaze": gaze
            })
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(" WebSocket error:", repr(e))


@router.websocket("/ws/calibration")
async def calibration_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = id(websocket)
    calibration_store[session_id] = []
    print(f"[+] Calibration session started: {session_id}")

    pending_meta = None

    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                pending_meta = json.loads(message["text"])
                # print(f"    Meta: {pending_meta}")

            elif "bytes" in message:
                if pending_meta is None:
                    print("    [!] Image received without metadata, skipping.")
                    continue

                # print("Message received",message['bytes'])
                point_name = pending_meta.get("point", "unknown").replace(" ", "_") 
                # print(f"    Received image for point: {point_name}")
                image_array = np.frombuffer(message['bytes'], dtype=np.uint8)
                frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                # print("Frame shape:", frame.shape)
                # BGR -> RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # OpenCV -> MediaPipe
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                result = detector.detect(mp_image)
                # print(result.face_blendshapes[0])
                face_count = len(result.face_landmarks)
                print("Faces detected:", face_count)
                blendshape_dict = {c.category_name: c.score for c in result.face_blendshapes[0]}
                calibration_store[session_id].append(blendshape_dict)
                gaze = classify_gaze_binary(blendshape_dict)
                print(f"    [{point_name}] gaze={gaze} ({len(calibration_store[session_id])}/9)")

                pending_meta = None

                if len(calibration_store[session_id]) == 9:
                    thresholds = compute_thresholds(calibration_store[session_id])
                    session_thresholds[session_id] = thresholds
                    print(f"[✓] Calibration complete. Thresholds: {thresholds}")
                    await websocket.send_text(json.dumps({
                        "status": "complete",
                        "points_received": 9,
                        "session_id": str(session_id),
                        "thresholds": thresholds,
                    }))

    except WebSocketDisconnect:
        print(f"[-] Calibration session {session_id} disconnected. Points: {len(calibration_store.get(session_id, []))}")
    except Exception as e:
        print(f"🔥 Calibration error: {repr(e)}")


@router.websocket("/ws/transcript")
async def transcript_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "unknown")
    print(f"[+] Transcript session started: {session_id}")

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            print(f"[transcript] Received {len(audio_bytes)} bytes of audio")

            # Raw PCM float32 mono 16kHz expected from frontend
            audio_array = np_audio.frombuffer(audio_bytes, dtype=np_audio.float32)

            segments, _ = whisper_model.transcribe(
                audio_array,
                beam_size=5,
                vad_filter=True,
                language="en",
                condition_on_previous_text=True,
                no_speech_threshold=0.6,
                temperature=0.0,
            )
            transcript = " ".join(seg.text.strip() for seg in segments if seg.text.strip())

            print(f"[transcript] {transcript}")
            await websocket.send_json({
                "session_id": session_id,
                "transcript": transcript,
            })

    except WebSocketDisconnect:
        print(f"[-] Transcript session {session_id} disconnected")
    except Exception as e:
        print(f" Transcript error: {repr(e)}")

