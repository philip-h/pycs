from pycs.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Classroom(db.Model):
    """Classroom table"""

    __tablename__ = "classroom"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_code: Mapped[str]
    year: Mapped[int]
    sem: Mapped[int]
    teacher_id: Mapped[int]
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="classroom")
    users: Mapped[list["User"]] = relationship(
        secondary="user_classroom", back_populates="classes"
    )

    def __repr__(self) -> str:
        return f"<Classroom {self.id=} {self.course_code=} >"
