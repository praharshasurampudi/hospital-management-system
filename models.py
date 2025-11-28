"""
models.py — SQLAlchemy models for the HMS application
Fully compatible with app.py and all blueprints you generated.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


# -----------------------------
# Roles (constants)
# -----------------------------
class Role:
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


# -----------------------------
# User Model (Account)
# -----------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / doctor / patient

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# -----------------------------
# Department / Specialization
# -----------------------------
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)


# -----------------------------
# Doctor Profile
# -----------------------------
class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    specialization = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))

    user = db.relationship("User", backref=db.backref("doctor_profile", uselist=False))
    department = db.relationship("Department", backref=db.backref("doctors", lazy="dynamic"))


# -----------------------------
# Patient Profile
# -----------------------------
class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    phone = db.Column(db.String(30))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    address = db.Column(db.Text)

    user = db.relationship("User", backref=db.backref("patient_profile", uselist=False))


# -----------------------------
# Appointment
# -----------------------------
class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)

    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    status = db.Column(
        db.String(20), default="Booked"
    )  # Booked / Completed / Cancelled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref=db.backref("appointments", lazy="dynamic"))
    doctor = db.relationship("Doctor", backref=db.backref("appointments", lazy="dynamic"))


# -----------------------------
# Treatment Details
# -----------------------------
class Treatment(db.Model):
    __tablename__ = "treatments"

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointments.id"), nullable=False, unique=True
    )

    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointment = db.relationship(
        "Appointment",
        backref=db.backref("treatment", uselist=False)
    )


# -----------------------------
# DB Initialization (NO init_app HERE)
# -----------------------------
def init_models(app=None):
    """
    Create all tables programmatically.
    IMPORTANT: app.py already calls db.init_app(app). Do NOT call it again here.
    """
    if app:
        with app.app_context():
            db.create_all()
    else:
        db.create_all()


# -----------------------------
# Seed Default Admin
# -----------------------------
def seed_admin():
    """
    Create a pre-existing admin user if missing.
    Called automatically in app.py after tables created.
    """
    admin_email = "admin@email.com"
    admin = User.query.filter_by(email=admin_email).first()

    if not admin:
        admin = User(
            email=admin_email,
            name="Admin",
            role=Role.ADMIN,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("✔ Default admin created:", admin_email)
    else:
        print("✔ Admin already exists:", admin_email)
# -----------------------------
# Availability (new)
# -----------------------------
class Availability(db.Model):
    """
    Per-doctor per-date/per-time availability slot.
    If a record exists:
      - available == True  -> doctor says slot is open (subject to no appointment)
      - available == False -> doctor explicitly marks slot as blocked
    If no record exists, we fallback to checking only appointments (slot considered free if no appointment).
    """
    __tablename__ = "availabilities"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    available = db.Column(db.Boolean, default=True, nullable=False)

    doctor = db.relationship("Doctor", backref=db.backref("availabilities", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "date", "time", name="uix_doctor_date_time"),
    )
