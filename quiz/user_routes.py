import logging
from sqlalchemy.orm import Session
from core.database import get_db
from fastapi import APIRouter, HTTPException, Depends, Security
from quiz.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserSignIn,
    UserLogIn,
    UserInfo,
)
from fastapi.security import HTTPAuthorizationCredentials
from .schemas.invite import InviteBase
from .schemas.request import RequestBase
from .service import UserService, auth_required

router = APIRouter()

logger = logging.getLogger("quiz-logger")


@router.post("/login", response_model=UserLogIn)
async def login(
    user_details: UserSignIn, db: Session = Depends(get_db)
) -> UserLogIn | HTTPException:
    user_repo = UserService(db=db)
    return await user_repo.login_user(user_details=user_details)


@router.get("/refresh_token")
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
):
    expired_token = credentials.credentials
    return UserService.auth_handler.refresh_token(expired_token)


@router.get("/about/{pk}", response_model=UserInfo)
async def user_detail(pk: int, db: Session = Depends(get_db)) -> UserInfo:
    user_repo = UserService(db=db)
    return await user_repo.get_detail_user(pk=pk)


@router.get("/", response_model=list[UserInfo])
async def user_list(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[UserInfo]:
    user_repo = UserService(db=db)
    return await user_repo.get_user_list(skip=skip, limit=limit)


@router.get("/me", response_model=UserBase)
@auth_required
async def about_me(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> UserBase:
    user_repo = UserService(db=db)
    return await user_repo.get_current_user(credentials=credentials)


@router.post("/register", status_code=201, response_model=UserBase)
async def register(user_details: UserCreate, db: Session = Depends(get_db)) -> UserBase:
    user_repo = UserService(db=db)
    return await user_repo.create_user(user_details=user_details)


@router.put("/update", status_code=201, response_model=UserBase)
async def user_update(
    user_details: UserUpdate,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> UserBase:
    user_repo = UserService(db=db)
    return await user_repo.update_user(
        user_details=user_details, credentials=credentials
    )


@router.delete("/delete", status_code=204)
async def user_delete(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    user_repo = UserService(db=db)
    return await user_repo.delete_user(credentials=credentials)


@router.get("/invites", response_model=list[InviteBase])
async def invites_list(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> [InviteBase]:
    user_repo = UserService(db=db)
    return await user_repo.get_invites_list(
        credentials=credentials, skip=skip, limit=limit
    )


@router.post("/invites/{pk}", status_code=200)
async def accept_invite(
    pk: int,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    user_repo = UserService(db=db)
    return await user_repo.accept_invite(invite_id=int(pk), credentials=credentials)


@router.post("/invites/disapprove/{pk}", status_code=200)
async def disapprove_invite(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    user_repo = UserService(db=db)
    return await user_repo.disapprove_invite(invite_id=int(pk), credentials=credentials)


@router.post("/request/{pk}", response_model=RequestBase)
async def request_create(
    pk: int,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> RequestBase:
    user_repo = UserService(db=db)
    return await user_repo.create_request(company_id=int(pk), credentials=credentials)
