import psutil
import os
import time
from typing import Optional, Callable
from dataclasses import dataclass
from src.engine.logger import logger, telemetry_log

@dataclass
class MemoryUsage:
    percent: float
    used_mb: float
    available_mb: float

class MemoryGuard:
    """
    Monitors system memory usage and enforces hard limits to prevent system crashes.
    """
    def __init__(self, limit_percent: float = 75.0):
        self.limit_percent = limit_percent
        self.process = psutil.Process(os.getpid())
        self.baseline = self.get_current_usage()
        
        logger.debug(f"MemoryGuard initialized. Baseline: {self.baseline.percent}% used, Process: {self.baseline.used_mb:.1f}MB")

    def get_current_usage(self) -> MemoryUsage:
        mem = psutil.virtual_memory()
        process_mem = self.process.memory_info().rss / (1024 * 1024)
        usage = MemoryUsage(
            percent=mem.percent,
            used_mb=process_mem,
            available_mb=mem.available / (1024 * 1024)
        )
        
        # Log every sample to the telemetry sink
        telemetry_log(f"RAM: {usage.percent}% | Process: {usage.used_mb:.1f}MB | Available: {usage.available_mb:.1f}MB")
        
        return usage

    def check_memory(self):
        """
        Check if memory usage exceeds the limit. Raises MemoryError if it does.
        """
        usage = self.get_current_usage()
        if usage.percent > self.limit_percent:
            error_msg = (
                f"Memory limit exceeded: {usage.percent}% (Limit: {self.limit_percent}%). "
                f"Process is using {usage.used_mb:.2f} MB. "
                "Operation aborted to prevent system crash."
            )
            logger.critical(error_msg)
            raise MemoryError(error_msg)

    def monitor_operation(self, callback: Optional[Callable[[MemoryUsage], None]] = None):
        """
        A simple heartbeat for long-running operations.
        """
        self.check_memory()
        if callback:
            callback(self.get_current_usage())
