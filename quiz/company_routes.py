from fastapi import APIRouter, Depends, Security, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.database import get_db
from quiz.models.db_models import User, Company, Invite, Request
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


@router.get("/")
async def company_list(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> [CompanyBase]:
    return await CompanyService.get_company_list(skip=skip, limit=limit, db=db)


@auth_required
@router.post("/create")
async def company_create(
    company_details: CompanyCreate,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> HTTPException | CompanyCreated:
    user_email = await UserService.get_current_user_email(credentials=credentials)
    user = db.query(User).filter_by(email=user_email).first()
    company = db.query(Company).filter_by(owner=user.id).first()
    if company:
        return HTTPException(status_code=401, detail="You already have company")
    return await CompanyService.create_company(
        company_details=company_details, user=user, db=db
    )


@router.post("/update")
async def company_update(
    company_details: CompanyUpdate,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> CompanyUpdated | HTTPException:
    user_email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=user_email, db=db)
    company = db.query(Company).filter_by(owner=user.id).first()
    if not company:
        return HTTPException(status_code=401, detail="You don't have company yet")
    return await CompanyService.update_company(
        company_details=company_details, company=company, user=user
    )


@router.delete("/delete", status_code=204)
async def company_delete(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> None:
    user_email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=user_email, db=db)
    company = db.query(Company).filter_by(owner=user.id).first()
    await CompanyService.delete_company(company_id=company.id)


@router.post("/invite/{pk}")
async def invite_create(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> InviteBase | HTTPException:

    user_email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=user_email, db=db)
    user_to_invite = db.query(User).filter_by(id=int(pk)).first()
    company = db.query(Company).filter_by(owner=user.id).first()
    invite = db.query(Invite).filter_by(company=company.id, user=int(pk)).first()
    if not user_to_invite:
        return HTTPException(status_code=401, detail="User with id doesn't exist")
    if user_to_invite in company.employees:
        return HTTPException(status_code=401, detail="User already in company")
    if not company:
        return HTTPException(status_code=401, detail="You don't have company yet")
    if invite:
        return HTTPException(status_code=401, detail="User already invited")

    return await CompanyService.create_invite(
        user_to_invite_id=int(pk), company_id=company.id
    )


@router.post("/delete/{pk}")
async def remove_from_company(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> dict | HTTPException:

    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    user_to_remove = db.query(User).filter_by(id=int(pk)).first()
    company = db.query(Company).filter_by(owner=user.id).first()

    if user_to_remove not in company.employees:
        return HTTPException(status_code=401, detail="User with id isn't in company")

    if not company:
        return HTTPException(status_code=401, detail="You don't have company yet")

    return await CompanyService.remove_from_company(
        company=company, user_to_remove=user_to_remove, db=db
    )


@router.post("/admins/{pk}")
async def add_to_admins(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> dict | HTTPException:

    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    user_to_add = db.query(User).filter_by(id=int(pk)).first()
    company = db.query(Company).filter_by(owner=user.id).first()

    if user_to_add not in company.employees:
        return HTTPException(status_code=401, detail="User with id isn't in compony")
    if user_to_add in company.admins:
        return HTTPException(status_code=401, detail="User is already admin")
    if not company:
        return HTTPException(status_code=401, detail="You don't have company yet")

    return await CompanyService.add_to_admin(
        company=company, user_to_add=user_to_add, db=db
    )


@router.post("/admins/delete/{pk}")
async def remove_from_admins(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> dict | HTTPException:

    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    user_to_remove = db.query(User).filter_by(id=int(pk)).first()
    company = db.query(Company).filter_by(owner=user.id).first()

    if user_to_remove not in company.admins:
        return HTTPException(status_code=401, detail="User with id isn't in admins")

    if not company:
        return HTTPException(status_code=401, detail="You don't have company yet")

    return await CompanyService.remove_from_admin(
        company=company, user_to_remove=user_to_remove, db=db
    )


@router.get("/requests")
async def requests_list(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> RequestBase:
    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    company = db.query(Company).filter_by(owner=user.id).first()
    return await CompanyService.get_request_list(
        company_id=company.id, skip=skip, limit=limit, db=db
    )


@router.post("/request/{pk}")
async def accept_request(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> dict | HTTPException:

    email = await UserService.get_current_user_email(credentials=credentials)
    owner = UserService.get_user_by_email(email=email, db=db)
    request = db.query(Request).filter_by(id=int(pk)).first()
    company = db.query(Company).filter_by(owner=owner.id).first()

    if not request:
        return HTTPException(status_code=401, detail="Request doesn't exist")

    if request.company != company.id:
        return HTTPException(
            status_code=401, detail="This is not yours company request"
        )

    user = db.query(User).filter_by(id=request.user).first()
    return await CompanyService.accept_request(
        company=company, user=user, db=db, request_id=int(pk)
    )


@router.post("/invites/disapprove/{pk}")
async def disapprove_request(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> dict | HTTPException:

    email = await UserService.get_current_user_email(credentials=credentials)
    owner = UserService.get_user_by_email(email=email, db=db)
    request = db.query(Request).filter_by(id=int(pk)).first()
    company = db.query(Company).filter_by(owner=owner.id).first()

    if not request:
        return HTTPException(status_code=401, detail="Request doesn't exist")

    if request.company != company.id:
        return HTTPException(
            status_code=401, detail="This is not yours company request"
        )

    return await CompanyService.disapprove_request(
        user_id=request.user, request_id=request.id
    )
