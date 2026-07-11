import logging
import logging.handlers
import os

def setup_logging(app_name: str = "elite_etl", log_dir: str = "logs"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if called multiple times in the same process
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler for stdout
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler for persistence (Rotating, max 5MB per file, keep 3 backups)
    log_file = os.path.join(log_dir, f"{app_name}.log")
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def get_logger(module_name: str):
    """
    Get a child logger for a specific module, inheriting handlers from the parent 'elite_etl'
    """
    return logging.getLogger(f"elite_etl.{module_name}")
