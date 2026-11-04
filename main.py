from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Annotated, Optional, List, Literal
from services.db_connection import insert_jd,Base, engine,search_jd_by_role, insert_interview,search_jd_resume,search_all_jds,get_resume_link,insert_user,search_user_by_email,insert_metadata,get_all_interviews_from_db,get_interview_data
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




from list_blobs import get_files_from_blob
@app.get("/list_blobs")
async def list_blobs():
    return {"files": get_files_from_blob("JDs/")}




from fastapi import APIRouter, BackgroundTasks, Form, File, UploadFile, HTTPException
from starlette.concurrency import run_in_threadpool

router = APIRouter()


@app.post("/interview-candidate", response_model=InterviewResponse)
async def create_interview_candidate(
    background_tasks: BackgroundTasks,
    user_id: Annotated[int, Form(...)],
    candidate_name: Annotated[str, Form(...)],
    candidate_email: Annotated[str, Form(...)],
    l2_panel: Annotated[str, Form(...)],
    l2_email: Annotated[str, Form(...)],
    level: Annotated[str, Form(...)],
    jd_name: Annotated[str, Form(...)],
    jd_url: Annotated[str, Form(...)],
    role: Annotated[str, Form(...)],
    tsc: Annotated[str, Form(...)],
    file: Annotated[UploadFile | None, File()] = None,
):
    # 1. Upload the resume only if one was provided
    resume_path = None
    print(f"JD URL : {jd_url}")
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
        jd_url=jd_url,
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
    jd_url: str,
    resume_path: str | None,
):
    try:
        # Mark preparation as processing
        from list_blobs import find_blob_url
        from utils.read_blob import extract_pdf_text
        # 4. Read JD and resume text from Blob Storage
        # print(f"JD Name: {jd_name}")
        # url=find_blob_url(jd_name)
        print("==============")
        print(f"JD URL: {jd_url}")
        print("==============")

        jd_text = await run_in_threadpool(extract_pdf_text, jd_url)

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


@app.get("/get-all-interviews/")
async def get_all_interviews():
    interviews = get_all_interviews_from_db()
    return {"interviews": interviews}


@app.get("/get-interview-details/{interview_id}")
async def get_interview_details(interview_id: str):
    interview = get_interview_data(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"interview": interview}
from typing import List


class BulkCandidate(BaseModel):
    candidate_name: str
    candidate_email: str


class BulkInterviewResponse(BaseModel):
    message: str
    total_requested: int
    created: list[str]      # interview_ids successfully created
    failed: list[dict]      # [{candidate_email, error}]


@app.post("/bulk/interviews", response_model=BulkInterviewResponse)
async def bulk_create_interviews(
    background_tasks: BackgroundTasks,
    user_id: Annotated[int, Form(...)],
    candidates: Annotated[str, Form(...)],          # JSON string: '[{"candidate_name":"A","candidate_email":"a@x.com"}, ...]'
    l2_panel: Annotated[str, Form(...)],
    l2_email: Annotated[str, Form(...)],
    level: Annotated[str, Form(...)],
    jd_name: Annotated[str, Form(...)],
    jd_url: Annotated[str, Form(...)],
    role: Annotated[str, Form(...)],
    tsc: Annotated[str, Form(...)],
):
    import json as json_lib

    try:
        candidate_list = json_lib.loads(candidates)
        parsed_candidates = [BulkCandidate(**c) for c in candidate_list]
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid 'candidates' JSON. Expected a list of {{candidate_name, candidate_email}}. Error: {e}",
        )

    if not parsed_candidates:
        raise HTTPException(status_code=400, detail="At least one candidate is required.")

    created_ids: list[str] = []
    failed: list[dict] = []

    for candidate in parsed_candidates:
        try:
            interview = Interview(
                user_id=user_id,
                candidate_name=candidate.candidate_name,
                candidate_email=candidate.candidate_email,
                role=role,
                tsc=tsc,
                l2_panel=l2_panel,
                l2_email=l2_email,
                level=level,
                jd_name=jd_name,
                jd_url=jd_url,
                resume_path=None,
                l1_status="Pending",
                l2_status="Pending",
            )

            created_interview = await run_in_threadpool(insert_interview, interview)

            background_tasks.add_task(
                prepare_interview,
                interview_id=created_interview.interview_id,
                candidate_name=candidate.candidate_name,
                candidate_email=candidate.candidate_email,
                role=role,
                jd_name=jd_name,
                jd_url=jd_url,
                resume_path=None,
            )

            created_ids.append(created_interview.interview_id)

        except Exception as e:
            print(f"Failed to create interview for {candidate.candidate_email}: {e}")
            failed.append({"candidate_email": candidate.candidate_email, "error": str(e)})

    return BulkInterviewResponse(
        message="Bulk interview creation processed.",
        total_requested=len(parsed_candidates),
        created=created_ids,
        failed=failed,
    )

