"""
services/medusa_sync.py

Cliente REST asíncrono hacia la Admin API de Medusa (v2).
Responsable de: autenticación, upsert de productos, y mapeo del schema
"NexPOS Product" (generado por Gemini) -> "Medusa Product".

Diseño: sigue el mismo patrón de servicio que GeminiService / StockService
("Fat Models, Thin Routers"). Se instancia una sola vez (singleton a nivel
de módulo) y se inyecta en los routers vía Depends() o se importa directo.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any
from datetime import datetime
import httpx
from sqlmodel import Session, select
from database.models import SyncQueue
from core.config import settings

logger = logging.getLogger("medusa_sync")

REQUEST_TIMEOUT = 15.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5

class MedusaSyncError(Exception):
    """Error genérico de sincronización con Medusa."""

class MedusaAuthError(MedusaSyncError):
    """Fallo de autenticación contra la Admin API de Medusa."""

class MedusaSyncService:
    def __init__(self, base_url: str = settings.MEDUSA_URL) -> None:
        self.base_url = base_url.rstrip("/") if base_url else "http://localhost:9000"
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=REQUEST_TIMEOUT)

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    async def _get_auth_header(self) -> dict[str, str]:
        if settings.MEDUSA_ADMIN_API_KEY:
            # Secret key admin: no expira, no requiere login.
            return {"Authorization": f"Bearer {settings.MEDUSA_ADMIN_API_KEY}"}

        # Fallback: login email/password, cacheado ~ 1h (ajustar a tu config de Medusa)
        if self._token and time.time() < self._token_expires_at:
            return {"Authorization": f"Bearer {self._token}"}

        raise MedusaAuthError(
            "Faltan credenciales de Medusa: define MEDUSA_ADMIN_API_KEY"
        )

    # ------------------------------------------------------------------
    # HTTP interno con reintentos
    # ------------------------------------------------------------------
    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = await self._get_auth_header()
        headers.update(kwargs.pop("headers", {}))

        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await self._client.request(method, path, headers=headers, **kwargs)
                if resp.status_code == 401 and settings.MEDUSA_ADMIN_API_KEY is None:
                    # Token expirado, forzar re-login y reintentar una vez
                    self._token = None
                    headers = await self._get_auth_header()
                    continue
                if resp.status_code >= 500:
                    raise MedusaSyncError(f"Medusa 5xx: {resp.status_code} {resp.text}")
                return resp
            except (httpx.TransportError, MedusaSyncError) as exc:
                last_exc = exc
                logger.warning(
                    "Intento %s/%s fallido contra Medusa (%s %s): %s",
                    attempt, MAX_RETRIES, method, path, exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        raise MedusaSyncError(f"Fallaron {MAX_RETRIES} intentos contra Medusa: {last_exc}")

    # ------------------------------------------------------------------
    # Mapeo de schema: NexPOS (Gemini) -> Medusa
    # ------------------------------------------------------------------
    @staticmethod
    def _map_product_payload(nexpos_product: dict, tenant_id: str) -> dict:
        variants = nexpos_product.get("variants") or [
            {
                "title": "Default",
                "sku": nexpos_product.get("sku"),
                "prices": [
                    {
                        "amount": int(round(nexpos_product.get("price", 0) * 100)),  # Medusa usa centavos
                        "currency_code": nexpos_product.get("currency", "usd"),
                    }
                ],
            }
        ]

        return {
            "title": nexpos_product.get("title", ""),
            "description": nexpos_product.get("description", ""),
            "status": "published" if nexpos_product.get("is_active", True) else "draft",
            "options": nexpos_product.get("options", [{"title": "Default"}]),
            "variants": variants,
            "images": [{"url": url} for url in nexpos_product.get("image_urls", [])],
            "metadata": {
                "tenant_id": tenant_id,
                "nexpos_product_id": str(nexpos_product.get("id", "")),
                "source": "nexpos-ai-webbuilder",
            },
        }

    # ------------------------------------------------------------------
    # API pública del servicio
    # ------------------------------------------------------------------
    async def find_by_nexpos_id(self, tenant_id: str, nexpos_product_id: str) -> dict | None:
        resp = await self._request(
            "GET",
            "/admin/products",
            params={"q": nexpos_product_id, "limit": 1},
        )
        resp.raise_for_status()
        results = resp.json().get("products", [])
        for p in results:
            meta = p.get("metadata") or {}
            if meta.get("nexpos_product_id") == str(nexpos_product_id) and meta.get("tenant_id") == tenant_id:
                return p
        return None

    async def create_product(self, nexpos_product: dict, tenant_id: str) -> dict:
        payload = self._map_product_payload(nexpos_product, tenant_id)
        resp = await self._request("POST", "/admin/products", json=payload)
        if resp.status_code not in (200, 201):
            raise MedusaSyncError(f"Error creando producto en Medusa: {resp.status_code} {resp.text}")
        return resp.json()["product"]

    async def update_product(self, medusa_product_id: str, nexpos_product: dict, tenant_id: str) -> dict:
        payload = self._map_product_payload(nexpos_product, tenant_id)
        resp = await self._request("POST", f"/admin/products/{medusa_product_id}", json=payload)
        if resp.status_code != 200:
            raise MedusaSyncError(f"Error actualizando producto en Medusa: {resp.status_code} {resp.text}")
        return resp.json()["product"]

    async def sync_bulk_price(self, medusa_product: dict, price_bulk: float) -> None:
        """
        Crea o actualiza un Price List B2B con el precio mayorista en Medusa v2.
        Usa la sintaxis 'rules' correcta.
        """
        variants = medusa_product.get("variants", [])
        if not variants:
            logger.warning("No variants found — skipping bulk price sync")
            return
        variant_id = variants[0]["id"]

        # Buscar el Customer Group "Wholesale"
        groups_resp = await self._request(
            "GET",
            "/admin/customer-groups",
            params={"q": "Wholesale"},
        )
        groups = groups_resp.json().get("customer_groups", [])
        wholesale = next((g for g in groups if g["name"] == "Wholesale"), None)

        if not wholesale:
            logger.warning("Customer Group 'Wholesale' no existe — creando")
            create_resp = await self._request(
                "POST",
                "/admin/customer-groups",
                json={"name": "Wholesale"},
            )
            wholesale = create_resp.json()["customer_group"]

        # Buscar Price List existente para Wholesale
        pl_resp = await self._request(
            "GET",
            "/admin/price-lists",
            params={"q": "Mayorista B2B"},
        )
        price_lists = pl_resp.json().get("price_lists", [])
        existing_pl = next(
            (p for p in price_lists if "Mayorista B2B" in p.get("name", "")),
            None
        )

        bulk_price_cents = int(price_bulk * 100)
        rules = {"customer_group_id": [wholesale["id"]]}

        if existing_pl:
            await self._request(
                "POST",
                f"/admin/price-lists/{existing_pl['id']}/prices/batch",
                json={
                    "prices": [
                        {
                            "variant_id": variant_id,
                            "amount": bulk_price_cents,
                            "currency_code": "usd",
                        }
                    ]
                }
            )
        else:
            await self._request(
                "POST",
                "/admin/price-lists",
                json={
                    "name": "Mayorista B2B — Descuento 30%",
                    "description": "Precios mayoristas automáticos desde NexPOS",
                    "type": "sale",
                    "status": "active",
                    "rules": rules,
                    "prices": [
                        {
                            "variant_id": variant_id,
                            "amount": bulk_price_cents,
                            "currency_code": "usd",
                        }
                    ],
                }
            )
        logger.info(f"✅ Precio bulk ${price_bulk} sincronizado al grupo Wholesale (variant {variant_id})")


    def enqueue(self, db: Session, entity_type: str, payload: dict, error: str = "") -> None:
        item = SyncQueue(
            entity_type=entity_type,
            entity_id=str(payload.get("id", "")),
            payload=payload,
            status="pending",
            last_error=error,
        )
        db.add(item)
        db.commit()
        logger.info(f"📥 Encolado {entity_type} {payload.get('id')} para reintento")


    async def sync_product_safe(
        self,
        nexpos_product: dict,
        tenant_id: str,
        db: Session,
        known_medusa_id: str | None = None,
    ) -> dict:
        """
        Punto de entrada seguro: maneja reintentos en memoria (Singleton) y
        si falla, lo encola a la BD (SyncQueue).
        """
        try:
            medusa_id = known_medusa_id
            if not medusa_id:
                existing = await self.find_by_nexpos_id(tenant_id, nexpos_product.get("id", ""))
                medusa_id = existing["id"] if existing else None

            if medusa_id:
                logger.info("Producto %s ya existe en Medusa (%s), actualizando.", nexpos_product.get("id"), medusa_id)
                medusa_product = await self.update_product(medusa_id, nexpos_product, tenant_id)
            else:
                logger.info("Producto %s no existe en Medusa, creando.", nexpos_product.get("id"))
                medusa_product = await self.create_product(nexpos_product, tenant_id)

            # Sync bulk price
            if nexpos_product.get("price_bulk"):
                await self.sync_bulk_price(medusa_product, nexpos_product["price_bulk"])

            return {"status": "synced", "medusa_id": medusa_product["id"]}

        except MedusaSyncError as e:
            logger.error(f"❌ Error al sincronizar producto {nexpos_product.get('id')}: {e}")
            self.enqueue(db, "product", nexpos_product, error=str(e))
            return {"status": "failed", "error": str(e)}
        except Exception as e:
            logger.error(f"⚠️ Medusa no disponible o error fatal. Encolando: {e}")
            self.enqueue(db, "product", nexpos_product, error=str(e))
            return {"status": "queued", "error": str(e)}

    async def process_queue(self, db: Session) -> dict:
        """Procesa hasta 50 items pendientes en sync_queue."""
        stmt = (
            select(SyncQueue)
            .where(SyncQueue.status.in_(["pending", "failed"]))
            .where(SyncQueue.attempts < SyncQueue.max_attempts)
            .order_by(SyncQueue.created_at)
            .limit(50)
        )
        items = db.exec(stmt).all()

        processed, errors = 0, 0
        for item in items:
            item.attempts += 1
            item.status = "processing"
            item.updated_at = datetime.utcnow()
            db.add(item)
            db.commit()

            try:
                # Assuming product for now; can branch on entity_type later
                tenant_id = item.payload.get("tenant_id") or "default"
                result = await self.sync_product_safe(item.payload, tenant_id, db, item.payload.get("medusa_product_id"))
                item.status = "done" if result["status"] == "synced" else "failed"
                if result.get("error"):
                    item.last_error = result["error"]
                processed += 1
            except Exception as e:
                item.status = "failed"
                item.last_error = str(e)
                errors += 1

            item.updated_at = datetime.utcnow()
            db.add(item)
            db.commit()

        return {"processed": processed, "errors": errors, "total": len(items)}


    async def aclose(self) -> None:
        await self._client.aclose()


# Singleton a nivel de módulo
medusa_sync_service = MedusaSyncService()
