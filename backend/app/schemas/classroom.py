from uuid import UUID
from pydantic import Field, field_validator
from app.schemas import RequestModel


class SubjectInput(RequestModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default='', max_length=2000)

    @field_validator('title')
    @classmethod
    def title_not_blank(cls, value):
        if len(value.strip()) < 2: raise ValueError('Enter a subject title.')
        return value.strip()


class CourseInput(RequestModel):
    title: str = Field(min_length=2, max_length=150)
    content: str = Field(min_length=10, max_length=20000)

    @field_validator('title', 'content')
    @classmethod
    def not_blank(cls, value):
        if not value.strip(): raise ValueError('This field cannot be blank.')
        return value.strip()


class QuestionInput(RequestModel):
    course_id: UUID
    prompt: str = Field(min_length=3, max_length=3000)
    expected_answer: str = Field(min_length=1, max_length=3000)
    rubric: str = Field(default='', max_length=2000)

    @field_validator('prompt', 'expected_answer')
    @classmethod
    def not_blank(cls, value):
        if not value.strip(): raise ValueError('This field cannot be blank.')
        return value.strip()


class QuizInput(RequestModel):
    subject_id: UUID
    title: str = Field(min_length=2, max_length=150)
    questions: list[QuestionInput] = Field(min_length=1, max_length=20)


class QuizAnswer(RequestModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=3000)
    reasoning: str = Field(min_length=3, max_length=3000)

    @field_validator('answer', 'reasoning')
    @classmethod
    def not_blank(cls, value):
        if not value.strip(): raise ValueError('Give an answer and explain your reasoning.')
        return value.strip()


class SubmissionInput(RequestModel):
    responses: list[QuizAnswer] = Field(min_length=1, max_length=20)
