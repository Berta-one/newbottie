#!/usr/bin/env python3
"""
Integrated Startup Script for Bottie Lightweight Dashboard
Combines dashboard API with data collection in a single memory-optimized process
"""

import asyncio
import os
import sys
import json
import logging
import signal
from datetime import datetime
import uvicorn
import psutil
import gc
import sqlite3
from typing import Dict, Any

# Import our optimized components
from lightweight_dashboard_api import app, data_manager, ws_manager
from memory_optimized_trader import OptimizedDataCollector, MemoryMonitor

# Configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = "0.0.0.0"
MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "400"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

# Configure comprehensive logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/bottie.log', mode='a') if os.path.exists('/tmp') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegratedBottieSystem:
    """Integrated system combining dashboard and data collection"""
    
    def __init__(self):
        self.memory_monitor = MemoryMonitor()
        self.data_collector = OptimizedDataCollector() if not DEMO_MODE else None
        self.running = False
        self.tasks = []
        
        # System stats
        self.start_time = datetime.now()
        self.stats = {
            'uptime_seconds': 0,
            'total_requests': 0,
            'memory_peak_mb': 0,
            'errors_count': 0,
            'websocket_connections': 0
        }
        
        logger.info("🚀 Integrated Bottie system initializing...")
    
    def log_system_info(self):
        """Log detailed system information at startup"""
        try:
            # System info
            memory_info = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            logger.info("=" * 60)
            logger.info("🖥️  SYSTEM INFORMATION")
            logger.info("=" * 60)
            logger.info(f"📊 Total RAM: {memory_info.total / 1024**3:.1f} GB")
            logger.info(f"💾 Available RAM: {memory_info.available / 1024**3:.1f} GB")
            logger.info(f"🏭 CPU Cores: {cpu_count}")
            logger.info(f"🐍 Python: {sys.version.split()[0]}")
            logger.info(f"📍 Working Directory: {os.getcwd()}")
            logger.info(f"🌐 Port: {PORT}")
            logger.info(f"💡 Demo Mode: {DEMO_MODE}")
            logger.info(f"🎯 Memory Limit: {MAX_MEMORY_MB}MB")
            logger.info("=" * 60)
            
            # Environment variables
            logger.info("🔧 ENVIRONMENT CONFIGURATION")
            logger.info("=" * 60)
            env_vars = [
                'MAX_MEMORY_MB', 'LOG_LEVEL', 'DEMO_MODE', 'UPDATE_INTERVAL',
                'MAX_STORED_RECORDS', 'MAX_LOG_ENTRIES', 'BINANCE_API_KEY',
                'BINANCE_TESTNET', 'PORT'
            ]
            
            for var in env_vars:
                value = os.getenv(var, 'Not set')
                if 'KEY' in var or 'SECRET' in var:
                    value = '***HIDDEN***' if value != 'Not set' else 'Not set'
                logger.info(f"{var}: {value}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ System info logging error: {e}")
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_monitoring_tasks(self):
        """Start all monitoring and data collection tasks"""
        try:
            # Memory monitoring task
            self.tasks.append(asyncio.create_task(self.memory_monitoring_loop()))
            
            # Stats update task
            self.tasks.append(asyncio.create_task(self.stats_update_loop()))
            
            # WebSocket broadcast task
            self.tasks.append(asyncio.create_task(self.websocket_broadcast_loop()))
            
            # Database maintenance task
            self.tasks.append(asyncio.create_task(self.database_maintenance_loop()))
            
            logger.info(f"✅ Started {len(self.tasks)} monitoring tasks")
            
        except Exception as e:
            logger.error(f"❌ Task startup error: {e}")
            raise
    
    async def memory_monitoring_loop(self):
        """Continuous memory monitoring with alerts"""
        logger.info("🧠 Memory monitoring started")
        
        while self.running:
            try:
                # Get current memory usage
                process = psutil.Process()
                memory = process.memory_info().rss / 1024 / 1024
                
                # Update peak memory
                if memory > self.stats['memory_peak_mb']:
                    self.stats['memory_peak_mb'] = memory
                
                # Memory alerts
                memory_percent = (memory / MAX_MEMORY_MB) * 100
                
                if memory_percent > 95:
                    logger.critical(f"🚨 CRITICAL MEMORY: {memory:.1f}MB ({memory_percent:.1f}%)")
                    await self.emergency_memory_cleanup()
                elif memory_percent > 85:
                    logger.warning(f"⚠️ HIGH MEMORY: {memory:.1f}MB ({memory_percent:.1f}%)")
                    await self.routine_memory_cleanup()
                elif memory_percent > 70:
                    logger.info(f"💾 Memory usage: {memory:.1f}MB ({memory_percent:.1f}%)")
                
                # Log detailed memory info every 5 minutes
                if datetime.now().second == 0 and datetime.now().minute % 5 == 0:
                    await self.log_detailed_memory_info()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Memory monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def log_detailed_memory_info(self):
        """Log detailed memory information"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            logger.info("📊 DETAILED MEMORY REPORT")
            logger.info(f"RSS Memory: {memory_info.rss / 1024**2:.1f} MB")
            logger.info(f"VMS Memory: {memory_info.vms / 1024**2:.1f} MB")
            logger.info(f"Memory Percent: {process.memory_percent():.1f}%")
            logger.info(f"Peak Memory: {self.stats['memory_peak_mb']:.1f} MB")
            logger.info(f"Open File Descriptors: {process.num_fds()}")
            logger.info(f"Threads: {process.num_threads()}")
            
            # Database size
            if os.path.exists('/tmp/bottie_lite.db'):
                db_size = os.path.getsize('/tmp/bottie_lite.db') / 1024
                logger.info(f"Database Size: {db_size:.1f} KB")
            
        except Exception as e:
            logger.error(f"❌ Memory info error: {e}")
    
    async def emergency_memory_cleanup(self):
        """Emergency memory cleanup procedures"""
        logger.warning("🧹 Emergency memory cleanup initiated")
        
        try:
            # Clear data manager caches
            if hasattr(data_manager, 'recent_trades'):
                while len(data_manager.recent_trades) > 25:
                    data_manager.recent_trades.popleft()
            
            if hasattr(data_manager, 'recent_signals'):
                while len(data_manager.recent_signals) > 25:
                    data_manager.recent_signals.popleft()
            
            if hasattr(data_manager, 'logs'):
                while len(data_manager.logs) > 50:
                    data_manager.logs.popleft()
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"🗑️ Emergency cleanup: {collected} objects collected")
            
        except Exception as e:
            logger.error(f"❌ Emergency cleanup error: {e}")
    
    async def routine_memory_cleanup(self):
        """Routine memory cleanup"""
        try:
            # Light cleanup
            gc.collect()
            
            # Database cleanup
            await self.cleanup_database()
            
        except Exception as e:
            logger.error(f"❌ Routine cleanup error: {e}")
    
    async def cleanup_database(self):
        """Clean up old database entries"""
        try:
            if os.path.exists('/tmp/bottie_lite.db'):
                conn = sqlite3.connect('/tmp/bottie_lite.db')
                cursor = conn.cursor()
                
                # Get current sizes
                cursor.execute("SELECT COUNT(*) FROM trades")
                trades_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM signals")
                signals_count = cursor.fetchone()[0]
                
                # Clean if too many records
                if trades_count > 1000:
                    cursor.execute("DELETE FROM trades WHERE id IN (SELECT id FROM trades ORDER BY id LIMIT 500)")
                
                if signals_count > 1000:
                    cursor.execute("DELETE FROM signals WHERE id IN (SELECT id FROM signals ORDER BY id LIMIT 500)")
                
                cursor.execute("VACUUM")
                conn.commit()
                conn.close()
                
                logger.info(f"🧹 Database cleanup: {trades_count} trades, {signals_count} signals")
            
        except Exception as e:
            logger.error(f"❌ Database cleanup error: {e}")
    
    async def stats_update_loop(self):
        """Update system statistics"""
        while self.running:
            try:
                # Update uptime
                uptime = (datetime.now() - self.start_time).total_seconds()
                self.stats['uptime_seconds'] = int(uptime)
                self.stats['websocket_connections'] = len(ws_manager.connections) if ws_manager else 0
                
                # Log stats every 10 minutes
                if int(uptime) % 600 == 0:  # Every 10 minutes
                    logger.info("📈 SYSTEM STATISTICS")
                    logger.info(f"⏱️ Uptime: {uptime/3600:.1f} hours")
                    logger.info(f"🌐 WebSocket Connections: {self.stats['websocket_connections']}")
                    logger.info(f"💾 Peak Memory: {self.stats['memory_peak_mb']:.1f}MB")
                    logger.info(f"❌ Errors: {self.stats['errors_count']}")
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"❌ Stats update error: {e}")
                self.stats['errors_count'] += 1
                await asyncio.sleep(60)
    
    async def websocket_broadcast_loop(self):
        """Regular WebSocket data broadcasts"""
        broadcast_interval = int(os.getenv("WEBSOCKET_BROADCAST_INTERVAL", "15"))
        
        while self.running:
            try:
                if ws_manager.connections:
                    # Get fresh data
                    table_data = data_manager.get_table_data()
                    
                    # Add system stats to broadcast
                    table_data['system_stats'] = self.stats
                    
                    # Broadcast to all connections
                    await ws_manager.broadcast({
                        'type': 'data_update',
                        'data': table_data
                    })
                
                await asyncio.sleep(broadcast_interval)
                
            except Exception as e:
                logger.error(f"❌ WebSocket broadcast error: {e}")
                await asyncio.sleep(broadcast_interval)
    
    async def database_maintenance_loop(self):
        """Regular database maintenance"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self.cleanup_database()
                logger.info("🔧 Database maintenance completed")
                
            except Exception as e:
                logger.error(f"❌ Database maintenance error: {e}")
                await asyncio.sleep(3600)
    
    async def startup(self):
        """Complete system startup"""
        try:
            logger.info("🚀 Starting Bottie Lightweight Dashboard System")
            
            # Log system information
            self.log_system_info()
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Set running flag
            self.running = True
            
            # Start all monitoring tasks
            await self.start_monitoring_tasks()
            
            logger.info("✅ All systems operational!")
            logger.info(f"🌐 Dashboard available at: http://localhost:{PORT}")
            logger.info(f"📡 WebSocket endpoint: ws://localhost:{PORT}/ws")
            logger.info("🎛️ Real-time table-based dashboard ready!")
            
        except Exception as e:
            logger.error(f"❌ Startup error: {e}")
            raise
    
    async def shutdown(self):
        """Graceful system shutdown"""
        logger.info("🛑 Initiating graceful shutdown...")
        
        try:
            # Stop the running flag
            self.running = False
            
            # Cancel all tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Final cleanup
            gc.collect()
            
            # Log final stats
            uptime = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"📊 Final Stats - Uptime: {uptime/3600:.1f}h, Peak Memory: {self.stats['memory_peak_mb']:.1f}MB")
            logger.info("✅ Shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

# Create the integrated system instance
bottie_system = IntegratedBottieSystem()

# Add health check endpoint to main app
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        process = psutil.Process()
        memory = process.memory_info().rss / 1024 / 1024
        
        # Check database
        db_ok = True
        try:
            conn = sqlite3.connect('/tmp/bottie_lite.db')
            conn.execute("SELECT 1").fetchone()
            conn.close()
        except:
            db_ok = False
        
        health_status = {
            "status": "healthy" if memory < MAX_MEMORY_MB and db_ok else "degraded",
            "timestamp": datetime.now().isoformat(),
            "memory_mb": round(memory, 1),
            "memory_limit_mb": MAX_MEMORY_MB,
            "memory_percent": round((memory / MAX_MEMORY_MB) * 100, 1),
            "database_ok": db_ok,
            "websocket_connections": len(ws_manager.connections) if ws_manager else 0,
            "demo_mode": DEMO_MODE,
            "uptime_seconds": int((datetime.now() - bottie_system.start_time).total_seconds()) if 'bottie_system' in globals() else 0
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Add memory status endpoint
@app.get("/memory")
async def memory_status():
    """Detailed memory status"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": round(memory_info.rss / 1024**2, 1),
            "vms_mb": round(memory_info.vms / 1024**2, 1),
            "percent": round(process.memory_percent(), 1),
            "peak_mb": bottie_system.stats['memory_peak_mb'] if 'bottie_system' in globals() else 0,
            "limit_mb": MAX_MEMORY_MB,
            "available_mb": round(MAX_MEMORY_MB - (memory_info.rss / 1024**2), 1),
            "threads": process.num_threads(),
            "fds": process.num_fds(),
            "gc_counts": gc.get_count()
        }
        
    except Exception as e:
        return {"error": str(e)}

# Custom ASGI application with startup/shutdown events
@app.on_event("startup")
async def on_startup():
    """FastAPI startup event"""
    await bottie_system.startup()

@app.on_event("shutdown") 
async def on_shutdown():
    """FastAPI shutdown event"""
    await bottie_system.shutdown()

def main():
    """Main entry point"""
    try:
        logger.info("🚀 Bottie Lightweight Dashboard - Starting Up")
        
        # Configure uvicorn for memory efficiency
        config = uvicorn.Config(
            app=app,
            host=HOST,
            port=PORT,
            log_level=LOG_LEVEL.lower(),
            access_log=False,  # Disable access logs to save memory
            workers=1,         # Single worker to minimize memory
            loop="asyncio",
            lifespan="on"
        )
        
        server = uvicorn.Server(config)
        server.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Main execution error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()