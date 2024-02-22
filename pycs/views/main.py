from datetime import datetime
from http import HTTPStatus
import os
from pathlib import Path

from flask import Blueprint, current_app, redirect, render_template, request, url_for
from flask_login import current_user
import markdown
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from pycs.controllers import assignment as ass_controller
from pycs.forms import UploadCodeForm
from pycs.grader import GradingStrategy, ICS3UGrader, ICS4UGrader

from . import login_required

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    """The main page of the application"""

    # Authentication required for this route!
    # Stated explicitly here because @login_required always
    # redirects to index
    if not current_user.is_authenticated:
        return render_template("landing.html")

    if len(current_user.classes) == 1:
        class_id = current_user.classes[0].id
        return redirect(url_for(".student_home", class_id=class_id))

    return render_template("classes.html")


@bp.get("/app/<int:class_id>")
@login_required
def student_home(class_id: int):
    if not current_user.is_authenticated:
        return redirect(url_for(".index"))

    assignments_scores = ass_controller.get_class_assignments_of_user(
        class_id, current_user.id
    ).fetchall()

    assignments = ass_controller.assignments_scores_to_dict(assignments_scores)
    student_avg = ass_controller.calc_overall_avg(assignments_scores)

    return render_template(
        "student_home.html",
        assignments=assignments,
        student_avg=student_avg,
        today=datetime.today(),
    )


@bp.route("/app/<int:class_id>/assignment/<int:a_id>", methods=["GET", "POST"])
@login_required
def student_assignment(class_id: int, a_id: int):
    user_assignment = next(
        (ua for ua in current_user.assignment_associations if ua.assignment_id == a_id),
        None,
    )

    assignment = (
        ass_controller.get_assignment_by_id(a_id)
        if user_assignment is None
        else user_assignment.assignment
    )

    # If we can't find the assignment for whatever reason...
    if assignment is None:
        abort(HTTPStatus.NOT_FOUND)

    # SQLite only really does incremental primary keys.
    # This bit of code stopes snoopy students from checking
    # assignments by increasing the id in the url
    # that I've created and are not supposed to be viseble yet.
    if not assignment.visible and not current_user.is_admin:
        abort(HTTPStatus.NOT_FOUND)

    form = None
    if assignment.submission_required:
        form = UploadCodeForm()

        if form.validate_on_submit():
            # Make student directory if it dne
            student_dir = os.path.join(
                current_app.config["UPLOAD_FOLDER"], f"{current_user.student_number}"
            )
            if not os.path.exists(student_dir):
                os.makedirs(student_dir)

            uploaded_file = form.code.data
            filename = secure_filename(uploaded_file.filename)
            if assignment.verify_filename(filename):
                upload_path = os.path.join(
                    student_dir,
                    f"{filename}",
                )

                # Save the code in the upload path
                uploaded_file.save(upload_path)

                # Score the user's submission
                grader: GradingStrategy = (
                    ICS3UGrader(Path(upload_path))
                    if class_id == 1
                    else ICS4UGrader(Path(upload_path))
                )
                try:
                    score, comments = grader.grade_student()
                except FileNotFoundError:
                    score, comments = (
                        0,
                        f"Tell Mr. Habib  that he forgot to upload the test file to assignment: {assignment.name}",
                    )

                # Has the user already submitted? If so, we are just updating the score
                if user_assignment is not None:
                    ass_controller.update_ass_score(user_assignment, score, comments)
                else:
                    ass_controller.score_ass(current_user, assignment, score, comments)

                return redirect(request.url)
            else:
                form.code.errors.append(
                    f"Uploaded file must be named {assignment.required_filename}. Yours is {filename}"
                )

    instructions = markdown.markdown(
        assignment.instructions, extensions=["fenced_code", "tables", "attr_list"]
    )
    return render_template(
        "view_assignment.html",
        assignment=assignment,
        instructions=instructions,
        data=user_assignment,
        form=form,
    )
