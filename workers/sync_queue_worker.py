"""
sync_queue_worker.py
Corre como servicio worker en Render.
Procesa la sync_queue cada 5 minutos.
"""
import asyncio
import logging
from datetime import datetime
from sqlmodel import Session
from database.session import engine
from services.medusa_sync import process_sync_queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 300  # 5 minutos

async def run_worker():
    logger.info("🚀 sync_queue_worker iniciado")
    while True:
        try:
            with Session(engine) as db:
                result = await process_sync_queue(db)
                if result["total"] > 0:
                    logger.info(
                        f"✅ Cola procesada: {result['processed']} ok, "
                        f"{result['errors']} errores de {result['total']} total"
                    )
        except Exception as e:
            logger.error(f"❌ Error en worker: {e}")

        await asyncio.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    asyncio.run(run_worker())
