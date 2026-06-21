from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database.session import get_session
from database.models import UIConfig, User
from web.dependencies import get_current_user_jwt, require_roles
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter()

class UIConfigRequest(BaseModel):
    layout: dict
    theme: dict

class UIConfigResponse(BaseModel):
    page_name: str
    layout: dict
    theme: dict
    updated_at: datetime

# Default configuration to prevent broken UI
DEFAULT_LAYOUT = {
    "modules": ["header", "catalog", "cart", "footer"],
    "grid_cols": 12
}

DEFAULT_THEME = {
    "primary_color": "#4F46E5",
    "secondary_color": "#10B981",
    "mode": "dark"
}

@router.get("/ui-config/{page_name}", response_model=UIConfigResponse)
def get_ui_config(
    page_name: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user_jwt)
):
    # Fetch from database, isolated by user's tenant_id
    config = session.exec(
        select(UIConfig).where(
            UIConfig.tenant_id == user.tenant_id,
            UIConfig.page_name == page_name
        )
    ).first()

    if not config:
        # Return standard default embedded in code
        return UIConfigResponse(
            page_name=page_name,
            layout=DEFAULT_LAYOUT,
            theme=DEFAULT_THEME,
            updated_at=datetime.utcnow()
        )

    try:
        parsed_layout = json.loads(config.layout_json)
    except Exception:
        parsed_layout = DEFAULT_LAYOUT

    try:
        parsed_theme = json.loads(config.theme_json)
    except Exception:
        parsed_theme = DEFAULT_THEME

    return UIConfigResponse(
        page_name=config.page_name,
        layout=parsed_layout,
        theme=parsed_theme,
        updated_at=config.updated_at
    )

@router.put("/ui-config/{page_name}", response_model=UIConfigResponse)
def update_ui_config(
    page_name: str,
    data: UIConfigRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_roles(["admin", "superadmin"]))
):
    # Fetch existing config for this page and tenant
    config = session.exec(
        select(UIConfig).where(
            UIConfig.tenant_id == user.tenant_id,
            UIConfig.page_name == page_name
        )
    ).first()

    layout_str = json.dumps(data.layout)
    theme_str = json.dumps(data.theme)

    if not config:
        config = UIConfig(
            tenant_id=user.tenant_id,
            page_name=page_name,
            layout_json=layout_str,
            theme_json=theme_str,
            updated_at=datetime.utcnow()
        )
    else:
        config.layout_json = layout_str
        config.theme_json = theme_str
        config.updated_at = datetime.utcnow()

    session.add(config)
    session.commit()
    session.refresh(config)

    return UIConfigResponse(
        page_name=config.page_name,
        layout=data.layout,
        theme=data.theme,
        updated_at=config.updated_at
    )
