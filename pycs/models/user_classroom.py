from pycs.extensions import db
from sqlalchemy import Column, ForeignKey


user_classroom = db.Table(
    "user_classroom",
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("classroom_id", ForeignKey("classroom.id"), primary_key=True),
)
