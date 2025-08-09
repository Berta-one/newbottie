#!/usr/bin/env python3
"""
Enhanced Headless Trading Bot with Integrated Portfolio Engine
Now includes dynamic portfolio scanning + quantum/AI models
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project directories to path
sys.path.append('.')
sys.path.append('./engine')
sys.path.append('./ml')
sys.path.append('./quantum')

# Import the new integrated engine
from engine.integrated_portfolio_engine import IntegratedPortfolioEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/headless_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnhancedHeadlessBot:
    """Enhanced bot that combines portfolio scanning with AI trading"""
    
    def __init__(self):
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Initialize the integrated engine
        self.engine = IntegratedPortfolioEngine()
        
        logger.info("🚀 Enhanced Headless Trading Bot initialized")
    
    async def run(self):
        """Run the enhanced bot"""
        try:
            logger.info("Starting enhanced headless bot with integrated portfolio engine...")
            await self.engine.start()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise

async def main():
    """Main entry point"""
    bot = EnhancedHeadlessBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())