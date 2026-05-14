from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.course import CourseStatus, CourseVisibility

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    visibility: CourseVisibility = CourseVisibility.public
    allow_download: bool = True
    status: CourseStatus = CourseStatus.draft

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    visibility: Optional[CourseVisibility] = None
    allow_download: Optional[bool] = None
    status: Optional[CourseStatus] = None

class AuthorResponse(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    slug: str
    category: Optional[str] = None
    tags: Optional[str] = None
    file_type: Optional[str] = None
    status: CourseStatus
    visibility: CourseVisibility
    allow_download: bool
    views: int
    author: AuthorResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    html_content: Optional[str] = None