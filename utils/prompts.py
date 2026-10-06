from services.llm_connection import get_azure_response
def get_questions(jd, resume):
    prompt = f"""
    -You are an AI interview question generator. I need you to generate the Questions in a proper technical questions with medium and high difficulty levels. This interview will be L1 technical interview with 35 to 45 minutes duration. Generate 20 questions include descriptive and Coding questions .
    - The Questions should be human conventional and should not include any jargon or overly complex language and should be easy to understand.
    -Do not add any unnecessary context or explanations or any extra notes. Only provide the questions in a numbered list format. Each question should be clear, concise, and directly related to the skills and qualifications mentioned in the JD and Resume.
    - Follow the proper format for each question.
    -Following are the Job Description (JD) and Resume
    - Reminder it is a live interview and not a written test. So, the questions should be designed to assess the candidate's practical knowledge and problem-solving abilities in a real-world context.
    Job Description:
    {jd}

    Resume:
    {resume}

    Interview Questions:
    """
    response = get_azure_response(prompt)
    return response
