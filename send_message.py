import os
import sys
import re
from twilio.rest import Client
from typing import Literal, Tuple

# Get Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")


def validate_phone_number(phone_number: str) -> Tuple[bool, str]:
    """
    Validate phone number format. Should be in E.164 format (+[country code][number]).
    
    Args:
        phone_number: The phone number to validate
        
    Returns:
        Tuple of (is_valid, formatted_number)
    """
    # Basic validation - starts with + and contains only digits after that
    if not phone_number.startswith('+'):
        return False, "Phone number must start with '+' followed by country code (e.g., +1 for US)"
    
    # Remove any non-digit characters except the leading +
    cleaned_number = '+' + re.sub(r'\D', '', phone_number[1:])
    
    # Check if it has a reasonable length (most phone numbers are 7-15 digits)
    if len(cleaned_number) < 8 or len(cleaned_number) > 16:
        return False, f"Phone number {cleaned_number} has an invalid length"
    
    return True, cleaned_number


def send_message(
    to_phone_number: str, 
    message: str, 
    message_type: Literal["sms", "whatsapp"] = "sms"
) -> bool:
    """
    Send a message using Twilio API.
    
    Args:
        to_phone_number: The recipient's phone number (including country code, e.g., +1234567890)
        message: The message content
        message_type: Type of message to send - "sms" or "whatsapp"
        
    Returns:
        Boolean indicating whether the message was sent successfully
    """
    # Check if Twilio credentials are available
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        print("Error: Twilio credentials not found in environment variables.")
        return False
    
    # Validate the phone number
    is_valid, result = validate_phone_number(to_phone_number)
    if not is_valid:
        print(f"Error: {result}")
        return False
    
    # Use the validated phone number
    validated_phone = result
    
    try:
        # Create Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Format phone numbers for WhatsApp if necessary
        from_number = TWILIO_PHONE_NUMBER
        to_number = validated_phone
        
        if message_type == "whatsapp":
            # Twilio requires WhatsApp numbers to be in the format 'whatsapp:+1234567890'
            from_number = f"whatsapp:{TWILIO_PHONE_NUMBER}"
            to_number = f"whatsapp:{validated_phone}"
        
        # Send message
        twilio_message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        print(f"{message_type.upper()} message sent successfully to {validated_phone}!")
        print(f"Message SID: {twilio_message.sid}")
        return True
        
    except Exception as e:
        print(f"Error sending {message_type} message: {str(e)}")
        return False


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 3:
        print("Usage: python send_message.py <phone_number> <message> [message_type]")
        print("Example SMS: python send_message.py +1234567890 'Hello from TAPBuddy!' sms")
        print("Example WhatsApp: python send_message.py +1234567890 'Hello from TAPBuddy!' whatsapp")
        sys.exit(1)
    
    # Get the arguments
    to_phone_number = sys.argv[1]
    message_content = sys.argv[2]
    
    # Get optional message type (default to SMS)
    message_type = "sms"
    if len(sys.argv) > 3:
        if sys.argv[3].lower() in ["whatsapp", "wa"]:
            message_type = "whatsapp"
        elif sys.argv[3].lower() in ["sms", "text"]:
            message_type = "sms"
        else:
            print(f"Warning: Unknown message type '{sys.argv[3]}', defaulting to 'sms'")
    
    # Validate the phone number first (without sending)
    is_valid, result = validate_phone_number(to_phone_number)
    if not is_valid:
        print(f"Error: {result}")
        print("Please provide a valid phone number in E.164 format (e.g., +1234567890)")
        sys.exit(1)
    
    # Display what we're about to do
    print(f"Sending {message_type.upper()} message to {result}...")
    print(f"Message: {message_content}")
    
    # Send the message
    send_message(to_phone_number, message_content, message_type)