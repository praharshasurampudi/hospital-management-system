"""
Authentication blueprint (login / logout / patient registration).
Assumes LoginManager is configured in app.py and templates:
- templates/auth_login.html
- templates/auth_register.html
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Patient, Role
from forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Redirect already-logged-in users to their dashboard
    if current_user.is_authenticated:
        if current_user.role == Role.ADMIN:
            return redirect(url_for("admin.dashboard"))
        if current_user.role == Role.DOCTOR:
            return redirect(url_for("doctor.dashboard"))
        return redirect(url_for("patient.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            # Redirect by role
            if user.role == Role.ADMIN:
                return redirect(url_for("admin.dashboard"))
            if user.role == Role.DOCTOR:
                return redirect(url_for("doctor.dashboard"))
            return redirect(url_for("patient.dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("auth_login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Patients can self-register. Doctors are created by admin.
    if current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("auth.register"))

        user = User(email=email, name=form.name.data.strip(), role=Role.PATIENT)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        patient = Patient(
            user_id=user.id,
            phone=form.phone.data,
            age=form.age.data,
            gender=form.gender.data,
            address=form.address.data,
        )
        db.session.add(patient)
        db.session.commit()

        flash("Account created. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth_register.html", form=form)
