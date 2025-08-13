# engine/websocket_data_manager.py
"""
Free WebSocket Data Manager - Compatibility Layer
Provides a unified interface for the free WebSocket implementation using python-binance.
This replaces the previous ccxt-pro dependency with a completely free solution.
"""

import logging
from typing import Optional, Dict, List, Any
from .free_websocket_manager import FreeBinanceWebSocketManager

# Global WebSocket manager instance
_websocket_manager: Optional[FreeBinanceWebSocketManager] = None

def get_websocket_manager() -> Optional[FreeBinanceWebSocketManager]:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    return _websocket_manager

async def initialize_websocket_data(
    symbols: List[str],
    kline_symbols: List[str] = None,
    api_key: str = None,
    api_secret: str = None
) -> bool:
    """
    Initialize the free WebSocket data manager.
    
    Args:
        symbols: List of symbols for ticker streams (e.g., ['BTCUSDT', 'ETHUSDT'])
        kline_symbols: List of symbols for kline/OHLCV streams (default: use symbols)
        api_key: Binance API key for account updates (optional)
        api_secret: Binance API secret for account updates (optional)
    
    Returns:
        bool: True if initialization successful
    """
    global _websocket_manager
    
    try:
        # Initialize the free WebSocket manager
        _websocket_manager = FreeBinanceWebSocketManager(
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Start ticker streams for real-time price data
        if symbols:
            await _websocket_manager.start_ticker_streams(symbols)
            logging.info(f"Free WebSocket ticker streams started for {len(symbols)} symbols")
        
        # Start kline streams for OHLCV data (if different from ticker symbols)
        if kline_symbols:
            await _websocket_manager.start_kline_streams(kline_symbols)
            logging.info(f"Free WebSocket kline streams started for {len(kline_symbols)} symbols")
        
        # Start account updates if API credentials provided
        if api_key and api_secret:
            await _websocket_manager.start_user_data_stream()
            logging.info("Free WebSocket account updates enabled")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to initialize free WebSocket manager: {e}")
        _websocket_manager = None
        return False

def cleanup_websocket_data():
    """Clean up WebSocket connections."""
    global _websocket_manager
    
    if _websocket_manager:
        try:
            _websocket_manager.close()
            logging.info("Free WebSocket manager connections closed")
        except Exception as e:
            logging.error(f"Error closing WebSocket connections: {e}")
        finally:
            _websocket_manager = None
