import os
import logging
from src.infrastructure.logging import setup_logging, get_logger

def test_setup_logging(tmpdir):
    log_dir = str(tmpdir.mkdir("logs"))
    
    logger = setup_logging(app_name="test_app", log_dir=log_dir)
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2
    
    test_logger = logging.getLogger("test_app.test_module")
    test_logger.info("This is a test log message")
    
    log_file = os.path.join(log_dir, "test_app.log")
    assert os.path.exists(log_file)
    
    with open(log_file, "r") as f:
        content = f.read()
        assert "This is a test log message" in content
        assert "test_app.test_module" in content
