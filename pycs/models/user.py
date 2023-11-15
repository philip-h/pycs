from flask_login import UserMixin
from pycs.extensions import db
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(db.Model, UserMixin):
    """User table"""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_number: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str]
    password_hash: Mapped[str]
    role: Mapped[str]

    assignment_associations: Mapped[list["UserAssignment"]] = relationship(
        back_populates="user"
    )
    assignments: Mapped[list["Assignment"]] = association_proxy(
        "assignment_associations", "assignment"
    )

    classes: Mapped[list["Classroom"]] = relationship(
        secondary="user_classroom", back_populates="users"
    )


    def __repr__(self):
        return f"<User {self.first_name=} {self.student_number=}>"

    @property
    def is_admin(self):
        """Mainly used for the Flask-Admin package"""
        return self.role == "Teacher"
