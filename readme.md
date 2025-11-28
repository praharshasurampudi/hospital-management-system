# 📘 **Hospital Management System (HMS)**

A role-based web application built using **Flask**, **SQLite**, **Bootstrap**, and **Jinja2** to manage hospital operations such as appointments, patient history, doctor availability, and treatment records.

---

## 🏥 **Project Overview**

The Hospital Management System (HMS) is designed to streamline patient–doctor–admin interactions by digitizing the workflows commonly used in hospitals. It supports role-based access (Admin, Doctor, Patient) with separate dashboards and permissions.

The system uses **Flask** on the backend and **SQLite** as the database, created programmatically (no manual creation allowed). The project follows MVC-like structure using Blueprints.

---

## 🚀 **Core Features**

### 👨‍💼 **Admin**

* Pre-created superuser (cannot register)
* Dashboard with:

  * Total doctors, patients, appointments
  * Search functionality (doctors, patients, appointments)
  * Doctor table & Patient table
  * Upcoming appointments list
* Add, edit, delete doctors
* Manage patient history
* Delete/blacklist patients
* View all appointments

---

### 👨‍⚕️ **Doctor**

* Login with credentials created by Admin
* Dashboard with:

  * Today's appointments
  * Weekly appointments
  * Patient list
  * Availability calendar (7-day view)
* Set availability (green = available, red = blocked)
* Mark appointments as completed/cancelled
* Add diagnosis, prescriptions, and notes
* View full patient treatment history

---

### 🧑‍🦰 **Patient**

* Self-registration & login
* Dashboard with:

  * Specializations/departments
  * Doctor profiles
  * Doctor availability (next 7 days)
* Book, reschedule, cancel appointments
* View medical history:

  * Diagnosis
  * Prescriptions
  * Notes
* Edit profile

---

## 🛠 **Tech Stack**

| Component      | Technology                             |
| -------------- | -------------------------------------- |
| Backend        | Python Flask                           |
| Frontend       | HTML5, CSS3, Bootstrap 5, Jinja2       |
| Database       | SQLite (auto-created programmatically) |
| ORM            | Flask-SQLAlchemy                       |
| Authentication | Flask-Login                            |
| Forms          | Flask-WTF / WTForms                    |

---

## 📁 **Project Structure**

```
hms/
│
├─ app.py
├─ admin.py
├─ doctor.py
├─ patient.py
├─ auth.py
├─ models.py
├─ forms.py
├─ utils.py
│
├─ requirements.txt
├─ README.md
│
├─ instance/
│   └─ hms.sqlite      # generated automatically (DO NOT CREATE MANUALLY)
│
└─ templates/
    ├─ base.html
    ├─ auth_login.html
    ├─ auth_register.html
    │
    ├─ admin/
    │   ├─ dashboard.html
    │   ├─ add_doctor.html
    │   ├─ patient_history.html
    │   └─ appointments.html
    │
    ├─ doctor/
    │   ├─ dashboard.html
    │   ├─ appointment_detail.html
    │   ├─ availability.html
    │   └─ patient_history.html
    │
    └─ patient/
        ├─ dashboard.html
        ├─ department_detail.html
        ├─ doctor_profile.html
        ├─ doctor_availability.html
        └─ patient_history.html
```

---

## ⚙️ **Installation & Setup**

### 1️⃣ Clone or extract the project

```
cd hms
```

### 2️⃣ Create a virtual environment

```
python -m venv venv
```

### 3️⃣ Activate virtual environment

#### Windows (PowerShell)

```
.\venv\Scripts\Activate.ps1
```

#### macOS/Linux

```
source venv/bin/activate
```

### 4️⃣ Install dependencies

```
pip install -r requirements.txt
```

### 5️⃣ Run the application

```
python app.py
```

### 6️⃣ Open in browser

```
http://127.0.0.1:5000
```

---

## 🔐 **Default Admin Login**

The app automatically seeds an admin account during first run.

| Field    | Value                                                   |
| -------- | ------------------------------------------------------- |
| Email    | **[admin@email.com](mailto:admin@email.com** |
| Password | **admin123**                                            |

> Admin can then create doctor accounts and manage the system.

---

## 🗂 **Database**

* SQLite database at: `instance/hms.sqlite`
* Created programmatically by `init_models(app)`
* NO manual creation allowed (as per project requirement)
* Models include:

  * User (Admin/Doctor/Patient)
  * Doctor
  * Patient
  * Department
  * Appointment
  * Treatment
  * Availability (Doctor schedule)

---

## 🔍 **Search Feature**

Admin can search from the dashboard:

* Doctor name
* Doctor specialization
* Patient name
* Patient phone
* Patient email
* Appointment: patient/doctor name
* Date search (format `YYYY-MM-DD`)

Search is dynamic and filters all tables live.

---

## 📡 **API Endpoints (Optional)**

If you implemented REST APIs (recommended but optional):

```
GET /api/doctors
GET /api/patients
POST /api/appointments
PUT /api/doctor/<id>/availability
...
```
