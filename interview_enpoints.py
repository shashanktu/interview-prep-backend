import uuid
import os
from fastapi import APIRouter,HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect , BackgroundTasks
from starlette.concurrency import run_in_threadpool
from list_blobs import find_blob_url
from utils.upload_files import upload_blob
from services.db_connection import get_resume_link,update_interview_status,get_interview_status,get_interview_questions_db,get_interview_data,get_jd_path ,update_interview
from utils.read_blob import extract_pdf_text
from utils.prompts import get_questions
from models.models import InterviewMetadata
from services.db_connection import insert_metadata
from services.feedback import generate_and_save_feedback
import datetime
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

# @router.post("/start-interview/{interview_id}")
# async def start_interview(interview_id: str):
#     int_status=get_interview_status(interview_id)
#     if int_status=="Scheduled":
#         update_interview_status(interview_id=interview_id, status="Active")
#         #logic to create a temp file 
#         with open(f"{interview_id}_temp.txt", "w") as temp_file:
#             temp_file.write("")
#         return {"message": "Interview started successfully"}
#     else:
#         return {"message": "Interview is not in a scheduled state and cannot be started."}
    
# @router.post("/end_interview/{interview_id}")
# async def end_interview(interview_id: str):
#     int_status=get_interview_status(interview_id)
#     if int_status=="Active":
#         update_interview_status(interview_id=interview_id, status="Completed")
#         return {"message": "Interview ended successfully"}
#     else:
#         return {"message": "Interview is not in an active state and cannot be ended."}

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
# async def get_interview_questions(interview_id: str):
#     result = get_resume_link(interview_id)
#     result_dict = dict(result._mapping)
#     print("\n",result_dict)
    
#     resume_path = result_dict.get("resume_path")
#     jd_name = result_dict.get("jd_name")
#     print(f"Resume path: {resume_path},\n JD name: {jd_name}")
#     jd_path= find_blob_url(file_name=jd_name)
#     if not resume_path:
#         raise HTTPException(status_code=404, detail="Resume not found")
#     if not jd_path:
#         raise HTTPException(status_code=404, detail="JD not found")

#     ques=generate_questions(resume_path=resume_path,jd_path=jd_path)
#     return {"questions": ques}



@router.post("/upload_selfie/{interview_id}/{candidate_name}")
async def upload_selfie(interview_id: str, candidate_name: str, file: UploadFile = File(...)):
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
    





# @router.post("/start-interview/{interview_id}")
# async def start_interview(interview_id: str):
#     int_status = get_interview_status(interview_id)
#     if int_status == "Scheduled":
#         update_interview_status(interview_id=interview_id, status="Active")
#         with open(f"{interview_id}_temp.txt", "w") as temp_file:
#             temp_file.write("")
#         return {"message": "Interview started successfully"}
#     else:
#         return {"message": "Interview is not in a scheduled state and cannot be started."}


# @router.post("/append_transcription/{interview_id}/")
# def append_transcription(interview_id: str, question: str, transcription: str):
#     int_status = get_interview_status(interview_id)
#     if int_status != "Active":
#         raise HTTPException(status_code=400, detail="Interview is not active. Cannot append transcription.")

#     temp_file_path = f"{interview_id}_temp.txt"
#     if not os.path.exists(temp_file_path):
#         raise HTTPException(status_code=404, detail="Interview session file not found. Did you call /start-interview first?")

#     try:
#         with open(temp_file_path, "a") as temp_file:
#             temp_file.write(f"Q: {question}\nA: {transcription}\n\n")
#         return {"message": "Transcription appended successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error appending transcription: {str(e)}")


# @router.post("/end_interview/{interview_id}")
# async def end_interview(interview_id: str):
#     int_status = get_interview_status(interview_id)
#     if int_status != "Active":
#         return {"message": "Interview is not in an active state and cannot be ended."}

#     temp_file_path = f"{interview_id}_temp.txt"
#     full_transcription = ""

#     if os.path.exists(temp_file_path):
#         with open(temp_file_path, "r") as temp_file:
#             full_transcription = temp_file.read()

#         interview_metadata = InterviewMetadata(
#             interview_id=interview_id,
#             key="full_transcription",
#             value=full_transcription
#         )
#         insert_metadata(interview_metadata)

#         os.remove(temp_file_path)

#     update_interview_status(interview_id=interview_id, status="Completed")
#     return {"message": "Interview ended successfully"}


@router.post("/start-interview/{interview_id}")
async def start_interview(interview_id: str):
    int_status = get_interview_status(interview_id)
    
    try:
        if int_status == "Scheduled":
            update_interview(interview_id="112233", status="Active", attempt_date=datetime.datetime.now())
            update_interview(interview_id=interview_id, status="Active", attempt_date=datetime.datetime.now())
            active_interviews.add(interview_id)  # cache it
            with open(f"{interview_id}_temp.txt", "w") as temp_file:
                temp_file.write("")
            return {"message": "Interview started successfully"}
        else:
            raise HTTPException(status_code=400, detail="Interview is not in a scheduled state and cannot be started.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")



@router.post("/append_transcription/{interview_id}/")
def append_transcription(interview_id: str, question: str, transcription: str):
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


# @router.post("/end_interview/{interview_id}")
# async def end_interview(interview_id: str):
#     print(f"Active interviews before ending: {active_interviews}")
#     if interview_id not in active_interviews:
#         return {"message": "Interview is not in an active state and cannot be ended."}

#     temp_file_path = f"{interview_id}_temp.txt"
#     full_transcription = ""

#     if os.path.exists(temp_file_path):
#         with open(temp_file_path, "r") as temp_file:
#             full_transcription = temp_file.read()

#         interview_metadata = InterviewMetadata(
#             interview_id=interview_id,
#             key="full_transcription",
#             value=full_transcription
#         )
#         insert_metadata(interview_metadata)

#         os.remove(temp_file_path)

#     update_interview_status(interview_id=interview_id, status="Completed")
#     active_interviews.discard(interview_id)  # remove from cache
#     return {"message": "Interview ended successfully"}





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
        jd_url = get_jd_path(interview_id)
        jd = extract_pdf_text(jd_url)
        generate_and_save_feedback(interview_id, full_transcription, jd, full_transcription)

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