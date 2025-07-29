import logging
def catch_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Failsafe triggered: {e}")
            return None
    return wrapper
