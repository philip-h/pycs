"""
author: @philiph
Database models for Pycs using Flask-SQLAlchemy
"""

from datetime import datetime
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class UserAssignment(Base):
    """User-Assignment association table"""

    __tablename__ = "user_assignment"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignment.id"), primary_key=True
    )
    score: Mapped[int]
    comments: Mapped[str]

    user: Mapped["User"] = relationship(back_populates="assignment_associations")
    assignment: Mapped["Assignment"] = relationship(back_populates="user_associations")

    def __repr__(self):
        return f"<UserAssignment {self.user_id=} {self.assignment_id=}>"



class User(Base, UserMixin):
    """User table"""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_number: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str]
    password_hash: Mapped[str]
    role: Mapped[str] = mapped_column(default="Student")
    assignment_associations: Mapped[list["UserAssignment"]] = relationship(
        back_populates="user"
    )
    assignments: Mapped[list["Assignment"]] = association_proxy(
        "assignment_associations", "assignment"
    )

    def __init__(self, student_number, first_name, password, role="Student"):
        self.student_number = student_number
        self.first_name = first_name
        self.password_hash = generate_password_hash(password)
        self.role = role

    def __repr__(self):
        return f"<User {self.first_name=} {self.student_number=}>"

    @hybrid_property
    def password(self):
        """Password property to hide password hashing"""
        return self.password_hash

    @password.setter
    def password(self, new_password):
        """Password setter to hide password hashing"""
        self.password_hash = generate_password_hash(new_password)

    def verify_password(self, password):
        """Ensure hashed password in database matches given password"""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Mainly used for the Flask-Admin package"""
        return self.role == "Teacher"


class Assignment(Base):
    """Assignment table"""

    __tablename__ = "assignment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    total_points: Mapped[int] = mapped_column(default=4)
    required_filename: Mapped[str]
    due_date: Mapped[datetime]
    visible: Mapped[bool]

    user_associations: Mapped[list["UserAssignment"]] = relationship(
        back_populates="assignment"
    )
    users: Mapped[list["User"]] = association_proxy("user_associations", "user")

    def __repr__(self):
        return f"<Assignment {self.name=} {self.total_points=}>"

    def verify_filename(self, filename):
        return filename == self.required_filename
