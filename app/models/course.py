from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class CourseVisibility(str, enum.Enum):
    public = "public"
    private = "private"
    restricted = "restricted"

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    html_content = Column(Text, nullable=True)
    status = Column(Enum(CourseStatus), default=CourseStatus.draft)
    visibility = Column(Enum(CourseVisibility), default=CourseVisibility.public)
    allow_download = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="courses")