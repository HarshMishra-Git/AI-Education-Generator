import os
import logging
import requests
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Get API keys and settings from environment variables
RUNWAY_ML_API_KEY = os.environ.get("RUNWAY_ML_API_KEY", "")
TEMP_DIR = os.environ.get("TEMP_DIR", "./temp")

def generate_video(content: Dict[str, Any], subject: str, audio_path: str, user_id: Optional[int] = None) -> str:
    """
    Generate a video using text-to-video APIs based on the content and audio.
    Enhanced to support additional content features and personalization.
    
    Args:
        content: The generated educational content (title, script, scenes, etc.)
        subject: The subject area (for context-appropriate visuals)
        audio_path: Path to the generated audio file
        user_id: Optional user ID for personalized video generation
        
    Returns:
        Path to the generated video file
    """
    logger.info(f"Starting enhanced video generation for {content['title']}")
    
    try:
        # Create temporary directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Generate a unique ID for this video
        video_id = str(uuid.uuid4())
        output_path = os.path.join(TEMP_DIR, f"{video_id}.mp4")
        
        # Generate metadata for the video - this will be useful for analytics and tracking
        metadata = {
            "title": content.get("title", "Educational Video"),
            "subject": subject,
            "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id,
            "content_type": "enhanced" if "interactive_elements" in content else "standard"
        }
        
        # Save metadata alongside the video for future reference
        metadata_path = os.path.join(TEMP_DIR, f"{video_id}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Choose the appropriate video generation method based on available APIs
        if RUNWAY_ML_API_KEY:
            # Use RunwayML API to generate the video
            video_path = generate_with_runway(content, subject, audio_path, output_path)
        else:
            # Check for subject-specific generation methods
            if subject == "Coding":
                video_path = generate_coding_video(content, audio_path, output_path)
            elif subject == "Science":
                video_path = generate_science_video(content, audio_path, output_path)
            else:
                # Fallback to a basic video generation method
                video_path = generate_basic_video(content, subject, audio_path, output_path)
        
        # Generate a companion content file with interactive elements
        if "interactive_elements" in content:
            companion_path = os.path.join(TEMP_DIR, f"{video_id}_companion.json")
            generate_companion_content(content, companion_path)
        
        logger.info(f"Enhanced video generation completed: {video_path}")
        return video_path
        
    except Exception as e:
        logger.error(f"Error in video generation: {str(e)}", exc_info=True)
        # Create an error video file with information
        error_path = os.path.join(TEMP_DIR, "error_video.mp4")
        with open(error_path, 'w') as f:
            f.write(f"Error generating video: {str(e)}\n")
            f.write(f"Title: {content.get('title', 'Unknown')}\n")
            f.write(f"Subject: {subject}\n")
        return error_path


def generate_with_runway(content: Dict[str, Any], subject: str, audio_path: str, output_path: str) -> str:
    """
    Generate a video using RunwayML API with enhanced scene descriptions and visual elements.
    This implementation handles the expanded content structure with visual elements.
    
    Returns:
        Path to the generated video file
    """
    logger.info("Generating enhanced video with RunwayML API")
    
    try:
        api_key = RUNWAY_ML_API_KEY
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Extract scenes from content
        scenes = content.get("scenes", [])
        
        # Create enhanced prompts for each scene, incorporating visual elements
        prompts = []
        for scene in scenes:
            # Use visual_elements if available for more specific scene generation
            visual_elements = scene.get("visual_elements", "")
            
            # Combine description and visual elements for a richer prompt
            prompt = scene["description"]
            if visual_elements:
                prompt += f" {visual_elements}"
                
            prompts.append({
                "prompt": prompt,
                "duration": scene.get("duration_seconds", 15),
                "style": get_subject_style(subject),  # Apply subject-specific style
                "negative_prompt": "poor quality, blurry, distorted"  # Avoid common issues
            })
        
        # In a production implementation, we would make actual API calls to RunwayML
        # For demonstration, we're simulating the process
        logger.info(f"Would send {len(prompts)} enhanced scenes to RunwayML API")
        
        # Simulate video generation process with progress logging
        logger.info("Simulating enhanced video generation process...")
        for i, prompt in enumerate(prompts):
            logger.info(f"Processing scene {i+1}/{len(prompts)}: {prompt['prompt'][:50]}...")
            time.sleep(0.5)  # Simulate processing time
        
        # Create a more detailed demonstration file since we're not actually generating video
        with open(output_path, 'w') as f:
            f.write(f"TAPBUDDY EDUCATIONAL VIDEO\n")
            f.write(f"==========================\n\n")
            f.write(f"Title: {content['title']}\n")
            f.write(f"Description: {content['description']}\n\n")
            
            # Include learning objectives
            if "learning_objectives" in content:
                f.write("LEARNING OBJECTIVES:\n")
                for i, obj in enumerate(content["learning_objectives"]):
                    f.write(f"{i+1}. {obj}\n")
                f.write("\n")
            
            # Include key points
            f.write("KEY POINTS:\n")
            for i, point in enumerate(content.get("key_points", [])):
                f.write(f"{i+1}. {point}\n")
            f.write("\n")
            
            # Include script
            f.write("SCRIPT:\n")
            f.write(content['script'])
            f.write("\n\n")
            
            # Include detailed scene descriptions
            f.write("SCENES:\n")
            for i, scene in enumerate(scenes):
                f.write(f"Scene {i+1}: {scene.get('description', '')}\n")
                f.write(f"Narration: {scene.get('narration', '')}\n")
                if "visual_elements" in scene:
                    f.write(f"Visual Elements: {scene.get('visual_elements', '')}\n")
                f.write(f"Duration: {scene.get('duration_seconds', 15)} seconds\n\n")
        
        logger.info(f"Enhanced video representation saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating video with RunwayML: {str(e)}", exc_info=True)
        return generate_basic_video(content, subject, audio_path, output_path)


def generate_basic_video(content: Dict[str, Any], subject: str, audio_path: str, output_path: str) -> str:
    """
    Generate a basic video by combining images with audio.
    Enhanced to include more educational elements and structure.
    
    Returns:
        Path to the generated video file
    """
    logger.info("Generating enhanced basic video with images and audio")
    
    try:
        # Create a comprehensive text representation of the video content
        with open(output_path, 'w') as f:
            f.write(f"TAPBUDDY EDUCATIONAL VIDEO\n")
            f.write(f"==========================\n\n")
            f.write(f"Title: {content['title']}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Description: {content['description']}\n\n")
            
            # Include learning objectives
            if "learning_objectives" in content:
                f.write("LEARNING OBJECTIVES:\n")
                for i, obj in enumerate(content["learning_objectives"]):
                    f.write(f"{i+1}. {obj}\n")
                f.write("\n")
            
            # Include detailed key points
            if "key_points_detailed" in content:
                f.write("KEY POINTS:\n")
                for i, point_data in enumerate(content["key_points_detailed"]):
                    point = point_data.get("point", "")
                    explanation = point_data.get("explanation", "")
                    f.write(f"{i+1}. {point}\n")
                    if explanation:
                        f.write(f"   Explanation: {explanation}\n")
                f.write("\n")
            elif "key_points" in content:
                f.write("KEY POINTS:\n")
                for i, point in enumerate(content["key_points"]):
                    f.write(f"{i+1}. {point}\n")
                f.write("\n")
            
            # Include script
            f.write("SCRIPT:\n")
            f.write(content['script'])
            f.write("\n\n")
            
            # Include detailed scene descriptions
            f.write("SCENES:\n")
            for i, scene in enumerate(content.get('scenes', [])):
                f.write(f"Scene {i+1}: {scene.get('description', '')}\n")
                f.write(f"Narration: {scene.get('narration', '')}\n")
                if "visual_elements" in scene:
                    f.write(f"Visual Elements: {scene.get('visual_elements', '')}\n")
                f.write(f"Duration: {scene.get('duration_seconds', 15)} seconds\n\n")
            
            # Include interactive elements if available
            if "interactive_elements" in content:
                interactive = content["interactive_elements"]
                
                if "questions" in interactive and interactive["questions"]:
                    f.write("ASSESSMENT QUESTIONS:\n")
                    for i, q in enumerate(interactive["questions"]):
                        f.write(f"Q{i+1}: {q.get('question', '')}\n")
                        f.write(f"A{i+1}: {q.get('answer', '')}\n\n")
                
                if "activities" in interactive and interactive["activities"]:
                    f.write("HANDS-ON ACTIVITIES:\n")
                    for i, activity in enumerate(interactive["activities"]):
                        if isinstance(activity, dict):
                            f.write(f"Activity {i+1}: {activity.get('title', '')}\n")
                            f.write(f"Description: {activity.get('description', '')}\n")
                            f.write(f"Materials: {activity.get('materials_needed', 'None')}\n\n")
                        else:
                            f.write(f"Activity {i+1}: {activity}\n\n")
            
            # Include additional resources if available
            if "additional_resources" in content:
                f.write("ADDITIONAL RESOURCES:\n")
                for i, resource in enumerate(content["additional_resources"]):
                    f.write(f"Resource {i+1}: {resource.get('title', '')}\n")
                    f.write(f"Type: {resource.get('type', '')}\n")
                    f.write(f"Description: {resource.get('description', '')}\n\n")
        
        logger.info(f"Enhanced basic video content saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating basic video: {str(e)}", exc_info=True)
        # Create a minimal error video file
        error_path = os.path.join(TEMP_DIR, "error_video.mp4")
        with open(error_path, 'w') as f:
            f.write(f"Error generating video: {str(e)}")
        return error_path


def generate_coding_video(content: Dict[str, Any], audio_path: str, output_path: str) -> str:
    """
    Generate a video specifically optimized for coding lessons.
    Includes code snippets, syntax highlighting, and step-by-step explanations.
    
    Returns:
        Path to the generated video file
    """
    logger.info("Generating coding-specific educational video")
    
    try:
        # For demonstration, we'll create a text representation of what this would look like
        with open(output_path, 'w') as f:
            f.write(f"CODING EDUCATIONAL VIDEO: {content['title']}\n")
            f.write(f"===============================================\n\n")
            f.write(f"Description: {content['description']}\n\n")
            
            # Include learning objectives
            if "learning_objectives" in content:
                f.write("LEARNING OBJECTIVES:\n")
                for i, obj in enumerate(content["learning_objectives"]):
                    f.write(f"{i+1}. {obj}\n")
                f.write("\n")
            
            # Extract coding examples from scenes and script
            f.write("CODE SNIPPETS:\n")
            scenes = content.get('scenes', [])
            code_snippets_found = False
            
            # Look for code blocks in the scenes
            for i, scene in enumerate(scenes):
                narration = scene.get('narration', '')
                description = scene.get('description', '')
                
                # Check if this scene contains code examples
                if ('code' in description.lower() or 'code' in narration.lower() or 
                    'example' in description.lower() or 'function' in narration.lower()):
                    f.write(f"Snippet {i+1} ({scene.get('duration_seconds', 15)} seconds):\n")
                    f.write(f"Description: {description}\n")
                    f.write(f"Explanation: {narration}\n\n")
                    code_snippets_found = True
            
            if not code_snippets_found:
                f.write("Basic programming examples would be included here based on the topic.\n\n")
            
            # Include debugging tips section
            f.write("DEBUGGING TIPS:\n")
            f.write("1. Common errors and their solutions\n")
            f.write("2. Testing strategies\n")
            f.write("3. Code optimization techniques\n\n")
            
            # Include the interactive coding exercises
            interactive = content.get("interactive_elements", {})
            if "activities" in interactive and interactive["activities"]:
                f.write("CODING EXERCISES:\n")
                for i, activity in enumerate(interactive["activities"]):
                    if isinstance(activity, dict):
                        f.write(f"Exercise {i+1}: {activity.get('title', '')}\n")
                        f.write(f"Instructions: {activity.get('description', '')}\n")
                        f.write(f"Tools needed: {activity.get('materials_needed', 'Code editor')}\n\n")
                    else:
                        f.write(f"Exercise {i+1}: {activity}\n\n")
            
            # Include the main script content
            f.write("MAIN TUTORIAL CONTENT:\n")
            f.write(content['script'])
            f.write("\n\n")
            
            # Include practice problems
            f.write("PRACTICE PROBLEMS:\n")
            questions = interactive.get("questions", [])
            for i, question in enumerate(questions):
                f.write(f"Problem {i+1}: {question.get('question', '')}\n")
                f.write(f"Solution: {question.get('answer', '')}\n\n")
        
        logger.info(f"Coding video content saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating coding video: {str(e)}", exc_info=True)
        return generate_basic_video(content, "Coding", audio_path, output_path)


def generate_science_video(content: Dict[str, Any], audio_path: str, output_path: str) -> str:
    """
    Generate a video specifically optimized for science lessons.
    Includes visualizations of experiments, scientific diagrams, and simulations.
    
    Returns:
        Path to the generated video file
    """
    logger.info("Generating science-specific educational video")
    
    try:
        # For demonstration, we'll create a text representation of what this would look like
        with open(output_path, 'w') as f:
            f.write(f"SCIENCE EDUCATIONAL VIDEO: {content['title']}\n")
            f.write(f"===============================================\n\n")
            f.write(f"Description: {content['description']}\n\n")
            
            # Include learning objectives
            if "learning_objectives" in content:
                f.write("LEARNING OBJECTIVES:\n")
                for i, obj in enumerate(content["learning_objectives"]):
                    f.write(f"{i+1}. {obj}\n")
                f.write("\n")
            
            # Scientific concepts section
            f.write("KEY SCIENTIFIC CONCEPTS:\n")
            for i, point in enumerate(content.get("key_points", [])):
                f.write(f"{i+1}. {point}\n")
            f.write("\n")
            
            # Extract experimental demonstrations from scenes
            f.write("VISUAL DEMONSTRATIONS & EXPERIMENTS:\n")
            scenes = content.get('scenes', [])
            
            for i, scene in enumerate(scenes):
                description = scene.get('description', '')
                narration = scene.get('narration', '')
                visual_elements = scene.get('visual_elements', '')
                
                # Check if this scene contains demonstrations or experiments
                if ('experiment' in description.lower() or 'demonstration' in description.lower() or
                    'observe' in narration.lower() or 'diagram' in visual_elements.lower()):
                    f.write(f"Demonstration {i+1} ({scene.get('duration_seconds', 15)} seconds):\n")
                    f.write(f"Description: {description}\n")
                    if visual_elements:
                        f.write(f"Visual Elements: {visual_elements}\n")
                    f.write(f"Explanation: {narration}\n\n")
            
            # Include the main script content
            f.write("SCIENTIFIC EXPLANATION:\n")
            f.write(content['script'])
            f.write("\n\n")
            
            # Include real-world applications
            f.write("REAL-WORLD APPLICATIONS:\n")
            # Extract applications from the content if possible
            applications_found = False
            for scene in scenes:
                if 'application' in scene.get('description', '').lower() or 'real world' in scene.get('narration', '').lower():
                    f.write(f"- {scene.get('description', '')}\n")
                    applications_found = True
            
            if not applications_found:
                f.write("Real-world applications of these scientific concepts would be detailed here.\n\n")
            
            # Include the hands-on experiments
            interactive = content.get("interactive_elements", {})
            if "activities" in interactive and interactive["activities"]:
                f.write("HANDS-ON EXPERIMENTS:\n")
                for i, activity in enumerate(interactive["activities"]):
                    if isinstance(activity, dict):
                        f.write(f"Experiment {i+1}: {activity.get('title', '')}\n")
                        f.write(f"Procedure: {activity.get('description', '')}\n")
                        f.write(f"Materials needed: {activity.get('materials_needed', 'Standard laboratory equipment')}\n\n")
                    else:
                        f.write(f"Experiment {i+1}: {activity}\n\n")
        
        logger.info(f"Science video content saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating science video: {str(e)}", exc_info=True)
        return generate_basic_video(content, "Science", audio_path, output_path)


def generate_companion_content(content: Dict[str, Any], output_path: str) -> None:
    """
    Generate a companion content file with interactive elements, additional resources,
    and extended learning materials.
    
    Args:
        content: The educational content dictionary
        output_path: Path to save the companion content file
    """
    logger.info("Generating companion content file")
    
    try:
        companion_data = {
            "title": content.get("title", ""),
            "description": content.get("description", ""),
            "interactive_elements": content.get("interactive_elements", {}),
            "additional_resources": content.get("additional_resources", []),
            "key_points_detailed": content.get("key_points_detailed", []),
            "learning_objectives": content.get("learning_objectives", [])
        }
        
        with open(output_path, 'w') as f:
            json.dump(companion_data, f, indent=2)
        
        logger.info(f"Companion content saved to {output_path}")
    
    except Exception as e:
        logger.error(f"Error generating companion content: {str(e)}", exc_info=True)


def get_subject_style(subject: str) -> str:
    """
    Get the appropriate visual style for a subject to guide video generation.
    
    Args:
        subject: The educational subject
        
    Returns:
        A style description for the video generation
    """
    styles = {
        "Visual Arts": "artistic, colorful, creative, aesthetic, design-focused",
        "Performing Arts": "dynamic, expressive, theatrical, movement-based",
        "Coding": "modern, tech-oriented, clean, structured, digital",
        "Financial Literacy": "professional, clear, graph-based, analytical",
        "Science": "precise, laboratory, experimental, diagram-based, factual"
    }
    
    return styles.get(subject, "educational, clear, engaging, informative")
