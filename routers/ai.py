from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import json
# In a real scenario, you'd use google-genai or google.generativeai here
# For the MVP, we simulate the structure or call the REST API directly
import httpx
from database import get_db
from models import User
from web.dependencies import get_current_user

router = APIRouter(prefix="/api/ai", tags=["AI Services"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class CopyRequest(BaseModel):
    product_name: str
    category: Optional[str] = None
    context: Optional[str] = None

class ThemeRequest(BaseModel):
    description: str

class ImageRequest(BaseModel):
    prompt: str

@router.post("/copy")
async def generate_copy(req: CopyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key no configurada en el backend.")
    
    # Simple prompt for Gemini 2.5 Flash-Lite
    prompt = f"Genera 3 opciones de copy de ventas persuasivo para el producto '{req.product_name}'. Categoría: {req.category}. Contexto extra: {req.context}. Devuelve solo los textos numerados."
    
    try:
        # Pseudo-code for Gemini REST API call
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {"success": True, "copies": text.split("\n")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/theme")
async def generate_theme(req: ThemeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key no configurada.")
    
    prompt = f"""Crea una paleta de colores para una tienda online descrita como: '{req.description}'.
    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta (reemplazando los hex por los sugeridos):
    {{
      "bg": "#ffffff",
      "primary": "#000000",
      "secondary": "#cccccc",
      "cardBg": "#f0f0f0",
      "border": "#dddddd",
      "text": "#333333",
      "shadow": "0 4px 6px rgba(0,0,0,0.1)"
    }}
    No agregues markdown, ni backticks, ni comentarios."""
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
            )
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            # Limpiar posible texto extra
            text = text.replace('```json', '').replace('```', '').strip()
            theme_json = json.loads(text)
            return {"success": True, "theme": theme_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parseando tema: {str(e)}")

@router.post("/image")
async def generate_image(req: ImageRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simulación de generación de imagen (Gemini Imagen 4 Fast o Vertex AI)
    return {"success": True, "image_url": "https://placehold.co/600x400/png?text=Generated+Image"}
