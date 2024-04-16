from datetime import datetime

from flask import flash
from sqlalchemy.exc import IntegrityError

from pycs.extensions import db
from pycs.models import Assignment, User, UserAssignment, Weighting


def create_assignment(new_ass):
    """Create a new assignment"""
    db.session.add(new_ass)
    db.session.commit()


def get_all_assignments():
    """Get all assignments"""
    return (
        db.session.execute(db.select(Assignment).order_by(db.desc(Assignment.id)))
        .scalars()
        .all()
    )


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
    user_assignment = UserAssignment(user_id=user.id, score=score, comments=comments)
    db.session.commit()
    assignment.user_associations.append(user_assignment)
    user.assignment_associations.append(user_assignment)
    db.session.commit()


def update_ass_score(user_assignment, score, comments):
    """Update the score and comments on a particular assignment"""
    user_assignment.score = score
    user_assignment.comments = comments
    db.session.commit()


def upload_assignment_grades(a_id, grades) -> int:
    """Upload grades from a csv file

    Returns:
        The number of grades successfully input
    """

    count = 0
    ass = get_assignment_by_id(a_id)
    if ass is None:
        return count

    for grade_item in grades:
        if "Score" not in grade_item or "Email" not in grade_item:
            flash("CSV must contain Email and Score headings", "error")
            return 0
        # D2L has student number under Email column
        student_number = grade_item["Email"]
        user = db.session.execute(
            db.select(User).where(User.student_number == student_number)
        ).scalar_one_or_none()
        if user is None:
            flash(f"Could not upload marks for {grade_item['First Name']}", "error")
            continue
        # Check to see if a score exists
        ua = db.session.execute(
            db.select(UserAssignment).where(
                UserAssignment.user_id == user.id, UserAssignment.assignment_id == a_id
            )
        ).scalar_one_or_none()
        score = float(grade_item["Score"]) if grade_item["Score"].strip() != "" else 0
        if ua is None:
            score_ass(user, ass, score, "Uploaded from D2L")
        else:
            update_ass_score(ua, score, "Uploaded from D2L")
        count += 1
    return count


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
                    "total_points": a.total_points,
                    "total": a.total_points,
                    "class_id": a.class_id,
                }
            )

    return assignments


def calc_overall_avg(assignments_scores) -> float:
    """Calculate the student's average.
    Don't include missing assignments if we are not past the due date
    """
    # Get weightings from database
    weightings = db.session.execute(db.select(Weighting)).scalars()
    marks = {w.weight: [] for w in weightings}

    for a, ua in assignments_scores:
        if ua:
            marks[a.weighting.weight].append(ua.score / a.total_points)
        elif a.due_date < datetime.today():
            marks[a.weighting.weight].append(0)

    def _safe_len(lst: list) -> int:
        s = len(lst)
        return 1 if s == 0 else s

    avg = round(sum((sum(marks[w]) / _safe_len(marks[w]))*w for w in marks), 2)


    return avg
