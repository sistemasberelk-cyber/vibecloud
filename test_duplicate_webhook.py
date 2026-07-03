"""
test_duplicate_webhook.py

Simula que Medusa envía el MISMO webhook dos veces (esto pasa en la vida
real: reintentos de red, at-least-once delivery, etc.) y verifica que
NexPOS solo lo procesa una vez.

AJUSTAR antes de correr (marcado con TODO):
    - WEBHOOK_URL: el endpoint real que recibe el webhook de Medusa
      (el que dispara inventory-nexpos.ts / inventory-vibecloud.ts)
    - STOCK_CHECK_URL: endpoint para consultar el stock actual de un producto
    - NEXPOS_API_KEY: la key que usa Medusa para autenticar contra NexPOS

Uso:
    python test_duplicate_webhook.py
"""

import asyncio
import os
import sys
import uuid

import httpx

# ── Config — AJUSTAR a tu entorno real ──────────────────────────────
NEXPOS_BASE_URL = os.getenv("NEXPOS_BASE_URL", "http://localhost:8000")
NEXPOS_API_KEY = os.getenv("NEXPOS_API_KEY", "")

# TODO: confirmar la ruta real. Basado en el subscriber de Fase 1:
#   axios.post(`${NEXPOS_URL}/api/v1/inventory/deduct-from-order`, ...)
WEBHOOK_PATH = "/api/v1/inventory/deduct-from-order"

# TODO: un producto/SKU real que exista en tu DB de prueba, con stock > 0
TEST_PRODUCT_ID = os.getenv("TEST_PRODUCT_ID", "test-nexpos-0001")

# TODO: endpoint para leer el stock actual (ajustar al que exista en tu API)
STOCK_CHECK_PATH = f"/api/v1/products/{TEST_PRODUCT_ID}"


async def get_stock(client: httpx.AsyncClient) -> int:
    resp = await client.get(STOCK_CHECK_PATH)
    resp.raise_for_status()
    data = resp.json()
    # TODO: ajustar la clave según tu schema real (stock / quantity / etc.)
    return data.get("stock", data.get("quantity"))


async def send_webhook(client: httpx.AsyncClient, event_id: str, quantity: int = 1) -> httpx.Response:
    payload = {
        "id": event_id,               # simula el id de evento de Medusa
        "order_id": f"order_test_{event_id[:8]}",
        "source": "medusa_storefront",
        "items": [
            {"product_id": TEST_PRODUCT_ID, "quantity": quantity}
        ],
    }
    headers = {"x-api-key": NEXPOS_API_KEY} if NEXPOS_API_KEY else {}
    return await client.post(WEBHOOK_PATH, json=payload, headers=headers)


async def run() -> None:
    print("== Test de idempotencia: webhook duplicado ==\n")

    if not NEXPOS_API_KEY:
        print("[WARNING] NEXPOS_API_KEY no seteada - el request puede fallar por auth.")
        print("Exportala si tu endpoint la requiere.\n")

    async with httpx.AsyncClient(base_url=NEXPOS_BASE_URL, timeout=15.0) as client:
        # 1. Stock inicial
        try:
            stock_before = await get_stock(client)
            print(f"[1/4] Stock inicial de {TEST_PRODUCT_ID}: {stock_before}")
        except Exception as exc:
            print("ERROR: No pude leer el stock inicial. Ajusta STOCK_CHECK_PATH. Error: {}".format(exc))
            sys.exit(1)

        # 2. Generar UN evento con ID fijo (simula el mismo webhook)
        event_id = str(uuid.uuid4())
        print(f"[2/4] Enviando webhook por primera vez (event_id={event_id})...")
        resp1 = await send_webhook(client, event_id, quantity=1)
        print(f"      → status {resp1.status_code}")

        # 3. Reenviar EXACTAMENTE el mismo event_id (simula reintento/duplicado)
        print(f"[3/4] Reenviando el MISMO webhook (event_id={event_id})...")
        resp2 = await send_webhook(client, event_id, quantity=1)
        print(f"      → status {resp2.status_code}")
        # Si tu handler está bien hecho, este segundo request debería:
        #   - devolver 200 igual (no romper al llamador) PERO
        #   - no volver a descontar stock
        # o devolver algo como 409/200 con {"status": "already_processed"}

        # 4. Verificar stock final
        stock_after = await get_stock(client)
        print(f"[4/4] Stock final de {TEST_PRODUCT_ID}: {stock_after}\n")

        expected = stock_before - 1  # solo UN descuento, aunque llegó 2 veces
        if stock_after == expected:
            print("SUCCESS: IDEMPOTENCIA OK. Stock descontado una sola vez ({} -> {}).".format(stock_before, stock_after))
        elif stock_after == stock_before - 2:
            print("ERROR: BUG DE IDEMPOTENCIA. Se desconto DOS veces ({} -> {}).".format(stock_before, stock_after))
            sys.exit(1)
        else:
            print("WARNING: Resultado inesperado. Esperaba {}, obtuve {}.".format(expected, stock_after))
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run())
