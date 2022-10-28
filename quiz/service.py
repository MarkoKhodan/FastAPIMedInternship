from functools import wraps
from random import randint
import logging
from fastapi import Security, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import EmailStr
from sqlalchemy import desc
from sqlalchemy.orm import Session
from core.auth import Auth
from core.hashing import Hasher
from core.utils import VerifyToken
from .schemas.result import ResultBase
from .schemas.answers import AnswerRead
from .schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyBase,
    CompanyCreated,
    CompanyUpdated,
)
from .schemas.invite import InviteBase
from .schemas.questions import QuestionRead, QuestionPass, QuestionAnswerRead
from .schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizList,
    QuizInfo,
    QuizPass,
    QuizQuestions,
)
from .schemas.request import RequestBase
from .schemas.user import (
    UserCreate,
    UserUpdate,
    UserBase,
    UserSignIn,
    UserLogIn,
    UserInfo,
)
from core.database import database, get_db, redis_db
from quiz.models.db_models import (
    users,
    User,
    Company,
    Invite,
    Request,
    Answer,
    Question,
    Quiz,
    Result,
)

logger = logging.getLogger("quiz-logger")


class UserService:
    security = HTTPBearer()
    auth_handler = Auth()

    def __init__(self, db: Session):
        self.db = db

    async def login_user(self, user_details: UserSignIn) -> UserLogIn | HTTPException:
        user = await self.get_user_by_email(email=user_details.email)
        if user is None:
            raise HTTPException(status_code=404, detail="Invalid email")
        if not Hasher.verify_password(user_details.password, user.password):
            raise HTTPException(status_code=404, detail="Invalid password")
        token = self.auth_handler.encode_token(user.email)
        return UserLogIn(token=token, username=user.username, email=user.email)

    async def get_user_list(self, skip: int = 0, limit: int = 100) -> list[UserInfo]:
        user_list = self.db.query(User).offset(skip).limit(limit).all()

        return [
            UserInfo(id=user.id, email=user.email, username=user.username)
            for user in user_list
        ]

    async def get_detail_user(self, pk: int) -> UserInfo:
        user = self.db.query(User).filter_by(id=int(pk)).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return UserInfo(id=user.id, email=user.email, username=user.username)

    async def create_user(self, user_details: UserCreate) -> UserBase:
        user = await self.get_user_by_email(email=user_details.email)

        if user:
            raise HTTPException(status_code=401, detail="Account already exists")

        if user_details.confirm_password != user_details.password:
            raise HTTPException(status_code=401, detail="Invalid password")

        hashed_password = Hasher.get_password_hash(user_details.password)
        user_details.password = hashed_password
        new_user = User(
            email=user_details.email,
            username=user_details.username,
            password=hashed_password,
        )

        self.db.add(new_user)
        self.db.commit()
        return UserBase(**user_details.dict(), id=new_user.id)

    async def update_user(
        self, user_details: UserUpdate, credentials: HTTPAuthorizationCredentials
    ) -> UserBase:
        user = await self.get_current_user(credentials=credentials)
        hashed_password = Hasher.get_password_hash(user_details.password)
        user_details.password = hashed_password
        user = self.db.query(User).filter_by(id=user.id).first()
        user.update(**user_details.dict())
        self.db.commit()
        logger.debug(f"User with id {user.id} updated")
        return UserBase(**user_details.dict(), email=user.email, id=user.id)

    async def delete_user(
        self, credentials: HTTPAuthorizationCredentials
    ) -> HTTPException:
        user_details = await self.get_current_user(credentials=credentials)
        user = self.db.query(User).filter_by(id=user_details.id).first()
        self.db.delete(user)
        self.db.commit()
        logger.debug(f"User with id {user.id} deleted")
        return HTTPException(status_code=204, detail=f"User with id{user.id} deleted")

    async def get_current_user_email(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> EmailStr:

        auth_token = VerifyToken(credentials.credentials).verify()
        email = auth_token.get("email")
        if email:
            return email

        else:
            email = self.auth_handler.decode_token(token=credentials.credentials)
            return email

    async def get_user_by_email(self, email) -> User:
        user = self.db.query(User).filter_by(email=email).first()
        return user

    async def get_current_user(
        self, credentials: HTTPAuthorizationCredentials
    ) -> UserBase:
        email = await self.get_current_user_email(credentials=credentials)
        user = await self.get_user_by_email(email=email)
        return UserBase(
            id=user.id, password=user.password, email=user.email, username=user.username
        )

    async def get_invites_list(
        self, credentials: HTTPAuthorizationCredentials, skip: int = 0, limit: int = 100
    ) -> list[InviteBase]:
        user = await self.get_current_user(credentials=credentials)
        invites_list = (
            self.db.query(Invite)
            .filter_by(user=user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [InviteBase(**invite.dict()) for invite in invites_list]

    async def accept_invite(
        self, invite_id: int, credentials: HTTPAuthorizationCredentials
    ) -> HTTPException:
        user = await self.get_user_by_email(
            await self.get_current_user_email(credentials)
        )
        invite = self.db.query(Invite).filter_by(id=invite_id).first()

        if not invite:
            raise HTTPException(status_code=401, detail="Invite doesn't exist")

        if invite.user != user.id:
            raise HTTPException(status_code=401, detail="This is not yours invite")

        company = self.db.query(Company).filter_by(id=invite.company).first()
        company.employees.append(user)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        invite = self.db.query(Invite).filter_by(id=invite_id).first()
        self.db.delete(invite)
        self.db.commit()
        return HTTPException(
            status_code=200, detail=f"Welcome to {company.name} company"
        )

    async def disapprove_invite(
        self, invite_id: int, credentials: HTTPAuthorizationCredentials
    ) -> HTTPException:
        user = await self.get_user_by_email(
            await self.get_current_user_email(credentials)
        )
        invite = self.db.query(Invite).filter_by(id=invite_id).first()

        if not invite:
            raise HTTPException(status_code=401, detail="Invite doesn't exist")

        if invite.user != user.id:
            raise HTTPException(status_code=401, detail="This is not yours invite")
        company = self.db.query(Company).filter_by(id=invite.company).first()
        invite = self.db.query(Invite).filter_by(id=invite_id).first()
        self.db.delete(invite)
        self.db.commit()
        return HTTPException(
            status_code=200, detail=f"Invite from company {company.name} is disapproved"
        )

    async def create_request(
        self, company_id: int, credentials: HTTPAuthorizationCredentials
    ) -> RequestBase:
        user = await self.get_current_user(credentials=credentials)
        company = self.db.query(Company).filter_by(id=company_id).first()

        if not company:
            raise HTTPException(status_code=401, detail="Company with id doesn't exist")
        if user in company.employees:
            raise HTTPException(status_code=401, detail="You are already in company")

        request = (
            self.db.query(Request).filter_by(company=company.id, user=user.id).first()
        )

        if request:
            raise HTTPException(
                status_code=401, detail="You have request already, wait for approve"
            )
        request = Request(user=user.id, company=company.id)
        self.db.add(request)
        self.db.commit()
        return RequestBase(user=user.id, company=company.id, id=request.id)



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
                user = User(
                    username=user_details["username"],
                    email=user_details["email"],
                    password=Hasher.get_password_hash(user_details["password"]),
                )
                db.add(user)
                db.commit()
                authorized = True

        elif UserService.auth_handler.decode_token(jwt_token):

            authorized = True
        if authorized is not True:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await func(credentials, db, *args, **kwargs)

    return wrapper


class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    async def get_company_by_id(self, id: int) -> Company:
        company = self.db.query(Company).filter_by(id=id).first()
        return company

    async def get_company_list(
        self, skip: int = 0, limit: int = 100
    ) -> list[CompanyBase]:
        company_list = (
            self.db.query(Company)
            .filter_by(visibility=True)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            CompanyBase(
                id=company.id,
                name=company.name,
                description=company.description,
                visibility=company.visibility,
                owner=company.owner,
                employees=company.employees,
            )
            for company in company_list
        ]

    async def create_company(
        self,
        user_repo: UserService,
        company_details: CompanyCreate,
        credentials: HTTPAuthorizationCredentials,
    ) -> CompanyCreated:
        user = await user_repo.get_current_user(credentials=credentials)
        user_company = self.db.query(Company).filter_by(owner=user.id).first()
        if user_company:
            raise HTTPException(status_code=401, detail="You already have company")
        company = self.db.query(Company).filter_by(name=company_details.name).first()
        if company:
            raise HTTPException(
                status_code=401, detail="Company with name already created"
            )
        company_to_create = Company(**company_details.dict(), owner=user.id)
        self.db.add(company_to_create)
        self.db.commit()
        return CompanyCreated(
            **company_details.dict(), id=company_to_create.id, owner=user.id
        )

    async def update_company(
        self,
        company_details: CompanyUpdate,
        user_repo: UserService,
        credentials: HTTPAuthorizationCredentials,
    ) -> CompanyUpdated:
        user = await user_repo.get_current_user(credentials=credentials)
        company = self.db.query(Company).filter_by(owner=user.id).first()
        if not company:
            raise HTTPException(status_code=401, detail="You don't have company yet")
        company = self.db.query(Company).filter_by(id=company.id).first()
        company.update(**company_details.dict())
        self.db.commit()
        return CompanyUpdated(**company_details.dict(), id=company.id, owner=user.id)

    async def delete_company(
        self, user_repo: UserService, credentials: HTTPAuthorizationCredentials
    ) -> HTTPException:
        user = await user_repo.get_current_user(credentials=credentials)
        company = self.db.query(Company).filter_by(owner=user.id).first()
        if not company:
            raise HTTPException(status_code=401, detail="You don't have company yet")
        self.db.delete(company)
        self.db.commit()
        return HTTPException(
            status_code=204, detail=f"Company with id{company.id} deleted"
        )

    async def create_invite(
        self,
        user_repo: UserService,
        user_to_invite_id: int,
        credentials: HTTPAuthorizationCredentials,
    ) -> InviteBase:
        user = await user_repo.get_current_user(credentials=credentials)
        user_to_invite = self.db.query(User).filter_by(id=user_to_invite_id).first()
        company = self.db.query(Company).filter_by(owner=user.id).first()
        invite = (
            self.db.query(Invite)
            .filter_by(company=company.id, user=user_to_invite_id)
            .first()
        )
        if not user_to_invite:
            raise HTTPException(status_code=401, detail="User with id doesn't exist")
        if user_to_invite in company.employees:
            raise HTTPException(status_code=401, detail="User already in company")
        if not company:
            raise HTTPException(status_code=401, detail="You don't have company yet")
        if invite:
            raise HTTPException(status_code=401, detail="User already invited")

        invite = Invite(user=user_to_invite_id, company=company.id)
        self.db.add(invite)
        self.db.commit()
        return InviteBase(id=invite.id, company=invite.company, user=invite.user)

    async def remove_from_company(
        self,
        user_repo: UserService,
        credentials: HTTPAuthorizationCredentials,
        user_to_remove_id: int,
    ) -> HTTPException:
        user = await user_repo.get_current_user(credentials=credentials)
        user_to_remove = self.db.query(User).filter_by(id=user_to_remove_id).first()
        company = self.db.query(Company).filter_by(owner=user.id).first()
        if user_to_remove not in company.employees:
            raise HTTPException(status_code=401, detail="User with id isn't in company")
        if not company:
            raise HTTPException(status_code=401, detail="You don't have company yet")
        company.employees.remove(user_to_remove)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return HTTPException(
            status_code=204,
            detail=f"User with id{user_to_remove_id} removed from company",
        )

    async def add_to_admin(
        self,
        user_repo: UserService,
        credentials: HTTPAuthorizationCredentials,
        user_to_admin_id: int,
    ) -> HTTPException:
        user = await user_repo.get_current_user(credentials=credentials)
        user_to_add = self.db.query(User).filter_by(id=user_to_admin_id).first()
        company = self.db.query(Company).filter_by(owner=user.id).first()

        if user_to_add not in company.employees:
            raise HTTPException(status_code=401, detail="User with id isn't in compony")
        if user_to_add in company.admins:
            raise HTTPException(status_code=401, detail="User is already admin")
        if not company:
            raise HTTPException(status_code=401, detail="You don't have company yet")

        company.admins.append(user_to_add)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return HTTPException(
            status_code=200, detail=f"User with id{user_to_admin_id} added to admins"
        )

    async def remove_from_admin(
        self,
        user_repo: UserService,
        credentials: HTTPAuthorizationCredentials,
        user_to_remove_id: int,
    ) -> HTTPException:
        user = await user_repo.get_current_user(credentials=credentials)
        user_to_remove = self.db.query(User).filter_by(id=user_to_remove_id).first()
        company = self.db.query(Company).filter_by(owner=user.id).first()

        if user_to_remove not in company.admins:
            raise HTTPException(status_code=401, detail="User with id isn't in admins")

        if not company:
            raise HTTPException(status_code=401, detail="You don't have company yet")

        company.admins.remove(user_to_remove)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return HTTPException(
            status_code=204,
            detail=f"User with id {user_to_remove.id} is removed from admins",
        )

    async def get_request_list(
        self,
        user_repo: UserService,
        credentials: HTTPAuthorizationCredentials,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RequestBase]:
        user = await user_repo.get_current_user(credentials=credentials)
        company = self.db.query(Company).filter_by(owner=user.id).first()
        request_list = (
            self.db.query(Request)
            .filter_by(company=company.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            RequestBase(id=request.id, user=request.user_id, company=request.company_id)
            for request in request_list
        ]

    async def accept_request(
        self,
        user_repo: UserService,
        credentials: HTTPAuthorizationCredentials,
        request_id: int,
    ) -> HTTPException:
        owner = await user_repo.get_current_user(credentials=credentials)
        request = self.db.query(Request).filter_by(id=request_id).first()
        company = self.db.query(Company).filter_by(owner=owner.id).first()

        if not request:
            raise HTTPException(status_code=401, detail="Request doesn't exist")

        if request.company != company.id:
            raise HTTPException(
                status_code=401, detail="This is not yours company request"
            )

        user = self.db.query(User).filter_by(id=request.user).first()
        company.employees.append(user)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        request = self.db.query(Request).filter_by(id=request_id).first()
        self.db.delete(request)
        self.db.commit()

        return HTTPException(
            status_code=200, detail=f"Request from user {user.id} is accepted"
        )

    async def disapprove_request(
        self,
        user_repo: UserService,
        credentials: HTTPAuthorizationCredentials,
        request_id: int,
    ) -> HTTPException:

        owner = await user_repo.get_current_user(credentials=credentials)
        request = self.db.query(Request).filter_by(id=request_id).first()
        company = self.db.query(Company).filter_by(owner=owner.id).first()

        if not request:
            raise HTTPException(status_code=401, detail="Request doesn't exist")

        if request.company != company.id:
            raise HTTPException(
                status_code=401, detail="This is not yours company request"
            )

        user = self.db.query(User).filter_by(id=request.user).first()
        request = self.db.query(Request).filter_by(id=request_id).first()
        self.db.delete(request)
        self.db.commit()

        return HTTPException(
            status_code=200, detail=f"Request from user {user.id} is disapproved"
        )


class QuizService:
    def __init__(self, db: Session, credentials: HTTPAuthorizationCredentials):
        self.db = db
        self.user_service = UserService(self.db)
        self.company_service = CompanyService(self.db)
        self.credentials = credentials

    async def check_if_company_exist_and_usr_have_rights(
        self, company: Company
    ) -> None:
        user = await self.user_service.get_current_user(credentials=self.credentials)
        if not company:
            raise HTTPException(
                status_code=401, detail=f"Company with given id doesn't exist"
            )
        if not user.id == company.owner and user.id not in company.admins:
            raise HTTPException(
                status_code=401,
                detail="You don't have rights to add quizes in this company",
            )

    async def check_quiz_exist_in_company(self, quiz_id: int, company_id: int) -> None:
        quiz = self.db.query(Quiz).filter_by(id=quiz_id, company_id=company_id).first()
        if not quiz:
            raise HTTPException(
                status_code=401,
                detail=f"Quiz with id {quiz_id} not found in your company",
            )

    async def add_questions_and_answers_to_quiz(
        self, quiz_info: QuizCreate, quiz: Quiz
    ):
        for question in quiz_info.questions:
            question_to_add = Question(
                question_title=question.question_title, quiz_id=quiz.id
            )
            self.db.add(question_to_add)
            self.db.commit()
            for answer in question.answers:
                answer_to_add = Answer(
                    answer_text=answer.answer_text,
                    is_correct=answer.is_correct,
                    question_id=question_to_add.id,
                )
                self.db.add(answer_to_add)
                self.db.commit()

    async def update_questions_and_answers_in_quiz(
        self, quiz_info: QuizUpdate, quiz: Quiz
    ):
        for question in quiz_info.questions:
            question_to_add = self.db.query(Question).filter_by(quiz=quiz.id).first()
            question_to_add.update(question_title=question.question_title)
            self.db.commit()
            for answer in question.answers:
                answer_to_add = (
                    self.db.query(Answer).filter_by(question=question_to_add.id).first()
                )
                answer_to_add.update(
                    answer_text=answer.answer_text, is_correct=answer.is_correct
                )
                self.db.commit()

    async def create_quiz(
        self,
        quiz_info: QuizCreate,
        company_id: int,
    ) -> QuizList:
        company = await self.company_service.get_company_by_id(id=company_id)
        await self.check_if_company_exist_and_usr_have_rights(company=company)
        quiz = (
            self.db.query(Quiz)
            .filter_by(title=quiz_info.title, company_id=company_id)
            .first()
        )
        if quiz:
            raise HTTPException(
                status_code=401, detail="Quiz with this name already existed"
            )
        quiz = Quiz(
            title=quiz_info.title,
            description=quiz_info.description,
            company_id=company_id,
        )
        self.db.add(quiz)
        self.db.commit()

        await self.add_questions_and_answers_to_quiz(quiz_info=quiz_info, quiz=quiz)

        return QuizList(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            company=quiz.company_id,
        )

    async def update_quiz(
        self,
        quiz_info: QuizUpdate,
        quiz_id: int,
        company_id: int,
    ) -> QuizList:
        company = await self.company_service.get_company_by_id(id=company_id)
        await self.check_if_company_exist_and_usr_have_rights(company=company)

        await self.check_quiz_exist_in_company(quiz_id=quiz_id, company_id=company_id)

        quiz = self.db.query(Quiz).filter_by(id=quiz_id, company_id=company_id).first()
        quiz.update(title=quiz_info.title, description=quiz_info.description)
        self.db.commit()

        await self.update_questions_and_answers_in_quiz(quiz_info=quiz_info, quiz=quiz)

        return QuizList(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            company=quiz.company,
        )

    async def delete_quiz(
        self,
        quiz_id: int,
        company_id: int,
    ) -> HTTPException:
        company = await self.company_service.get_company_by_id(id=company_id)

        await self.check_if_company_exist_and_usr_have_rights(company=company)
        await self.check_quiz_exist_in_company(quiz_id=quiz_id, company_id=company_id)

        quiz = self.db.query(Quiz).filter_by(id=quiz_id, company_id=company_id).first()
        self.db.delete(quiz)
        self.db.commit()

        return HTTPException(status_code=204, detail=f"Quiz deleted")

    async def get_quiz_list(
        self, company_id: int, skip: int = 0, limit: int = 100
    ) -> list[QuizList]:
        quiz_list = (
            self.db.query(Quiz)
            .filter_by(company_id=company_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            QuizList(
                id=quiz.id,
                title=quiz.title,
                description=quiz.description,
                passing_frequency=quiz.passing_frequency,
                company=quiz.company_id,
            )
            for quiz in quiz_list
        ]

    @staticmethod
    async def check_if_quiz_exist(quiz: Quiz) -> None:
        if not quiz:
            raise HTTPException(
                status_code=401,
                detail=f"Quiz with id not found",
            )

    async def get_quiz_info(self, quiz_id: int) -> QuizInfo:
        quiz = self.db.query(Quiz).filter_by(id=quiz_id).first()
        await self.check_if_quiz_exist(quiz=quiz)
        return QuizInfo(id=quiz.id, title=quiz.title, description=quiz.description)

    async def get_quiz_questions(self, quiz_id: int) -> QuizQuestions:
        quiz = self.db.query(Quiz).filter_by(id=quiz_id).first()
        await self.check_if_quiz_exist(quiz=quiz)
        return QuizQuestions(
            id=quiz.id,
            questions=[
                QuestionRead(
                    id=question.id,
                    question_title=question.question_title,
                    answers=[
                        AnswerRead(id=answer.id, answer_text=answer.answer_text)
                        for answer in question.answers
                    ],
                )
                for question in quiz.questions
            ],
        )

    @staticmethod
    async def check_if_all_questions_passed(
        quiz_answers: QuizPass, questions_quantity: int
    ) -> None:
        if len(quiz_answers.answers) < questions_quantity:
            raise HTTPException(
                status_code=401,
                detail="You should give answer for all questions in quiz",
            )

    async def validate_answers(self, quiz: Quiz, answer: QuestionPass) -> None:
        if answer.question_id not in [question.id for question in quiz.questions]:
            raise HTTPException(
                status_code=401, detail="Not valid question id for this quiz"
            )
        answers_in_question = (
            self.db.query(Answer).filter_by(question_id=answer.question_id).all()
        )
        if answer.choosed_answer_id not in [
            answer.id for answer in answers_in_question
        ]:
            raise HTTPException(
                status_code=401, detail="Not valid answer id for question"
            )

    async def update_user_average_result(
        self, user: User, correct_answers: int, questions_quantity: int
    ) -> None:
        user.correct_answers += correct_answers
        user.passed_questions += questions_quantity
        self.db.commit()
        self.db.refresh(user)
        user.average_result = user.correct_answers / user.passed_questions * 100
        self.db.commit()

    @staticmethod
    async def create_result_with_previous(
        previous_result: Result,
        quiz: Quiz,
        user: User,
        correct_answers: int,
        quiz_result: float,
    ) -> Result:
        attempts = previous_result.attempts + 1
        total_correct_answers = previous_result.correct_answers + correct_answers
        average_result = (
            total_correct_answers / (len(quiz.questions) * attempts)
        ) * 100
        result = Result(
            user_id=user.id,
            company_id=quiz.company_id,
            result=quiz_result,
            attempts=attempts,
            correct_answers=total_correct_answers,
            average_result=average_result,
            quiz_id=quiz.id,
        )
        return result

    @staticmethod
    async def create_result_without_previous(
        quiz: Quiz, user: User, correct_answers: int, quiz_result: float
    ) -> Result:
        result = Result(
            user_id=user.id,
            company_id=quiz.company_id,
            result=quiz_result,
            attempts=1,
            correct_answers=correct_answers,
            average_result=quiz_result,
            quiz_id=quiz.id,
        )
        return result

    async def create_quiz_result(
        self, correct_answers: int, questions_quantity: int, user: User, quiz: Quiz
    ) -> Result:

        quiz_result = correct_answers / questions_quantity * 100

        previous_result = (
            self.db.query(Result)
            .filter_by(user_id=user.id, quiz_id=quiz.id)
            .order_by(desc("created_at"))
            .first()
        )
        if previous_result:
            result = await self.create_result_with_previous(
                previous_result=previous_result,
                quiz=quiz,
                user=user,
                correct_answers=correct_answers,
                quiz_result=quiz_result,
            )

        else:
            result = await self.create_result_without_previous(
                quiz=quiz,
                user=user,
                correct_answers=correct_answers,
                quiz_result=quiz_result,
            )
        self.db.add(result)
        self.db.commit()
        await self.update_user_average_result(
            user=user,
            correct_answers=correct_answers,
            questions_quantity=questions_quantity,
        )

        return result

    async def pass_quiz(self, quiz_id: int, quiz_answers: QuizPass) -> ResultBase:
        email = await self.user_service.get_current_user_email(self.credentials)
        user = await self.user_service.get_user_by_email(email=email)
        quiz = self.db.query(Quiz).filter_by(id=quiz_id).first()
        await self.check_if_quiz_exist(quiz=quiz)
        correct_answers = 0
        questions_quantity = len(quiz.questions)

        await self.check_if_all_questions_passed(
            quiz_answers=quiz_answers, questions_quantity=questions_quantity
        )

        for answer in quiz_answers.answers:
            await self.validate_answers(quiz=quiz, answer=answer)

            answer = (
                self.db.query(Answer).filter_by(id=answer.choosed_answer_id).first()
            )
            if answer.is_correct:
                correct_answers += 1
            await redis_db.set(
                f"{user.id}:{answer.question.id}", answer.answer_text, ex=172800
            )

        result = await self.create_quiz_result(
            correct_answers=correct_answers,
            questions_quantity=questions_quantity,
            user=user,
            quiz=quiz,
        )

        return ResultBase(
            id=result.id,
            user=result.user_id,
            company=result.company_id,
            result=result.result,
            quiz_id=result.quiz_id,
            attempts=result.attempts,
            average_result=result.average_result,
            created_at=result.created_at,
        )

    async def get_answer_from_redis(self, question_id: int) -> QuestionAnswerRead:
        user = await self.user_service.get_current_user(self.credentials)
        key = f"{str(user.id)}:{str(question_id)}"
        answer = await redis_db.get(key)
        if not answer:
            raise HTTPException(
                status_code=401, detail="You didn't ask for that question yet"
            )
        return QuestionAnswerRead(id=question_id, answer=answer)
