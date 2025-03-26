import os
import sys
from twilio.rest import Client

def send_test_sms(to_number: str, message: str | None = None):
    """
    Send a test SMS message using Twilio.
    This function is for testing purposes only to verify Twilio credentials.
    
    Args:
        to_number: The recipient's phone number (including country code, e.g., +1234567890)
        message: Optional custom message. If not provided, a default message will be used.
    """
    # Get Twilio credentials
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # Default message if none provided
    default_message = "This is a test message from TAPBuddy AI Video Generator"
    message_to_send = message if message is not None else default_message
    
    # Check if credentials are available
    if not account_sid or not auth_token or not from_number:
        print("Error: Twilio credentials not found in environment variables.")
        return False
    
    try:
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Send SMS message
        sms_message = client.messages.create(
            body=message_to_send,
            from_=from_number,
            to=to_number
        )
        
        print(f"SMS message sent successfully to {to_number}!")
        print(f"Message SID: {sms_message.sid}")
        return True
    except Exception as e:
        print(f"Error sending SMS message: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if a phone number was provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python send_test_sms.py <phone_number> [message]")
        print("Example: python send_test_sms.py +1234567890 'Hello from TAPBuddy!'")
        sys.exit(1)
    
    # Get the phone number from command-line arguments
    to_phone_number = sys.argv[1]
    
    # Get optional message from command-line arguments
    message = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Send the SMS message
    send_test_sms(to_phone_number, message)