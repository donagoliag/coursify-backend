from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import subprocess
from app.database import get_db
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseDetailResponse
from app.services.course import (
    get_courses, get_course_by_slug, get_teacher_courses,
    create_course, update_course, delete_course
)
from app.core.deps import get_current_user, get_current_teacher, get_current_admin
from app.core.config import settings
from app.models.user import User
from app.models.course import Course, CourseStatus

router = APIRouter(prefix="/api/courses", tags=["Courses"])

def convert_file_to_html(file_path: str, file_type: str) -> str:
    try:
        if file_type == "ipynb":
            import nbformat
            from nbconvert import HTMLExporter
            with open(file_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
            exporter = HTMLExporter()
            exporter.template_name = "basic"
            html_content, _ = exporter.from_notebook_node(nb)
            return html_content

        elif file_type == "md":
            import markdown
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return markdown.markdown(
                content,
                extensions=[
                    "fenced_code",
                    "tables",
                    "toc",
                    "codehilite",
                    "nl2br",
                ]
            )
    except Exception as e:
        return f"<p>Erreur de conversion : {str(e)}</p>"
    
@router.get("/", response_model=List[CourseResponse])
def list_courses(
    skip: int = 0,
    limit: int = 12,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return get_courses(db, skip=skip, limit=limit, category=category, search=search)

@router.get("/popular", response_model=List[CourseResponse])
def popular_courses(limit: int = 6, db: Session = Depends(get_db)):
    return db.query(Course).filter(
        Course.status == CourseStatus.published
    ).order_by(Course.views.desc()).limit(limit).all()

@router.get("/my-courses", response_model=List[CourseResponse])
def my_courses(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    return get_teacher_courses(db, current_user.id)

@router.get("/{slug}", response_model=CourseDetailResponse)
def get_course(slug: str, db: Session = Depends(get_db)):
    return get_course_by_slug(db, slug)

@router.post("/", response_model=CourseResponse)
def create_new_course(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    visibility: str = Form("public"),
    allow_download: bool = Form(True),
    status: str = Form("draft"),
    source_type: Optional[str] = Form("editor"),  # 'editor' ou 'upload'
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    from app.schemas.course import CourseCreate
    from app.models.course import CourseVisibility, CourseStatus

    course_data = CourseCreate(
        title=title,
        description=description,
        category=category,
        tags=tags,
        visibility=visibility,
        allow_download=allow_download,
        status=status,
    )
    course = create_course(db, course_data, current_user)

    if file:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["ipynb", "md"]:
            raise HTTPException(status_code=400, detail="Format non supporté")

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, f"{course.slug}.{ext}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if source_type == 'upload':
            html_content = None  # pas de conversion pour les uploads
        else:
            html_content = convert_file_to_html(file_path, ext)

        course.file_path = file_path
        course.file_type = 'upload' if source_type == 'upload' else ext
        course.html_content = html_content
        db.commit()
        db.refresh(course)

    return course

@router.put("/{course_id}", response_model=CourseResponse)
def update_existing_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    return update_course(db, course_id, course_data, current_user)

@router.delete("/{course_id}")
def delete_existing_course(
    course_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    return delete_course(db, course_id, current_user)

@router.get("/{course_id}/download")
def download_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    if not course.allow_download:
        raise HTTPException(status_code=403, detail="Téléchargement non autorisé")
    if not course.file_path or not os.path.exists(course.file_path):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return FileResponse(course.file_path, filename=os.path.basename(course.file_path))

@router.post("/{course_id}/duplicate", response_model=CourseResponse)
def duplicate_course(
    course_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    original = db.query(Course).filter(Course.id == course_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    if original.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé")

    from app.services.course import generate_slug
    new_slug = generate_slug(f"{original.title} copie", db)

    duplicate = Course(
        title=f"{original.title} (copie)",
        description=original.description,
        slug=new_slug,
        category=original.category,
        tags=original.tags,
        file_type=original.file_type,
        html_content=original.html_content,
        status=CourseStatus.draft,
        visibility=original.visibility,
        allow_download=original.allow_download,
        author_id=current_user.id,
    )
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    return duplicate

@router.put("/{course_id}/full")
def update_course_full(
    course_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    visibility: str = Form("public"),
    allow_download: bool = Form(True),
    status: str = Form("draft"),
    source_type: str = Form("editor"),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    if course.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé")

    course.title = title
    course.description = description
    course.category = category
    course.tags = tags
    course.visibility = visibility
    course.allow_download = allow_download
    course.status = status

    if file:
        ext = file.filename.split(".")[-1].lower()
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, f"{course.slug}.{ext}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if source_type == 'upload':
            html_content = None
            course.file_type = 'upload'
        else:
            html_content = convert_file_to_html(file_path, ext)
            course.file_type = ext

        course.file_path = file_path
        course.html_content = html_content

    db.commit()
    db.refresh(course)
    return course