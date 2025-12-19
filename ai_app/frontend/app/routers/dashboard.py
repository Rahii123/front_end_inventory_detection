from fastapi import APIRouter, Request, Depends, Cookie
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import TrainingJob, Prediction
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    user_id: str | None = Cookie(default=None)
):
    if not user_id:
        return RedirectResponse(url="/login")
    
    # Fetch stats
    total_training = db.query(TrainingJob).count()
    total_predictions = db.query(Prediction).count()
    
    print(f"DASHBOARD DIAGNOSTIC: Found {total_training} training jobs and {total_predictions} predictions.")
    
    recent_training = db.query(TrainingJob).order_by(TrainingJob.id.desc()).limit(5).all()
    recent_predictions = db.query(Prediction).order_by(Prediction.id.desc()).limit(5).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": True,
        "total_training": total_training,
        "total_predictions": total_predictions,
        "recent_training": recent_training,
        "recent_predictions": recent_predictions,
        "active_page": "dashboard"
    })
