# @router.post("/end_interview/{interview_id}")
# async def end_interview(
#     interview_id: str,
#     background_tasks: BackgroundTasks,
# ):
#     if interview_id not in active_interviews:
#         raise HTTPException(
#             status_code=409,
#             detail="Interview is not active or has already ended",
#         )
#     temp_file_path = f"{interview_id}_temp.txt"

#     try:
#         if not os.path.exists(temp_file_path):
#             raise HTTPException(
#                 status_code=404,
#                 detail="Interview transcript file not found",
#             )

#         with open(temp_file_path, "r", encoding="utf-8") as f:
#             full_transcription = f.read()

#         # 1. Save the transcript FIRST
#         interview_metadata = InterviewMetadata(
#             interview_id=interview_id,
#             key="full_transcription",
#             value=full_transcription,
#         )
#         insert_metadata(interview_metadata)

#         # 2. Mark the interview as completed
#         update_interview_status(
#             interview_id=interview_id,
#             status="Completed",
#         )

#         # 3. Remove it from the in-memory active cache
#         active_interviews.discard(interview_id)
#         jd_url = get_jd_path(interview_id)
#         jd = extract_pdf_text(jd_url)

#         # 4. Schedule feedback generation
#         background_tasks.add_task(
#             generate_and_save_feedback,
#             interview_id,
#             full_transcription,
#             jd,
#             full_transcription,
#         )

#         # 5. Remove the temp file only after saving the transcript
#         os.remove(temp_file_path)

#         return {
#             "message": "Interview ended successfully",
#             "interview_id": interview_id,
#             "feedback_status": "Pending",
#         }

#     except HTTPException:
#         raise

#     except Exception as e:
#         print(f"Error finalizing interview {interview_id}: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail="Failed to finalize interview",
#         )


# from services.db_connection import update_interview
# import datetime
# update_interview(interview_id="112233", status="Active", attempt_date=datetime.datetime.now())






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


# @app.post("/upload_jd", response_model=UploadResponse)
# async def upload_file(
#     role: str = Form(...),        # From UploadRequest model
#     file: UploadFile = File(...)  # File cannot be in BaseModel
# ):
#     allowed_types = [
#         "application/pdf",
#         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#     ]

#     if file.content_type not in allowed_types:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid file type. Only PDF and DOCX files are allowed."
#         )
    
#     #function to check if the role already exists in database
#     if search_jd_by_role(role):
#         raise HTTPException(
#             status_code=400,
#             detail=f"Role '{role}' already exists. Please choose a different role name."
#         )
#     result= await upload_blob(file=file,folder_name="JD")
  
#     jd = JD(
#         role=role,
#         path=result['url']
#     )

#     inserted_jd = insert_jd(jd)
    

#     return UploadResponse(
#         message="File uploaded successfully",
#         role=role,
#         filename=file.filename,
#         url=result['url']
#     )


