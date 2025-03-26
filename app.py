import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set up SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "tapbuddy-development-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///tapbuddy.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Import models and routes after app initialization
with app.app_context():
    # Create all tables
    from models import User, VideoRequest, Video
    db.create_all()
    
    # Import route modules
    import routes.web
    import routes.api
    
    # Register routes
    app.register_blueprint(routes.web.bp)
    app.register_blueprint(routes.api.bp, url_prefix="/api")

# Health check route
@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0"})
