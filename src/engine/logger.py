import sys
import os
from pathlib import Path
from loguru import logger

def setup_logger(log_dir: Path, level: str = "INFO"):
    """
    Configures Loguru with multiple sinks:
    1. Console (Rich compatible)
    2. logs/app.log (General events)
    3. logs/resources.log (Memory/CPU telemetry)
    4. logs/audit.jsonl (Structured chain of custody)
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()

    # 1. Console Handler (Brief for the user)
    logger.add(
        sys.stderr, 
        format="<level>{level: <8}</level> | <cyan>{message}</cyan>", 
        level=level,
        colorize=True,
        filter=lambda record: "audit" not in record["extra"] and "telemetry" not in record["extra"]
    )

    # 2. Application Log (Rotating file)
    logger.add(
        log_dir / "app.log",
        rotation="100 MB",
        retention="30 days",
        level="DEBUG",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        filter=lambda record: "audit" not in record["extra"] and "telemetry" not in record["extra"]
    )

    # 3. Telemetry Log (Memory/CPU tracking)
    logger.add(
        log_dir / "resources.log",
        rotation="50 MB",
        retention="7 days",
        level="TRACE",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
        filter=lambda record: "telemetry" in record["extra"]
    )

    # 4. Audit Log (Structured JSONL)
    logger.add(
        log_dir / "audit.jsonl",
        rotation="500 MB",
        level="INFO",
        serialize=True, # Outputs as JSON
        filter=lambda record: "audit" in record["extra"]
    )

    logger.info(f"Logging system initialized. Level: {level}")

# Global accessors for tagged logging
def audit_log(event: str, **kwargs):
    logger.bind(audit=True).info(event, **kwargs)

def telemetry_log(message: str, **kwargs):
    logger.bind(telemetry=True).trace(message, **kwargs)
