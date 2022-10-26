from fastapi import APIRouter, Security, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from starlette import status

from core.database import get_db
from quiz.schemas.quiz import QuizCreate, QuizBase, QuizUpdate, QuizList
from quiz.service import UserService, QuizService

router = APIRouter()


@router.post("/create/{pk}", response_model=QuizList)
async def quiz_create(
    quiz_info: QuizCreate,
    pk: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
) -> QuizList:
    quiz_repo = QuizService(db=db, credentials=credentials)

    return await quiz_repo.create_quiz(
        quiz_info=quiz_info,
        company_id=int(pk),
    )


@router.post("/update/{company_id}/{quiz_id}", response_model=QuizList)
async def quiz_update(
    quiz_info: QuizUpdate,
    quiz_id: int,
    company_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
) -> QuizList:
    quiz_repo = QuizService(db=db, credentials=credentials)

    return await quiz_repo.update_quiz(
        quiz_info=quiz_info,
        company_id=int(company_id),
        quiz_id=int(quiz_id),
    )


@router.post("/delete/{company_id}/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def quiz_update(
    quiz_id: int,
    company_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
) -> HTTPException:
    quiz_repo = QuizService(db=db, credentials=credentials)

    return await quiz_repo.delete_quiz(
        company_id=int(company_id),
        quiz_id=int(quiz_id),
    )


@router.get("/{company_id}", response_model=list[QuizList])
async def quiz_list(
    company_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[QuizList]:
    quiz_repo = QuizService(db=db)
    return await quiz_repo.get_quiz_list(
        company_id=int(company_id), skip=skip, limit=limit
    )
