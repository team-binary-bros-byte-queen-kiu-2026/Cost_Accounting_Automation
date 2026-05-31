"""
POST /analyze — upload an image, get back a cost estimate.
Lab 5 primary endpoint.
"""
import base64
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from ..agents.graph import run_estimation
from ..services.rate_limiter import check_rate_limit
from ..services.session_store import set_estimate

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_SIZE_MB = 10


@router.post("/analyze")
async def analyze_image(request: Request, file: UploadFile = File(...)):
    check_rate_limit(request, "analyze")

    # Validate file type and size
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are accepted.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image must be under {MAX_SIZE_MB}MB.")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    session_id = str(uuid.uuid4())

    try:
        final_state = run_estimation(session_id=session_id, image_base64=image_base64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    estimate = final_state.get("cost_estimate")
    if not estimate:
        raise HTTPException(status_code=500, detail="Could not generate estimate from image.")

    # Store estimate in session for chat follow-up
    set_estimate(session_id, estimate)

    return {
        "session_id": session_id,
        "estimate": estimate,
        "model_used": final_state.get("model_used"),
        "fallback_triggered": final_state.get("fallback_triggered"),
        "approval_required": final_state.get("approval_required"),
    }
