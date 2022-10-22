from functools import wraps
from random import randint

from fastapi import Security, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import EmailStr
from sqlalchemy.orm import Session
from core.auth import Auth
from core.hashing import Hasher
from core.utils import VerifyToken
from .schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyBase,
    CompanyCreated,
    CompanyUpdated,
    CompanyList,
)
from .schemas.invite import InviteBase
from .schemas.request import RequestBase
from .schemas.user import UserCreate, UserUpdate, UserBase
from core.database import database, get_db
from quiz.models.db_models import (
    users,
    User,
    Company,
    companies,
    Invite,
    invites,
    requests,
    Request,
)


class UserService:
    security = HTTPBearer()
    auth_handler = Auth()

    @staticmethod
    async def get_user_list(
        skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
    ) -> [UserBase]:
        user_list = db.query(User).offset(skip).limit(limit).all()

        return user_list

    @staticmethod
    async def get_detail_user(pk: int) -> UserBase:
        user = await database.fetch_one(
            query=users.select().where(users.c.id == int(pk))
        )
        if user is not None:
            return user

    @staticmethod
    async def create_user(user_details: UserCreate) -> UserBase:
        hashed_password = Hasher.get_password_hash(user_details.password)
        user_details.password = hashed_password
        post = users.insert().values(
            username=user_details.username,
            email=user_details.email,
            password=user_details.password,
        )
        pk = await database.execute(post)

        return UserBase(**{**user_details.dict(), "id": pk})

    @staticmethod
    async def update_user(pk: int, email, user_details: UserUpdate) -> UserBase:
        hashed_password = Hasher.get_password_hash(user_details.password)
        user_details.password = hashed_password
        post = users.update().where(users.c.id == pk).values(**user_details.dict())
        await database.execute(post)
        return UserBase(**{**user_details.dict(), "email": email, "id": pk})

    @staticmethod
    async def delete_user(pk: int) -> None:
        user = users.delete().where((users.c.id == pk))
        return await database.execute(user)

    @staticmethod
    async def get_current_user_email(
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> EmailStr:

        auth_token = VerifyToken(credentials.credentials).verify()
        email = auth_token.get("email")
        if email:
            return email

        else:
            email = UserService.auth_handler.decode_token(token=credentials.credentials)

            return email

    @staticmethod
    def get_user_by_email(email, db: Session = Depends(get_db)) -> UserBase:
        user = db.query(User).filter_by(email=email).first()
        return user

    @staticmethod
    async def get_invites_list(
        user, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
    ) -> [InviteBase]:

        invites_list = (
            db.query(Invite).filter_by(user=user.id).offset(skip).limit(limit).all()
        )
        return invites_list

    @staticmethod
    async def accept_invite(company, user, db, invite_id) -> dict:
        company.employees.append(user)
        db.add(company)
        db.commit()
        db.refresh(company)
        invite = invites.delete().where((invites.c.id == invite_id))
        await database.execute(invite)
        return {"message": f"Welcome to {company.name} company"}

    @staticmethod
    async def disapprove_invite(company, invite_id) -> dict:
        invite = invites.delete().where((invites.c.id == invite_id))
        await database.execute(invite)
        return {"message": f"Invite from company {company.name} is disapproved"}

    @staticmethod
    async def create_request(user_id: int, company_id: int) -> RequestBase:

        post = requests.insert().values(company=company_id, user=user_id)

        pk = await database.execute(post)
        return RequestBase(**{"id": pk, "company": company_id, "user": user_id})

    @staticmethod
    async def get_companies_list(
        skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
    ) -> [CompanyList]:
        # company_list = db.query(Company).where(visibility=True).offset(skip).limit(limit).all()
        return company_list


def auth_required(func):
    @wraps(func)
    async def wrapper(
        credentials: HTTPAuthorizationCredentials = Security(UserService.security),
        db: Session = Depends(get_db),
        *args,
        **kwargs,
    ):

        authorized = False
        auth_token = VerifyToken(credentials.credentials).verify()
        email = auth_token.get("email")
        jwt_token = credentials.credentials
        if email:
            user = db.query(User).filter_by(email=email).first()
            if user:
                authorized = True
            else:
                user_details = {
                    "username": email,
                    "email": email,
                    "password": str(randint(1000000, 9999999)),
                }
                post = users.insert().values(
                    username=user_details["username"],
                    email=user_details["email"],
                    password=Hasher.get_password_hash(user_details["password"]),
                )
                await database.execute(post)
                authorized = True
        elif UserService.auth_handler.decode_token(jwt_token):
            authorized = True
        if authorized is not True:
            return HTTPException(status_code=401, detail="Invalid token")
        return await func(credentials, db, *args, **kwargs)

    return wrapper


class CompanyService:
    @staticmethod
    async def get_company_list(
        skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
    ) -> [CompanyBase]:
        company_list = (
            db.query(Company).filter_by(visibility=True).offset(skip).limit(limit).all()
        )
        return company_list

    @staticmethod
    async def create_company(
        company_details: CompanyCreate, user, db: Session = Depends(get_db)
    ) -> HTTPException | CompanyCreated:
        company = db.query(Company).filter_by(name=company_details.name).first()
        if company:
            return HTTPException(
                status_code=401, detail="Company with name already created"
            )

        post = companies.insert().values(
            name=company_details.name,
            description=company_details.description,
            owner=user.id,
            visibility=True,
        )
        pk = await database.execute(post)
        return CompanyCreated(**{**company_details.dict(), "id": pk, "owner": user.id})

    @staticmethod
    async def update_company(
        company_details: CompanyUpdate, company, user
    ) -> CompanyUpdated:
        post = (
            companies.update()
            .where(companies.c.id == company.id)
            .values(**company_details.dict())
        )
        await database.execute(post)
        return CompanyUpdated(
            **{**company_details.dict(), "id": company.id, "owner": user.id}
        )

    @staticmethod
    async def delete_company(company_id: int) -> None:
        company = companies.delete().where((companies.c.id == company_id))
        return await database.execute(company)

    @staticmethod
    async def create_invite(user_to_invite_id: int, company_id: int) -> InviteBase:

        post = invites.insert().values(company=company_id, user=user_to_invite_id)

        pk = await database.execute(post)
        return InviteBase(
            **{"id": pk, "company": company_id, "user": user_to_invite_id}
        )

    @staticmethod
    async def remove_from_company(company, user_to_remove, db) -> dict:
        company.employees.remove(user_to_remove)
        db.add(company)
        db.commit()
        db.refresh(company)
        return {"message": f"User with id {user_to_remove.id} is removed from company"}

    @staticmethod
    async def add_to_admin(company, user_to_add, db) -> dict:
        company.admins.append(user_to_add)
        db.add(company)
        db.commit()
        db.refresh(company)
        return {"message": f"User with id {user_to_add.id} is added to admins"}

    @staticmethod
    async def remove_from_admin(company, user_to_remove, db) -> dict:
        company.admins.remove(user_to_remove)
        db.add(company)
        db.commit()
        db.refresh(company)
        return {"message": f"User with id {user_to_remove.id} is removed from admins"}

    @staticmethod
    async def get_request_list(
        company_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
    ) -> [InviteBase]:
        request_list = (
            db.query(Request)
            .filter_by(company=company_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return request_list

    @staticmethod
    async def accept_request(company, user, db, request_id) -> dict:
        company.employees.append(user)
        db.add(company)
        db.commit()
        db.refresh(company)
        request = requests.delete().where(requests.c.id == request_id)
        await database.execute(request)
        return {"message": f"Request from user {user.id} is accepted"}

    @staticmethod
    async def disapprove_request(user_id, request_id) -> dict:
        request = requests.delete().where((requests.c.id == request_id))
        await database.execute(request)
        return {"message": f"Invite from user {user_id} is disapproved"}
