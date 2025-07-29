from engine.executor import execute_order
from engine.signal_generator import generate_signal
from engine.risk_manager import apply_risk_management
from engine.trading_core import get_price_data

TRADING_SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt"]

def run_live_trading():
    for symbol in TRADING_SYMBOLS:
        print(f"Processing {symbol}")
        data = get_price_data(symbol)
        signal = generate_signal(data, symbol)
        if signal:
            size = apply_risk_management(symbol, signal)
            execute_order(signal, size, symbol)

if __name__ == "__main__":
    run_live_trading()
