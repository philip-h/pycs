from pycs.extensions import db
from pycs.models import Assignment, UserAssignment
from datetime import datetime

from sqlalchemy.exc import IntegrityError


def create_assignment(new_ass):
    """Create a new assignment"""
    db.session.add(new_ass)
    db.session.commit()


def get_all_assignments():
    """Get all assignments"""
    return db.session.execute(
        db.select(Assignment).order_by(db.desc(Assignment.id))
    ).scalars().all()


def get_assignment_by_id(a_id: int):
    """Get an assignment by it's id"""
    return db.session.execute(
        db.select(Assignment).where(Assignment.id == a_id)
    ).scalar_one_or_none()


def get_class_assignments_of_user(class_id: int, user_id: int):
    """Get all assignments, and all the scores of all the assignments.
    If an assignment has not been submitted, the UserAssignment is None"""
    assignments_scores = db.session.execute(
        db.select(Assignment, UserAssignment)
        .outerjoin(
            UserAssignment,
            (UserAssignment.assignment_id == Assignment.id)
            & (UserAssignment.user_id == user_id),
        )
        .where(Assignment.class_id == class_id)
        .order_by(db.desc(Assignment.id))
    )
    return assignments_scores


def score_ass(user, assignment, score, comments):
    """Add a new User_Assignment association, thus grading the student's assignment"""
    user_assignment = UserAssignment(score=score, comments=comments)
    assignment.user_associations.append(user_assignment)
    user.assignment_associations.append(user_assignment)
    try:
        db.session.commit()
    except IntegrityError:
        pass


def update_ass_score(user_assignment, score, comments):
    """Update the score and comments on a particular assignment"""
    user_assignment.score = score
    user_assignment.comments = comments
    db.session.commit()


def assignments_scores_to_dict(assignments_scores):
    assignments = {}
    for a, ua in assignments_scores:
        if a.unit_name not in assignments:
            assignments[a.unit_name] = []

        if ua is None:
            if a.due_date < datetime.today():
                score = 0
            else:
                score = None
        else:
            score = ua.score

        # Don't send invisible assignments
        if a.visible:
            assignments[a.unit_name].append(
                {
                    "id": a.id,
                    "name": a.name,
                    "due_date": a.due_date,
                    "score": score,
                    "total": a.total_points,
                    "class_id": a.class_id,
                }
            )

    return assignments


def calc_overall_avg(assignments_scores) -> float:
    """Calculate the student's average.
    Don't include missing assignments if we are not past the due date
    """
    marks, weights = [], []
    for a, ua in assignments_scores:
        if ua:
            marks.append(ua.score / a.total_points)
            weights.append(a.weight)
        elif a.due_date < datetime.today():
            marks.append(0)
            weights.append(a.weight)

    if len(marks) == 0:
        avg = 0
    else:
        avg = round(
            (sum(m * w for m, w in zip(marks, weights)) / sum(weights)) * 100, 2
        )

    return avg
