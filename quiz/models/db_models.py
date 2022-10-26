from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression

from core.database import Base

company_user = Table(
    "company_user",
    Base.metadata,
    Column("company_id", Integer(), ForeignKey("companies.id"), primary_key=True),
    Column("user_id", Integer(), ForeignKey("users.id"), primary_key=True),
)

company_admins = Table(
    "company_admins",
    Base.metadata,
    Column("company_id", Integer(), ForeignKey("companies.id"), primary_key=True),
    Column("user_id", Integer(), ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    username = Column(String(64), unique=True)
    email = Column(String(64), unique=True)
    password = Column(String(64))
    companies = relationship(
        "Company", secondary=company_user, back_populates="employees"
    )
    is_admin_in = relationship(
        "Company", secondary=company_admins, back_populates="admins"
    )

    def update(self, username: str, password: str):
        self.username = username
        self.password = password


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String(64), unique=True)
    description = Column(String(255))
    visibility = Column(
        Boolean,
        unique=False,
        server_default=expression.true(),
        nullable=False,
        default=True,
    )
    owner = Column(Integer, ForeignKey("users.id"))
    employees = relationship("User", secondary=company_user, back_populates="companies")
    admins = relationship(
        "User", secondary=company_admins, back_populates="is_admin_in"
    )

    def update(self, name: str, description: str, visibility: bool):
        self.name = name
        self.description = description
        self.visibility = visibility


class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    company = Column(Integer, ForeignKey("companies.id"))
    user = Column(Integer, ForeignKey("users.id"))


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    company = Column(Integer, ForeignKey("companies.id"))
    user = Column(Integer, ForeignKey("users.id"))


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    title = Column(String(64), nullable=False)
    description = Column(String(255), nullable=False)
    passing_frequency = Column(Integer)
    company = Column(Integer, ForeignKey("companies.id"))

    def update(self, title: str, description: str):
        self.title = title
        self.description = description


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    question_title = Column(String(255), nullable=False)
    quiz = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"))

    def update(self, question_title: str):
        self.question_title = question_title


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    answer_text = Column(String(255), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    question = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))

    def update(self, answer_text: str, is_correct: bool):
        self.answer_text = answer_text
        self.is_correct = is_correct


users = User.__table__
companies = Company.__table__
invites = Invite.__table__
requests = Request.__table__
