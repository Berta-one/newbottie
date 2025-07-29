# engine/autonomous_engine_ws.py

from engine.execution_manager import ExecutionManager
from utils import get_live_market_data
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutonomousWS")

class AutonomousEngine:
    def __init__(self, num_assets):
        self.manager = ExecutionManager(num_assets)

    async def run(self):
        logger.info("🚀 Autonomous Engine (WebSocket) starting...")

        while True:
            try:
                market_data = await get_live_market_data()
                self.manager.run_cycle(market_data)
            except Exception as e:
                logger.error(f"💥 Error in run loop: {e}")
            await asyncio.sleep(60)  # Run cycle every minute

# Entry point
if __name__ == "__main__":
    ae = AutonomousEngine(num_assets=3)
    asyncio.run(ae.run())