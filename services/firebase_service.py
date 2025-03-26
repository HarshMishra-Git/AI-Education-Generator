import os
import logging
import json
import firebase_admin
from firebase_admin import credentials, storage
from google.cloud import storage as google_storage
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Get Firebase settings from environment variables
FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS", "")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET", "")

# Firebase app instance
firebase_app = None

def initialize_firebase():
    """
    Initialize Firebase app with credentials.
    This will use the Firebase credentials from environment variables.
    """
    global firebase_app
    
    try:
        # Check if Firebase is already initialized
        if firebase_app is not None:
            return firebase_app
        
        # Check if Firebase credentials are provided
        if FIREBASE_CREDENTIALS:
            # Try to parse the credentials from environment variable (JSON string)
            try:
                cred_dict = json.loads(FIREBASE_CREDENTIALS)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError:
                # If not a JSON string, assume it's a path to the credentials file
                cred = credentials.Certificate(FIREBASE_CREDENTIALS)
            
            # Initialize the app
            firebase_app = firebase_admin.initialize_app(cred, {
                'storageBucket': FIREBASE_STORAGE_BUCKET
            })
            
            logger.info("Firebase app initialized successfully")
            return firebase_app
        else:
            logger.warning("Firebase credentials not provided, using local storage")
            return None
            
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}", exc_info=True)
        return None


def upload_file_to_firebase(file_path: str, destination_path: str) -> bool:
    """
    Upload a file to Firebase Storage.
    
    Args:
        file_path: Path to the local file
        destination_path: Destination path in Firebase Storage
        
    Returns:
        Boolean indicating whether the upload was successful
    """
    logger.info(f"Uploading file to Firebase: {file_path} -> {destination_path}")
    
    try:
        # Initialize Firebase if not already
        app = initialize_firebase()
        
        if app is None:
            logger.warning("Firebase not initialized, storing file locally")
            return False
        
        # Get bucket
        bucket = storage.bucket()
        
        # Upload file
        blob = bucket.blob(destination_path)
        blob.upload_from_filename(file_path)
        
        # Make the file publicly accessible
        blob.make_public()
        
        logger.info(f"File uploaded successfully to Firebase: {blob.public_url}")
        return True
        
    except Exception as e:
        logger.error(f"Error uploading file to Firebase: {str(e)}", exc_info=True)
        return False


def get_firebase_url(firebase_path: str) -> str:
    """
    Get the public URL for a file in Firebase Storage.
    
    Args:
        firebase_path: Path to the file in Firebase Storage
        
    Returns:
        Public URL for the file
    """
    try:
        # Initialize Firebase if not already
        app = initialize_firebase()
        
        if app is None:
            # Return a placeholder URL if Firebase is not initialized
            return f"https://storage.googleapis.com/{FIREBASE_STORAGE_BUCKET}/{firebase_path}"
        
        # Get bucket
        bucket = storage.bucket()
        
        # Get blob
        blob = bucket.blob(firebase_path)
        
        # Get public URL
        url = blob.public_url
        
        return url
        
    except Exception as e:
        logger.error(f"Error getting Firebase URL: {str(e)}", exc_info=True)
        # Return a placeholder URL
        return f"https://storage.googleapis.com/{FIREBASE_STORAGE_BUCKET}/{firebase_path}"
