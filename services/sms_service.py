import os
import logging
import re
from twilio.rest import Client
from typing import Dict, Any, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Get Twilio credentials from environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN") 
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def validate_phone_number(phone_number: str) -> Tuple[bool, str]:
    """
    Validate phone number format. Should be in E.164 format (+[country code][number]).
    
    Args:
        phone_number: The phone number to validate
        
    Returns:
        Tuple of (is_valid, formatted_number_or_error_message)
    """
    # Basic validation - starts with + and contains only digits after that
    if not phone_number.startswith('+'):
        return False, "Phone number must start with '+' followed by country code"
    
    # Remove any non-digit characters except the leading +
    cleaned_number = '+' + re.sub(r'\D', '', phone_number[1:])
    
    # Check if it has a reasonable length (most phone numbers are 7-15 digits)
    if len(cleaned_number) < 8 or len(cleaned_number) > 16:
        return False, f"Phone number {cleaned_number} has an invalid length"
    
    return True, cleaned_number

def send_sms_message(to_phone_number: str, message: str) -> bool:
    """
    Send an SMS message using Twilio API.
    
    Args:
        to_phone_number: The recipient's phone number (including country code, e.g., +1234567890)
        message: The message content
        
    Returns:
        Boolean indicating whether the message was sent successfully
    """
    logger.info(f"Preparing to send SMS message to {to_phone_number}")
    
    # Check if Twilio credentials are available
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        logger.error("Twilio credentials not found in environment variables")
        return False
    
    # Validate phone number
    is_valid, result = validate_phone_number(to_phone_number)
    if not is_valid:
        logger.error(f"Invalid phone number: {result}")
        return False
    
    validated_phone = result
    
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send SMS message
        sms_message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=validated_phone
        )
        
        logger.info(f"SMS message sent successfully to {validated_phone} with SID: {sms_message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending SMS message: {str(e)}", exc_info=True)
        return False

def handle_sms_webhook(webhook_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Process incoming SMS webhook from Twilio.
    
    Args:
        webhook_data: The webhook data from Twilio
        
    Returns:
        Tuple of (phone_number, message_body) if successful, (None, None) otherwise
    """
    logger.info("Processing SMS webhook")
    
    try:
        # Extract the phone number and message body from the webhook data
        # Twilio webhook structure: https://www.twilio.com/docs/messaging/webhooks
        
        # Check if it's a regular SMS message (not WhatsApp)
        if 'From' in webhook_data and not webhook_data.get('From', '').startswith('whatsapp:'):
            # Extract the phone number
            raw_phone_number = webhook_data['From']
            
            # Validate the phone number
            is_valid, result = validate_phone_number(raw_phone_number)
            if not is_valid:
                logger.warning(f"Invalid phone number received in webhook: {result}")
                return None, None
            
            # Use the validated phone number
            phone_number = result
            
            # Extract the message body
            message_body = webhook_data.get('Body', '')
            if not message_body:
                logger.warning("Empty message body received in webhook")
                return phone_number, ""
            
            logger.info(f"Received SMS message from {phone_number}: {message_body[:50]}...")
            return phone_number, message_body
        else:
            logger.warning("Webhook data does not contain SMS message information")
            return None, None
            
    except Exception as e:
        logger.error(f"Error processing SMS webhook: {str(e)}", exc_info=True)
        return None, None