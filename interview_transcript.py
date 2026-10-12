import numpy as np_audio
from fastapi import APIRouter,HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from azure.core.credentials import AzureKeyCredential
from azure.ai.transcription import TranscriptionClient
from azure.ai.transcription.models import TranscriptionContent, TranscriptionOptions
import io
import wave
import os
endpoint=os.getenv("TRANSCRIPT_ENDPOINT")
api_key=os.getenv("TRANSCRIPT_API_KEY")

router=APIRouter(
    prefix="/transcript",
    tags=["transcript"]
)

# Get configuration from environment variables

# Create the transcription client
client = TranscriptionClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

# Options are the same for every request, so build once
azure_transcription_options = TranscriptionOptions(locales=["en-US"])

AZURE_AUDIO_SAMPLE_RATE = 16000  # must match what the frontend records at


def pcm_float32_to_wav_bytes(audio_bytes: bytes, sample_rate: int = AZURE_AUDIO_SAMPLE_RATE) -> io.BytesIO:
    """Wrap raw float32 PCM samples (as sent by the frontend) into an
    in-memory 16-bit PCM WAV file, since Azure's Transcription SDK expects
    a real audio container rather than bare PCM samples."""
    float_samples = np_audio.frombuffer(audio_bytes, dtype=np_audio.float32)

    # Convert [-1.0, 1.0] float32 -> int16 PCM
    int16_samples = np_audio.clip(float_samples, -1.0, 1.0)
    int16_samples = (int16_samples * 32767.0).astype(np_audio.int16)

    wav_stream = io.BytesIO()
    with wave.open(wav_stream, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int16_samples.tobytes())

    wav_stream.seek(0)
    return wav_stream


@router.websocket("/ws/azure-transcript/")
async def azure_transcript_websocket(websocket: WebSocket):
        await websocket.accept()
        session_id = websocket.query_params.get("session_id", "unknown")
        print(f"[+] Azure Transcript session started: {session_id}")

        try:
            while True:
                audio_bytes = await websocket.receive_bytes()
                print(f"[azure_transcript] Received {len(audio_bytes)} bytes of audio")
                audio_stream = pcm_float32_to_wav_bytes(audio_bytes)

                request_content = TranscriptionContent(
                    definition=azure_transcription_options,
                    audio=("audio.wav", audio_stream.read(), "audio/wav"),
                )

                result = client.transcribe(request_content)

                transcript_text = (
                    result.combined_phrases[0].text
                    if result.combined_phrases
                    else ""
                )

                print(f"Transcription: {transcript_text}")

                await websocket.send_json({
                    "session_id": session_id,
                    "transcript": transcript_text,
                })

        except WebSocketDisconnect:
            print(f"[-] Azure Transcript session {session_id} disconnected")
        except Exception as e:
            print(f"🔥 Azure Transcript error: {repr(e)}")
