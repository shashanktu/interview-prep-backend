import uuid
import os
from typing import Annotated
from fastapi import APIRouter,HTTPException, UploadFile, File, Query, WebSocket, WebSocketDisconnect , BackgroundTasks
from starlette.concurrency import run_in_threadpool
from list_blobs import find_blob_url
from utils.upload_files import upload_blob
from services.db_connection import get_resume_link,update_interview_status,get_interview_status,get_interview_questions_db,get_interview_data,get_jd_path ,update_interview
from utils.read_blob import extract_pdf_text
from utils.prompts import get_questions
from models.models import InterviewMetadata
from services.db_connection import insert_metadata
from services.feedback import generate_and_save_feedback
from face_detection import violation_tracker
import datetime
import json
router=APIRouter(
    prefix="/interview",
    tags=["interview"]
)

# In-memory cache of currently active interview sessions
active_interviews: set[str] = set()


def generate_questions(resume_path,jd_path):
    resume_text = extract_pdf_text(resume_path)
    jd_text = extract_pdf_text(jd_path)
    questions=get_questions(jd=jd_text, resume=resume_text)
    #logic to generate questions
    return questions

@router.get("/get-interview-details/{interview_id}")
async def get_interview_details(interview_id: str):
    result = get_interview_data(interview_id)
    return {"data": result}


@router.post("/get_questions/{interview_id}")
def get_interview_questions(interview_id):
    try:
        int_status=get_interview_status(interview_id)
        if int_status!="Active":
            raise HTTPException(status_code=400, detail="Interview is not active")
        else:
            questions= get_interview_questions_db(interview_id=interview_id)
            return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching interview questions: {str(e)}")




@router.post("/upload_selfie/{interview_id}/{candidate_name}")
async def upload_selfie(
    interview_id: str,
    candidate_name: str,
    file: Annotated[UploadFile, File(...)],
):
    try:
        int_status=get_interview_status(interview_id)
        if int_status!="Active":
            raise HTTPException(status_code=400, detail="Interview is not active. Cannot upload selfie.")
        
        else:
            selfie_path = f"selfie/{candidate_name}/{file.filename}"
            await upload_blob(file, selfie_path)
            interview_metadata = InterviewMetadata(
                interview_id=interview_id,
                key="selfie_uploaded",
                value="true"
            )
            insert_metadata(interview_metadata)
            return {"message": "Selfie uploaded successfully"}
    except Exception as e:
            interview_metadata = InterviewMetadata(
                interview_id=interview_id,
                key="selfie_uploaded",
                value="false"
            )
            insert_metadata(interview_metadata)
            raise HTTPException(status_code=500, detail=f"Error uploading selfie: {str(e)}")
    



def _write_empty_file(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("")


@router.post("/start-interview/{interview_id}")
async def start_interview(interview_id: str):
    int_status = get_interview_status(interview_id)

    try:
        if int_status == "Scheduled":
            await run_in_threadpool(
                update_interview,
                interview_id=interview_id,
                status="Active",
                attempt_date=datetime.datetime.now(),
            )
            active_interviews.add(interview_id)  # cache it
            await run_in_threadpool(_write_empty_file, f"{interview_id}_temp.txt")
            return {"message": "Interview started successfully"}
        else:
            raise HTTPException(status_code=400, detail="Interview is not in a scheduled state and cannot be started.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")



@router.post("/append_transcription/{interview_id}/")
def append_transcription(
    interview_id: str,
    question: Annotated[str, Query(...)],
    transcription: Annotated[str, Query(...)],
):
    # No DB call — just check in-memory cache
    if interview_id not in active_interviews:
        raise HTTPException(status_code=400, detail="Interview is not active. Cannot append transcription.")

    temp_file_path = f"{interview_id}_temp.txt"
    if not os.path.exists(temp_file_path):
        raise HTTPException(status_code=404, detail="Interview session file not found. Did you call /start-interview first?")

    try:
        with open(temp_file_path, "a") as temp_file:
            temp_file.write(f"Q: {question}\nA: {transcription}\n\n")
        return {"message": "Transcription appended successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error appending transcription: {str(e)}")




@router.post("/end_interview/{interview_id}")
async def end_interview(
    interview_id: str,
    background_tasks: BackgroundTasks,
):
    if interview_id not in active_interviews:
        raise HTTPException(
            status_code=409,
            detail="Interview is not active or has already ended",
        )

    temp_file_path = f"{interview_id}_temp.txt"
    if not os.path.exists(temp_file_path):
        raise HTTPException(
            status_code=404,
            detail="Interview transcript file not found",
        )

    try:
        full_transcription = await run_in_threadpool(_read_file, temp_file_path)

        # 1. Save the transcript FIRST
        interview_metadata = InterviewMetadata(
            interview_id=interview_id,
            key="full_transcription",
            value=full_transcription,
        )
        await run_in_threadpool(insert_metadata, interview_metadata)

        feedback_status_metadata = InterviewMetadata(
            interview_id=interview_id,
            key="feedback_status",
            value="pending",
        )
        await run_in_threadpool(insert_metadata, feedback_status_metadata)

        # 1b. Save the violation summary gathered during the interview
        violation_summary = violation_tracker.get_summary(interview_id)
        violation_metadata = InterviewMetadata(
            interview_id=interview_id,
            key="violation_summary",
            value=json.dumps(violation_summary),
        )
        await run_in_threadpool(insert_metadata, violation_metadata)
        violation_tracker.clear(interview_id)

        # 2. Mark the interview as completed
        await run_in_threadpool(
            update_interview_status,
            interview_id=interview_id,
            status="Completed",
        )

        # 3. Remove it from the in-memory active cache
        active_interviews.discard(interview_id)

        # 4. Schedule JD fetch + feedback generation entirely in background
        background_tasks.add_task(
            _generate_feedback_task,
            interview_id,
            full_transcription,
        )

        # 5. Remove the temp file only after saving the transcript
        os.remove(temp_file_path)

        return {
            "message": "Interview ended successfully",
            "interview_id": interview_id,
            "feedback_status": "Pending",
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error finalizing interview {interview_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to finalize interview",
        )


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _generate_feedback_task(interview_id: str, full_transcription: str):
    """Runs entirely in background — safe to do blocking I/O here."""
    try:
        from list_blobs import find_blob_url
        
        result = get_jd_path(interview_id)
        print(f"JD URL for interview {interview_id}: {result.jd_url}")
        print(type(result.jd_url))
        jd = extract_pdf_text(result.jd_url)
        generate_and_save_feedback(interview_id, full_transcription, jd)

        insert_metadata(
            InterviewMetadata(
                interview_id=interview_id,
                key="feedback_status",
                value="completed",
            )
        )
    except Exception as e:
        print(f"Feedback generation failed for {interview_id}: {str(e)}")
        insert_metadata(
            InterviewMetadata(
                interview_id=interview_id,
                key="feedback_status",
                value="failed",
            )
        )










