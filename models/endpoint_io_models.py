from pydantic import BaseModel
from typing import List

class RequestData(BaseModel):
    dataset_split: list[str]

class Task(BaseModel):
    # Celery task representation
    task_id: str
    status: str


class Result(BaseModel):
    # Celery task result
    task_id: str
    status: str
    result: str
    