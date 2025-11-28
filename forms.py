"""
WTForms for HMS (updated)
- DoctorForm now includes an optional password field so Admin can set doctor password.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, DateField, TimeField
from wtforms.validators import DataRequired, Email, Length, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=180)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=180)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    age = IntegerField("Age", validators=[Optional()])
    gender = StringField("Gender", validators=[Optional(), Length(max=20)])
    address = TextAreaField("Address", validators=[Optional()])
    submit = SubmitField("Register")


class DoctorForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=180)])
    specialization = StringField("Specialization", validators=[DataRequired(), Length(max=120)])
    bio = TextAreaField("Bio", validators=[Optional()])
    # Optional password field for admin to set/change doctor's password
    password = PasswordField("Password (set/change doctor password)", validators=[Optional(), Length(min=6)])
    submit = SubmitField("Save")


class AppointmentForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    time = TimeField("Time", validators=[DataRequired()])
    submit = SubmitField("Book Appointment")
