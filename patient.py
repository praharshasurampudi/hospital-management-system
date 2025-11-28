"""
Patient Blueprint

Features:
- Patient dashboard (departments, doctors, upcoming appointments)
- Department detail (doctors in a department)
- Doctor profile & recent patients
- Check doctor availability & book appointment (prevents double-booking)
- View/cancel appointment
- View full appointment history

Templates used (place under templates/patient/):
- dashboard.html
- department_detail.html
- doctor_profile.html
- doctor_availability.html
- patient_history.html
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date, datetime, time, timedelta

from models import db, Patient, Department, Doctor, Appointment, Role
from utils import is_slot_available

patient_bp = Blueprint("patient", __name__, template_folder="templates/patient")


# ---------------------------------------------------------
# Helper decorator: patient-only access
# ---------------------------------------------------------
def patient_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.PATIENT:
            flash("Patient login required.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
@patient_bp.route("/dashboard")
@login_required
@patient_required
def dashboard():
    # departments and doctors
    departments = Department.query.order_by(Department.name).all()
    # show active doctors only
    doctors = Doctor.query.join(Doctor.user).filter(Doctor.active == True).order_by(Doctor.user_id).all()

    patient = current_user.patient_profile
    upcoming = []
    if patient:
        upcoming = (
            Appointment.query.filter_by(patient_id=patient.id)
            .filter(Appointment.date >= date.today())
            .order_by(Appointment.date, Appointment.time)
            .all()
        )

    return render_template("patient/dashboard.html", departments=departments, doctors=doctors, upcoming=upcoming)


# ---------------------------------------------------------
# Department detail (lists doctors)
# ---------------------------------------------------------
@patient_bp.route("/department/<int:dept_id>")
@login_required
@patient_required
def department_detail(dept_id):
    dept = Department.query.get_or_404(dept_id)
    doctors = dept.doctors.order_by(Doctor.user_id).all()
    return render_template("patient/department_detail.html", dept=dept, doctors=doctors)


# ---------------------------------------------------------
# Doctor profile (shows doctor info & recent patients)
# ---------------------------------------------------------
@patient_bp.route("/doctor/<int:doctor_id>")
@login_required
@patient_required
def doctor_profile(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    recent = (
        Appointment.query.filter_by(doctor_id=doctor.id)
        .order_by(Appointment.date.desc(), Appointment.time.desc())
        .limit(6)
        .all()
    )
    return render_template("patient/doctor_profile.html", doctor=doctor, recent=recent)


# ---------------------------------------------------------
# Check availability & book slot (GET shows slots, POST books)
# ---------------------------------------------------------
@patient_bp.route("/doctor/<int:doctor_id>/availability", methods=["GET", "POST"])
@login_required
@patient_required
def check_availability(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)

    # default time slots for demo; adapt as needed or add persistent Availability model
    default_slots = [time(9, 0), time(11, 0), time(14, 0), time(16, 0)]
    today = date.today()
    availability = []
    for d_offset in range(0, 7):
        d = today + timedelta(days=d_offset)
        slot_items = []
        for s in default_slots:
            free = is_slot_available(doctor.id, d, s)
            slot_items.append({
                "value": f"{d.isoformat()}|{s.strftime('%H:%M')}",
                "label": s.strftime("%H:%M"),
                "available": free
            })
        availability.append({"date": d.isoformat(), "slots": slot_items})

    if request.method == "POST":
        slot_value = request.form.get("slot")
        if not slot_value:
            flash("Please select a slot to book.", "warning")
            return redirect(url_for("patient.check_availability", doctor_id=doctor_id))

        date_str, time_str = slot_value.split("|")
        appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        appt_time = datetime.strptime(time_str, "%H:%M").time()

        patient = current_user.patient_profile
        if not patient:
            flash("Patient profile not found.", "danger")
            return redirect(url_for("patient.dashboard"))

        # final check to prevent race conditions / double-booking
        if not is_slot_available(doctor.id, appt_date, appt_time):
            flash("Selected slot is no longer available. Please choose another.", "warning")
            return redirect(url_for("patient.check_availability", doctor_id=doctor_id))

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=appt_date,
            time=appt_time,
            status="Booked"
        )
        db.session.add(appt)
        db.session.commit()
        flash("Appointment booked successfully.", "success")
        return redirect(url_for("patient.dashboard"))

    return render_template("patient/doctor_availability.html", doctor=doctor, availability=availability)


# ---------------------------------------------------------
# View single appointment (ensure ownership)
# ---------------------------------------------------------
@patient_bp.route("/appointments/<int:aid>/view")
@login_required
@patient_required
def view_appointment(aid):
    appt = Appointment.query.get_or_404(aid)
    patient_profile = current_user.patient_profile
    if not patient_profile or appt.patient_id != patient_profile.id:
        flash("Not authorized to view this appointment.", "warning")
        return redirect(url_for("patient.dashboard"))

    # reuse patient_history template with single appointment
    return render_template("patient/patient_history.html", appointments=[appt])


# ---------------------------------------------------------
# Cancel appointment (patient)
# ---------------------------------------------------------
@patient_bp.route("/appointments/<int:aid>/cancel")
@login_required
@patient_required
def cancel_appointment(aid):
    appt = Appointment.query.get_or_404(aid)
    patient_profile = current_user.patient_profile
    if not patient_profile or appt.patient_id != patient_profile.id:
        flash("Not authorized to cancel this appointment.", "warning")
        return redirect(url_for("patient.dashboard"))

    appt.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("patient.dashboard"))


# ---------------------------------------------------------
# Full history (list of past + future appointments)
# ---------------------------------------------------------
@patient_bp.route("/history")
@login_required
@patient_required
def history():
    patient_profile = current_user.patient_profile
    appointments = []
    if patient_profile:
        appointments = (
            Appointment.query.filter_by(patient_id=patient_profile.id)
            .order_by(Appointment.date.desc(), Appointment.time.desc())
            .all()
        )
    return render_template("patient/patient_history.html", appointments=appointments)
