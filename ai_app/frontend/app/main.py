from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.db.database import engine, Base, get_db, SessionLocal
from app.db import models
from app.routers import auth, dashboard, train, predict
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Vision Pro")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(train.router)
app.include_router(predict.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/login")

# Seed initial user
def seed_user():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.username == "admin").first()
    if not user:
        user = models.User(
            username="admin",
            hashed_password=get_password_hash("admin123")
        )
        db.add(user)
        db.commit()
    db.close()

seed_user()
