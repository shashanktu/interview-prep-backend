from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from services.db_connection import insert_jd,Base, engine,search_jd_by_role, insert_interview,search_jd_resume,search_all_jds
from models.models import JD, Interview , User
from services.database import engine, Base
from utils.upload_files import upload_blob
from utils.email_service import send_interview_email
from utils.read_blob import extract_pdf_text
from utils.prompts import get_questions
Base.metadata.create_all(bind=engine)


app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model (for documentation only, cannot be used directly with file uploads)
class UploadRequest(BaseModel):
    role: str

# Response model
class UploadResponse(BaseModel):
    message: str
    role: str
    filename: str
    url:str

class InterviewCandidate(BaseModel):
    candidate_name: str
    candidate_email: str
    role: str
    assessment_difficulty: str
    candidate_resume: str | None = None


class InterviewResponse(BaseModel):
    interview_id: str
    candidate_name: str
    candidate_email: str
    role: str
    tsc: str
    resume_path: str | None = None
    message: str

class InterviewDetails(BaseModel):
    govt_id: Optional[str]
    selfie: Optional[str]
    video: Optional[str]
    transcript: Optional[str]

class SaveMappingRequest(BaseModel):
    role: str
    filePath: str
    url: str
    timestamp: str


@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.post("/upload_jd", response_model=UploadResponse)
async def upload_file(
    role: str = Form(...),        # From UploadRequest model
    file: UploadFile = File(...)  # File cannot be in BaseModel
):
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF and DOCX files are allowed."
        )
    
    #function to check if the role already exists in database
    if search_jd_by_role(role):
        raise HTTPException(
            status_code=400,
            detail=f"Role '{role}' already exists. Please choose a different role name."
        )
    result= await upload_blob(file=file,folder_name="JD")
  
    jd = JD(
        role=role,
        path=result['url']
    )

    inserted_jd = insert_jd(jd)
    

    return UploadResponse(
        message="File uploaded successfully",
        role=role,
        filename=file.filename,
        id=inserted_jd.id,
        url=result['url']
    )




@app.post("/interview-candidate", response_model=InterviewResponse)
async def create_interview_candidate(
    user_id: int = Form(...),                  # Logged-in HR user ID
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    l2_panel: str = Form(...),
    l2_email: str = Form(...),
    level: str = Form(...),
    jd_name: str = Form(...),
    role: str = Form(...),
    tsc: str = Form(...),
    file: UploadFile | None = File(None)       # Candidate resume (optional)
):
    # Validate that the JD exists for the given role
    jd = search_jd_by_role(role)
    if not jd:
        raise HTTPException(
            status_code=404,
            detail=f"No Job Description found for role: {role}"
        )
    
    result= await upload_blob(file=file,folder_name=f"{candidate_name}/Resume")

    resume_path = result['url'] if file else None
    print(f"Uploaded jd {jd_name}")
    interview = Interview(
        user_id=user_id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        role=role,
        tsc=tsc,
        l2_panel=l2_panel,
        l2_email=l2_email,
        level=level,
        jd_name=jd_name,
        resume_path=resume_path,
        l1_status="Pending",
        l2_status="Pending"
    )

    created_interview = insert_interview(interview)
    result=send_interview_email(
        candidate_email=candidate_email,
        candidate_name=candidate_name,
        interview_link="https://example.com/interview",
        interview_id=created_interview.interview_id,
        role=role
    )

    print(f"Email sent successfully: {result}")

    return InterviewResponse(
        interview_id=created_interview.interview_id,
        candidate_name=created_interview.candidate_name,
        candidate_email=created_interview.candidate_email,
        tsc=created_interview.tsc,
        role=created_interview.role,
        resume_path=created_interview.resume_path,
        message="Interview created successfully"
    )
from services.llm_connection import get_azure_response
@app.get("/test-azure")
async def test_azure():
    result = get_azure_response("HI")
    return {"result": result}

@app.get("/generate-questions/{interview_id}")
async def generate_questions(interview_id: str):
    result = search_jd_resume(interview_id)
    if (result.jd_path is None) or (result.resume_path is None):
        return {"error": "No matching JD or resume found."}
    jd_text = extract_pdf_text(result.jd_path)
    resume_text = extract_pdf_text(result.resume_path)
    questions=get_questions(jd=jd_text, resume=resume_text)
    return {
        "interview_id": interview_id,
        "questions": questions
    }


# @app.put("/update-interview/{interview_id}")
# async def update_interview(interview_id: str,):
#     # Validate that the interview exists
#     existing_interview = search_interview_by_id(interview_id)
#     if not existing_interview:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No interview found with ID: {interview_id}"
#         )
#     return {"message": "Interview updated successfully"}



@app.get("/get_jds")
async def get_jds():
    jds = search_all_jds()
    print(jds[0])
    return {"jds": [jd.role for jd in jds]}


from list_blobs import get_files_from_blob
@app.get("/list_blobs")
async def list_blobs():
    return {"files": get_files_from_blob("JD/")}


@app.post("/api/save-mapping")
async def save_mapping(payload: SaveMappingRequest | list[SaveMappingRequest]):
    if isinstance(payload, list):
        return {"mappings": [m.model_dump() for m in payload]}
    return payload.model_dump()

@app.post("/media/{interview_id}")
async def upload_interview_media(
    interview_id: int,
    media_types: List[
        Literal[
            "aadhar",
            "selfie",
            "video",
            "transcription"
        ]
    ] = Form(...),
    files: List[UploadFile] = File(...)
):

    if len(files) != len(media_types):
        raise HTTPException(
            status_code=400,
            detail="Number of files must match number of media types"
        )

    allowed_types = {
        "aadhar": {
            "image/jpeg",
            "image/png",
            "application/pdf"
        },
        "selfie": {
            "image/jpeg",
            "image/png"
        },
        "video": {
            "video/mp4",
            "video/webm",
            "video/quicktime"
        },
        "transcription": {
            "text/plain",
            "application/json",
            "text/vtt"
        }
    }

    uploaded_files = []

    for file, media_type in zip(files, media_types):

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is missing"
            )

        if file.content_type not in allowed_types[media_type]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid file type for {media_type}: "
                    f"{file.content_type}"
                )
            )

        # ----------------------------------------
        # YOUR STORAGE LOGIC
        # ----------------------------------------

        # blob_path = await upload_to_blob(
        #     interview_id=interview_id,
        #     media_type=media_type,
        #     file=file
        # )

        blob_path = None

        # ----------------------------------------
        # YOUR DB LOGIC
        # ----------------------------------------

        # interview_details.<media_type>_path = blob_path

        uploaded_files.append({
            "media_type": media_type,
            "filename": file.filename,
            "content_type": file.content_type,
            "blob_path": blob_path
        })

    return {
        "message": "Media uploaded successfully",
        "interview_id": interview_id,
        "files": uploaded_files
    }

@app.post("/end_interview/{interview_id}")
async def end_interview(interview_id: str):
    # Logic to end the interview
    return {"message": "Interview ended successfully"}