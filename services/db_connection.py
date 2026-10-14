from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from models.models import JD, Interview, User, InterviewMetadata
from utils.config import DB_URL

# Database connection logic here
def get_db_connection():
    # Example connection logic using SQLAlchemy
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #NOSONAR

    return SessionLocal()



Base = declarative_base()

engine = create_engine(DB_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


from models.models import JD, Interview, User



def insert_user(user: User):
    db = get_db_connection()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def search_user_by_email(email: str):
    db = get_db_connection()
    return db.query(User).filter(User.associate_email == email).one_or_none()



def insert_interview(interview: Interview):
    db = get_db_connection()
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def insert_jd(jd):
    db = get_db_connection()
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


#Search jd by role
def search_jd_by_role(role):
    db = get_db_connection()
    return db.query(JD).filter(JD.role == role).one_or_none()

def search_jd_resume(interview_id):
    db = get_db_connection()
    result = (
    db.query(
        JD.path.label("jd_path"),
        Interview.resume_path
    )
    .join(JD, Interview.role == JD.role)
    .filter(
        Interview.interview_id == interview_id
    )
    .one_or_none()
)
    return result


# get all the role names from the table
def search_all_jds():
    db = get_db_connection()
    return db.query(JD.role).all()

def get_resume_link(
    interview_id
):
    db = get_db_connection()
    result = (
        db.query(Interview.resume_path,
        Interview.jd_name
)
        .filter(Interview.interview_id == interview_id)
        .one_or_none()
    )
    return result


def get_interview_status(interview_id: str):
    db = get_db_connection()
    interview = db.query(Interview).filter(Interview.interview_id == interview_id).one_or_none()
    return interview.status if interview else None

#function to change the status of the interview
def update_interview_status(interview_id: str,status:str):
    db = get_db_connection()
    interview = db.query(Interview).filter(Interview.interview_id == interview_id).one_or_none()
    if not interview:
        return None
    interview.status = status
    db.commit()
    return interview

def insert_metadata(metadata: InterviewMetadata):
    db = get_db_connection()
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    return metadata


def get_interview_questions_db(interview_id: str):
    db = get_db_connection()
    result = db.query(InterviewMetadata).filter(InterviewMetadata.interview_id == interview_id).all()
    return result


def get_interview_data(interview_id: str):
    db = get_db_connection()
    result = db.query(Interview).filter(Interview.interview_id == interview_id).one_or_none()
    return result
