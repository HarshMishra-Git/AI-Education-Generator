import os
import sys
from services.whatsapp_service import send_whatsapp_message

def send_test_whatsapp(to_phone_number: str, message: str | None = None):
    """
    Send a test WhatsApp message using the TAPBuddy service.
    
    Args:
        to_phone_number: The recipient's phone number (including country code, e.g., +1234567890)
        message: Optional custom message. If not provided, a default message will be used.
    """
    default_message = "Hello from TAPBuddy! This is a test WhatsApp message. Reply with '#Science #Photosynthesis #Beginner How does photosynthesis work?' to test the video generation system."
    message_to_send = message if message is not None else default_message
    
    # Check if Twilio credentials are available
    if not os.environ.get("TWILIO_ACCOUNT_SID") or not os.environ.get("TWILIO_AUTH_TOKEN") or not os.environ.get("TWILIO_PHONE_NUMBER"):
        print("Error: Twilio credentials not found in environment variables.")
        return False
    
    # Send the WhatsApp message
    result = send_whatsapp_message(to_phone_number, message_to_send)
    
    if result:
        print(f"WhatsApp message sent successfully to {to_phone_number}")
        return True
    else:
        print(f"Failed to send WhatsApp message to {to_phone_number}")
        return False

if __name__ == "__main__":
    # Check if a phone number was provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python send_whatsapp.py <phone_number> [message]")
        print("Example: python send_whatsapp.py +1234567890 'Hello from TAPBuddy!'")
        sys.exit(1)
    
    # Get the phone number from command-line arguments
    to_phone_number = sys.argv[1]
    
    # Get optional message from command-line arguments
    message = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Send the WhatsApp message
    send_test_whatsapp(to_phone_number, message)