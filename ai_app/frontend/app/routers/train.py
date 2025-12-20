from fastapi import APIRouter, Request, Form, Depends, Cookie, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import TrainingJob
import json
import httpx
import traceback

router = APIRouter(tags=["train"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/train")
async def train_redirect():
    return RedirectResponse(url="/train/get/config")

@router.get("/train/get/config", response_class=HTMLResponse)
async def train_view(request: Request, db: Session = Depends(get_db), user_id: str | None = Cookie(default=None)):
    if not user_id:
        return RedirectResponse(url="/login")
    
    # Get latest config from DB (fallback)
    config = db.query(TrainingJob).order_by(TrainingJob.id.desc()).first()
    
    # Try to fetch latest config from external API
    from app.core.config import settings
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.TRAIN_CONFIG_URL, timeout=10.0)
            if response.status_code == 200:
                remote_config = response.json()
                # If we have remote config, we could update our local DB or just pass it to template
                # For now, let's just make sure we use the remote data if available
                # Assuming remote_config has similar structure
                if isinstance(remote_config, dict) and "epochs" in remote_config:
                    # Update or create local record to sync
                    new_config = TrainingJob(
                        epochs=remote_config.get("epochs", 50),
                        batch_size=remote_config.get("batch_size", 32),
                        learning_rate=str(remote_config.get("learning_rate", "0.0001")),
                        model_name=remote_config.get("model_name", "yolo12").lower(),
                        classes=remote_config.get("classes", 1),
                        augmentation=remote_config.get("augmentation", True),
                        status="synced"
                    )
                    db.add(new_config)
                    db.commit()
                    db.refresh(new_config)
                    config = new_config
    except Exception as e:
        print(f"Error fetching remote config: {e}")

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
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "model_name": model_name,
                "classes": classes,
                "augmentation": is_augmented
            }
            response = await client.post(settings.UPDATE_CONFIG_URL, json=payload, timeout=10.0)
            print(f"External API response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to sync config with external API: {e}")
        traceback.print_exc()

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
    
    success = False
    error_msg = None
    
    try:
        async with httpx.AsyncClient() as client:
            # Prepare payload from config
            payload = {}
            if config:
                payload = {
                    "epochs": config.epochs,
                    "batch_size": config.batch_size,
                    "learning_rate": config.learning_rate,
                    "model_name": config.model_name,
                    "classes": config.classes,
                    "augmentation": config.augmentation
                }
            
            response = await client.post(settings.START_TRAINING_URL, json=payload, timeout=30.0)
            print(f"Training start response: {response.status_code} - {response.text}")
            if response.status_code in [200, 201, 202]:
                success = True
            else:
                error_msg = f"API Error: {response.status_code}"
    except Exception as e:
        print(f"Failed to trigger training: {e}")
        traceback.print_exc()
        error_msg = str(e)
    
    # Update status to training if successful
    if success and config:
        config.status = "training"
        db.commit()
        return {"status": "started", "message": "Training is start wait"}
    else:
        return {"status": "error", "message": error_msg or "Could not start training"}
