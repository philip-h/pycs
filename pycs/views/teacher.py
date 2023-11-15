from datetime import datetime
from os import walk
from flask import Blueprint, current_app, redirect, render_template, url_for
from pycs.controllers import user as user_controller
from pycs.controllers import assignment as ass_controller
from pycs.controllers import classroom as class_controller
from pycs.controllers import commit_change
from pycs.forms import AssignmentForm, ClassroomForm
from pycs.models.assignment import Assignment
from pycs.models.classroom import Classroom

from . import login_required

bp = Blueprint("teacher", __name__)


@bp.get("/")
@login_required
def index():
    return render_template("teacher/home.html")


###############################################################################
####################           STUDENTS DASHBORD           ####################
###############################################################################


@bp.get("/students")
@login_required
def view_students():
    students = user_controller.get_all_students()
    return render_template("teacher/view_students.html", students=students)


@bp.get("/students/<int:student_number>/course/<int:class_id>")
@login_required
def view_student(student_number: int, class_id: int):
    user = user_controller.get_user_by_student_number(student_number)

    assignments_scores = ass_controller.get_class_assignments_of_user(class_id, user.id)

    # Needed so that the generator doesn't run out the second time I use it
    assignments_scores = list(assignments_scores)
    assignments = ass_controller.assignments_scores_to_dict(assignments_scores)
    student_avg = ass_controller.calc_overall_avg(assignments_scores)

    return render_template(
        "teacher/view_student.html",
        assignments=assignments,
        student_avg=student_avg,
        user=user,
        class_id=class_id,
        today=datetime.today(),
    )


@bp.get("/students/<int:student_number>/course/<int:class_id>/assignment/<int:a_id>")
@login_required
def view_student_assignment(student_number: int, class_id: int, a_id: int):
    user = user_controller.get_user_by_student_number(student_number)
    user_assignment = next(
        (ua for ua in user.assignment_associations if ua.assignment_id == a_id),
        None,
    )

    assignment = (
        ass_controller.get_assignment_by_id(a_id)
        if user_assignment is None
        else user_assignment.assignment
    )

    return render_template(
        "teacher/view_student_assignment.html",
        assignment=assignment,
        data=user_assignment,
    )


###############################################################################
####################      ASSIGNMENTS DASHBORD             ####################
###############################################################################


@bp.get("/assignments")
@login_required
def view_assignments():
    assignments = ass_controller.get_all_assignments()
    return render_template("teacher/view_assignments.html", assignments=assignments)


@bp.route("/assignments/new", methods=["GET", "POST"])
@bp.route("/assignments/<int:a_id>", methods=["GET", "POST"])
@login_required
def view_edit_assignment(a_id: int | None = None):
    if a_id is not None:
        assignment = ass_controller.get_assignment_by_id(a_id)
    else:
        assignment = Assignment()

    form = AssignmentForm(obj=assignment)

    if form.validate_on_submit():
        form.populate_obj(assignment)
        if a_id is not None:
            commit_change()
        else:
            ass_controller.create_assignment(assignment)

        return redirect(url_for(".view_assignments"))

    return render_template("teacher/view_assignment.html", form=form)


###############################################################################
####################        CLASSES DASHBORD               ####################
###############################################################################


@bp.get("/classes")
@login_required
def view_classes():
    classrooms = class_controller.get_all_classes()
    current_app.logger.info("Classrooms :D" + str(len(classrooms)))
    return render_template("teacher/view_classes.html", classrooms=classrooms)


@bp.route("/classes/new", methods=["GET", "POST"])
@bp.route("/classes/<int:class_id>", methods=["GET", "POST"])
@login_required
def view_edit_classes(class_id: int | None = None):
    if class_id is not None:
        classroom = class_controller.get_classroom_by_id(class_id)
    else:
        classroom = Classroom()

    form = ClassroomForm(obj=classroom)

    if form.validate_on_submit():
        form.populate_obj(classroom)
        if class_id is not None:
            commit_change()
        else:
            class_controller.create_class(classroom)

        return redirect(url_for(".view_classes"))

    return render_template("teacher/view_class.html", form=form)
