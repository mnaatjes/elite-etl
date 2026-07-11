from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel

class AsyncJobResponse(BaseModel):
    message: str = "Job accepted for processing"
    job_id: UUID

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[Any] = None
