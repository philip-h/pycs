from werkzeug.security import check_password_hash, generate_password_hash

from pycs.exc import JoinCodeInvalidException

from pycs.extensions import db
from pycs.models import Classroom, User


def get_all_users():
    return db.session.execute(db.select(User).order_by(User.first_name)).scalars().all()

def get_all_students():
    return db.session.execute(db.select(User).where(User.role == "Student").order_by(User.first_name)).scalars().all()


def create_student(*, student_number, first_name, password, join_code):
    """Create a new student in the database.

    Raises:
        JoinCodeInvalidException
        sqlalchemy.exc.IntegrityError
    """

    new_user = User(
        student_number=student_number,
        first_name=first_name,
        password_hash=generate_password_hash(password),
        role="Student",
    )
    the_class = db.session.execute(db.select(Classroom).where(Classroom.join_code == join_code)).scalar_one_or_none() 
    if the_class is None:
        raise JoinCodeInvalidException(f"Invalid join code: {join_code}")

    new_user.classes.append(the_class)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def get_user_by_student_number(student_number):
    return db.session.execute(
        db.select(User).where(User.student_number == student_number)
    ).scalar_one_or_none()


def verify_password(user_password_hash, form_password):
    return check_password_hash(user_password_hash, form_password)


def change_user_password(user, current_pass, new_pass):
    if not verify_password(user.password_hash, current_pass):
        return "Current password does not match password in database."

    if verify_password(user.password_hash, new_pass):
        return "New password cannot mactch password in database."

    user.password_hash = generate_password_hash(new_pass)
    db.session.commit()
    return None
