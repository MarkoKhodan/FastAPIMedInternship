import logging
from sqlalchemy.orm import Session
from core.database import get_db, database
from core.hashing import Hasher
from quiz.models.db_models import users, Invite, Company, Request
from fastapi import APIRouter, HTTPException, Depends, Security
from quiz.schemas.user import UserBase, UserCreate, UserUpdate, UserSignIn, UserLogIn
from fastapi.security import HTTPAuthorizationCredentials

from .schemas.company import CompanyList
from .schemas.invite import InviteBase
from .schemas.request import RequestBase
from .service import UserService, auth_required

router = APIRouter()

logger = logging.getLogger("quiz-logger")


@router.post("/login")
async def login(
    user_details: UserSignIn, db: Session = Depends(get_db)
) -> UserLogIn | HTTPException:
    user = UserService.get_user_by_email(email=user_details.email, db=db)
    if user is None:
        return HTTPException(status_code=404, detail="Invalid email")
    if not Hasher.verify_password(user_details.password, user.password):
        return HTTPException(status_code=404, detail="Invalid password")
    token = UserService.auth_handler.encode_token(user.email)
    return UserLogIn(**{"token": token, "username": user.username, "email": user.email})


@router.get("/refresh_token")
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
):
    expired_token = credentials.credentials
    return UserService.auth_handler.refresh_token(expired_token)


@router.get("/about/{pk}", response_model=UserBase)
async def user_detail(pk) -> UserBase | HTTPException:
    user = await UserService.get_detail_user(pk)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    logger.debug(f"User with id {pk} details displayed")
    return user


@router.get("/")
async def user_list(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> [UserBase]:
    logger.debug(f"User list displayed")
    return await UserService.get_user_list(skip=skip, limit=limit, db=db)


@router.get("/me", response_model=UserBase)
@auth_required
async def about_me(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> UserBase:
    email = await UserService.get_current_user_email(credentials=credentials)
    user = await database.fetch_one(query=users.select().where(users.c.email == email))
    return user


@router.post("/register", status_code=201)
async def register(
    user_details: UserCreate, db: Session = Depends(get_db)
) -> UserBase | HTTPException:
    user = UserService.get_user_by_email(email=user_details.email, db=db)

    if user:
        return HTTPException(status_code=401, detail="Account already exists")

    if user_details.confirm_password == user_details.password:
        logger.debug(f"User created")
        return await UserService.create_user(user_details)
    else:
        return HTTPException(status_code=401, detail="Invalid password")


@router.put("/update", status_code=201)
async def user_update(
    user_details: UserUpdate,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> UserBase:
    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    logger.debug(f"User with id {user.id} updated")
    return await UserService.update_user(
        pk=user.id, user_details=user_details, email=email
    )


@router.delete("/delete", status_code=204)
async def user_delete(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> None:
    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    logger.debug(f"User with id {user.id} deleted from database")
    await UserService.delete_user(pk=user.id)


@router.get("/invites")
async def invites_list(
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> [InviteBase]:
    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    return await UserService.get_invites_list(user=user, skip=skip, limit=limit, db=db)


@router.post("/invites/{pk}")
async def accept_invite(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> dict | HTTPException:

    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    invite = db.query(Invite).filter_by(id=int(pk)).first()

    if not invite:
        return HTTPException(status_code=401, detail="Invite doesn't exist")

    if invite.user != user.id:
        return HTTPException(status_code=401, detail="This is not yours invite")

    company = db.query(Company).filter_by(id=invite.company).first()

    return await UserService.accept_invite(
        company=company, user=user, db=db, invite_id=invite.id
    )


@router.post("/invites/disapprove/{pk}")
async def disapprove_invite(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> dict | HTTPException:

    email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=email, db=db)
    invite = db.query(Invite).filter_by(id=int(pk)).first()

    if not invite:
        return HTTPException(status_code=401, detail="Invite doesn't exist")

    if invite.user != user.id:
        return HTTPException(status_code=401, detail="This is not yours invite")

    company = db.query(Company).filter_by(id=invite.company).first()

    return await UserService.disapprove_invite(company=company, invite_id=invite.id)


@router.post("/request/{pk}")
async def request_create(
    pk,
    credentials: HTTPAuthorizationCredentials = Security(UserService.security),
    db: Session = Depends(get_db),
) -> RequestBase | HTTPException:

    user_email = await UserService.get_current_user_email(credentials=credentials)
    user = UserService.get_user_by_email(email=user_email, db=db)
    company = db.query(Company).filter_by(id=int(pk)).first()

    if not company:
        return HTTPException(status_code=401, detail="Company with id doesn't exist")
    if user in company.employees:
        return HTTPException(status_code=401, detail="You are already in company")

    request = db.query(Request).filter_by(company=company.id, user=user.id).first()

    if request:
        return HTTPException(
            status_code=401, detail="You have request already, wait for approve"
        )

    return await UserService.create_request(user_id=user.id, company_id=int(pk))
