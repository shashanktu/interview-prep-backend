import uuid
from fastapi import APIRouter,HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from list_blobs import find_blob_url
from services.db_connection import get_resume_link
from utils.read_blob import extract_pdf_text
from utils.prompts import get_questions
router=APIRouter(
    prefix="/interview",
    tags=["interview"]
)
def generate_questions(resume_path,jd_path):
    resume_text = extract_pdf_text(resume_path)
    jd_text = extract_pdf_text(jd_path)
    questions=get_questions(jd=jd_text, resume=resume_text)
    #logic to generate questions
    return questions

@router.post("/start-interview/{interview_id}")
async def start_interview(interview_id: str):
    #logic to create a session for the interview and mark it as started in the database
    session_id=str(uuid.uuid4())
    return {"message": "Interview started successfully", "session_id": session_id}




@router.post("/end_interview/{interview_id}")
async def end_interview(interview_id: str):
    # Logic to end the interview
    return {"message": "Interview ended successfully"}

@router.post("/get_questions/{interview_id}")
async def get_interview_questions(interview_id: str):
    result = get_resume_link(interview_id)
    result_dict = dict(result._mapping)
    print("\n",result_dict)
    
    resume_path = result_dict.get("resume_path")
    jd_name = result_dict.get("jd_name")
    print(f"Resume path: {resume_path},\n JD name: {jd_name}")
    jd_path= find_blob_url(file_name=jd_name)
    if not resume_path:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not jd_path:
        raise HTTPException(status_code=404, detail="JD not found")

    ques=generate_questions(resume_path=resume_path,jd_path=jd_path)
    return {"questions": ques}

