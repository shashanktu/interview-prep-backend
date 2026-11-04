from services.db_connection import save_interview_feedback
from utils.prompts import get_feedback


def generate_and_save_feedback(
    interview_id: str,
    transcript: str,
    jd:str
):
    try:
        print(f"Starting feedback generation for {interview_id}")

        # 1. Call your LLM with the transcript
        feedback = get_feedback(transcript, jd)

        # 2. Persist the generated feedback in PostgreSQL
        save_interview_feedback(
            interview_id=interview_id,
            feedback=feedback,
        )

        print(
            "Feedback generated successfully for %s",
            interview_id,
        )
        print("================================")
        print(f"Feedback content for {interview_id}:\n{feedback}")
        print("================================")

    except Exception as e:
        print(f"Error generating feedback for {interview_id}: {str(e)}")

       