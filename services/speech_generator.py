import os
import logging
import requests
import json
import uuid
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Get API keys and settings from environment variables
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
TEMP_DIR = os.environ.get("TEMP_DIR", "./temp")

def generate_speech(script: str) -> str:
    """
    Generate speech audio from script text using text-to-speech services.
    Currently uses ElevenLabs if available, with fallback to a placeholder.
    
    Args:
        script: The narration script text
        
    Returns:
        Path to the generated audio file
    """
    logger.info("Starting speech generation")
    
    try:
        # Create temporary directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Generate a unique ID for this audio
        audio_id = str(uuid.uuid4())
        output_path = os.path.join(TEMP_DIR, f"{audio_id}.mp3")
        
        # Check if ELEVENLABS_API_KEY is available
        if ELEVENLABS_API_KEY:
            # Use ElevenLabs for voice generation
            audio_path = generate_with_elevenlabs(script, output_path)
        else:
            # Create a placeholder audio file with the script text
            audio_path = create_placeholder_audio(script, output_path)
        
        logger.info(f"Speech generation completed: {audio_path}")
        return audio_path
        
    except Exception as e:
        logger.error(f"Error in speech generation: {str(e)}", exc_info=True)
        # Return a placeholder/error audio path
        return create_placeholder_audio(
            f"Error generating speech. {str(e)}",
            os.path.join(TEMP_DIR, "error_audio.mp3")
        )


def generate_with_elevenlabs(script: str, output_path: str) -> str:
    """
    Generate speech using ElevenLabs API.
    
    Args:
        script: The narration script text
        output_path: Path to save the generated audio
        
    Returns:
        Path to the generated audio file
    """
    logger.info("Generating speech with ElevenLabs API")
    
    try:
        # ElevenLabs API endpoint for text-to-speech
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        
        # Request headers
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        # Request body
        data = {
            "text": script,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        # Send POST request to ElevenLabs API
        logger.info("Sending request to ElevenLabs API")
        response = requests.post(url, json=data, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Save the audio to the output path
            with open(output_path, "wb") as audio_file:
                audio_file.write(response.content)
            logger.info(f"ElevenLabs audio saved to {output_path}")
            return output_path
        else:
            # Log the error and fall back to placeholder
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return create_placeholder_audio(script, output_path)
            
    except Exception as e:
        logger.error(f"Error with ElevenLabs API: {str(e)}", exc_info=True)
        return create_placeholder_audio(script, output_path)


def create_placeholder_audio(script: str, output_path: str) -> str:
    """
    Create a placeholder audio file with the script text.
    In a real implementation, this would be replaced with a local TTS solution.
    
    Args:
        script: The narration script text
        output_path: Path to save the placeholder audio
        
    Returns:
        Path to the placeholder audio file
    """
    logger.info("Creating placeholder audio file")
    
    try:
        # Create a text file with the script as a placeholder for the audio
        with open(output_path, "w") as f:
            f.write(script)
        
        logger.info(f"Placeholder audio created at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating placeholder audio: {str(e)}", exc_info=True)
        # Create a minimal error audio file
        error_path = os.path.join(TEMP_DIR, "error_audio.mp3")
        with open(error_path, "w") as f:
            f.write(f"Error creating audio: {str(e)}")
        return error_path
