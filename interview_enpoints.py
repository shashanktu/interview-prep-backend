import uuid
from fastapi import APIRouter,HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect

router=APIRouter(
    prefix="/interview",
    tags=["interview"]
)
@router.post("/start-interview/{interview_id}")
async def start_interview(interview_id: str):
    #logic to create a session for the interview and mark it as started in the database
    session_id=str(uuid.uuid4())
    return {"message": "Interview started successfully", "session_id": session_id}


@router.get("/interview-questions/{interview_id}")
async def get_interview_questions(interview_id: str):


    return {"questions": ["Tell me about yourself.", "What are your strengths?", "What are your weaknesses?"]}



@router.post("/end_interview/{interview_id}")
async def end_interview(interview_id: str):
    # Logic to end the interview
    return {"message": "Interview ended successfully"}




