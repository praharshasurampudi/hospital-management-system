"""
Utility helpers:
- is_slot_available: prevent double-booking
- simple search helpers for doctors/patients (optional)
"""

from models import Appointment

def is_slot_available(doctor_id, appt_date, appt_time, appointment_id=None):
    """
    Check whether the doctor has a non-cancelled appointment at the given date/time.
    This function only checks for appointments (not doctor-set availability).
    """
    q = Appointment.query.filter_by(doctor_id=doctor_id, date=appt_date, time=appt_time)
    if appointment_id:
        q = q.filter(Appointment.id != appointment_id)
    existing = q.filter(Appointment.status != "Cancelled").first()
    return existing is None


def search_doctors_by_name_or_specialization(term):
    from models import Doctor, User
    key = f"%{term}%"
    return Doctor.query.join(User).filter((User.name.ilike(key)) | (Doctor.specialization.ilike(key))).all()


def search_patients_by_name_or_phone(term):
    from models import Patient, User
    key = f"%{term}%"
    return Patient.query.join(User).filter((User.name.ilike(key)) | (Patient.phone.ilike(key))).all()
