from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from database import get_db
from models import Settings, User
from web.dependencies import get_current_user

router = APIRouter(prefix="/api/store", tags=["Store Settings"])

class ThemeUpdateRequest(BaseModel):
    theme_id: str

@router.put("/theme")
async def update_store_theme(req: ThemeUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Find settings for tenant
    settings = db.exec(select(Settings).where(Settings.tenant_id == current_user.tenant_id)).first()
    
    if not settings:
        # Create default settings if not exist
        settings = Settings(tenant_id=current_user.tenant_id, company_name="VibeCloud", ui_theme=req.theme_id)
        db.add(settings)
    else:
        settings.ui_theme = req.theme_id
        
    db.commit()
    return {"success": True, "theme_id": req.theme_id}
