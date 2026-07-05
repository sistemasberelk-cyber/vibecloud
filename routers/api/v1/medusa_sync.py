from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from typing import Dict, Any

from database.session import get_session
from database.models import SyncQueue
from services.medusa_sync import medusa_sync_service

router = APIRouter(prefix="/medusa", tags=["medusa_sync"])

@router.post("/sync-all")
async def sync_all_products(request: Request, db: Session = Depends(get_session)) -> Dict[str, Any]:
    # Obtener el tenant_id actual del request state (asumiendo middleware de tenant)
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        # En caso de testing/fallback
        tenant_id = "default"
        
    try:
        # Asegurar canal B2B primero
        await medusa_sync_service.ensure_sales_channel()
        
        result = await medusa_sync_service.sync_all_products(db, tenant_id=tenant_id)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing all products: {str(e)}")


@router.get("/sync-status")
def get_sync_status(tenant_id: str = "default", db: Session = Depends(get_session)) -> Dict[str, Any]:
    stmt = select(SyncQueue).where(SyncQueue.status.in_(["pending", "failed"]))
    pending_items = db.exec(stmt).all()
    
    return {
        "status": "success",
        "pending_count": len(pending_items),
        "items": [
            {
                "id": item.id,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "status": item.status,
                "attempts": item.attempts,
                "last_error": item.last_error
            }
            for item in pending_items
        ]
    }


@router.post("/process-queue")
async def process_sync_queue(db: Session = Depends(get_session)) -> Dict[str, Any]:
    try:
        result = await medusa_sync_service.process_queue(db)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing queue: {str(e)}")
