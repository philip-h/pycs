from pycs.extensions import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class UserAssignment(db.Model):
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
