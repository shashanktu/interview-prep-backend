import uuid
from fastapi import APIRouter,HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from list_blobs import find_blob_url
from utils.upload_files import upload_blob
from services.db_connection import get_resume_link,update_interview_status,get_interview_status,get_interview_questions_db
from utils.read_blob import extract_pdf_text
from utils.prompts import get_questions
from models.models import InterviewMetadata
from services.db_connection import insert_metadata
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
    int_status=get_interview_status(interview_id)
    if int_status=="Scheduled":
        update_interview_status(interview_id=interview_id, status="Active")
        return {"message": "Interview started successfully"}
    else:
        return {"message": "Interview is not in a scheduled state and cannot be started."}
    
@router.post("/end_interview/{interview_id}")
async def end_interview(interview_id: str):
    int_status=get_interview_status(interview_id)
    if int_status=="Active":
        update_interview_status(interview_id=interview_id, status="Completed")
        return {"message": "Interview ended successfully"}
    else:
        return {"message": "Interview is not in an active state and cannot be ended."}

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