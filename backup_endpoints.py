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