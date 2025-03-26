import os
import logging
import re
from twilio.rest import Client
from typing import Dict, Any, Tuple, Optional, List

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

def send_whatsapp_message(to_phone_number: str, message: str) -> bool:
    """
    Send a WhatsApp message using Twilio API.
    
    Args:
        to_phone_number: The recipient's phone number (including country code, e.g., +1234567890)
        message: The message content
        
    Returns:
        Boolean indicating whether the message was sent successfully
    """
    logger.info(f"Preparing to send WhatsApp message to {to_phone_number}")
    
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
        
        # Format phone numbers
        # Twilio requires WhatsApp numbers to be in the format 'whatsapp:+1234567890'
        from_whatsapp_number = f"whatsapp:{TWILIO_PHONE_NUMBER}"
        to_whatsapp_number = f"whatsapp:{validated_phone}"
        
        # Send message
        twilio_message = client.messages.create(
            body=message,
            from_=from_whatsapp_number,
            to=to_whatsapp_number
        )
        
        logger.info(f"WhatsApp message sent successfully to {validated_phone} with SID: {twilio_message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}", exc_info=True)
        return False


def handle_whatsapp_webhook(webhook_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Process incoming WhatsApp webhook from Twilio.
    
    Args:
        webhook_data: The webhook data from Twilio
        
    Returns:
        Tuple of (phone_number, message_body) if successful, (None, None) otherwise
    """
    logger.info("Processing WhatsApp webhook")
    
    try:
        # Extract the phone number and message body from the webhook data
        # Twilio webhook structure: https://www.twilio.com/docs/messaging/webhooks
        
        # Check if it's a WhatsApp message
        if 'From' in webhook_data and webhook_data.get('From', '').startswith('whatsapp:'):
            # Extract the phone number (remove 'whatsapp:' prefix)
            raw_phone_number = webhook_data['From'].replace('whatsapp:', '')
            
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
            
            logger.info(f"Received WhatsApp message from {phone_number}: {message_body[:50]}...")
            return phone_number, message_body
        else:
            logger.warning("Webhook data does not contain WhatsApp message information")
            return None, None
            
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}", exc_info=True)
        return None, None
