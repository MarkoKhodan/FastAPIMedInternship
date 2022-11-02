import io

import pandas as pandas
from fastapi import APIRouter, Security, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import StreamingResponse, FileResponse

from core.database import get_db
from quiz.schemas.questions import QuestionAnswerRead
from quiz.schemas.result import ResultBase
from quiz.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizList,
    QuizInfo,
    QuizPass,
    QuizQuestions,
)
from quiz.service import UserService, QuizService

router = APIRouter()


def get_quiz_service(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
):
    return QuizService(db=db, credentials=credentials)


@router.post("/create/{pk}", response_model=QuizList)
async def quiz_create(
    quiz_info: QuizCreate, pk: int, quiz_repo: QuizService = Depends(get_quiz_service)
) -> QuizList:

    return await quiz_repo.create_quiz(
        quiz_info=quiz_info,
        company_id=int(pk),
    )


@router.post("/update/{company_id}/{quiz_id}", response_model=QuizList)
async def quiz_update(
    quiz_info: QuizUpdate,
    quiz_id: int,
    company_id: int,
    quiz_repo: QuizService = Depends(get_quiz_service),
) -> QuizList:

    return await quiz_repo.update_quiz(
        quiz_info=quiz_info,
        company_id=int(company_id),
        quiz_id=int(quiz_id),
    )


@router.post("/delete/{company_id}/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def quiz_update(
    quiz_id: int, company_id: int, quiz_repo: QuizService = Depends(get_quiz_service)
) -> HTTPException:

    return await quiz_repo.delete_quiz(
        company_id=int(company_id),
        quiz_id=int(quiz_id),
    )


@router.get("/{company_id}", response_model=list[QuizList])
async def quiz_list(
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    quiz_repo: QuizService = Depends(get_quiz_service),
) -> list[QuizList]:
    return await quiz_repo.get_quiz_list(
        company_id=int(company_id), skip=skip, limit=limit
    )


@router.get("/info/{quiz_id}", response_model=QuizInfo)
async def quiz_info(
    quiz_id: int, quiz_repo: QuizService = Depends(get_quiz_service)
) -> QuizInfo:
    return await quiz_repo.get_quiz_info(quiz_id=quiz_id)


@router.get("/read_question/{quiz_id}", response_model=QuizQuestions)
async def quiz_read_question(
    quiz_id: int, quiz_repo: QuizService = Depends(get_quiz_service)
) -> QuizQuestions:
    return await quiz_repo.get_quiz_questions(quiz_id=quiz_id)


@router.post("/pass/{quiz_id}", response_model=ResultBase)
async def quiz_pass(
    quiz_answers: QuizPass,
    quiz_id: int,
    quiz_repo: QuizService = Depends(get_quiz_service),
) -> ResultBase:
    return await quiz_repo.pass_quiz(quiz_id=quiz_id, quiz_answers=quiz_answers)


@router.get("/get_my_answers/", status_code=status.HTTP_200_OK)
async def redis_test(
    quiz_repo: QuizService = Depends(get_quiz_service),
) -> FileResponse:

    return await quiz_repo.get_user_answers_from_redis()


@router.get("/get_all_answers_for_company/{company_id}", status_code=status.HTTP_200_OK)
async def redis_test(
    company_id: int, quiz_repo: QuizService = Depends(get_quiz_service)
) -> FileResponse:

    return await quiz_repo.get_all_company_user_answers_from_redis(
        company_id=company_id
    )


@router.get(
    "/get_answers_for_company_employee/{company_id}/{employee_id}",
    status_code=status.HTTP_200_OK,
)
async def redis_test(
    company_id: int,
    employee_id: int,
    quiz_repo: QuizService = Depends(get_quiz_service),
) -> FileResponse:

    return await quiz_repo.get_company_employee_answers_from_redis(
        company_id=company_id, employee_id=employee_id
    )
