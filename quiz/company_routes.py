from fastapi import APIRouter, Depends, Security, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from quiz.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyBase,
    CompanyCreated,
    CompanyUpdated,
)
from quiz.schemas.invite import InviteBase
from quiz.schemas.request import RequestBase
from quiz.service import CompanyService, UserService, auth_required

router = APIRouter()


@router.get("/", response_model=list[CompanyBase])
async def company_list(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[CompanyBase]:
    company_repo = CompanyService(db=db)
    return await company_repo.get_company_list(skip=skip, limit=limit)


@auth_required
@router.post("/create", response_model=CompanyCreated)
async def company_create(
    company_details: CompanyCreate,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> CompanyCreated:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.create_company(
        company_details=company_details, credentials=credentials, user_repo=user_repo
    )


@router.post("/update", response_model=CompanyUpdated)
async def company_update(
    company_details: CompanyUpdate,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> CompanyUpdated:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.update_company(
        company_details=company_details, credentials=credentials, user_repo=user_repo
    )


@router.delete("/delete", status_code=204)
async def company_delete(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.delete_company(
        credentials=credentials, user_repo=user_repo
    )


@router.post("/invite/{pk}", response_model=InviteBase)
async def invite_create(
    pk: int,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> InviteBase:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.create_invite(
        user_to_invite_id=int(pk), credentials=credentials, user_repo=user_repo
    )


@router.post("/delete/{pk}", status_code=204)
async def remove_from_company(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.remove_from_company(
        user_to_remove_id=int(pk), credentials=credentials, user_repo=user_repo
    )


@router.post("/admins/{pk}", status_code=204)
async def add_to_admins(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.add_to_admin(
        user_to_admin_id=int(pk), credentials=credentials, user_repo=user_repo
    )


@router.post("/admins/delete/{pk}", status_code=204)
async def remove_from_admins(
    pk: int,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.remove_from_admin(
        user_to_remove_id=int(pk), credentials=credentials, user_repo=user_repo
    )


@router.get("/requests", response_model=list[RequestBase])
async def requests_list(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[RequestBase]:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.get_request_list(
        skip=skip, limit=limit, credentials=credentials, user_repo=user_repo
    )


@router.post("/request/{pk}", status_code=204)
async def accept_request(
    pk: int,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.accept_request(
        request_id=int(pk), credentials=credentials, user_repo=user_repo
    )


@router.post("/invites/disapprove/{pk}", status_code=204)
async def disapprove_request(
    pk: int,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException:
    company_repo = CompanyService(db=db)
    user_repo = UserService(db=db)
    return await company_repo.disapprove_request(
        request_id=int(pk), credentials=credentials, user_repo=user_repo
    )
