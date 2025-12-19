from fastapi import APIRouter, Request, UploadFile, File, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import random
import httpx
import json
import traceback
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Prediction
from app.core.config import settings

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
                except Exception as parse_err:
                    # If not JSON, maybe it's raw text?
                    text_resp = response.text.strip()
                    if text_resp and len(text_resp) < 50:
                        prediction_result = text_resp
                    else:
                        error_message = f"Received non-JSON response or Parse Error: {str(parse_err)} | Text: {text_resp[:100]}"
            else:
                error_message = f"Remote API Error (Status {response.status_code}): {response.text[:200]}"
                
    except httpx.ConnectError:
        error_message = f"Connection Failed: Unable to reach {settings.EXTERNAL_PREDICTOR_API}. Is ngrok running?"
    except httpx.TimeoutException:
        error_message = "Connection Timed Out: The AI server took too long to respond (60s limit)."
    except Exception as e:
        traceback.print_exc()
        error_message = f"Unexpected Error ({type(e).__name__}): {str(e)}"
    
    # Store in database if successful
    if prediction_result and not error_message:
        print(f"DEBUG: Attempting to store prediction for {file.filename}")
        print(f"DEBUG: Data: {prediction_result}, {confidence}")
        try:
            new_prediction = Prediction(
                filename=file.filename,
                prediction_text=str(prediction_result),
                confidence=float(confidence)
            )
            db.add(new_prediction)
            db.flush() # Try to flush before commit to catch early errors
            db.commit()
            print(f"SUCCESS: Stored prediction for {file.filename} (ID: {new_prediction.id}) in database.")
        except Exception as db_err:
            db.rollback()
            print(f"CRITICAL ERROR: Failed to store in database: {str(db_err)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"DEBUG: Skipping storage. Result: {prediction_result}, Error: {error_message}")

    return templates.TemplateResponse("predict.html", {
        "request": request, 
        "user": True, 
        "prediction": str(prediction_result) if prediction_result else None,
        "confidence": float(confidence) if confidence else 0,
        "error": error_message,
        "active_page": "predict"
    })
