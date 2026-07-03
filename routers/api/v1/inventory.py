from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlmodel import Session
from database.session import get_session
from database.models import ProcessedWebhook
from pydantic import BaseModel
from typing import Optional
from core.config import settings

router = APIRouter()

class DeductOrderRequest(BaseModel):
    order_id: str
    source: str = "medusa_storefront"

@router.post("/deduct-from-order")
def deduct_from_order(
    request: DeductOrderRequest,
    x_api_key: Optional[str] = Header(None),
    session: Session = Depends(get_session)
):
    if not x_api_key or x_api_key != settings.MEDUSA_ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    event_id = f"deduct_{request.order_id}"
    
    # Idempotency Check
    existing = session.get(ProcessedWebhook, event_id)
    if existing:
        return Response(status_code=200, content="Already processed (idempotent)")
    
    # TODO: Implement actual inventory deduction logic here for VibeCloud 
    # For now we just mark it as processed
    
    webhook_log = ProcessedWebhook(
        event_id=event_id,
        source=request.source,
        status="processed"
    )
    session.add(webhook_log)
    session.commit()
    
    return {"status": "success", "order_id": request.order_id}
