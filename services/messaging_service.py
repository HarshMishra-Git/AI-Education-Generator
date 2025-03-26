import logging
from typing import Dict, Any, Tuple, Optional, Literal

from services.whatsapp_service import send_whatsapp_message, handle_whatsapp_webhook, validate_phone_number
from services.sms_service import send_sms_message, handle_sms_webhook

# Configure logging
logger = logging.getLogger(__name__)

def send_message(
    to_phone_number: str, 
    message: str, 
    message_type: str = "sms"
) -> bool:
    """
    Send a message using the appropriate messaging service.
    
    Args:
        to_phone_number: The recipient's phone number (including country code, e.g., +1234567890)
        message: The message content
        message_type: Type of message to send - "sms" or "whatsapp" (any other value defaults to "sms")
        
    Returns:
        Boolean indicating whether the message was sent successfully
    """
    # Normalize message_type to handle any case
    normalized_type = message_type.lower() if isinstance(message_type, str) else "sms"
    
    logger.info(f"Sending {normalized_type} message to {to_phone_number}")
    
    # Validate the phone number before proceeding
    is_valid, result = validate_phone_number(to_phone_number)
    if not is_valid:
        logger.error(f"Invalid phone number: {result}")
        return False
    
    validated_phone = result
    
    # Use the appropriate service based on message type
    if normalized_type == "whatsapp":
        return send_whatsapp_message(validated_phone, message)
    else:  # Default to SMS
        return send_sms_message(validated_phone, message)

def handle_message_webhook(webhook_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], str]:
    """
    Process incoming message webhook from Twilio, determining whether it's 
    an SMS or WhatsApp message.
    
    Args:
        webhook_data: The webhook data from Twilio
        
    Returns:
        Tuple of (phone_number, message_body, message_type) if successful, 
        (None, None, "") otherwise
    """
    logger.info("Processing message webhook")
    
    # Check if it's a WhatsApp message
    if 'From' in webhook_data and webhook_data.get('From', '').startswith('whatsapp:'):
        phone_number, message_body = handle_whatsapp_webhook(webhook_data)
        message_type = "whatsapp"
    else:
        # Assume it's an SMS message
        phone_number, message_body = handle_sms_webhook(webhook_data)
        message_type = "sms"
    
    if phone_number and message_body is not None:
        return phone_number, message_body, message_type
    else:
        return None, None, ""