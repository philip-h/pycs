import csv
from datetime import datetime
import io
import os
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    send_file,
    url_for,
)
import markdown
from werkzeug.utils import secure_filename

from pycs.controllers import user as user_controller
from pycs.controllers import assignment as ass_controller
from pycs.controllers import classroom as class_controller
from pycs.controllers import commit_change
from pycs.forms import AssignmentForm, ClassroomForm, UploadMarksForm
from pycs.models.assignment import Assignment
from pycs.models.classroom import Classroom

from . import teacher_login_required

bp = Blueprint("teacher", __name__)


@bp.get("/")
@teacher_login_required
def index():
    return render_template("teacher/home.html")


###############################################################################
####################           STUDENTS DASHBORD           ####################
###############################################################################


@bp.get("/students")
@teacher_login_required
def view_students():
    students = user_controller.get_all_students()
    return render_template("teacher/view_students.html", students=students)


@bp.get("/students/<int:student_number>/course/<int:class_id>")
@teacher_login_required
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
@teacher_login_required
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

    instructions = markdown.markdown(
        assignment.instructions, extensions=["fenced_code"]
    )
    return render_template(
        "teacher/view_student_assignment.html",
        assignment=assignment,
        instructions=instructions,
        data=user_assignment,
        user=user,
        form=None,
    )


###############################################################################
####################      ASSIGNMENTS DASHBORD             ####################
###############################################################################


@bp.get("/assignments")
@teacher_login_required
def view_assignments():
    assignments = ass_controller.get_all_assignments()
    return render_template("teacher/view_assignments.html", assignments=assignments)


@bp.route("/assignments/new", methods=["GET", "POST"])
@bp.route("/assignments/<int:a_id>", methods=["GET", "POST"])
@teacher_login_required
def view_edit_assignment(a_id: int | None = None):
    if a_id is not None:
        assignment = ass_controller.get_assignment_by_id(a_id)
    else:
        assignment = Assignment()

    form = AssignmentForm(obj=assignment)

    if form.validate_on_submit():
        # Commit changes to database
        form.populate_obj(assignment)
        if a_id is not None:
            commit_change()
        else:
            ass_controller.create_assignment(assignment)

        # Handle upload of pytest/junit files (optional)
        if "unit_test_upload" in form:
            uploaded_file = form.unit_test_upload.data
            filename = secure_filename(uploaded_file.filename)
            _, ext = os.path.splitext(filename)
            upload_error = None
            if ext == ".py":
                pytest_upload_dir = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], "tests"
                )
                if not os.path.exists(pytest_upload_dir):
                    os.makedirs(pytest_upload_dir)

                upload_path = os.path.join(pytest_upload_dir, filename)

                try:
                    uploaded_file.save(pytest_upload_dir)
                except OSError:
                    upload_error = f"Could not upload file {filename}: OSError"
            elif ext == ".java":
                junit_upload_dir = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], "tests-java"
                )
                if not os.path.exists(junit_upload_dir):
                    os.makedirs(junit_upload_dir)

                upload_path = os.path.join(junit_upload_dir, filename)

                try:
                    uploaded_file.save(upload_path)
                except OSError:
                    upload_error = f"Could not upload file {filename}: OSError"
            else:
                upload_error = f"Could not upload file, not .py or .java"

            if upload_error is not None:
                flash(upload_error)
        return redirect(url_for(".view_assignments"))

    return render_template("teacher/assignment_form.html", form=form)


###############################################################################
####################        CLASSES DASHBORD               ####################
###############################################################################


@bp.get("/classes")
@teacher_login_required
def view_classes():
    classrooms = class_controller.get_all_classes()
    current_app.logger.info("Classrooms :D" + str(len(classrooms)))
    return render_template("teacher/view_classes.html", classrooms=classrooms)


@bp.route("/classes/new", methods=["GET", "POST"])
@bp.route("/classes/<int:class_id>", methods=["GET", "POST"])
@teacher_login_required
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

    return render_template("teacher/class_form.html", form=form)


###############################################################################
####################        Mark Import / Export           ####################
###############################################################################


@bp.get("/import")
@teacher_login_required
def import_marks():
    assignments = ass_controller.get_all_assignments()
    return render_template(
        "teacher/view_assignments_for_import.html", assignments=assignments
    )


@bp.route("/import/<int:a_id>", methods=["GET", "POST"])
def assignment_import(a_id):
    form = UploadMarksForm()
    if form.validate_on_submit():
        grades = csv.DictReader(io.StringIO(form.marks.data.read().decode("utf-8")))
        count = ass_controller.upload_assignment_grades(a_id, grades)
        if count != 0:
            flash(f"{count} grades uploaded", "info")
        else:
            flash("There was an issue uploading grades", "error")
        return redirect(url_for(".import_marks"))

    return render_template("teacher/import_assignment.html", form=form)


def _export_marks(class_id: int) -> (str, str):
    # Create a file
    classroom = class_controller.get_classroom_by_id(class_id)
    # Header row
    header = ",".join(
        ["Name", "Student Number", "Average"]
        + [
            a.name
            for a in sorted(classroom.assignments, key=lambda x: x.id, reverse=True)
        ]
    )
    body = ""

    for user in classroom.users:
        assignment_scores = ass_controller.get_class_assignments_of_user(
            class_id, user.id
        ).fetchall()
        avg = ass_controller.calc_overall_avg(assignment_scores)
        body_line = ",".join(
            [user.first_name, user.student_number, str(avg)]
            + [str(ua.score) if ua else "0" for _, ua in assignment_scores]
        )
        # body_line = ",".join([user.first_name] + [str(ua.score) for ua in sorted(user.assignment_associations, key=lambda x: x.assignment_id)])
        body += body_line + "\n"

    file_name = Path(f"marks_{classroom.course_code}_{datetime.today()}.csv")
    file_directory = os.path.join(current_app.config["EXPORTED_FILES"])
    with open(file_directory / file_name, "w") as f_out:
        f_out.write(f"{header}\n{body}")

    return file_directory, file_name


@bp.get("/export3u")
@teacher_login_required
def export_3u_marks():
    file_directory, file_name = _export_marks(class_id=1)
    data = io.BytesIO()
    with open(file_directory / file_name, mode="rb") as f_out:
        data.write(f_out.read())
    data.seek(0)
    os.remove(file_directory / file_name)
    return send_file(
        data, mimetype="text/csv", download_name=str(file_name), as_attachment=True
    )


@bp.get("/export4u")
@teacher_login_required
def export_4u_marks():
    file_directory, file_name = _export_marks(class_id=2)
    data = io.BytesIO()
    with open(file_directory / file_name, mode="rb") as f_out:
        data.write(f_out.read())
    data.seek(0)
    os.remove(file_directory / file_name)
    return send_file(
        data, mimetype="text/csv", download_name=str(file_name), as_attachment=True
    )
