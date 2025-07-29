# quantum/healthcheck.py

from quantum.backends import get_active_backend, get_backend_provider

def check_backend_health():
    name, btype = get_active_backend(return_type=True)
    backend = get_backend_provider().get_backend(name)

    if hasattr(backend, 'status'):
        status = backend.status()
        return {
            "name": name,
            "type": btype,
            "operational": status.operational,
            "pending_jobs": status.pending_jobs,
            "status_msg": status.status_msg
        }
    else:
        return {
            "name": name,
            "type": btype,
            "operational": True,
            "pending_jobs": 0,
            "status_msg": "Simulated backend OK"
        }