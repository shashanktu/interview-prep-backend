from sqlalchemy import Column, Integer, String, Date, Time, func, Text, ForeignKey
from services.database import Base
import uuid


def generate_interview_id():
    return f"VAM-{uuid.uuid4().hex[:8].upper()}"



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    associate_name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    created_at = Column(Date, default=func.current_date(), nullable=False)
    created_time = Column(Time, default=func.current_time(), nullable=False)


class JD(Base):
    __tablename__ = "jd"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(255), nullable=False, unique=True)
    path = Column(Text, nullable=False)




class Interview(Base):
    __tablename__ = "interview"

    interview_id = Column(String, primary_key=True, default=generate_interview_id, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False, unique=True)
    tsc = Column(String(255), nullable=False)
    role = Column(String(255), ForeignKey("jd.role"), nullable=False)
    l2_panel = Column(String(255), nullable=True)
    l2_email = Column(String(255), nullable=True)
    level = Column(String(50), nullable=True)
    jd_name = Column(String(255), nullable=True)
    resume_path = Column(Text, nullable=False)
    l1_status = Column(String(50), nullable=True)
    l1_result = Column(String(50), nullable=True)
    l2_status = Column(String(50), nullable=True)
    l2_result = Column(String(50), nullable=True)