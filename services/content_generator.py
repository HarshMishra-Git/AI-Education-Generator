import os
import json
import logging
import re
import google.generativeai as genai
from typing import Dict, Any, List, Optional

# Get Gemini API key from environment variables
from config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Get Gemini API key from environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure the Gemini API if key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_educational_content(subject: str, topic: str, level: str, query: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate educational content using Gemini API based on the student's query,
    subject, topic, and level. If user_id is provided, personalization is applied.
    
    Args:
        subject: The subject area (e.g., Visual Arts, Coding, Science)
        topic: The specific topic within the subject
        level: The difficulty level (Beginner, Intermediate, Advanced)
        query: The student's actual question or request
        user_id: Optional user ID for personalization based on past requests
    
    Returns:
        Dictionary containing the enhanced generated content
    """
    logger.info(f"Generating content for {subject} - {topic} ({level})")
    
    try:
        # Create a model instance with faster version
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Get user's past learning history for personalization if user_id is provided
        personalization_context = ""
        if user_id:
            try:
                from app import app
                with app.app_context():
                    from models import get_db, VideoRequest
                    db_session = get_db()
                    past_requests = db_session.query(VideoRequest).filter(
                        VideoRequest.user_id == user_id
                    ).order_by(VideoRequest.created_at.desc()).limit(5).all()
                    
                    if past_requests:
                        personalization_context = "Based on the student's learning history:\n"
                        for req in past_requests:
                            personalization_context += f"- Previously studied {req.subject}: {req.topic} at {req.level} level\n"
                        personalization_context += "\nTailor the content to build upon this prior knowledge.\n"
                    
                    logger.info(f"Added personalization context based on user {user_id}'s history")
            except Exception as e:
                logger.warning(f"Could not retrieve personalization data: {str(e)}")
        
        # Determine if this is a specialized subject that needs additional handling
        subject_specific_instructions = get_subject_specific_instructions(subject)
        
        # First, generate a title and description with learning objectives
        title_prompt = f"""
        Create a catchy, engaging educational title, brief description, and learning objectives for:
        Subject: {subject}
        Topic: {topic}
        Level: {level}
        Student Query: {query}
        
        {personalization_context}
        {subject_specific_instructions}

        Return exactly in this JSON format:
        {{
          "title": "Your catchy title here",
          "description": "Your brief description here (2-3 sentences)",
          "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"]
        }}
        
        Be educational and appropriate for {level} level students. Return ONLY the JSON.
        """
        
        logger.info("Generating title, description and learning objectives")
        title_response = model.generate_content(title_prompt)
        title_content = title_response.text
        
        # Parse title, description and learning objectives - with better error handling
        title = f"Learning about {topic} in {subject}"
        description = f"An educational video about {topic} for {level} students"
        learning_objectives = []
        
        try:
            # Try to extract JSON if response contains other text
            json_start = title_content.find('{')
            json_end = title_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = title_content[json_start:json_end]
                title_data = json.loads(json_content)
                title = title_data.get("title", title)
                description = title_data.get("description", description)
                learning_objectives = title_data.get("learning_objectives", [])
                
                # Ensure learning_objectives is a list
                if not isinstance(learning_objectives, list):
                    learning_objectives = [str(learning_objectives)]
            else:
                # No JSON found, try to extract title and description directly
                title_match = title_content.split("title", 1)
                if len(title_match) > 1 and ":" in title_match[1]:
                    title = title_match[1].split(":", 1)[1].strip().strip('"').strip()[:100]
                
                desc_match = title_content.split("description", 1)
                if len(desc_match) > 1 and ":" in desc_match[1]:
                    description = desc_match[1].split(":", 1)[1].strip().strip('"').strip()[:200]
                
                # Try to extract learning objectives
                objectives_match = title_content.split("learning_objectives", 1)
                if len(objectives_match) > 1:
                    obj_text = objectives_match[1]
                    # Look for list items
                    learning_objectives = []
                    lines = obj_text.split("\n")
                    for line in lines:
                        if "-" in line or "*" in line or re.match(r'^\d+\.', line):
                            obj = re.sub(r'^[\-\*\d\.]+\s*', '', line).strip()
                            if obj:
                                learning_objectives.append(obj)
                
                logger.warning(f"Using text extraction for title/description: {title[:30]}...")
        except Exception as e:
            logger.warning(f"Could not parse title/description: {str(e)}")
        
        # Now, generate key points with expanded information
        key_points_prompt = f"""
        List 4-6 key educational points about:
        Subject: {subject}
        Topic: {topic}
        Level: {level}
        Student Query: {query}
        
        {personalization_context}
        {subject_specific_instructions}

        For each key point, provide a brief explanation of why it's important.
        Return in this JSON format:
        [
          {{
            "point": "Key point 1",
            "explanation": "Why this point is important"
          }},
          // more points here...
        ]
        
        Return ONLY the JSON array.
        """
        
        logger.info("Generating key points")
        key_points_response = model.generate_content(key_points_prompt)
        key_points_content = key_points_response.text
        
        # Parse key points with better error handling
        key_points = []
        key_points_with_explanations = []
        
        try:
            # Try to find array in response
            array_start = key_points_content.find('[')
            array_end = key_points_content.rfind(']') + 1
            
            if array_start >= 0 and array_end > array_start:
                array_content = key_points_content[array_start:array_end]
                key_points_data = json.loads(array_content)
                
                if isinstance(key_points_data, list):
                    for point_data in key_points_data:
                        if isinstance(point_data, dict):
                            point = point_data.get("point", "")
                            explanation = point_data.get("explanation", "")
                            
                            if point:
                                key_points.append(point)
                                key_points_with_explanations.append({
                                    "point": point,
                                    "explanation": explanation
                                })
                elif isinstance(key_points_data, str):
                    key_points = [key_points_data]
                    key_points_with_explanations = [{"point": key_points_data, "explanation": ""}]
            
            # If we couldn't get key points from JSON, try text extraction
            if not key_points:
                # Split by numbered bullets, newlines, or dashes
                lines = key_points_content.split('\n')
                current_point = ""
                current_explanation = ""
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Check if this is a new point
                    is_new_point = False
                    for prefix in ['•', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.']:
                        if line.startswith(prefix):
                            # If we already have a point, save it before starting a new one
                            if current_point:
                                key_points.append(current_point)
                                key_points_with_explanations.append({
                                    "point": current_point,
                                    "explanation": current_explanation
                                })
                            
                            # Start a new point
                            current_point = line.replace(prefix, '', 1).strip()
                            current_explanation = ""
                            is_new_point = True
                            break
                    
                    # If not a new point, add to current explanation
                    if not is_new_point and current_point:
                        current_explanation += " " + line
                
                # Add the last point if we have one
                if current_point:
                    key_points.append(current_point)
                    key_points_with_explanations.append({
                        "point": current_point,
                        "explanation": current_explanation
                    })
                
                logger.warning(f"Using text extraction for key points: Found {len(key_points)} points")
        except Exception as e:
            logger.warning(f"Could not parse key points: {str(e)}")
        
        # If we still don't have key points, use defaults
        if not key_points:
            key_points = [f"Understanding {topic} in {subject}"]
            key_points_with_explanations = [{"point": f"Understanding {topic} in {subject}", "explanation": ""}]
        
        # Generate interactive elements (questions, activities)
        interactive_prompt = f"""
        Create educational interactive elements for:
        Subject: {subject}
        Topic: {topic}
        Level: {level}
        
        {personalization_context}
        {subject_specific_instructions}

        Return exactly in this JSON format:
        {{
          "questions": [
            {{
              "question": "Question text here?",
              "answer": "Answer text here"
            }},
            // more questions here...
          ],
          "activities": [
            {{
              "title": "Activity title",
              "description": "Activity description and instructions",
              "materials_needed": "Any materials needed (or 'None')"
            }},
            // more activities here...
          ]
        }}
        
        Include 2-3 thought-provoking questions with answers.
        Include 1-2 hands-on activities students can try themselves.
        Make everything appropriate for {level} level students.
        Return ONLY the JSON.
        """
        
        logger.info("Generating interactive elements")
        interactive_response = model.generate_content(interactive_prompt)
        interactive_content = interactive_response.text
        
        # Parse interactive elements
        questions = []
        activities = []
        
        try:
            # Try to extract JSON if response contains other text
            json_start = interactive_content.find('{')
            json_end = interactive_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = interactive_content[json_start:json_end]
                interactive_data = json.loads(json_content)
                
                # Extract questions
                if "questions" in interactive_data and isinstance(interactive_data["questions"], list):
                    for q_data in interactive_data["questions"]:
                        if isinstance(q_data, dict) and "question" in q_data:
                            questions.append({
                                "question": q_data.get("question", ""),
                                "answer": q_data.get("answer", "")
                            })
                
                # Extract activities
                if "activities" in interactive_data and isinstance(interactive_data["activities"], list):
                    for a_data in interactive_data["activities"]:
                        if isinstance(a_data, dict) and ("title" in a_data or "description" in a_data):
                            activities.append({
                                "title": a_data.get("title", f"Activity for {topic}"),
                                "description": a_data.get("description", ""),
                                "materials_needed": a_data.get("materials_needed", "None")
                            })
            else:
                # Text extraction for interactive elements
                # (This is a simplified extraction as a fallback)
                lines = interactive_content.split('\n')
                current_section = None
                current_item = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for section headers
                    lower_line = line.lower()
                    if "question" in lower_line and ":" not in lower_line:
                        current_section = "questions"
                        # Save previous item if exists
                        if current_item and "question" in current_item:
                            questions.append(current_item)
                        current_item = {}
                    elif "activit" in lower_line and ":" not in lower_line:
                        current_section = "activities"
                        # Save previous item if exists
                        if current_item and "title" in current_item:
                            activities.append(current_item)
                        current_item = {}
                    
                    # Extract content based on section
                    if current_section == "questions":
                        if "question" in lower_line and ":" in line:
                            # Save previous item if exists
                            if "question" in current_item:
                                questions.append(current_item)
                                current_item = {}
                            current_item["question"] = line.split(":", 1)[1].strip()
                        elif "answer" in lower_line and ":" in line:
                            current_item["answer"] = line.split(":", 1)[1].strip()
                            # Save this Q&A pair
                            if "question" in current_item:
                                questions.append(current_item)
                                current_item = {}
                    
                    elif current_section == "activities":
                        if "title" in lower_line and ":" in line:
                            # Save previous item if exists
                            if "title" in current_item:
                                activities.append(current_item)
                                current_item = {}
                            current_item["title"] = line.split(":", 1)[1].strip()
                        elif "description" in lower_line and ":" in line:
                            current_item["description"] = line.split(":", 1)[1].strip()
                        elif "material" in lower_line and ":" in line:
                            current_item["materials_needed"] = line.split(":", 1)[1].strip()
                            # Save this activity
                            if "title" in current_item or "description" in current_item:
                                activities.append(current_item)
                                current_item = {}
                
                # Add the last item if not already added
                if current_section == "questions" and "question" in current_item:
                    questions.append(current_item)
                elif current_section == "activities" and ("title" in current_item or "description" in current_item):
                    activities.append(current_item)
        except Exception as e:
            logger.warning(f"Could not parse interactive elements: {str(e)}")
        
        # Generate additional resources
        resources_prompt = f"""
        Suggest educational resources for further learning about:
        Subject: {subject}
        Topic: {topic}
        Level: {level}
        
        {subject_specific_instructions}

        Return exactly in this JSON format:
        [
          {{
            "type": "website", 
            "title": "Resource title", 
            "description": "Brief description"
          }},
          // more resources here...
        ]
        
        Include 3-4 different types of resources (websites, videos, books, practice exercises).
        Make all resources appropriate for {level} level students.
        Resources should be specific and educational.
        Return ONLY the JSON array.
        """
        
        logger.info("Generating additional resources")
        resources_response = model.generate_content(resources_prompt)
        resources_content = resources_response.text
        
        # Parse additional resources
        additional_resources = []
        
        try:
            # Try to find array in response
            array_start = resources_content.find('[')
            array_end = resources_content.rfind(']') + 1
            
            if array_start >= 0 and array_end > array_start:
                array_content = resources_content[array_start:array_end]
                resources_data = json.loads(array_content)
                
                if isinstance(resources_data, list):
                    for resource in resources_data:
                        if isinstance(resource, dict):
                            additional_resources.append({
                                "type": resource.get("type", "website"),
                                "title": resource.get("title", f"Resource for {topic}"),
                                "description": resource.get("description", "")
                            })
            else:
                # Text extraction for resources
                lines = resources_content.split('\n')
                current_resource = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this is a new resource (starts with bullet or number)
                    is_new_resource = False
                    for prefix in ['•', '-', '*', '1.', '2.', '3.', '4.', '5.']:
                        if line.startswith(prefix):
                            # Save previous resource if exists
                            if current_resource and "title" in current_resource:
                                additional_resources.append(current_resource)
                            
                            # Start a new resource
                            current_resource = {
                                "type": "website",  # Default type
                                "title": line.replace(prefix, '', 1).strip(),
                                "description": ""
                            }
                            
                            # Try to determine resource type from the line
                            lower_line = line.lower()
                            if "video" in lower_line or "youtube" in lower_line or "watch" in lower_line:
                                current_resource["type"] = "video"
                            elif "book" in lower_line or "read" in lower_line:
                                current_resource["type"] = "book"
                            elif "exercise" in lower_line or "practice" in lower_line or "worksheet" in lower_line:
                                current_resource["type"] = "practice"
                            
                            is_new_resource = True
                            break
                    
                    # If this continues a resource description
                    if not is_new_resource and current_resource and "title" in current_resource:
                        if not current_resource["description"]:
                            current_resource["description"] = line
                        else:
                            current_resource["description"] += " " + line
                
                # Add the last resource if not already added
                if current_resource and "title" in current_resource:
                    additional_resources.append(current_resource)
        except Exception as e:
            logger.warning(f"Could not parse additional resources: {str(e)}")
        
        # Generate script and scenes with visual elements
        script_prompt = f"""
        Create an educational script and detailed scene descriptions for a video about:
        Subject: {subject}
        Topic: {topic}
        Level: {level}
        Student Query: {query}
        
        {personalization_context}
        {subject_specific_instructions}

        Return exactly in this JSON format:
        {{
          "script": "Your complete script here",
          "scenes": [
            {{
              "description": "Detailed visual description for scene 1",
              "narration": "What is said in scene 1",
              "visual_elements": "Key visual elements to include (diagrams, text overlays, etc.)",
              "duration_seconds": 10
            }},
            // more scenes here...
          ]
        }}
        
        The script should be educational and detailed (2-3 minutes).
        Include 5-8 scenes total with specific visual descriptions.
        Each scene should have clear visual elements described.
        Make the content appropriate for {level} level students.
        Return ONLY the JSON.
        """
        
        logger.info("Generating script and scenes")
        script_response = model.generate_content(script_prompt)
        script_content = script_response.text
        
        # Parse script and scenes with better error handling
        script = f"In this video, we'll explore {topic} in {subject}."
        scenes = []
        
        try:
            # Try to extract JSON if response contains other text
            json_start = script_content.find('{')
            json_end = script_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = script_content[json_start:json_end]
                script_data = json.loads(json_content)
                script = script_data.get("script", script)
                
                scenes_data = script_data.get("scenes", [])
                for scene in scenes_data:
                    if isinstance(scene, dict):
                        scenes.append({
                            "description": scene.get("description", f"Scene about {topic}"),
                            "narration": scene.get("narration", f"Information about {topic}"),
                            "visual_elements": scene.get("visual_elements", ""),
                            "duration_seconds": scene.get("duration_seconds", 15)
                        })
            else:
                # Try to extract script directly
                script_parts = script_content.split("script", 1)
                if len(script_parts) > 1 and ":" in script_parts[1]:
                    script_text = script_parts[1].split("scenes", 1)[0].split(":", 1)[1].strip().strip('"').strip()
                    script = script_text
                
                # Extract scenes using regex or simple text parsing
                scenes_match = re.search(r'scenes.*?:(.*?)(?=\}|$)', script_content, re.DOTALL)
                if scenes_match:
                    scenes_text = scenes_match.group(1)
                    scene_blocks = re.findall(r'\{(.*?)\}', scenes_text, re.DOTALL)
                    
                    for block in scene_blocks:
                        scene = {}
                        
                        # Extract each property
                        desc_match = re.search(r'description.*?:(.*?)(?=,|\}|$)', block, re.DOTALL)
                        if desc_match:
                            scene["description"] = desc_match.group(1).strip().strip('"').strip()
                        
                        narr_match = re.search(r'narration.*?:(.*?)(?=,|\}|$)', block, re.DOTALL)
                        if narr_match:
                            scene["narration"] = narr_match.group(1).strip().strip('"').strip()
                        
                        visual_match = re.search(r'visual_elements.*?:(.*?)(?=,|\}|$)', block, re.DOTALL)
                        if visual_match:
                            scene["visual_elements"] = visual_match.group(1).strip().strip('"').strip()
                        
                        duration_match = re.search(r'duration_seconds.*?:(\d+)', block)
                        if duration_match:
                            scene["duration_seconds"] = int(duration_match.group(1))
                        else:
                            scene["duration_seconds"] = 15
                        
                        if "description" in scene or "narration" in scene:
                            scenes.append(scene)
                
                if not scenes:
                    # Default scenes
                    scenes = [
                        {
                            "description": f"Introduction to {topic}",
                            "narration": f"Welcome to this educational video about {topic} in {subject}.",
                            "visual_elements": "Title screen with topic name and engaging background",
                            "duration_seconds": 10
                        },
                        {
                            "description": f"Explaining the basics of {topic}",
                            "narration": f"Let's start by understanding the basics of {topic}.",
                            "visual_elements": "Simple diagram showing key concepts",
                            "duration_seconds": 20
                        }
                    ]
                
                logger.warning(f"Using text extraction for script: {script[:30]}...")
        except Exception as e:
            logger.warning(f"Could not parse script/scenes: {str(e)}")
            # Default values are already set
        
        # Ensure we have default values for missing fields
        if not learning_objectives:
            learning_objectives = generate_default_content("learning_objectives", subject, topic)
        
        if not key_points_with_explanations:
            key_points_with_explanations = [{
                "point": point,
                "explanation": ""
            } for point in key_points]
        
        if not questions:
            questions = generate_default_content("questions", subject, topic)
        
        if not activities:
            activities = generate_default_content("activities", subject, topic)
        
        if not additional_resources:
            additional_resources = generate_default_content("additional_resources", subject, topic)
        
        if not scenes:
            scenes = generate_default_content("scenes", subject, topic)
        
        # Combine all parts into our final content dictionary
        content = {
            "title": title,
            "description": description,
            "learning_objectives": learning_objectives,
            "key_points": key_points,
            "key_points_detailed": key_points_with_explanations,
            "script": script,
            "scenes": scenes,
            "interactive_elements": {
                "questions": questions,
                "activities": activities
            },
            "additional_resources": additional_resources
        }
        
        # Validate the required fields are present
        required_fields = ["title", "description", "script", "scenes", "key_points"]
        for field in required_fields:
            if field not in content:
                content[field] = generate_default_content(field, subject, topic)
        
        logger.info(f"Successfully generated enhanced content for {topic}")
        return content
    
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        # Return default content in case of an error
        return {
            "title": f"Learning about {topic} in {subject}",
            "description": f"An educational video about {topic} for {level} students",
            "learning_objectives": generate_default_content("learning_objectives", subject, topic),
            "key_points": [f"Basic understanding of {topic}"],
            "key_points_detailed": [{"point": f"Basic understanding of {topic}", "explanation": ""}],
            "script": f"In this video, we'll explore {topic} in {subject}. This is an important topic for {level} students.",
            "scenes": generate_default_content("scenes", subject, topic),
            "interactive_elements": {
                "questions": generate_default_content("questions", subject, topic),
                "activities": generate_default_content("activities", subject, topic)
            },
            "additional_resources": generate_default_content("additional_resources", subject, topic)
        }


def get_subject_specific_instructions(subject: str) -> str:
    """
    Get subject-specific instructions for content generation
    """
    if subject == "Coding":
        return """
        For coding lessons:
        1. Include specific code examples with line-by-line explanations
        2. Add debugging tips and common pitfalls
        3. Include practical exercises with solutions
        4. Ensure code is accurate and follows best practices
        5. Add interactive elements where students can modify code
        """
    elif subject == "Science":
        return """
        For science lessons:
        1. Include descriptions of visual experiments or demonstrations
        2. Explain scientific concepts using analogies
        3. Include real-world applications of the concepts
        4. Add visual representations of scientific processes
        5. Include questions that promote critical thinking
        """
    elif subject == "Financial Literacy":
        return """
        For financial lessons:
        1. Include practical examples with real numbers
        2. Add step-by-step calculations
        3. Explain financial concepts using everyday scenarios
        4. Include tips for practical application
        5. Add visual representations of financial concepts
        """
    elif subject == "Visual Arts":
        return """
        For visual arts lessons:
        1. Include descriptions of artistic techniques and styles
        2. Provide step-by-step instructions for creating art
        3. Include examples of notable artworks related to the topic
        4. Add tips for improving artistic skills
        5. Include visual references and color theory where applicable
        """
    elif subject == "Performing Arts":
        return """
        For performing arts lessons:
        1. Include descriptions of performance techniques
        2. Provide examples of notable performances
        3. Add tips for stage presence and expression
        4. Include practice exercises for skill development
        5. Explain cultural and historical context where relevant
        """
    else:
        return f"""
        For {subject} lessons:
        1. Provide clear, concise explanations of key concepts
        2. Include practical examples and applications
        3. Use visual aids and diagrams to illustrate points
        4. Add interactive elements to engage students
        5. Include questions that test understanding
        """


def generate_default_content(field: str, subject: str, topic: str) -> Any:
    """
    Generate default content for a specific field if the API response is missing it
    """
    if field == "title":
        return f"Learning about {topic} in {subject}"
    elif field == "description":
        return f"An educational video about {topic} in {subject}"
    elif field == "learning_objectives":
        return [
            f"Understand the basic concepts of {topic}",
            f"Apply knowledge of {topic} in practical situations",
            f"Analyze and evaluate information related to {topic}"
        ]
    elif field == "script":
        return f"In this video, we'll explore {topic} in {subject}."
    elif field == "scenes":
        return [
            {
                "description": f"Introduction to {topic}",
                "narration": f"Welcome to this educational video about {topic} in {subject}.",
                "visual_elements": "Title screen with topic name and relevant visuals",
                "duration_seconds": 10
            },
            {
                "description": f"Explaining the basics of {topic}",
                "narration": f"Let's start by understanding the basics of {topic}.",
                "visual_elements": "Simple diagram showing key concepts",
                "duration_seconds": 20
            }
        ]
    elif field == "key_points":
        return [f"Basic understanding of {topic}", f"Practical applications of {topic}", f"Key concepts in {topic}"]
    elif field == "questions":
        return [
            {"question": f"What is {topic}?", "answer": f"A basic explanation of {topic}."},
            {"question": f"How can you apply {topic} in real life?", "answer": f"There are several practical applications..."}
        ]
    elif field == "activities":
        return [
            {
                "title": f"Practice with {topic}",
                "description": f"Try this simple activity to reinforce your understanding of {topic}.",
                "materials_needed": "Pencil and paper"
            }
        ]
    elif field == "additional_resources":
        return [
            {"type": "website", "title": f"{subject} Resources", "description": f"Educational resources about {topic}."},
            {"type": "video", "title": f"{topic} Tutorial", "description": "Video tutorial with step-by-step instructions."},
            {"type": "practice", "title": "Practice Exercises", "description": "Exercises to reinforce learning."}
        ]
    return None
