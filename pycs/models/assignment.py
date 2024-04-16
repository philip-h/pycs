from datetime import datetime

from pycs.extensions import db
from sqlalchemy import ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Assignment(db.Model):
    """Assignment table"""

    __tablename__ = "assignment"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    instructions: Mapped[str]
    total_points: Mapped[int] = mapped_column(default=4)
    submission_required: Mapped[bool]
    required_filename: Mapped[str] = mapped_column(nullable=True)
    due_date: Mapped[datetime]
    visible: Mapped[bool]
    unit_name: Mapped[str]
    weight: Mapped[int] = mapped_column(ForeignKey("weighting.id"))
    class_id: Mapped[int] = mapped_column(ForeignKey("classroom.id"))

    weighting: Mapped["Weighting"] = relationship()
    classroom: Mapped["Classroom"] = relationship(back_populates="assignments")
    user_associations: Mapped[list["UserAssignment"]] = relationship(
        back_populates="assignment"
    )
    users: Mapped[list["User"]] = association_proxy("user_associations", "user")

    def __repr__(self):
        return f"<Assignment {self.name=} {self.total_points=}>"

    def verify_filename(self, filename):
        return filename == self.required_filename
