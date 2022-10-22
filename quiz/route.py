import logging
from sqlalchemy.orm import Session
from core.database import get_db
from core.hashing import Hasher
from quiz.models.user import User
from fastapi import APIRouter, HTTPException, Depends, Security
from quiz.schemas.user import UserBase, UserCreate, UserUpdate, UserSignIn
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
7
from .service import UserService, auth_required
router = APIRouter()
logger = logging.getLogger("quiz-logger")


@router.post("/login")
async def login(user_details: UserSignIn, db: Session = Depends(get_db)):
    user = UserService.get_user_by_email(email=user_details.email, db=db)
    if user is None:
        return HTTPException(status_code=401, detail="Invalid email")
    if not Hasher.verify_password(user_details.password, user.password):
        return HTTPException(status_code=401, detail="Invalid password")
    token = UserService.auth_handler.encode_token(user.email)
    return {"token": token, "username": {user.username}, "email": {user.email}}


@router.get("/refresh_token")
def refresh_token(credentials: HTTPAuthorizationCredentials = Security(UserService.security)):
    expired_token = credentials.credentials
    return UserService.auth_handler.refresh_token(expired_token)



@router.get("/about{pk}", response_model=UserBase)

async def user_detail(pk):
    user = await UserService.get_detail_user(pk)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    logger.debug(f"User with id {pk} details displayed")
    return user


@router.get("/")
async def user_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.debug(f"User list displayed")
    return await UserService.get_user_list(skip=skip, limit=limit, db=db)



@router.get("/me")
@auth_required
async def about_me(
        credentials: HTTPAuthorizationCredentials = Security(UserService.security),
        db: Session = Depends(get_db),
):
        email = await UserService.get_current_user_email(credentials=credentials)
        user = db.query(User).filter_by(email=email).first()
        return user


@router.post("/register", status_code=201)

async def register(user_details: UserCreate, db: Session = Depends(get_db)):
    user = UserService.get_user_by_email(email=user_details.email, db=db)

    if user:
        return HTTPException(status_code=401, detail="Account already exists")

    if user_details.confirm_password == user_details.password:
        logger.debug(f"User created")
        return await UserService.create_user(user_details)
    else:
        return HTTPException(status_code=401, detail="Invalid password")

@router.post("/", status_code=201, response_model=UserBase)
async def user_create(item: UserCreate):
    logger.debug(f"User created")
    return await service.create_user(item)



@router.put("/update", status_code=201)
@auth_required
async def user_update(
        user_details: UserUpdate,
        credentials: HTTPAuthorizationCredentials = Security(UserService.security),
        db: Session = Depends(get_db),
):
        email = await UserService.get_current_user_email(credentials=credentials)
        user = db.query(User).filter_by(email=email).first()
        logger.debug(f"User with id {user.id} updated")
        return await UserService.update_user(pk=user.id, user_details=user_details)


@router.delete("/delete", status_code=204)
@auth_required
async def user_delete(
        credentials: HTTPAuthorizationCredentials = Security(UserService.security),
        db: Session = Depends(get_db),
):
        email = await UserService.get_current_user_email(credentials=credentials)
        user = db.query(User).filter_by(email=email).first()
        logger.debug(f"User with id {user.id} deleted from database")
        await UserService.delete_user(pk=user.id)

