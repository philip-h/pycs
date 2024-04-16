from pycs.extensions import db
from sqlalchemy.orm import Mapped, mapped_column


class Weighting(db.Model):
    """Weighting table"""

    __tablename__ = "weighting"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    weight: Mapped[int]

    def __repr__(self) -> str:
        return f"<Weighting {self.id=} {self.name=} >"
