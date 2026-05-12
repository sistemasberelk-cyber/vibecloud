"""routers/auth.py — Login / Logout"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from database.models import Settings, Tenant, User
from database.session import get_session
from services.auth_service import AuthService
from web.compat_templates import CompatTemplates
from web.dependencies import get_settings

router = APIRouter(tags=["Auth"])

def _templates():
    return CompatTemplates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
@router.head("/login")
def login_page(request: Request, settings: Settings = Depends(get_settings)):
    return _templates().TemplateResponse("login.html", {"request": request, "settings": settings})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    user = session.exec(select(User).where(User.username == username)).first()
    admin_override = os.getenv("ADMIN_PASSWORD")
    is_override = False
    if user and user.role == "admin" and admin_override and password == admin_override:
        is_override = True

    if not user and admin_override and username == "admin" and password == admin_override:
        tenant_id = session.exec(select(Tenant.id).order_by(Tenant.id)).first() or 1
        user = User(
            username="admin",
            password_hash=AuthService.get_password_hash(password),
            role="admin",
            tenant_id=tenant_id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        is_override = True

    if not user or (not AuthService.verify_password(password, user.password_hash) and not is_override):
        return _templates().TemplateResponse(
            "login.html", {"request": request, "error": "Credenciales inválidas", "settings": settings}
        )
    request.session["user_id"] = user.id
    if user.role == "superadmin":
        return RedirectResponse("/tenants", status_code=302)
    return RedirectResponse("/", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
