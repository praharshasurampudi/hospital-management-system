# hms/admin.py (only the dashboard portion changed – you can replace the whole file if you prefer)

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date

from models import db, User, Doctor, Patient, Appointment, Role
from forms import DoctorForm

admin_bp = Blueprint('admin', __name__, template_folder='templates/admin')


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            flash("Admin access required", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)

    return wrapper


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Admin dashboard with optional search.
    Query string:
      ?q=search-term
    The search checks:
      - Doctors: user.name, specialization, user.email
      - Patients: user.name, patient.phone, user.email
      - Appointments: patient name, doctor name, date (exact match YYYY-MM-DD)
    If no q provided, returns unfiltered lists (paged/limited).
    """
    q = request.args.get('q', '').strip()
    # Base counts
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()

    # Default lists (unfiltered)
    doctors = Doctor.query.join(User).order_by(User.name).all()
    patients = Patient.query.join(User).order_by(User.name).all()
    upcoming = (
        Appointment.query.filter(Appointment.date >= date.today())
        .order_by(Appointment.date, Appointment.time)
        .limit(20)
        .all()
    )

    # If search query provided, filter results
    if q:
        key = f"%{q}%"
        # Doctors: name, specialization, email
        doctors = (
            Doctor.query.join(User)
            .filter(
                (User.name.ilike(key))
                | (Doctor.specialization.ilike(key))
                | (User.email.ilike(key))
            )
            .order_by(User.name)
            .all()
        )

        # Patients: name, phone, email
        patients = (
            Patient.query.join(User)
            .filter(
                (User.name.ilike(key))
                | (Patient.phone.ilike(key))
                | (User.email.ilike(key))
            )
            .order_by(User.name)
            .all()
        )

        # Appointments: search in patient name OR doctor name OR date (exact)
        # For date, if the q looks like YYYY-MM-DD we match on date
        appt_query = Appointment.query.join(Patient).join(Doctor).join(User, Patient.user)
        appt_filters = (
            (Patient.user.has(User.name.ilike(key))) |
            (Doctor.user.has(User.name.ilike(key)))
        )
        # Add email/phone search in appointments (patient)
        appt_filters = appt_filters | (Patient.user.has(User.email.ilike(key)))
        # If query matches a date format, also try matching Appointment.date
        try:
            # quick parse for exact date match: accept YYYY-MM-DD
            from datetime import datetime as _dt
            parsed = _dt.strptime(q, "%Y-%m-%d").date()
            appt_filters = appt_filters | (Appointment.date == parsed)
        except Exception:
            pass

        appointments = appt_query.filter(appt_filters).order_by(Appointment.date.desc(), Appointment.time.desc()).limit(200).all()
    else:
        appointments = (
            Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc())
            .limit(200)
            .all()
        )

    return render_template(
        'admin/dashboard.html',
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        doctors=doctors,
        patients=patients,
        upcoming=upcoming,
        appointments=appointments,
        q=q,
    )


@admin_bp.route('/doctors/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    form = DoctorForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "warning")
            return redirect(url_for('admin.add_doctor'))

        # Create doctor user account
        user = User(
            email=email,
            name=form.name.data.strip(),
            role=Role.DOCTOR,
        )

        # Use provided password if given, otherwise fallback to default.
        pwd = form.password.data.strip() if form.password.data else "doctor123"
        user.set_password(pwd)

        db.session.add(user)
        db.session.commit()

        # Create doctor profile
        doc = Doctor(
            user_id=user.id,
            specialization=form.specialization.data.strip(),
            bio=form.bio.data.strip() if form.bio.data else None,
        )
        db.session.add(doc)
        db.session.commit()

        flash(f"Doctor added successfully (login: {email} / password: {pwd})", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template("admin/add_doctor.html", form=form)


@admin_bp.route('/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(doctor_id):
    doc = Doctor.query.get_or_404(doctor_id)
    form = DoctorForm()

    if request.method == "GET":
        form.name.data = doc.user.name
        form.email.data = doc.user.email
        form.specialization.data = doc.specialization
        form.bio.data = doc.bio
        # We do NOT pre-fill password (never show existing password)

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        existing = User.query.filter_by(email=email).first()

        # Prevent using email of another user
        if existing and existing.id != doc.user.id:
            flash("Email already in use by another doctor!", "warning")
            return redirect(url_for("admin.edit_doctor", doctor_id=doctor_id))

        # Update fields
        doc.user.name = form.name.data.strip()
        doc.user.email = email
        doc.specialization = form.specialization.data.strip()
        doc.bio = form.bio.data.strip() if form.bio.data else None

        # If admin provided a new password, set it (otherwise leave unchanged)
        if form.password.data:
            new_pwd = form.password.data.strip()
            doc.user.set_password(new_pwd)

        db.session.commit()
        flash("Doctor details updated successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_doctor.html", form=form)


@admin_bp.route('/doctors/<int:doctor_id>/delete')
@login_required
@admin_required
def delete_doctor(doctor_id):
    doc = Doctor.query.get_or_404(doctor_id)
    user = User.query.get(doc.user_id)

    try:
        db.session.delete(doc)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash("Doctor deleted successfully.", "info")
    except Exception:
        db.session.rollback()
        flash("Error deleting doctor.", "danger")

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/patients/<int:patient_id>/history')
@login_required
@admin_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("admin/patient_history.html", patient=patient)

@admin_bp.route('/patients/<int:patient_id>/delete')
@login_required
@admin_required
def delete_patient(patient_id):
    """
    Delete (or soft-delete) a patient and its user account.
    If you prefer soft-delete, change this to set an 'active' flag instead.
    """
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get(patient.user_id)

    try:
        db.session.delete(patient)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash("Patient deleted successfully.", "info")
    except Exception:
        db.session.rollback()
        flash("Error deleting patient.", "danger")

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/appointments')
@login_required
@admin_required
def view_appointments():
    appointments = (
        Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/appointments.html", appointments=appointments)
