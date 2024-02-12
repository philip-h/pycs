import uuid

from pycs.extensions import db
from pycs.models import Classroom

def create_class(classroom):
    """Create a class"""
    
    join_codes_in_db = db.session.execute(db.select(Classroom.join_code)).scalars().all()
    # Create a unique class code
    new_join_code = str(uuid.uuid4())[:5].upper()
    while new_join_code in join_codes_in_db:
        new_join_code = str(uuid.uuid4())[:5].upper()


    classroom.join_code = new_join_code
    db.session.add(classroom)
    db.session.commit()


def get_all_classes():
    """Get all the classes"""
    return db.session.execute(db.select(Classroom)).scalars().all()


def get_classroom_by_id(class_id):
    """Get a classroom by it's id"""
    return db.session.execute(
        db.select(Classroom).where(Classroom.id == class_id)
    ).scalar_one_or_none()
