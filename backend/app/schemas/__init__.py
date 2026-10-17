from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequestModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Login(RequestModel):
    username: str = Field(min_length=3, max_length=32, pattern=r'^[A-Za-z0-9_]+$')
    password: str = Field(min_length=1, max_length=72)

    @field_validator('username')
    @classmethod
    def normalize(cls, value):
        return value.lower()

    @field_validator('password')
    @classmethod
    def byte_limit(cls, value):
        if len(value.encode('utf-8')) > 72:
            raise ValueError('Password must be at most 72 UTF-8 bytes.')
        return value


class Signup(Login):
    password: str = Field(min_length=10, max_length=72)
    role: Literal['learner', 'teacher'] = 'learner'
    invite_code: str = Field(default='', max_length=200)


class StartAttempt(RequestModel):
    exercise_id: UUID


class SelfReport(RequestModel):
    confidence: Literal['unsure', 'somewhat_sure', 'very_sure'] | None = None
    context: Literal['none', 'time_pressure', 'incomplete_work', 'misread', 'other'] | None = None
    context_note: str = Field(default='', max_length=1000)


class AgencyAction(RequestModel):
    action: Literal['pause', 'resume', 'help']
    reason: str = Field(default='', max_length=1000)


class Correction(SelfReport):
    segment_ids: list[UUID] = Field(min_length=1, max_length=20)
    broad_category: Literal['Concept', 'Logic', 'Execution', 'Output', 'Missing case']
    specific_reason: str = Field(min_length=1, max_length=80)
    explanation: str = Field(min_length=3, max_length=2000)

    @field_validator('explanation')
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 3:
            raise ValueError('Add a short explanation of your reasoning.')
        return value.strip()


class Challenge(RequestModel):
    alternative_hypothesis_id: UUID
    reason: str = Field(default='', max_length=2000)


class Answer(RequestModel):
    answer: str = Field(min_length=1, max_length=500)


class SupportIdentity(RequestModel):
    support_id: UUID


class SupportAnswer(Answer):
    support_id: UUID


class TaskResponse(Answer, SelfReport):
    task_id: UUID
    explanation: str = Field(min_length=3, max_length=2000)
    reasoning_tag: str = Field(min_length=1, max_length=80)

    @field_validator('explanation')
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 3:
            raise ValueError('Add a short explanation.')
        return value.strip()
