# trading_bot.py
import threading
import time

class TradingBot:
    def __init__(self, run_bot_fn):
        self._running = False
        self._thread = None
        self._run_bot_fn = run_bot_fn

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._loop_wrapper)
            self._thread.start()

    def _loop_wrapper(self):
        self._run_bot_fn(lambda: self._running)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def is_running(self):
        return self._running
