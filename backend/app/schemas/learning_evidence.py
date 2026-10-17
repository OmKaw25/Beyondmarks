from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class DelayedAnswer(StrictInput):
    answer: str = Field(min_length=1, max_length=5000)
    explanation: str = Field(min_length=1, max_length=5000)
    reasoning_tag: str = Field(min_length=1, max_length=80)


class ReviewInput(StrictInput):
    question_id: UUID
    answer_score: int = Field(ge=0, le=100, strict=True)
    reasoning_score: int = Field(ge=0, le=100, strict=True)
    feedback: str = Field(min_length=1, max_length=2000)
    misconception: str = Field(default='', max_length=1000)
    reason: str = Field(min_length=1, max_length=2000)
    dispute_id: UUID | None = None


class DisputeInput(StrictInput):
    question_id: UUID
    reason: str = Field(min_length=1, max_length=2000)
