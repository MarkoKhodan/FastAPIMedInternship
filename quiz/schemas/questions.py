from pydantic import BaseModel, conlist, validator

from quiz.schemas.answers import AnswerCreate, AnswerRead


def validate_answers(answers: conlist(AnswerCreate)) -> conlist(AnswerCreate):
    correct = 0
    for answer in answers:
        if answer["is_correct"]:
            correct += 1
    assert correct == 1, "You should have one correct answers in question"
    assert len(answers) >= 2, "You should have more than 2 answers in one question"
    return answers


class QuestionBase(BaseModel):
    id: int
    question_title: str
    quiz_id: int


class QuestionCreate(BaseModel):
    question_title: str
    answers: conlist(AnswerCreate, min_items=2)

    @validator("answers", pre=True)
    def questions_is_valid(
        cls, answers: conlist(AnswerCreate)
    ) -> conlist(AnswerCreate):
        return validate_answers(answers)


class QuestionRead(BaseModel):
    id: int
    question_title: str
    answers: conlist(AnswerRead)


class QuestionPass(BaseModel):
    question_id: int
    choosed_answer_id: int


class QuestionAnswerRead(BaseModel):
    id: int
    answer: str
