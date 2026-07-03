"""
test_medusa_sync.py

Script standalone para validar la conexión VibeCloud -> Medusa ANTES de
engancharlo al router de producción. No requiere pytest, corre directo:

    python test_medusa_sync.py

Prerrequisitos:
    - Medusa corriendo (local o staging) con al menos un Sales Channel default.
    - MEDUSA_ADMIN_API_KEY (o MEDUSA_ADMIN_EMAIL/PASSWORD) en tu entorno.
    - MEDUSA_BASE_URL apuntando a tu instancia (default http://localhost:9000).
"""

import asyncio
import sys

from services.medusa_sync import medusa_sync_service, MedusaSyncError, MedusaAuthError

# Producto de prueba simulando lo que generaría GeminiService
FAKE_AI_PRODUCT = {
    "id": "test-vibecloud-0001",
    "title": "Zapatilla Antigravity X1 (PoC Test)",
    "description": "Producto de prueba generado para validar Fase 1 de la fusión VibeCloud x Medusa.",
    "sku": "AGX1-TEST-001",
    "price": 149.99,
    "currency": "usd",
    "is_active": True,
    "image_urls": [],
}
TEST_TENANT_ID = "tenant-poc-001"


async def run() -> None:
    print("== PoC Fase 1: Test de conexión VibeCloud -> Medusa ==\n")

    # 1. Autenticación
    print("[1/3] Probando autenticación contra Medusa...")
    try:
        await medusa_sync_service._get_auth_header()
        print("      ✅ Autenticación OK.\n")
    except MedusaAuthError as exc:
        print(f"      ❌ Falló autenticación: {exc}")
        sys.exit(1)

    # 2. Crear producto (primera corrida)
    print("[2/3] Sincronizando producto de prueba (crear)...")
    try:
        result = await medusa_sync_service.sync_product(FAKE_AI_PRODUCT, TEST_TENANT_ID)
        medusa_id = result["id"]
        print(f"      ✅ Producto creado en Medusa. medusa_product_id = {medusa_id}\n")
    except MedusaSyncError as exc:
        print(f"      ❌ Falló la sincronización: {exc}")
        sys.exit(1)

    # 3. Volver a sincronizar el mismo producto (debe actualizar, NO duplicar)
    print("[3/3] Re-sincronizando el mismo producto (debe hacer UPDATE, no crear duplicado)...")
    try:
        updated = await medusa_sync_service.sync_product(
            FAKE_AI_PRODUCT, TEST_TENANT_ID, known_medusa_id=medusa_id
        )
        assert updated["id"] == medusa_id, "¡Se creó un producto duplicado en vez de actualizar!"
        print(f"      ✅ Idempotencia confirmada. Mismo ID: {updated['id']}\n")
    except (MedusaSyncError, AssertionError) as exc:
        print(f"      ❌ Falló la prueba de idempotencia: {exc}")
        sys.exit(1)

    print("== ✅ Todas las pruebas de Fase 1 pasaron. ==")
    print(f"Verifica en el Admin Panel de Medusa (http://localhost:7001 o tu URL) el producto: {medusa_id}")

    await medusa_sync_service.aclose()


if __name__ == "__main__":
    asyncio.run(run())
