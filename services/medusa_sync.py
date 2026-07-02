"""
medusa_sync.py — Servicio de sincronización NexPOS → Medusa v2
Mejoras v2:
- Sincroniza price_bulk a Price Lists B2B (Customer Groups)
- Cola de reintentos en sync_queue si Medusa está caído
- Worker para procesar la cola en background
"""

import httpx
import logging
from datetime import datetime
from sqlmodel import Session, select
from database.models import SyncQueue
from core.config import settings  # Use core.config since it's common

logger = logging.getLogger(__name__)

# ── Constante: headers de admin Medusa ──────────────────
def _admin_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.MEDUSA_ADMIN_API_KEY}",
        "Content-Type": "application/json",
    }

# ── Función existente EXTENDIDA con price_bulk ──────────
async def sync_product_to_medusa(
    nexpos_product: dict,
    db: Session
) -> dict:
    """
    Sincroniza un producto de NexPOS a Medusa.
    Si price_bulk está presente, también actualiza el Price List B2B.
    Si Medusa está caído, encola en sync_queue.
    """
    try:
        payload = _build_medusa_payload(nexpos_product)

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Intentar crear/actualizar el producto en Medusa
            medusa_id = nexpos_product.get("medusa_product_id")

            if medusa_id:
                resp = await client.post(
                    f"{settings.MEDUSA_URL}/admin/products/{medusa_id}",
                    json=payload,
                    headers=_admin_headers(),
                )
            else:
                resp = await client.post(
                    f"{settings.MEDUSA_URL}/admin/products",
                    json=payload,
                    headers=_admin_headers(),
                )
            resp.raise_for_status()
            medusa_data = resp.json()
            new_medusa_id = medusa_data["product"]["id"]

            # Si tiene precio bulk → sincronizar al grupo B2B
            if nexpos_product.get("price_bulk"):
                await _sync_bulk_price(
                    client=client,
                    medusa_product=medusa_data["product"],
                    price_bulk=nexpos_product["price_bulk"],
                )

            logger.info(
                f"✅ Producto {nexpos_product.get('id')} "
                f"sincronizado → Medusa {new_medusa_id}"
            )
            return {"status": "synced", "medusa_id": new_medusa_id}

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        # Medusa caído → encolar para reintento
        logger.warning(
            f"⚠️ Medusa no disponible. "
            f"Encolando producto {nexpos_product.get('id')}: {e}"
        )
        _enqueue(db, "product", nexpos_product)
        return {"status": "queued", "error": str(e)}

    except httpx.HTTPStatusError as e:
        logger.error(
            f"❌ Error HTTP al sincronizar "
            f"producto {nexpos_product.get('id')}: {e}"
        )
        _enqueue(db, "product", nexpos_product, error=str(e))
        return {"status": "failed", "error": str(e)}


# ── Helper: construir payload para Medusa ────────────────
def _build_medusa_payload(nexpos_product: dict) -> dict:
    """
    Construye el payload para la API de Medusa.
    Extiende lo que ya existía en la versión anterior.
    """
    variants = [
        {
            "title": "Default",
            "prices": [
                {
                    "amount": int(nexpos_product["price"] * 100),
                    "currency_code": "usd",
                }
            ],
            "inventory_quantity": nexpos_product.get("stock", 0),
            "manage_inventory": True,
            "sku": nexpos_product.get("sku", ""),
        }
    ]

    return {
        "title":       nexpos_product.get("title", ""),
        "description": nexpos_product.get("description", ""),
        "status":      nexpos_product.get("status", "draft"),
        "options":     nexpos_product.get("options", []),
        "images":      nexpos_product.get("images", []),
        "metadata":    nexpos_product.get("metadata", {}),
        "variants":    variants,
    }


# ── Helper: sincronizar precio bulk al grupo B2B ─────────
async def _sync_bulk_price(
    client: httpx.AsyncClient,
    medusa_product: dict,
    price_bulk: float,
) -> None:
    """
    Crea o actualiza un Price List B2B con el precio mayorista.
    Busca el Customer Group 'Wholesale' y asocia el precio.
    """
    # 1. Obtener el variant_id del primer variant
    variants = medusa_product.get("variants", [])
    if not variants:
        logger.warning("No variants found — skipping bulk price sync")
        return
    variant_id = variants[0]["id"]

    # 2. Buscar el Customer Group "Wholesale"
    groups_resp = await client.get(
        f"{settings.MEDUSA_URL}/admin/customer-groups",
        params={"q": "Wholesale"},
        headers=_admin_headers(),
    )
    groups = groups_resp.json().get("customer_groups", [])
    wholesale = next((g for g in groups if g["name"] == "Wholesale"), None)

    if not wholesale:
        logger.warning("Customer Group 'Wholesale' no existe — creando")
        create_resp = await client.post(
            f"{settings.MEDUSA_URL}/admin/customer-groups",
            json={"name": "Wholesale"},
            headers=_admin_headers(),
        )
        wholesale = create_resp.json()["customer_group"]

    # 3. Buscar Price List existente para Wholesale
    pl_resp = await client.get(
        f"{settings.MEDUSA_URL}/admin/price-lists",
        params={"q": "Mayorista B2B"},
        headers=_admin_headers(),
    )
    price_lists = pl_resp.json().get("price_lists", [])
    existing_pl = next(
        (p for p in price_lists if "Mayorista B2B" in p.get("name", "")),
        None
    )

    bulk_price_cents = int(price_bulk * 100)

    if existing_pl:
        # Actualizar precio en el Price List existente
        await client.post(
            f"{settings.MEDUSA_URL}/admin/price-lists/"
            f"{existing_pl['id']}/prices/batch",
            json={
                "prices": [
                    {
                        "variant_id": variant_id,
                        "amount": bulk_price_cents,
                        "currency_code": "usd",
                    }
                ]
            },
            headers=_admin_headers(),
        )
    else:
        # Crear nuevo Price List B2B
        await client.post(
            f"{settings.MEDUSA_URL}/admin/price-lists",
            json={
                "name": "Mayorista B2B — Descuento 30%",
                "description": "Precios mayoristas automáticos desde NexPOS",
                "type": "sale",
                "status": "active",
                "customer_groups": [{"id": wholesale["id"]}],
                "prices": [
                    {
                        "variant_id": variant_id,
                        "amount": bulk_price_cents,
                        "currency_code": "usd",
                    }
                ],
            },
            headers=_admin_headers(),
        )
    logger.info(
        f"✅ Precio bulk ${price_bulk} sincronizado "
        f"al grupo Wholesale (variant {variant_id})"
    )


# ── Helper: encolar en sync_queue ────────────────────────
def _enqueue(
    db: Session,
    entity_type: str,
    payload: dict,
    error: str = "",
) -> None:
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


# ── Worker: procesar la cola ─────────────────────────────
async def process_sync_queue(db: Session) -> dict:
    """
    Procesa hasta 50 items pendientes en sync_queue.
    Llamar desde un cron job o endpoint admin.
    """
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
            result = await sync_product_to_medusa(item.payload, db)
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
