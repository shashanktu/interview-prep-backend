from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from services.db_connection import insert_jd,Base, engine,search_jd_by_role, insert_interview,search_jd_resume,search_all_jds,get_resume_link,insert_user,search_user_by_email,insert_metadata
from models.models import JD, Interview , User, InterviewMetadata
from services.database import engine, Base
from utils.upload_files import upload_blob
from utils.email_service import send_interview_email
from utils.read_blob import extract_pdf_text
from utils.prompts import get_questions
Base.metadata.create_all(bind=engine)
from face_detection import router as face_router
from interview_transcript import router as audio_router
from interview_enpoints import router as interview_router
app = FastAPI()
app.include_router(face_router)
app.include_router(audio_router)
app.include_router(interview_router)
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



"""Working code """
# @app.post("/interview-candidate", response_model=InterviewResponse)
# async def create_interview_candidate(
#     user_id: int = Form(...),                  # Logged-in HR user ID
#     candidate_name: str = Form(...),
#     candidate_email: str = Form(...),
#     l2_panel: str = Form(...),
#     l2_email: str = Form(...),
#     level: str = Form(...),
#     jd_name: str = Form(...),
#     role: str = Form(...),
#     tsc: str = Form(...),
#     file: UploadFile | None = File(None)       # Candidate resume (optional)
# ):
   
    
#     result= await upload_blob(file=file,folder_name=f"candidates/{candidate_name}/Resume")

#     resume_path = result['url'] if file else None
#     print(f"Uploaded jd {jd_name}")
#     interview = Interview(
#         user_id=user_id,
#         candidate_name=candidate_name,
#         candidate_email=candidate_email,
#         role=role,
#         tsc=tsc,
#         l2_panel=l2_panel,
#         l2_email=l2_email,
#         level=level,
#         jd_name=jd_name,
#         resume_path=resume_path,
#         l1_status="Pending",
#         l2_status="Pending"
#     )

#     created_interview = insert_interview(interview)
#     result=send_interview_email(
#         candidate_email=candidate_email,
#         candidate_name=candidate_name,
#         interview_link="https://example.com/interview",
#         interview_id=created_interview.interview_id,
#         role=role
#     )

#     print(f"Email sent successfully: {result}")

#     return InterviewResponse(
#         interview_id=created_interview.interview_id,
#         candidate_name=created_interview.candidate_name,
#         candidate_email=created_interview.candidate_email,
#         tsc=created_interview.tsc,
#         role=created_interview.role,
#         resume_path=created_interview.resume_path,
#         message="Interview created successfully"
#     )
# from services.llm_connection import get_azure_response
# @app.get("/test-azure")
# async def test_azure():
#     result = get_azure_response("HI")
#     return {"result": result}

# @app.get("/generate-questions/{interview_id}")
# async def generate_questions(interview_id: str):
#     resume_link=get_resume_link(interview_id) 
#     resume_dict = dict(resume_link._mapping)
#     print(f"Resume link: {resume_dict}")

#     return resume_dict
   


# @app.get("/get_jds")
# async def get_jds():
#     jds = search_all_jds()
#     print(jds[0])
#     return {"jds": [jd.role for jd in jds]}


from list_blobs import get_files_from_blob
@app.get("/list_blobs")
async def list_blobs():
    return {"files": get_files_from_blob("JDs/")}


# @app.post("/api/save-mapping")
# async def save_mapping(payload: SaveMappingRequest | list[SaveMappingRequest]):
#     if isinstance(payload, list):
#         return {"mappings": [m.model_dump() for m in payload]}
#     return payload.model_dump()



from fastapi import APIRouter, BackgroundTasks, Form, File, UploadFile, HTTPException
from starlette.concurrency import run_in_threadpool

router = APIRouter()


@app.post("/interview-candidate", response_model=InterviewResponse)
async def create_interview_candidate(
    background_tasks: BackgroundTasks,
    user_id: int = Form(...),
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    l2_panel: str = Form(...),
    l2_email: str = Form(...),
    level: str = Form(...),
    jd_name: str = Form(...),
    jd_url: str = Form(...),
    role: str = Form(...),
    tsc: str = Form(...),
    file: UploadFile | None = File(None),
):
    # 1. Upload the resume only if one was provided
    resume_path = None

    if file and file.filename:
        upload_result = await upload_blob(
            file=file,
            folder_name=f"candidates/{candidate_name}/Resume",
        )
        resume_path = upload_result["url"]

    # 2. Create the interview record
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
        jd_url=jd_url,
        resume_path=resume_path,
        l1_status="Pending",
        l2_status="Pending",
        
    )

    created_interview = await run_in_threadpool(
        insert_interview, interview
    )

    # 3. Start preparation without making TAG wait for AI
    background_tasks.add_task(
        prepare_interview,
        interview_id=created_interview.interview_id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        role=role,
        jd_name=jd_name,
        resume_path=resume_path,
    )

    return InterviewResponse(
        interview_id=created_interview.interview_id,
        candidate_name=created_interview.candidate_name,
        candidate_email=created_interview.candidate_email,
        tsc=created_interview.tsc,
        role=created_interview.role,
        resume_path=created_interview.resume_path,
        message="Interview created. Questions are being prepared.",
    )


async def prepare_interview(
    interview_id: str,
    candidate_name: str,
    candidate_email: str,
    role: str,
    jd_name: str,
    resume_path: str | None,
):
    try:
        # Mark preparation as processing
        from list_blobs import find_blob_url
        from utils.read_blob import extract_pdf_text
        # 4. Read JD and resume text from Blob Storage
        url=find_blob_url(jd_name)
        print(f"JD URL: {url}/n=========================")

        jd_text = await run_in_threadpool(extract_pdf_text, url)

        if resume_path:
            resume_text = await run_in_threadpool(extract_pdf_text, resume_path)
        else:
            resume_text = ""
        from utils.prompts import get_questions
        # 5. Generate structured questions using your LLM
        questions = await run_in_threadpool(get_questions, jd_text, resume_text)

        if not questions:
            raise ValueError("Question generation returned no questions")

        # 6. Persist the complete question set before sending the invite
        # await run_in_threadpool(
        #     save_interview_questions,
        #     interview_id,
        #     questions,
        # )
        print("code after interview questions generated")
        print(f"Interview questions saved successfully for {interview_id} with questions\n{questions}")
        interview_metadata = InterviewMetadata(
            interview_id=interview_id,
            key="questions",
            value=str(questions)
        )
        await run_in_threadpool(insert_metadata, interview_metadata)

        # 7. Send the invitation only after questions are saved
        email_result = await run_in_threadpool(
            send_interview_email,
            candidate_email=candidate_email,
            candidate_name=candidate_name,
            interview_link="https://valuemomentum.com/",
            interview_id=interview_id,
            role=role,
        )

        print(f"Email sent successfully: {email_result}")

        print(f"Interview {interview_id} prepared and invite submitted")

    except Exception as exc:
        print(f"Interview preparation failed for {interview_id}: {exc}")





import uuid
import bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

class UserCreateRequest(BaseModel):
    vam_id: str | None = None
    associate_name: str
    associate_email: str
    associate_password: str
    associate_role: str

class UserResponse(BaseModel):
    id: int
    associate_name: str
    vam_id: str
    associate_email: str
    associate_role: str
    message: str

@app.post("/users", response_model=UserResponse)
async def create_user(payload: UserCreateRequest):
    existing_user = search_user_by_email(payload.associate_email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail=f"User with email '{payload.associate_email}' already exists."
        )

    hashed_password = hash_password(payload.associate_password)

    user = User(
        associate_name=payload.associate_name,
        vam_id=payload.vam_id or f"VAM-{uuid.uuid4().hex[:8].upper()}",
        associate_email=payload.associate_email,
        associate_password=hashed_password,
        associate_role=payload.associate_role
    )

    created_user = insert_user(user)

    return UserResponse(
        id=created_user.id,
        associate_name=created_user.associate_name,
        vam_id=created_user.vam_id,
        associate_email=created_user.associate_email,
        associate_role=created_user.associate_role,
        message="User created successfully"
    )





class UserLoginRequest(BaseModel):
    associate_email: str
    associate_password: str

class UserLoginResponse(BaseModel):
    id: int
    associate_name: str
    vam_id: str
    associate_email: str
    associate_role: str
    message: str

@app.post("/login", response_model=UserLoginResponse)
async def login_user(payload: UserLoginRequest):
    user = search_user_by_email(payload.associate_email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(payload.associate_password, user.associate_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return UserLoginResponse(
        id=user.id,
        associate_name=user.associate_name,
        vam_id=user.vam_id,
        associate_email=user.associate_email,
        associate_role=user.associate_role,
        message="Login successful"
    )


