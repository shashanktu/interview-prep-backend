from services.llm_connection import get_azure_response
def get_questions(jd, resume):
    prompt = f"""
    You are an AI technical interview question generator.

    Generate exactly 20 technical interview questions for an L1 technical interview
    with a duration of 35–45 minutes.

    JOB DESCRIPTION (JD):
    {jd}

    CANDIDATE RESUME:
    {resume}

    QUESTION GENERATION REQUIREMENTS:

    1. Generate exactly 20 questions with medium and high difficulty levels.

    2. Distribute the questions as follows:
    - Questions 1-5: Based on the Job Description.
    - Questions 6-10: Based on the candidate's Resume.
    - Questions 11-20: Practical, real-world questions combining relevant
        skills from the JD and Resume.

    3. Include both descriptive and coding questions.
    - Descriptive questions should assess technical understanding,
        practical experience, and problem-solving abilities.
    - Coding questions should require the candidate to write, explain,
        debug, or improve code during the live interview.
    - Include appropriate coding questions based on the candidate's
        relevant programming languages and technical skills.

    4. Difficulty distribution:
    - 8 medium-difficulty questions.
    - 12 high-difficulty questions.

    5. Question types:
    - Include descriptive and coding questions.
    - Assign each question a type of either "descriptive" or "coding".
    - Ensure coding questions are practical and suitable for a live
        technical discussion rather than lengthy written examinations.

    6. Interview suitability:
    - The interview lasts 35-45 minutes, so prioritize questions that
        can reasonably be discussed or solved within the available time.
    - Focus on technical knowledge, implementation decisions,
        debugging, optimization, and real-world problem-solving.
    - Questions must be clear, concise, conversational, and easy to
        understand.
    - Avoid unnecessary jargon, theoretical trivia, duplicate questions,
        and overly complex wording.
    - Do not ask questions unrelated to the JD or Resume.
    - Do not assume a technology or skill that is not supported by the
        JD or Resume.
    - For resume-based questions, assess the candidate's actual
        experience without assuming that every resume claim is correct.

    7. Question quality:
    - Each question must ask one clear primary question.
    - Avoid questions that contain their own answers.
    - Do not include answers, hints, explanations, evaluation criteria,
        introductions, conclusions, or additional notes.

    8. Output format:
    Return ONLY valid JSON.
    Do not use Markdown code fences or any text outside the JSON.
    Use the following exact JSON structure:

    {{
        "questions": [
        {{
            "question_number": 1,
            "source": "JD",
            "question_type": "descriptive",
            "difficulty": "medium",
            "question": "Question text"
        }},
        {{
            "question_number": 2,
            "source": "Resume",
            "question_type": "coding",
            "difficulty": "high",
            "question": "Question text"
        }}
        ]
    }}

    9. JSON validation rules:
    - The "questions" field must contain exactly 20 objects.
    - Question numbers must be consecutive integers from 1 to 20.
    - The "source" field must be one of "JD", "Resume", or "Combined".
    - Questions 1-5 must have source "JD".
    - Questions 6-10 must have source "Resume".
    - Questions 11-20 must have source "Combined".
    - The "question_type" field must be either "descriptive" or "coding".
    - The "difficulty" field must be either "medium" or "high".
    - Ensure the distribution contains exactly 8 medium and 12 high
        difficulty questions.
    - Escape quotation marks and special characters correctly.
    - Ensure the output is parseable using Python's json.loads().

    Generate the questions now.
    """


    # prompt = f"""
    # -You are an AI interview question generator. I need you to generate the Questions in a proper technical questions with medium and high difficulty levels. This interview will be L1 technical interview with 35 to 45 minutes duration. Generate 20 questions include descriptive and Coding questions .
    # - The Questions should be human conventional and should not include any jargon or overly complex language and should be easy to understand.
    # -Do not add any unnecessary context or explanations or any extra notes. Only provide the questions in a numbered list format. Each question should be clear, concise, and directly related to the skills and qualifications mentioned in the JD and Resume.
    # - Follow the proper format for each question.
    # -Following are the Job Description (JD) and Resume
    # - Reminder it is a live interview and not a written test. So, the questions should be designed to assess the candidate's practical knowledge and problem-solving abilities in a real-world context.
    # - Generate 5 Questions each from Job Description and 5 from Resume.
    # Job Description:
    # {jd}

    # Resume:
    # {resume}

    # Interview Questions:
    # Follow the below format for each question:
    
    # Question 1: [Insert the first question here]
    # """
   
    response = get_azure_response(prompt)
    return response
