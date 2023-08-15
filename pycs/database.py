"""
author: @philiph
A database configuration module
"""

import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import scoped_session, sessionmaker

database_env = os.getenv("DATABASE")
database_path = database_env if database_env is not None else "pycs.db"

engine = create_engine(f"sqlite:///{database_path}")
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


def init_db():
    import pycs.models

    # Create all of the tables
    pycs.models.Base.metadata.create_all(bind=engine)

def clear_db():
    import pycs.models

    # Create all of the tables
    pycs.models.Base.metadata.drop_all(bind=engine)