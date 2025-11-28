# app.py
"""
Flask application factory and entrypoint for HMS.

Place this file at: hms/app.py
Run with: python app.py
"""

import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager

# Import the shared db and helper functions from models
from models import db, init_models, seed_admin, User, Role

def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    # Basic config
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI",
            "sqlite:///{}".format(os.path.join(app.instance_path, "hms.sqlite")),
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    # ensure instance folder exists (for SQLite file)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions (register db once)
    db.init_app(app)

    # Login manager
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Create tables and seed admin within app context
    with app.app_context():
        init_models(app)   # will call db.create_all() safely
        seed_admin()       # create default admin if missing

    # Register blueprints (import here to avoid circular imports)
    from auth import auth_bp
    from admin import admin_bp
    from doctor import doctor_bp
    from patient import patient_bp

    app.register_blueprint(auth_bp)                     # /login, /register
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(doctor_bp, url_prefix="/doctor")
    app.register_blueprint(patient_bp, url_prefix="/patient")

    # Simple root
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app


if __name__ == "__main__":
    # When run directly, create the app and start the dev server.
    # This prints a clear message so you know it's running.
    app = create_app()
    print("Starting HMS Flask app on http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
