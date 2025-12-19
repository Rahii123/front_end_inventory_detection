from fastapi import APIRouter, Request, Form, Depends, Cookie, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import TrainingJob
import json

router = APIRouter(tags=["train"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/train")
async def train_redirect():
    return RedirectResponse(url="/train/get/config")

@router.get("/train/get/config", response_class=HTMLResponse)
async def train_view(request: Request, db: Session = Depends(get_db), user_id: str | None = Cookie(default=None)):
    if not user_id:
        return RedirectResponse(url="/login")
    
    # Get latest config
    config = db.query(TrainingJob).order_by(TrainingJob.id.desc()).first()
    
    return templates.TemplateResponse("train_view.html", {
        "request": request, 
        "user": True, 
        "config": config,
        "active_page": "train"
    })

@router.get("/train/update/config", response_class=HTMLResponse)
async def train_update_page(request: Request, db: Session = Depends(get_db), user_id: str | None = Cookie(default=None)):
    if not user_id:
        return RedirectResponse(url="/login")
    
    config = db.query(TrainingJob).order_by(TrainingJob.id.desc()).first()
    
    return templates.TemplateResponse("train_update.html", {
        "request": request, 
        "user": True, 
        "config": config,
        "active_page": "train"
    })

@router.post("/train/update/config", response_class=HTMLResponse)
async def save_training_config(
    request: Request,
    epochs: int = Form(...),
    batch_size: int = Form(...),
    learning_rate: str = Form(...),
    model_name: str = Form(...),
    classes: int = Form(...),
    augmentation: str = Form("true"), # Accepting string from dropdown
    db: Session = Depends(get_db),
    user_id: str | None = Cookie(default=None)
):
    if not user_id:
        return RedirectResponse(url="/login")
    
    # Convert string "true"/"false" to actual boolean
    is_augmented = augmentation.lower() == "true"
    
    # Save new config to DB
    new_job = TrainingJob(
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        model_name=model_name.lower(),
        classes=classes,
        augmentation=is_augmented,
        status="configured"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Sync with external API using the specific "update config" URL
    from app.core.config import settings
    print(f"Syncing with external API: {settings.UPDATE_CONFIG_URL}")
    
    # Redirect with "adjusted=true" flag to show success message and training prompt
    return RedirectResponse(url="/train/get/config?adjusted=true", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/train/start")
async def start_training_process(db: Session = Depends(get_db), user_id: str | None = Cookie(default=None)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get latest config to send to training API
    config = db.query(TrainingJob).order_by(TrainingJob.id.desc()).first()
    
    from app.core.config import settings
    print(f"Triggering training at: {settings.START_TRAINING_URL}")
    # In production: httpx.post(settings.EXTERNAL_START_TRAIN_API, json=config_dict)
    
    # Update status to training
    if config:
        config.status = "training"
        db.commit()
    
    return {"status": "started", "message": "Training is start wait"}
