from typing import List

from fastapi import APIRouter, Security, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from quiz.schemas.company import CompanyUserLastActivity
from quiz.schemas.result import (
    QuizResultAvarage,
    UserResultAvarage,
    UserQuizResultAvarage,
    UserQuizLastActivity,
)
from quiz.schemas.user import UserAverageResult
from quiz.service import UserService, AnalyticService

router = APIRouter()


def get_analytic_service(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
):
    return AnalyticService(db=db, credentials=credentials)


@router.get("/quiz_avarege_result/{quiz_id}", response_model=List[QuizResultAvarage])
async def quiz_avarege_result(
    quiz_id: int,
    analytic_repo: AnalyticService = Depends(get_analytic_service),
) -> List[QuizResultAvarage]:
    return await analytic_repo.get_quiz_average_results(quiz_id=quiz_id)


@router.get(
    "/employee_avarege_result/{company_id}/{user_id}",
    response_model=List[UserResultAvarage],
)
async def employee_avarege_result(
    user_id: int,
    company_id: int,
    analytic_repo: AnalyticService = Depends(get_analytic_service),
) -> List[UserResultAvarage]:
    return await analytic_repo.get_employee_avarege_results(
        user_id=user_id, company_id=company_id
    )


@router.get(
    "/list_employees_last_activity/{company_id}",
    response_model=List[CompanyUserLastActivity],
)
async def list_employees_last_activity(
    company_id: int,
    analytic_repo: AnalyticService = Depends(get_analytic_service),
) -> List[CompanyUserLastActivity]:
    return await analytic_repo.get_employee_last_activity_list(company_id=company_id)


@router.get("/user_average_result/{user_id}", response_model=UserAverageResult)
async def user_average_result(
    user_id: int,
    analytic_repo: AnalyticService = Depends(get_analytic_service),
) -> UserAverageResult:
    return await analytic_repo.get_user_average_result(user_id=user_id)


@router.get(
    "/user_average_quiz_result/{quiz_id}", response_model=List[UserQuizResultAvarage]
)
async def user_average_quiz_result(
    quiz_id: int,
    analytic_repo: AnalyticService = Depends(get_analytic_service),
) -> List[UserQuizResultAvarage]:
    return await analytic_repo.get_user_average_quiz_result(quiz_id=quiz_id)


@router.get(
    "/list_user_quizzes_last_activity", response_model=List[UserQuizLastActivity]
)
async def list_quizzes_last_activity(
    analytic_repo: AnalyticService = Depends(get_analytic_service),
) -> List[UserQuizLastActivity]:
    return await analytic_repo.get_list_quizzes_last_activity()
