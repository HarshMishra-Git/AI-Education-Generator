from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.orm import Session
from models import get_db, VideoRequest, User
from typing import Optional, Dict, Any
import logging
from services.messaging_service import validate_phone_number

logger = logging.getLogger(__name__)
bp = Blueprint('web', __name__)

@bp.route("/")
def index():
    """
    Renders the home page
    """
    return render_template(
        "index.html", 
        title="TAPBuddy AI Video Generator"
    )

@bp.route("/dashboard")
def dashboard():
    """
    Dashboard to view video requests and their status with enhanced filtering and analytics
    """
    phone = request.args.get('phone')
    subject = request.args.get('subject')
    status = request.args.get('status')
    db = get_db()
    
    # Build the query with filters
    query = db.query(VideoRequest).order_by(VideoRequest.created_at.desc())
    
    if phone:
        # Filter by phone number if provided
        user = db.query(User).filter(User.phone_number == phone).first()
        if user:
            query = query.filter(VideoRequest.user_id == user.id)
        else:
            # No user found with this phone number
            return render_template(
                "dashboard.html",
                title="Dashboard - TAPBuddy AI Video Generator",
                requests=[],
                phone=phone,
                subject=subject,
                status=status,
                stats=get_empty_stats()
            )
    
    if subject and subject != "All":
        # Filter by subject
        query = query.filter(VideoRequest.subject == subject)
    
    if status and status != "All":
        # Filter by status
        query = query.filter(VideoRequest.status == status.lower())
    
    # Get requests with limit
    requests = query.limit(50).all()
    
    # Compute dashboard statistics
    stats = compute_dashboard_stats(requests)
    
    # Get unique subjects and statuses for filter dropdowns
    all_subjects = db.query(VideoRequest.subject).distinct().all()
    subjects = [s[0] for s in all_subjects] if all_subjects else []
    
    statuses = ["pending", "processing", "completed", "failed"]

    return render_template(
        "dashboard.html", 
        title="Dashboard - TAPBuddy AI Video Generator",
        requests=requests,
        phone=phone,
        subject=subject,
        status=status,
        subjects=subjects,
        statuses=statuses,
        stats=stats
    )

@bp.route("/submit_request", methods=["POST"])
def submit_request():
    """
    Submit a video request from the web interface with enhanced error handling 
    and messaging options
    """
    try:
        # Get form data
        phone_number = request.form.get("phone_number")
        subject = request.form.get("subject")
        topic = request.form.get("topic")
        level = request.form.get("level")
        query = request.form.get("query")
        message_type = request.form.get("message_type", "whatsapp")  # Default to WhatsApp if not specified
        
        # Validate phone number
        is_valid, formatted_number = validate_phone_number(phone_number)
        if not is_valid:
            flash(f"Invalid phone number: {formatted_number}", "error")
            return redirect(url_for("web.index", _anchor="request-form"))
        
        db = get_db()
        
        # Get or create user
        user = db.query(User).filter(User.phone_number == formatted_number).first()
        if not user:
            user = User(phone_number=formatted_number)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create a new video request with enhanced data
        video_request = VideoRequest(
            user_id=user.id,
            subject=subject,
            topic=topic,
            level=level,
            query=query,
            status="pending",
            # Store the preferred message delivery type
            request_metadata={
                "message_type": message_type,
                "source": "web_interface",
                "enhanced_features": True
            }
        )
        db.add(video_request)
        db.commit()
        
        # Build a more informative success message
        message_type_name = "SMS" if message_type == "sms" else "WhatsApp"
        flash_message = (
            f"Your {subject} video request about '{topic}' has been submitted successfully! "
            f"You will receive a notification via {message_type_name} when your video is ready."
        )
        
        # Redirect to the dashboard with a success message
        flash(flash_message, "success")
        return redirect(url_for("web.dashboard", phone=formatted_number))
    
    except Exception as e:
        logger.error(f"Error submitting request: {str(e)}", exc_info=True)
        flash(f"Error submitting request: {str(e)}", "error")
        return redirect(url_for("web.index", _anchor="request-form"))

@bp.route("/video_details/<int:request_id>")
def video_details(request_id: int):
    """
    Show detailed information about a specific video request
    """
    try:
        db = get_db()
        video_request = db.query(VideoRequest).filter(VideoRequest.id == request_id).first()
        
        if not video_request:
            flash("Video request not found.", "error")
            return redirect(url_for("web.dashboard"))
        
        return render_template(
            "video_details.html",
            title=f"Video Details - {video_request.topic}",
            request=video_request
        )
    
    except Exception as e:
        logger.error(f"Error retrieving video details: {str(e)}", exc_info=True)
        flash(f"Error retrieving video details: {str(e)}", "error")
        return redirect(url_for("web.dashboard"))

def compute_dashboard_stats(requests) -> Dict[str, Any]:
    """
    Compute statistics for the dashboard
    """
    # Initialize stats
    stats = {
        "total": len(requests),
        "completed": 0,
        "pending": 0,
        "processing": 0,
        "failed": 0,
        "subjects": {},
        "levels": {
            "Beginner": 0,
            "Intermediate": 0,
            "Advanced": 0
        }
    }
    
    # No requests, return empty stats
    if not requests:
        return stats
    
    # Compute stats
    for request in requests:
        # Status counts
        if request.status in stats:
            stats[request.status] += 1
        
        # Subject counts
        if request.subject not in stats["subjects"]:
            stats["subjects"][request.subject] = 0
        stats["subjects"][request.subject] += 1
        
        # Level counts
        if request.level in stats["levels"]:
            stats["levels"][request.level] += 1
    
    return stats

def get_empty_stats() -> Dict[str, Any]:
    """
    Return empty stats structure for when no requests are found
    """
    return {
        "total": 0,
        "completed": 0,
        "pending": 0,
        "processing": 0,
        "failed": 0,
        "subjects": {},
        "levels": {
            "Beginner": 0,
            "Intermediate": 0,
            "Advanced": 0
        }
    }
