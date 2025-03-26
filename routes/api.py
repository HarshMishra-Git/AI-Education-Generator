import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from typing import Dict, Any, Tuple, Optional, Literal
from models import get_db, User, VideoRequest, Video
from services.content_generator import generate_educational_content
from services.video_generator import generate_video
from services.speech_generator import generate_speech
from services.messaging_service import send_message, handle_message_webhook
from services.firebase_service import upload_file_to_firebase, get_firebase_url
from datetime import datetime
import json
import threading

bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@bp.route("/process_message_webhook", methods=["POST"])
def process_message_webhook():
    """
    Process incoming message webhook from Twilio.
    This endpoint receives messages (SMS or WhatsApp) from students and triggers the
    video generation process.
    """
    data = request.json or request.form.to_dict()
    logger.debug(f"Received message webhook: {json.dumps(data)}")

    try:
        # Process the incoming message (SMS or WhatsApp)
        phone_number, message_body, message_type = handle_message_webhook(data)

        if not phone_number or not message_body:
            return jsonify({"error": "Invalid message format"}), 400

        # Get database session
        db = get_db()

        # Get or create user
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            user = User(phone_number=phone_number)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Parse message to determine subject, topic, and level
        subject, topic, level, query = parse_message(message_body)

        # Create a new video request
        video_request = VideoRequest(
            user_id=user.id,
            subject=subject,
            topic=topic,
            level=level,
            query=query,
            status="pending"
        )
        db.add(video_request)
        db.commit()
        db.refresh(video_request)

        # Send acknowledgment to the user
        send_message(
            phone_number,
            f"Thanks for your request! We're generating a {subject} video about '{topic}' for you. This may take a few minutes.",
            message_type
        )

        # Start the video generation process in the background
        try:
            logger.info(f"Starting background thread for request {video_request.id}")
            thread = threading.Thread(
                target=process_video_request,
                args=(video_request.id, message_type)
            )
            thread.daemon = True
            thread.start()
            logger.info(f"Background thread started successfully for request {video_request.id}")
        except Exception as e:
            logger.error(f"Failed to start background thread: {str(e)}")
            return jsonify({"error": "Failed to start processing"}), 500

        return jsonify({"status": "success", "message": "Request received and processing started"})

    except Exception as e:
        logger.error(f"Error processing message webhook: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Keep the old endpoint for backward compatibility
@bp.route("/process_whatsapp_webhook", methods=["POST"])
def process_whatsapp_webhook():
    """
    Legacy endpoint for processing WhatsApp webhooks.
    Redirects to the unified message processing endpoint.
    """
    return process_message_webhook()


@bp.route("/video_status/<int:request_id>")
def get_video_status(request_id):
    """
    Get the status of a video generation request
    """
    db = get_db()
    video_request = db.query(VideoRequest).filter(VideoRequest.id == request_id).first()
    if not video_request:
        return jsonify({"error": "Request not found"}), 404

    response = {
        "id": video_request.id,
        "status": video_request.status,
        "created_at": video_request.created_at,
        "completed_at": video_request.completed_at,
        "subject": video_request.subject,
        "topic": video_request.topic
    }

    if video_request.status == "completed" and video_request.video:
        response["video_url"] = video_request.video.firebase_url

    return jsonify(response)


def process_video_request(request_id, message_type="whatsapp"):
    """
    Background task to process a video generation request

    Args:
        request_id: The ID of the video request to process
        message_type: The type of message to use for notifications ("sms" or "whatsapp")
    """
    MAX_PROCESSING_TIME = 300  # 5 minutes timeout
    start_time = datetime.utcnow()
    logger.info(f"Starting video generation process for request {request_id}, message type: {message_type}")

    # Get the session inside this task
    from app import app
    with app.app_context():
        db_session = get_db()

        try:
            # Get the request
            request = db_session.query(VideoRequest).filter(VideoRequest.id == request_id).first()
            if not request:
                logger.error(f"Request {request_id} not found")
                return

            logger.info(f"Starting processing for request {request_id}")
            # Update request status
            request.status = "processing"
            db_session.commit()
            db_session.flush()

            # Check for timeout
            if (datetime.utcnow() - start_time).total_seconds() > MAX_PROCESSING_TIME:
                raise TimeoutError("Video generation process timed out")

            # Send progress update
            user = db_session.query(User).filter(User.id == request.user_id).first()
            if user:
                send_message(
                    user.phone_number,
                    f"We're working on your video about '{request.topic}'. Starting content generation...",
                    message_type
                )

            try:
                # Generate educational content using Gemini API
                logger.info(f"Generating content for request {request_id}")
                content = generate_educational_content(
                    subject=request.subject,
                    topic=request.topic,
                    level=request.level,
                    query=request.query
                )

                # Generate speech using text-to-speech
                logger.info(f"Generating speech for request {request_id}")
                audio_file_path = generate_speech(content["script"])

                # Generate video using text-to-video APIs
                logger.info(f"Generating video for request {request_id}")
                video_file_path = generate_video(content, request.subject, audio_file_path)

                # Upload to Firebase
                firebase_path = f"videos/{request_id}/{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
                upload_file_to_firebase(video_file_path, firebase_path)
                firebase_url = get_firebase_url(firebase_path)

                # Create video record
                video = Video(
                    request_id=request.id,
                    title=content["title"],
                    description=content["description"],
                    firebase_url=firebase_url
                )
                db_session.add(video)

                # Update request status
                request.status = "completed"
                request.completed_at = datetime.utcnow()
                db_session.commit()

                # Send notification
                send_message(
                    user.phone_number,
                    f"Your video about '{request.topic}' is ready! Watch it here: {firebase_url}",
                    message_type
                )
            except Exception as e:
                logger.error(f"Error processing video request {request_id}: {str(e)}", exc_info=True)
                request.status = "failed"
                db_session.commit()

                # Send failure notification
                send_message(
                    user.phone_number,
                    f"We encountered an issue while generating your video about '{request.topic}'. Please try again.",
                    message_type
                )
        except Exception as e:
            logger.error(f"Error processing video request {request_id}: {str(e)}", exc_info=True)
            if request:
                request.status = "failed"
                db_session.commit()

            if user:
                send_message(
                    user.phone_number,
                    f"We encountered an issue while generating your video. Please try again.",
                    message_type
                )

def parse_message(message: str):
    """
    Parse the incoming WhatsApp message to extract subject, topic, level, and query.
    Format expected: #subject #topic #level followed by the query text
    Example: #Science #Photosynthesis #Beginner How does photosynthesis work?

    If tags are not provided, tries to intelligently determine them from the message content.
    """
    parts = message.split()
    subject = "General"
    topic = "General Topic"
    level = "Beginner"

    # Try to extract hashtags
    hashtags = [part for part in parts if part.startswith('#')]

    if len(hashtags) >= 3:
        # Extract subject, topic, and level from hashtags
        subject = hashtags[0][1:].capitalize()
        topic = hashtags[1][1:].capitalize()
        level = hashtags[2][1:].capitalize()

        # Remove hashtags from the original message to get the query
        query = " ".join([part for part in parts if not part.startswith('#')])
    else:
        # If hashtags are not provided, use the entire message as the query
        query = message

        # Try to determine subject from the message content
        if any(keyword in message.lower() for keyword in ["draw", "paint", "color", "design", "art"]):
            subject = "Visual Arts"
        elif any(keyword in message.lower() for keyword in ["dance", "music", "sing", "instrument", "perform"]):
            subject = "Performing Arts"
        elif any(keyword in message.lower() for keyword in ["code", "program", "python", "java", "html"]):
            subject = "Coding"
        elif any(keyword in message.lower() for keyword in ["money", "finance", "budget", "invest", "save"]):
            subject = "Financial Literacy"
        elif any(keyword in message.lower() for keyword in ["science", "biology", "chemistry", "physics", "experiment"]):
            subject = "Science"

        # Extract potential topic from the query (first 3-5 words)
        topic_words = parts[:min(5, len(parts))]
        topic = " ".join(topic_words)

    # Validate subject to ensure it's one of the supported categories
    valid_subjects = ["Visual Arts", "Performing Arts", "Coding", "Financial Literacy", "Science"]
    if subject not in valid_subjects:
        subject = "General"

    # Validate level
    valid_levels = ["Beginner", "Intermediate", "Advanced"]
    if level not in valid_levels:
        level = "Beginner"

    return subject, topic, level, query