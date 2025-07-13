# bot_controller.py
import threading
from main import run_bot_loop, initialize_bot

class BotController:
    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            if initialize_bot():
                self._running = True
                self._thread = threading.Thread(target=self._run_loop)
                self._thread.start()
                return True
            else:
                return False
        return True

    def _run_loop(self):
        run_bot_loop(lambda: self._running)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def is_running(self):
        return self._running
