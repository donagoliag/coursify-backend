from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.course import Course, CourseStatus
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate
import re
import os

def generate_slug(title: str, db: Session) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    original = slug
    counter = 1
    while db.query(Course).filter(Course.slug == slug).first():
        slug = f"{original}-{counter}"
        counter += 1
    return slug

def get_courses(db: Session, skip: int = 0, limit: int = 12,
                category: str = None, search: str = None,
                status: str = "published") -> list:
    query = db.query(Course)
    if status:
        query = query.filter(Course.status == status)
    if category:
        query = query.filter(Course.category == category)
    if search:
        query = query.filter(
            Course.title.ilike(f"%{search}%") |
            Course.description.ilike(f"%{search}%")
        )
    return query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()

def get_course_by_slug(db: Session, slug: str) -> Course:
    course = db.query(Course).filter(Course.slug == slug).first()
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    course.views += 1
    db.commit()
    db.refresh(course)
    return course

def get_teacher_courses(db: Session, teacher_id: int) -> list:
    return db.query(Course).filter(
        Course.author_id == teacher_id
    ).order_by(Course.created_at.desc()).all()

def create_course(db: Session, course_data: CourseCreate, author: User) -> Course:
    slug = generate_slug(course_data.title, db)
    course = Course(
        title=course_data.title,
        description=course_data.description,
        slug=slug,
        category=course_data.category,
        tags=course_data.tags,
        visibility=course_data.visibility,
        allow_download=course_data.allow_download,
        status=course_data.status,
        author_id=author.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

def update_course(db: Session, course_id: int, course_data: CourseUpdate, author: User) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    if course.author_id != author.id and author.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé")
    for field, value in course_data.dict(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course

def delete_course(db: Session, course_id: int, author: User) -> dict:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    if course.author_id != author.id and author.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé")
    db.delete(course)
    db.commit()
    return {"message": "Cours supprimé"}