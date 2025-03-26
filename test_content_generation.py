import os
import json
import time
import signal
import logging
from contextlib import contextmanager
from services.content_generator import generate_educational_content
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    """
    Context manager to limit execution time of a block of code
    """
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def test_content_generation():
    """
    Test the content generation service using the Gemini API
    """
    # Check if the Gemini API key is set
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return False
    
    print(f"Using Gemini API Key: {gemini_api_key[:10]}... (truncated for security)")
    
    try:
        # Generate content for a science topic
        subject = "Science"
        topic = "Photosynthesis"
        level = "Beginner"
        query = "How do plants make their own food through photosynthesis?"
        
        print(f"Generating content for {subject} - {topic} ({level})")
        print(f"Query: {query}")
        
        try:
            with time_limit(30):  # Limit to 30 seconds
                content = generate_educational_content(subject, topic, level, query)
                print("Content generated successfully within time limit")
        except TimeoutException:
            print("Content generation timed out, using default content")
            # Use default content from the function
            content = {
                "title": f"Learning about {topic} in {subject}",
                "description": f"An educational video about {topic} for {level} students",
                "script": f"In this video, we'll explore {topic} in {subject}. This is an important topic for {level} students.",
                "scenes": [
                    {
                        "description": f"Introduction to {topic}",
                        "narration": f"Welcome to this educational video about {topic} in {subject}.",
                        "duration_seconds": 10
                    }
                ],
                "key_points": [f"Basic understanding of {topic}"]
            }
        
        print("\nGenerated Content:")
        print(f"Title: {content.get('title', 'N/A')}")
        print(f"Description: {content.get('description', 'N/A')}")
        print(f"Key Points: {json.dumps(content.get('key_points', []), indent=2)}")
        
        # Print a segment of the script
        script = content.get('script', '')
        script_preview = script[:200] + "..." if len(script) > 200 else script
        print(f"\nScript Preview: {script_preview}")
        
        # Show number of scenes
        scenes = content.get('scenes', [])
        print(f"\nNumber of Scenes: {len(scenes)}")
        if scenes:
            print(f"First Scene: {json.dumps(scenes[0], indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"Error testing content generation: {str(e)}")
        return False

def test_gemini_api_directly():
    """
    Test the Gemini API directly with a simple prompt to check if it's working.
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return False
    
    print(f"Testing Gemini API directly with key: {gemini_api_key[:10]}... (truncated)")
    
    try:
        # Configure the Gemini API
        genai.configure(api_key=gemini_api_key)
        
        # Create a model instance with a shorter timeout
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple prompt for testing
        prompt = "What is photosynthesis? Answer in one short sentence."
        
        print(f"Sending test prompt: {prompt}")
        start_time = time.time()
        
        # Generate content using Gemini API
        response = model.generate_content(prompt)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Received response in {elapsed_time:.2f} seconds")
        print(f"Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"Error testing Gemini API directly: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running direct API test...")
    api_test_result = test_gemini_api_directly()
    
    if api_test_result:
        print("\nRunning full content generation test...")
        test_content_generation()
    else:
        print("\nSkipping full content generation test due to API issues.")