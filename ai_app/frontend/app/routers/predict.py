from fastapi import APIRouter, Request, UploadFile, File, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import random
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Prediction

router = APIRouter(tags=["predict"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/predict", response_class=HTMLResponse)
async def predict_page(request: Request, user_id: str | None = Cookie(default=None)):
    if not user_id:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("predict.html", {"request": request, "user": True})

@router.post("/predict", response_class=HTMLResponse)
async def predict(
    request: Request, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    user_id: str | None = Cookie(default=None)
):
    if not user_id:
        return RedirectResponse(url="/login")
    
    # Read file content
    content = await file.read()
    
    from app.core.config import settings
    import httpx
    import json
    
    prediction_result = None
    confidence = 0
    error_message = None
    
    try:
        async with httpx.AsyncClient() as client:
            # We use "file" as the key, which is standard for FastAPI UploadFile parameters
            files = {"file": (file.filename, content, file.content_type)}
            response = await client.post(settings.EXTERNAL_PREDICTOR_API, files=files, timeout=60.0)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Try to find a result in a very flexible way
                    # Priority 0: Nested predictions list (The structure found in the user's last message)
                    predictions = data.get("predictions")
                    if predictions and isinstance(predictions, list) and len(predictions) > 0:
                        # Take the first prediction as primary, but we'll store all class names
                        primary = predictions[0]
                        prediction_result = primary.get("class_name") or primary.get("label") or primary.get("prediction")
                        confidence = primary.get("confidence") or 0.99
                        
                        # If there are multiple, let's join them for the display result
                        if len(predictions) > 1:
                            all_classes = [p.get("class_name") or p.get("label") for p in predictions if p.get("class_name") or p.get("label")]
                            prediction_result = ", ".join(all_classes)
                    
                    # Priority 1: Specific known keys at root
                    if not prediction_result:
                        prediction_result = data.get("prediction") or data.get("label") or data.get("result") or data.get("class")
                    
                    # Priority 2: If it's a direct string or has a single value
                    if not prediction_result:
                        if isinstance(data, str):
                            prediction_result = data
                        elif isinstance(data, dict) and len(data) == 1:
                            prediction_result = list(data.values())[0]
                    
                    if prediction_result:
                        # Find confidence if exists (and not already set by Priority 0)
                        if not confidence:
                            confidence = data.get("confidence") or data.get("score") or 0.99
                    else:
                        error_message = f"Connected! But couldn't find a 'prediction' key in the response. Received: {json.dumps(data)}"
                except Exception:
                    # If not JSON, maybe it's raw text?
                    text_resp = response.text.strip()
                    if text_resp and len(text_resp) < 50:
                        prediction_result = text_resp
                    else:
                        error_message = f"Received non-JSON response from API: {text_resp[:200]}"
            else:
                error_message = f"The remote API returned an error (Status {response.status_code}). URL: {settings.EXTERNAL_PREDICTOR_API}"
                
    except httpx.ConnectError:
        error_message = f"Error in connection: Unable to reach {settings.EXTERNAL_PREDICTOR_API}. Please ensure your ngrok tunnel is active."
    except httpx.TimeoutException:
        error_message = "Error in connection: The request to the AI server timed out (60s limit)."
    except Exception as e:
        error_message = f"Unexpected Error: {str(e)}"
    
    # Store in database if successful
    if prediction_result and not error_message:
        try:
            new_prediction = Prediction(
                filename=file.filename,
                prediction_text=str(prediction_result),
                confidence=float(confidence)
            )
            db.add(new_prediction)
            db.commit()
            print(f"Stored prediction for {file.filename} in database.")
        except Exception as db_err:
            print(f"Failed to store prediction in database: {str(db_err)}")

    return templates.TemplateResponse("predict.html", {
        "request": request, 
        "user": True, 
        "prediction": str(prediction_result) if prediction_result else None,
        "confidence": float(confidence) if confidence else 0,
        "error": error_message,
        "active_page": "predict"
    })
