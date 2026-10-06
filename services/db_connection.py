from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from models.models import JD, Interview
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


def get_db_connection():
    return SessionLocal()


def insert_interview(interview: Interview):
    db = get_db_connection()
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview




def insert_jd(jd):
    db = get_db_connection()
    # Assuming you have a JD model defined
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