# doctor.py (updated availability handling)
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from datetime import date, datetime, time, timedelta

from models import db, Doctor, Appointment, Patient, Treatment, Role, Availability
from utils import is_slot_available

doctor_bp = Blueprint("doctor", __name__, template_folder="templates/doctor")


def doctor_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.DOCTOR:
            flash("Doctor access only.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


@doctor_bp.route("/dashboard")
@login_required
@doctor_required
def dashboard():
    doc = current_user.doctor_profile
    if not doc:
        flash("Doctor profile not found!", "danger")
        return redirect(url_for("auth.login"))

    today = date.today()

    # Today's appointments
    todays_appointments = (
        Appointment.query.filter_by(doctor_id=doc.id, date=today)
        .order_by(Appointment.time)
        .all()
    )

    # Week appointments
    week_later = today + timedelta(days=7)
    week_appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == doc.id,
            Appointment.date >= today,
            Appointment.date <= week_later,
        )
        .order_by(Appointment.date, Appointment.time)
        .all()
    )

    # Unique patients in week
    patient_set = set()
    patients = []
    for appt in week_appointments:
        if appt.patient_id not in patient_set:
            patients.append(appt.patient)
            patient_set.add(appt.patient_id)

    # Build availability grid using Availability model and appointments
    default_slots = [time(9, 0), time(11, 0), time(14, 0), time(16, 0)]
    availability = []
    for offset in range(0, 7):
        d = today + timedelta(days=offset)
        slots = []
        for s in default_slots:
            # Check if doctor explicitly set any availability record
            av = Availability.query.filter_by(doctor_id=doc.id, date=d, time=s).first()
            # If Availability record exists, use its flag (True => open, False => blocked)
            if av:
                slot_open = av.available and is_slot_available(doc.id, d, s)
                explicitly_set = True
                available_flag = av.available
            else:
                # fallback: slot is open if no appointment occupies it
                slot_open = is_slot_available(doc.id, d, s)
                explicitly_set = False
                available_flag = slot_open

            slots.append({
                "label": s.strftime("%H:%M"),
                "value": f"{d.isoformat()}|{s.strftime('%H:%M')}",
                "open": slot_open,            # slot can be booked (no appointment) AND availability permits
                "explicitly_set": explicitly_set,  # whether doctor explicitly set this slot
                "available_flag": available_flag   # doctor's chosen availability (True/False) or fallback
            })
        availability.append({"date": d.isoformat(), "slots": slots})

    return render_template(
        "doctor/dashboard.html",
        todays=todays_appointments,
        week_appts=week_appointments,
        patients=patients,
        availability=availability,
    )


# existing appointment_detail, mark_complete, cancel_appointment remain unchanged...
# (keep them as in your current doctor.py)

# Provide / Edit availability (persistent)
@doctor_bp.route("/availability", methods=["GET", "POST"])
@login_required
@doctor_required
def provide_availability():
    """
    Show an editable availability grid for the next 7 days.
    POST data contains checkboxes named like 'slot_{date}_{time}' to indicate available slots.
    Saves/updates Availability rows accordingly.
    """
    doc = current_user.doctor_profile
    if not doc:
        flash("Doctor profile not found", "danger")
        return redirect(url_for("auth.login"))

    today = date.today()
    default_slots = [time(9, 0), time(11, 0), time(14, 0), time(16, 0)]

    if request.method == "POST":
        # For each day & slot, read whether checkbox is in form -> available True; else False
        changes = []
        for d_offset in range(0, 7):
            d = today + timedelta(days=d_offset)
            for s in default_slots:
                form_key = f"slot_{d.isoformat()}_{s.strftime('%H%M')}"
                is_available_checked = form_key in request.form  # checkbox present if checked
                # find existing availability row
                av = Availability.query.filter_by(doctor_id=doc.id, date=d, time=s).first()
                if av:
                    # update if changed
                    if av.available != is_available_checked:
                        av.available = is_available_checked
                        changes.append((d, s, is_available_checked))
                else:
                    # create new row only if admin toggled availability (we can store both True/False)
                    # We'll create a record regardless so admin's choice is persisted.
                    av = Availability(doctor_id=doc.id, date=d, time=s, available=is_available_checked)
                    db.session.add(av)
                    changes.append((d, s, is_available_checked))
        db.session.commit()
        flash("Availability saved.", "success")
        return redirect(url_for("doctor.dashboard"))

    # GET: render an availability editing page
    availability = []
    for d_offset in range(0, 7):
        d = today + timedelta(days=d_offset)
        slots = []
        for s in default_slots:
            av = Availability.query.filter_by(doctor_id=doc.id, date=d, time=s).first()
            checked = av.available if av else False
            # slot disabled if an appointment already exists (can't mark available if booked)
            booked = not is_slot_available(doc.id, d, s)
            slots.append({
                "date": d.isoformat(),
                "time": s.strftime("%H:%M"),
                "form_key": f"slot_{d.isoformat()}_{s.strftime('%H%M')}",
                "checked": checked,
                "booked": booked
            })
        availability.append({"date": d.isoformat(), "slots": slots})

    return render_template("doctor/availability.html", availability=availability)
