from sqlalchemy import Column, Integer, String, Text,email
from services.database import Base
class interview_candidate(Base):
    __tablename__ = "interview_candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    interview_role = Column(String(255), nullable=False)
    assessment_difficulty = Column(String(255), nullable=False)
    resume_path = Column(Text, nullable=False)
    jd_name = Column(String(255), nullable=False)