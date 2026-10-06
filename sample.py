from openai import AzureOpenAI #type: ignore
import os
from dotenv import load_dotenv
load_dotenv()
def get_azure_response(text):  
    try:
        endpoint=os.getenv("AI_ENDPOINT")
        deployment=os.getenv("AI_MODEL")
        subscription_key=os.getenv("AI_CONTENT_KEY")
        api_version=os.getenv("AI_CONTENT_VERSION")
        print("=+="*30)
        print(endpoint, deployment, subscription_key, api_version)
        
        if not subscription_key:
            return "Error: AZURE_OPENAI_KEY not found in environment variables"
        
        client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
        )
        
        response = client.chat.completions.create(
        messages=[
        {
        "role": "system",
        "content": "You are a helpful assistant.",
        },
        {
        "role": "user",
        "content": text,
        }
        ],
        
        model=deployment
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return {"Azure Error": {str(e)},
        "endpoint": {endpoint},
        "deployment": {deployment},
        "subscription_key": {subscription_key},
        "api_version": {api_version}
        }
        
if __name__ == "__main__":
    print(get_azure_response("Hello, how are you?"))




from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2
import numpy as np
import datetime

app = FastAPI()


# @app.websocket("/ws/interview")
# async def interview_websocket(websocket: WebSocket):
#     await websocket.accept()
#     print("Client connected")

#     try:
#         while True:

#             # Receive binary JPEG frame
#             data = await websocket.receive_bytes()

#             # Convert bytes -> numpy array
#             image_array = np.frombuffer(data, dtype=np.uint8)

#             # Decode JPEG -> OpenCV image
#             frame = cv2.imdecode(
#                 image_array,
#                 cv2.IMREAD_COLOR
#             )

#             if frame is None:
#                 print("Invalid frame")
#                 continue

#             print(
#                 f"Received frame: "
#                 f"{frame.shape[1]}x{frame.shape[0]}"
#             )
#             print(f"Timestamp: {datetime.datetime.now()}")
           

#             face_cascade =  cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

#             eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
#             for (x, y, w, h) in faces:
#                 cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
#                 roi_gray = gray[y:y+h, x:x+w]
#                 roi_color = frame[y:y+h, x:x+w]
                
#                 # Detect eyes within the face region
#                 eyes = eye_cascade.detectMultiScale(roi_gray)
#                 for (ex, ey, ew, eh) in eyes:
#                     cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
            
#             cv2.imshow('Eye Tracking', frame)
            
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#             # ------------------------------------
#             # Your face detection here
#             # ------------------------------------

#             # Example:
#             #
#             # result = detect_face(frame)
#             #
#             # violations = detect_violations(frame)

#             await websocket.send_json({
#                 "status": "received",
#                 "message": "Frame processed"
#             })

#     except WebSocketDisconnect:

#         print("Client disconnected")

#     except Exception as e:

#         print("WebSocket error:", e)


import cv2
import numpy as np
import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


# ============================================================
# Load Haar Cascades ONCE when the application starts
# ============================================================

FACE_CASCADE_PATH = (
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

EYE_CASCADE_PATH = (
    cv2.data.haarcascades +
    "haarcascade_eye.xml"
)

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)


# Make sure the cascade files were loaded successfully
if face_cascade.empty():
    raise RuntimeError(
        f"Failed to load face cascade: {FACE_CASCADE_PATH}"
    )

if eye_cascade.empty():
    raise RuntimeError(
        f"Failed to load eye cascade: {EYE_CASCADE_PATH}"
    )

print("Face cascade loaded successfully")
print("Eye cascade loaded successfully")


# ============================================================
# WebSocket endpoint
# ============================================================

@app.websocket("/ws/interview")
async def interview_websocket(websocket: WebSocket):

    await websocket.accept()

    print("Client connected")

    try:

        while True:

            # ------------------------------------------------
            # 1. Receive binary JPEG frame
            # ------------------------------------------------

            data = await websocket.receive_bytes()

            # ------------------------------------------------
            # 2. Convert bytes -> NumPy array
            # ------------------------------------------------

            image_array = np.frombuffer(
                data,
                dtype=np.uint8
            )

            # ------------------------------------------------
            # 3. Decode JPEG -> OpenCV frame
            # ------------------------------------------------

            frame = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )

            if frame is None:
                print("Invalid frame received")
                continue

            print(
                f"Received frame: "
                f"{frame.shape[1]}x{frame.shape[0]}"
            )

            print(
                f"Timestamp: "
                f"{datetime.datetime.now()}"
            )

            # ------------------------------------------------
            # 4. Convert to grayscale
            # ------------------------------------------------

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            # ------------------------------------------------
            # 5. Detect faces
            # ------------------------------------------------

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            print(
                f"Faces detected: {len(faces)}"
            )

            # ------------------------------------------------
            # 6. Process each detected face
            # ------------------------------------------------

            for (x, y, w, h) in faces:

                # Draw face rectangle
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (255, 0, 0),
                    2
                )

                # ------------------------------------------------
                # Extract face region
                # ------------------------------------------------

                roi_gray = gray[
                    y:y + h,
                    x:x + w
                ]

                roi_color = frame[
                    y:y + h,
                    x:x + w
                ]

                # ------------------------------------------------
                # 7. Detect eyes inside face
                # ------------------------------------------------

                eyes = eye_cascade.detectMultiScale(
                    roi_gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(15, 15)
                )

                print(
                    f"Eyes detected: {len(eyes)}"
                )

                # ------------------------------------------------
                # 8. Draw eye rectangles
                # ------------------------------------------------

                for (ex, ey, ew, eh) in eyes:

                    cv2.rectangle(
                        roi_color,
                        (ex, ey),
                        (ex + ew, ey + eh),
                        (0, 255, 0),
                        2
                    )

            # ------------------------------------------------
            # 9. Display frame locally
            # ------------------------------------------------

            cv2.imshow(
                "Interview Face Tracking",
                frame
            )

            # Press Q to stop
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            # ------------------------------------------------
            # 10. Send result to React frontend
            # ------------------------------------------------

            await websocket.send_json({

                "status": "received",

                "message": "Frame processed",

                "timestamp": datetime.datetime.now().isoformat(),

                "face_count": len(faces),

                "eye_detection": True

            })

    # ========================================================
    # Client disconnected
    # ========================================================

    except WebSocketDisconnect:

        print("Client disconnected")

    # ========================================================
    # Other errors
    # ========================================================

    except Exception as e:

        print(
            "WebSocket error:",
            str(e)
        )

    finally:

        cv2.destroyAllWindows()

        print("WebSocket connection closed")



