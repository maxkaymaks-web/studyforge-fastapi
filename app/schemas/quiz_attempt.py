from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizAttemptBase(BaseModel):
    score: int = Field(ge=0, le=1000)
    max_score: int = Field(ge=1, le=1000)

    @model_validator(mode="after")
    def validate_scores(self) -> "QuizAttemptBase":
        if self.score > self.max_score:
            raise ValueError("score cannot exceed max_score")
        return self


class QuizAttemptCreate(QuizAttemptBase):
    topic_id: int


class QuizAttemptUpdate(QuizAttemptBase):
    pass


class QuizAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    user_id: int
    score: int
    max_score: int
    attempted_at: datetime

