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

import httpx

logger = logging.getLogger("medusa_sync")


# ---------------------------------------------------------------------------
# Configuración (env vars — agregar a tu .env / Settings de NexPOS)
# ---------------------------------------------------------------------------
MEDUSA_BASE_URL = os.getenv("MEDUSA_BASE_URL", "http://localhost:9000")

# Opción A (recomendada para PoC y prod): API key admin de larga duración,
# generada desde el Admin Panel de Medusa (Settings > API Key Management > Secret Key).
MEDUSA_ADMIN_API_KEY = os.getenv("MEDUSA_ADMIN_API_KEY")

# Opción B (fallback): login con email/password admin, cachea el JWT.
MEDUSA_ADMIN_EMAIL = os.getenv("MEDUSA_ADMIN_EMAIL")
MEDUSA_ADMIN_PASSWORD = os.getenv("MEDUSA_ADMIN_PASSWORD")

REQUEST_TIMEOUT = 15.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5


class MedusaSyncError(Exception):
    """Error genérico de sincronización con Medusa."""


class MedusaAuthError(MedusaSyncError):
    """Fallo de autenticación contra la Admin API de Medusa."""


class MedusaSyncService:
    def __init__(self, base_url: str = MEDUSA_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=REQUEST_TIMEOUT)

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    async def _get_auth_header(self) -> dict[str, str]:
        if MEDUSA_ADMIN_API_KEY:
            # Secret key admin: no expira, no requiere login.
            return {"Authorization": f"Bearer {MEDUSA_ADMIN_API_KEY}"}

        # Fallback: login email/password, cacheado ~ 1h (ajustar a tu config de Medusa)
        if self._token and time.time() < self._token_expires_at:
            return {"Authorization": f"Bearer {self._token}"}

        if not (MEDUSA_ADMIN_EMAIL and MEDUSA_ADMIN_PASSWORD):
            raise MedusaAuthError(
                "Faltan credenciales de Medusa: define MEDUSA_ADMIN_API_KEY "
                "o MEDUSA_ADMIN_EMAIL + MEDUSA_ADMIN_PASSWORD."
            )

        resp = await self._client.post(
            "/auth/user/emailpass",
            json={"email": MEDUSA_ADMIN_EMAIL, "password": MEDUSA_ADMIN_PASSWORD},
        )
        if resp.status_code != 200:
            raise MedusaAuthError(f"Login fallido en Medusa: {resp.status_code} {resp.text}")

        data = resp.json()
        self._token = data["token"]
        self._token_expires_at = time.time() + 3500  # ~58 min, ajustar si tu JWT vive menos
        return {"Authorization": f"Bearer {self._token}"}

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
                if resp.status_code == 401 and MEDUSA_ADMIN_API_KEY is None:
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
        """
        Convierte el producto generado por GeminiService (schema interno NexPOS)
        al payload que espera POST /admin/products de Medusa.

        Medusa no tiene multi-tenancy nativo -> usamos metadata.tenant_id como
        marca de origen, y opcionalmente sales_channel para aislar catálogos
        por tenant (recomendado si cada tenant es una tienda B2C distinta).
        """
        variants = nexpos_product.get("variants") or [
            {
                "title": "Default",
                "sku": nexpos_product.get("sku"),
                "prices": [
                    {
                        "amount": int(round(nexpos_product["price"] * 100)),  # Medusa usa centavos
                        "currency_code": nexpos_product.get("currency", "usd"),
                    }
                ],
            }
        ]

        return {
            "title": nexpos_product["title"],
            "description": nexpos_product.get("description", ""),
            "status": "published" if nexpos_product.get("is_active", True) else "draft",
            "options": nexpos_product.get("options", [{"title": "Default"}]),
            "variants": variants,
            "images": [{"url": url} for url in nexpos_product.get("image_urls", [])],
            "metadata": {
                "tenant_id": tenant_id,
                "nexpos_product_id": str(nexpos_product["id"]),
                "source": "nexpos-ai-webbuilder",
            },
        }

    # ------------------------------------------------------------------
    # API pública del servicio
    # ------------------------------------------------------------------
    async def find_by_nexpos_id(self, tenant_id: str, nexpos_product_id: str) -> dict | None:
        """Busca si el producto ya fue sincronizado, para hacer upsert idempotente."""
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

    async def sync_product(
        self,
        nexpos_product: dict,
        tenant_id: str,
        known_medusa_id: str | None = None,
    ) -> dict:
        """
        Punto de entrada único: crea si no existe, actualiza si ya existe.

        Preferir pasar `known_medusa_id` (leído de la columna
        `medusa_product_id` en tu tabla Products de NexPOS) en vez de
        depender de la búsqueda por metadata: es más rápido y evita
        falsos negativos si la búsqueda por texto de Medusa no indexa
        bien el campo `metadata.nexpos_product_id`.

        Si no se pasa `known_medusa_id` (ej. primera sync, o no guardaste
        el ID todavía), cae al fallback de búsqueda por metadata.
        """
        medusa_id = known_medusa_id
        if not medusa_id:
            existing = await self.find_by_nexpos_id(tenant_id, nexpos_product["id"])
            medusa_id = existing["id"] if existing else None

        if medusa_id:
            logger.info("Producto %s ya existe en Medusa (%s), actualizando.", nexpos_product["id"], medusa_id)
            return await self.update_product(medusa_id, nexpos_product, tenant_id)

        logger.info("Producto %s no existe en Medusa, creando.", nexpos_product["id"])
        return await self.create_product(nexpos_product, tenant_id)

    async def aclose(self) -> None:
        await self._client.aclose()


# Singleton a nivel de módulo, listo para importar en routers/products.py
medusa_sync_service = MedusaSyncService()
