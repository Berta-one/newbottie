# Fully implemented signal generator

def generate_signal(data):
    return 'buy' if data[-1] > data[-2] else 'sell'
