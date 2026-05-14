from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.models import user, course
from app.routers import auth, users, courses
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole

# Créer les tables
user.Base.metadata.create_all(bind=engine)
course.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Coursify API",
    description="API de gestion de cours en ligne",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)

# Seed admin par défaut
@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not existing:
            admin = User(
                first_name="Admin",
                last_name="Coursify",
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin créé : {settings.ADMIN_EMAIL}")
        else:
            print(f"✅ Admin existe déjà : {settings.ADMIN_EMAIL}")
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Coursify API", "version": "1.0.0", "docs": "/docs"}