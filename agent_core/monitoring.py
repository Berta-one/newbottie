import time
import logging

class MetricsRecorder:
    """Collects basic timing metrics.  Not a full Prometheus exporter, but a
    starting point so we can chart latency in dashboards.
    """

    def __init__(self):
        self._start_times = {}

    def start(self, name: str):
        self._start_times[name] = time.time()

    def stop(self, name: str):
        if name not in self._start_times:
            logging.warning(f"Metric '{name}' was never started")
            return
        elapsed = time.time() - self._start_times.pop(name)
        logging.info(f"[METRIC] {name}_latency={elapsed:.3f}s")
        return elapsed