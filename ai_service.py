import json
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
)

def generate_ability_questions(baby_name, age_months, development_goals):
    """
    Generate ability assessment questions using Claude based on baby age and goals.
    Returns a list of question dictionaries.
    """
    goals_text = ', '.join(development_goals)
    
    prompt = f"""You are a developmental psychology expert. Generate ability assessment questions for a {age_months}-month-old baby named {baby_name}, focusing on: {goals_text}.

Requirements:
1. Generate 5-8 questions total (mix across the selected goals)
2. Each question should be answerable by a parent with: "Mastered" / "On-Track" / "Not Sure"
3. Base on verified sources: CDC, ASQ (Ages & Stages Questionnaire), WHO milestones
4. Tone: warm, non-judgmental, empowering
5. Use baby name: {baby_name}

Format as JSON:
{{
  "questions": [
    {{
      "id": "abil_1",
      "domain": "Physical",
      "text": "Can {baby_name} roll from back to front on their own?",
      "age_range": "{age_months} months",
      "helpful_hint": "They don't need to do it perfectly every time."
    }},
    {{
      "id": "abil_2",
      "domain": "Cognitive",
      "text": "Does {baby_name} look for objects that roll or fall out of sight?",
      "age_range": "{age_months} months",
      "helpful_hint": "This shows object permanence development."
    }}
  ]
}}

Return ONLY valid JSON."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            response_text = response_text.rsplit('```', 1)[0].strip()
        
        questions_data = json.loads(response_text)
        return questions_data['questions']
    except Exception as e:
        print(f"Error generating questions: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return []

def generate_personalized_activities(baby_name, age_months, development_goals, ability_assessments):
    """
    Generate personalized activities based on ability assessment results.
    Returns a list of activity dictionaries.
    """
    goals_text = ', '.join(development_goals)
    
    ability_summary = []
    for assessment in ability_assessments:
        ability_summary.append({
            "domain": assessment['domain'],
            "ability": assessment['question_text'],
            "state": assessment['response']
        })
    
    prompt = f"""You are a developmental psychologist creating personalized activities for a parent.

Child: {baby_name}, {age_months} months old
Development Goals: {goals_text}

Ability Assessment Results:
{json.dumps(ability_summary, indent=2)}

Generate 3-5 personalized activities that:
1. Target the abilities marked as "On-Track" or "Not Sure" (needs support)
2. Celebrate abilities marked as "Mastered" with extension activities
3. Are age-appropriate and safe
4. Include clear materials, steps, and why it matters
5. Include a reflection prompt for the parent

Format as JSON:
{{
  "activities": [
    {{
      "title": "Rolling Practice with Favorite Toy",
      "description": "Help {baby_name} practice rolling by placing their favorite toy just out of reach",
      "materials": ["Soft mat", "Favorite toy", "Comfortable space"],
      "how_to": [
        "Lay {baby_name} on their back on a soft mat",
        "Place favorite toy to the side, slightly out of reach",
        "Encourage {baby_name} to reach and roll toward the toy",
        "Cheer and celebrate when they make any rolling motion",
        "Repeat 3-5 times, alternating sides"
      ],
      "why_it_helps": "Rolling builds core strength and coordination needed for sitting and crawling. It also develops spatial awareness and problem-solving as baby learns to move toward desired objects.",
      "target_domain": "Physical",
      "target_ability": "Rolling from back to front",
      "ability_state": "On-Track",
      "duration_min": 10,
      "safety_notes": "Always supervise. Use a soft surface. Stop if baby seems frustrated.",
      "reflection_prompt": "How did {baby_name} respond to this activity? Did they show more interest in rolling one direction?",
      "illustration_idea": "A happy parent and baby on a colorful mat, baby reaching toward a toy, mid-roll"
    }}
  ]
}}

Return ONLY valid JSON."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            response_text = response_text.rsplit('```', 1)[0].strip()
        
        activities_data = json.loads(response_text)
        return activities_data['activities']
    except Exception as e:
        print(f"Error generating activities: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return []

def generate_activity_illustration(activity_title, activity_description, baby_age_months):
    """
    Generate an accurate illustration for an activity using the illustration_idea from Claude.
    Returns a detailed prompt suitable for image generation.
    """
    # Determine baby's age category for accurate depiction
    if baby_age_months <= 6:
        age_desc = "newborn baby (0-6 months), lying on back or tummy"
    elif baby_age_months <= 12:
        age_desc = "infant (6-12 months), sitting with support or crawling"
    elif baby_age_months <= 24:
        age_desc = "toddler (1-2 years), standing or walking with help"
    elif baby_age_months <= 48:
        age_desc = "young toddler (2-4 years), actively playing"
    else:
        age_desc = "preschooler (4-6 years), engaged in activities"
    
    prompt = f"""A warm, gentle illustration of a parenting activity: {activity_title}.

Scene: {activity_description}

CRITICAL - Accurate representation:
- Baby age: {age_desc}
- Parent and baby doing the activity together
- Indoor home environment (living room, nursery, or play area)
- Soft, warm lighting

Visual style:
- Soft pastel color palette (pink #F4D9E8, blue #D6E8F7, mint #D4F1E4, cream #FDFAF5)
- Gentle, nurturing illustration style
- Simple, clean composition
- Focus on bonding and connection
- Baby looking happy and engaged
- Parent looking calm, loving, and attentive

Atmosphere: Warm, safe, encouraging, and joyful."""
    
    return prompt

def generate_activity_image(illustration_prompt, activity_title):
    """
    Generate an AI image for an activity based on the illustration prompt.
    Returns the path to the generated image or empty string if generation fails.
    
    MVP Implementation: Returns empty string (shows placeholder).
    Production Implementation: Integrate with image generation API (OpenAI DALL-E, Stability AI, etc.)
    via Replit integrations for secure API key management, then:
    1. Call image API with illustration_prompt
    2. Save generated image to attached_assets/activity_images/
    3. Return relative path: attached_assets/activity_images/{filename}.png
    """
    # MVP: Return empty string to show placeholder
    # This allows the system to work without external dependencies
    return ""

def generate_development_areas(baby_name, age_months, development_goals):
    """
    Call Claude to generate FUN development areas based on baby age + goals
    Uses playful names instead of clinical terms
    """
    color_map = {
        "Physical": "#D6E8F7",
        "Cognitive": "#D4F1E4",
        "Linguistic": "#FFE5CC",
        "Social-Emotional": "#F4D9E8"
    }
    
    emoji_map = {
        "Physical": "🤸",
        "Cognitive": "🧠",
        "Linguistic": "💬",
        "Social-Emotional": "💚"
    }
    
    if age_months <= 3:
        num_areas = 2
    elif age_months <= 6:
        num_areas = 3
    elif age_months <= 12:
        num_areas = 5
    elif age_months <= 24:
        num_areas = 6
    else:
        num_areas = 8
    
    goals_text = ', '.join(development_goals)
    
    prompt = f"""You are a child development expert creating FUN, playful area names (NOT clinical).

Generate {num_areas} development areas for a {age_months}-month-old baby named {baby_name}.
Development goals: {goals_text}

CRITICAL REQUIREMENTS:
1. Generate exactly {num_areas} areas
2. Use FUN, PLAYFUL names (NOT clinical/scary terms)
3. Each area gets EXACTLY 4 activities
4. Names should make parents excited, not worried
5. Include warm, encouraging descriptions

NAME STYLE EXAMPLES (good):
✅ "Puzzle Master Adventures" (instead of "Problem Solving")
✅ "Chat and Share Time" (instead of "Conversational Skills")
✅ "Wiggle and Bounce Fun" (instead of "Gross Motor Development")
✅ "Tiny Hands Explorer" (instead of "Fine Motor Control")
✅ "Feeling Friends" (instead of "Emotional Recognition")
✅ "Counting & Colors Party" (instead of "Number Recognition")
✅ "Story Time Adventures" (instead of "Narrative Skills")
✅ "Move and Play Games" (instead of "Physical Coordination")

NAME STYLE EXAMPLES (bad - avoid):
❌ "Speech and Language Disorder Prevention"
❌ "Gross Motor Milestone Tracking"
❌ "Cognitive Delay Intervention"
❌ "Emotional Regulation Deficit"

Format as JSON (ONLY return valid JSON):
{{
  "areas": [
    {{
      "name": "Puzzle Master Adventures",
      "type": "Cognitive",
      "age_min": 24,
      "age_max": 72,
      "description": "Fun problem-solving activities that help your little one think creatively and explore how things work!",
      "activity_count": 4
    }},
    {{
      "name": "Chat and Share Time",
      "type": "Linguistic",
      "age_min": 18,
      "age_max": 72,
      "description": "Playful conversations and storytelling moments that build your child's love of words and communication.",
      "activity_count": 4
    }}
  ]
}}

Make descriptions warm, encouraging, and parent-friendly (NOT scary or clinical).
EACH AREA MUST HAVE activity_count: 4 (fixed, not variable).
Return ONLY JSON, no markdown."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            response_text = response_text.rsplit('```', 1)[0].strip()
        
        areas_data = json.loads(response_text)
        
        for area in areas_data['areas']:
            area['color'] = color_map.get(area['type'], '#FDFAF5')
            area['emoji'] = emoji_map.get(area['type'], '🎯')
            area['activity_count'] = 4
        
        return areas_data['areas']
    except Exception as e:
        print(f"Error generating areas: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return []

def generate_activities_for_area(area_name, area_description, development_type, age_range_min, age_range_max):
    """
    Generate EXACTLY 4 activities for a specific development area
    All activities 5-10 minutes, age-appropriate, fun
    """
    prompt = f"""You are a child development expert. Generate EXACTLY 4 fun activities for this area:

Area: {area_name}
Development Type: {development_type}
Age Range: {age_range_min}-{age_range_max} months
Description: {area_description}

CRITICAL REQUIREMENTS:
1. Generate EXACTLY 4 activities (not 3, not 5, exactly 4)
2. Each activity: 5-10 minutes
3. All doable at home with common items
4. Safe, age-appropriate, FUN (not intimidating)
5. Tone: warm, encouraging, playful
6. Each activity has a fun emoji icon
7. Include materials, steps, why it helps, safety notes, reflection prompt

TONE EXAMPLES (good):
✅ "Wiggle and dance together!"
✅ "Explore different textures with your little explorer"
✅ "Play a fun hiding game"
❌ "Assess fine motor skills"
❌ "Evaluate bilateral coordination"

Format as JSON (ONLY return valid JSON):
{{
  "activities": [
    {{
      "title": "Activity Name",
      "short_description": "One-line fun description",
      "icon": "🎵",
      "materials": ["Item 1", "Item 2"],
      "how_to": [
        "Step 1: Description",
        "Step 2: Description",
        "Step 3: Description"
      ],
      "why_it_helps": "Why your child loves this & what they learn",
      "duration_min": 8,
      "safety_notes": "Keep it fun and safe",
      "reflection_prompt": "What did you notice?"
    }},
    {{
      "title": "Activity 2 Name",
      "short_description": "Description",
      "icon": "📚",
      "materials": ["Item"],
      "how_to": ["Step 1", "Step 2"],
      "why_it_helps": "Learning benefit",
      "duration_min": 7,
      "safety_notes": "Notes",
      "reflection_prompt": "Reflection question"
    }},
    {{
      "title": "Activity 3 Name",
      "short_description": "Description",
      "icon": "🎨",
      "materials": ["Item"],
      "how_to": ["Step 1", "Step 2"],
      "why_it_helps": "Learning benefit",
      "duration_min": 10,
      "safety_notes": "Notes",
      "reflection_prompt": "Reflection question"
    }},
    {{
      "title": "Activity 4 Name",
      "short_description": "Description",
      "icon": "🧩",
      "materials": ["Item"],
      "how_to": ["Step 1", "Step 2"],
      "why_it_helps": "Learning benefit",
      "duration_min": 6,
      "safety_notes": "Notes",
      "reflection_prompt": "Reflection question"
    }}
  ]
}}

Return ONLY JSON. Must have exactly 4 activities in the array."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            response_text = response_text.rsplit('```', 1)[0].strip()
        
        activities_data = json.loads(response_text)
        
        if len(activities_data['activities']) != 4:
            print(f"WARNING: Expected 4 activities, got {len(activities_data['activities'])}")
        
        return activities_data['activities']
    except Exception as e:
        print(f"Error generating activities for area: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return []

def generate_challenge_templates():
    """
    Generate 4 parent-child bonding challenge templates (30/90/180/365 days).
    Returns a list of challenge dictionaries.
    """
    prompt = """Create 4 parent-child bonding challenges for different durations. These are high-commitment programs that help parents build consistent bonding habits with their children.

Create challenges for: 30 days, 90 days, 180 days, and 365 days.

Each challenge should be:
- Lucrative and emotionally compelling
- Age-appropriate (0-6 years)
- Focused on building parent-child connection
- Transformational (clear before/after state)
- Encouraging and warm in tone

Return as JSON with this structure:
{
  "challenges": [
    {
      "duration": 30,
      "title": "30-Day Giggle Quest",
      "tagline": "Build Curiosity & Wonder",
      "description": "A 30-day adventure where you and your child explore the world together. Each day brings a new discovery, from sensory explorations to imaginative play. Perfect for building connection and fostering curiosity. By day 30, you'll notice your child asking more questions, laughing more, and seeking out new experiences—the foundation of lifelong learning.",
      "emoji": "🎯",
      "development_types": ["Physical", "Cognitive", "Linguistic", "Social-Emotional"]
    },
    {
      "duration": 90,
      "title": "90-Day Habit Hero",
      "tagline": "Develop Good Habits & Confidence",
      "description": "Transform your child's routine in 90 days. This challenge builds healthy habits like consistent playtime, outdoor exploration, and learning routines. Your child develops discipline, confidence, and independence. By day 90, bedtime routines are smoother, they're more curious, and you've created lasting positive patterns.",
      "emoji": "🦸",
      "development_types": ["Physical", "Cognitive", "Social-Emotional"]
    },
    {
      "duration": 180,
      "title": "180-Day Milestone Master",
      "tagline": "Unlock Major Developmental Leaps",
      "description": "Half a year of intentional development. Track your child's milestones across all developmental domains. This challenge creates sustained growth—from language expansion to complex problem-solving. By day 180, you'll see remarkable transformation in your child's confidence, vocabulary, motor skills, and emotional intelligence.",
      "emoji": "⭐",
      "development_types": ["Physical", "Cognitive", "Linguistic", "Social-Emotional"]
    },
    {
      "duration": 365,
      "title": "365-Day Growth Journey",
      "tagline": "A Year of Transformation",
      "description": "A full year of daily parent-child bonding activities tailored to your child's age. This is more than a challenge—it's a documented journey of growth. By day 365, you'll have created unbreakable bonds, fostered independence, developed key skills, and built a lifetime foundation for learning and emotional security.",
      "emoji": "🌟",
      "development_types": ["Physical", "Cognitive", "Linguistic", "Social-Emotional"]
    }
  ]
}

Return ONLY valid JSON, no markdown formatting."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            response_text = response_text.rsplit('```', 1)[0].strip()
        
        challenges_data = json.loads(response_text)
        
        return challenges_data['challenges']
    except Exception as e:
        print(f"Error generating challenge templates: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return []

def generate_challenge_daily_activities(challenge_duration, challenge_title, baby_age_months, num_days=10):
    """
    Generate sample daily activities for a challenge.
    For MVP, generates first 10 days. Full version would generate all days.
    """
    prompt = f"""Generate {num_days} daily parent-child bonding activities for the "{challenge_title}" challenge (total duration: {challenge_duration} days).

Target age: {baby_age_months} months old

Requirements for each activity:
- 10-15 minute duration
- Age-appropriate and safe
- Builds parent-child connection
- Variety across physical, cognitive, linguistic, social-emotional domains
- Materials should be common household items
- Clear, simple instructions
- Warm, encouraging tone

Format as JSON:
{{
  "activities": [
    {{
      "day_number": 1,
      "title": "Morning Cuddle & Song",
      "description": "Start the day with gentle cuddles and a favorite song",
      "materials": ["Your voice", "Comfortable spot"],
      "how_to": ["Sit comfortably with baby", "Sing a favorite song slowly", "Make gentle eye contact", "Add soft bouncing motions"],
      "why_it_helps": "Builds emotional security and language development through music and physical closeness",
      "duration_min": 10
    }}
  ]
}}

Return ONLY valid JSON with exactly {num_days} activities."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text.strip()
        
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            response_text = response_text.rsplit('```', 1)[0].strip()
        
        activities_data = json.loads(response_text)
        
        return activities_data['activities']
    except Exception as e:
        print(f"Error generating challenge activities: {e}")
        return []
