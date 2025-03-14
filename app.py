import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Google AI configuration
app.config["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY")
app.config["VECTOR_DB_HOST"] = os.environ.get("VECTOR_DB_HOST")
app.config["VECTOR_DB_API_KEY"] = os.environ.get("VECTOR_DB_API_KEY")

# User quotas
app.config["FREE_QUOTA"] = 5
app.config["PAID_QUOTA"] = int(os.environ.get("PAID_QUOTA", "100"))

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Register blueprints
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(admin_bp)

with app.app_context():
    import models
    db.create_all()
