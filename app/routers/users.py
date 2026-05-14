from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate, ChangePassword
from app.services.auth import create_user
from app.core.deps import get_current_user, get_current_admin
from app.core.security import verify_password, hash_password, decode_token, create_access_token
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus
from pydantic import BaseModel
from jose import JWTError

router = APIRouter(prefix="/api/users", tags=["Users"])

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh-token")
def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token invalide")
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        new_access_token = create_access_token({"sub": str(user.id)})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expiré ou invalide")

@router.post("/", response_model=UserResponse)
def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return create_user(db, user_data)

@router.get("/", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return db.query(User).order_by(User.created_at.desc()).all()

@router.get("/stats")
def get_platform_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    total_users = db.query(User).count()
    total_teachers = db.query(User).filter(User.role == UserRole.teacher).count()
    total_students = db.query(User).filter(User.role == UserRole.student).count()
    total_courses = db.query(Course).count()
    published_courses = db.query(Course).filter(
        Course.status == CourseStatus.published
    ).count()
    draft_courses = db.query(Course).filter(
        Course.status == CourseStatus.draft
    ).count()
    archived_courses = db.query(Course).filter(
        Course.status == CourseStatus.archived
    ).count()
    total_views = db.query(Course).with_entities(
        db.query(Course).statement.c.views
    ).all()

    from sqlalchemy import func
    views_result = db.query(func.sum(Course.views)).scalar()
    total_views = views_result or 0

    return {
        "total_users": total_users,
        "total_teachers": total_teachers,
        "total_students": total_students,
        "total_courses": total_courses,
        "published_courses": published_courses,
        "draft_courses": draft_courses,
        "archived_courses": archived_courses,
        "total_views": total_views,
    }

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user

@router.put("/me", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    for field, value in data.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password")
def change_password(
    data: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour"}

@router.put("/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user

@router.put("/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if role not in ["admin", "teacher", "student"]:
        raise HTTPException(status_code=400, detail="Rôle invalide")
    user.role = role
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Impossible de supprimer un admin")
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}