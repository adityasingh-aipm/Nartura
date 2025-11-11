from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import database
import ai_service
import json
import os
import random
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', os.urandom(24).hex())

@app.template_filter('from_json')
def from_json_filter(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return []
    return value if value else []

def get_now_playing():
    """
    Get current 'Now Playing' number.
    Returns a number between 101-999.
    """
    conn = database.get_db_connection()
    state = conn.execute('SELECT current_now_playing FROM app_state WHERE id = 1').fetchone()
    
    if not state:
        # Initialize if missing
        random_num = random.randint(101, 999)
        conn.execute('INSERT INTO app_state (id, current_now_playing) VALUES (1, ?)', (random_num,))
        conn.commit()
        conn.close()
        return random_num
    
    conn.close()
    return state['current_now_playing']


def update_now_playing():
    """
    Generate a new 'Now Playing' number.
    Call this when user visits the app (to create urgency/novelty).
    """
    new_number = random.randint(101, 999)
    conn = database.get_db_connection()
    conn.execute(
        'UPDATE app_state SET current_now_playing = ?, last_updated = CURRENT_TIMESTAMP WHERE id = 1',
        (new_number,)
    )
    conn.commit()
    conn.close()
    return new_number


def refresh_now_playing_if_needed():
    """
    Refresh 'Now Playing' on each page load (creates freshness).
    Optional: Can call with delay to avoid changing too frequently.
    """
    # Always generate new number for maximum urgency
    return update_now_playing()


def refresh_all_area_now_playing(baby_id):
    """
    Generate new UNIQUE 'now playing' numbers for ALL areas of a baby.
    Called on each /home visit to create freshness and variety.
    Each area gets a different random number (100-999).
    """
    conn = database.get_db_connection()
    
    # Get all areas for this baby
    areas = conn.execute(
        'SELECT id FROM development_areas WHERE baby_id = ?',
        (baby_id,)
    ).fetchall()
    
    if not areas:
        conn.close()
        return
    
    # Generate unique random numbers for all areas
    num_areas = len(areas)
    unique_numbers = random.sample(range(100, 1000), min(num_areas, 900))
    
    # Update each area with unique number
    for area, now_playing in zip(areas, unique_numbers):
        conn.execute(
            'UPDATE development_areas SET now_playing = ? WHERE id = ?',
            (now_playing, area['id'])
        )
    
    conn.commit()
    conn.close()
    print(f"DEBUG: Refreshed 'now playing' for {num_areas} areas with unique numbers")


def get_area_now_playing(area_id):
    """
    Get the 'now playing' number for a specific area.
    Returns the stored number or generates a random one if not set.
    """
    conn = database.get_db_connection()
    area = conn.execute(
        'SELECT now_playing FROM development_areas WHERE id = ?',
        (area_id,)
    ).fetchone()
    conn.close()
    
    return area['now_playing'] if area and area['now_playing'] else random.randint(100, 999)

database.init_db()
database.migrate_add_now_playing_column()

@app.route('/')
def index():
    """Landing page - show parent entry or redirect to home if session exists"""
    parent_id = session.get('parent_id')
    baby_uuid = session.get('baby_uuid')
    
    # If both parent and baby exist, go to home
    if parent_id and baby_uuid:
        baby = database.get_baby_by_uuid(baby_uuid)
        if baby:
            return redirect(url_for('home'))
    
    # If parent exists but no baby, go to create profile
    if parent_id:
        return redirect(url_for('create_profile'))
    
    # No parent - show parent entry screen
    return render_template('parent_entry.html')

@app.route('/parent-entry', methods=['POST'])
def parent_entry():
    """Handle parent contact info submission"""
    contact_info = request.form.get('contact_info', '').strip()
    
    if not contact_info:
        flash('Please enter your mobile number or email', 'error')
        return redirect(url_for('index'))
    
    # Basic validation
    if '@' in contact_info:
        # Email validation
        if not '.' in contact_info or len(contact_info) < 5:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('index'))
    else:
        # Mobile validation (simple check for digits)
        if not any(char.isdigit() for char in contact_info):
            flash('Please enter a valid mobile number', 'error')
            return redirect(url_for('index'))
    
    # Get or create parent
    parent_id = database.get_or_create_parent(contact_info)
    
    if not parent_id:
        flash('Something went wrong. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Store parent info in session
    session['parent_id'] = parent_id
    session['parent_contact'] = contact_info
    
    # Check if parent has existing babies
    existing_babies = database.get_babies_by_parent(parent_id)
    
    if existing_babies:
        # Returning parent - load their most recent baby
        most_recent_baby = existing_babies[0]
        session['baby_uuid'] = most_recent_baby['baby_uuid']
        flash(f'Welcome back! 🌿', 'success')
        return redirect(url_for('home'))
    else:
        # New parent - start onboarding
        flash('Welcome to Nurtura! Let\'s create your first baby profile 🌸', 'success')
        return redirect(url_for('create_profile'))

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    """Step 1: Create child profile (name + age group) - requires parent session"""
    # Ensure parent is authenticated
    if not session.get('parent_id'):
        flash('Please enter your contact information first', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        baby_name = request.form.get('baby_name', '').strip()
        age_group = request.form.get('age_group', '').strip()
        
        if not baby_name:
            flash('Please enter your child\'s name', 'error')
            return redirect(url_for('create_profile'))
        
        if not age_group:
            flash('Please select an age group', 'error')
            return redirect(url_for('create_profile'))
        
        # Store profile data in session for step 2
        session['baby_name'] = baby_name
        session['age_group'] = age_group
        
        return redirect(url_for('select_goals'))
    
    return render_template('create_profile.html')

@app.route('/select-goals', methods=['GET', 'POST'])
def select_goals():
    """Step 2: Select development goals - requires parent and baby data in session"""
    # Check if step 1 was completed
    if 'baby_name' not in session or not session.get('parent_id'):
        return redirect(url_for('create_profile'))
    
    if request.method == 'POST':
        development_goals = request.form.getlist('development_goals')
        
        if not development_goals:
            flash('Please select at least one development goal', 'error')
            return redirect(url_for('select_goals'))
        
        # Create baby profile in database with parent_id
        baby_uuid = database.create_baby(
            parent_id=session.get('parent_id'),
            baby_name=session['baby_name'],
            age_group=session['age_group'],
            avatar_emoji='👶',
            development_goals=development_goals
        )
        
        # Store UUID in session
        session['baby_uuid'] = baby_uuid
        
        # Clean up temporary session data
        session.pop('baby_name', None)
        session.pop('age_group', None)
        
        flash(f'Welcome to Nurtura! 🌸', 'success')
        return redirect(url_for('loading'))
    
    return render_template('select_goals.html')

@app.route('/loading')
def loading():
    """Show loading screen immediately - JS will trigger generation"""
    baby_uuid = session.get('baby_uuid')
    
    if not baby_uuid:
        return redirect(url_for('create_profile'))
    
    baby = database.get_baby_by_uuid(baby_uuid)
    
    if not baby:
        return redirect(url_for('create_profile'))
    
    return render_template('loading.html', baby_name=baby['baby_name'])

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """API endpoint to trigger AI content generation asynchronously"""
    baby_uuid = session.get('baby_uuid')
    parent_id = session.get('parent_id')
    
    if not baby_uuid or not parent_id:
        return jsonify({'error': 'Missing session data'}), 400
    
    baby = database.get_baby_by_uuid(baby_uuid)
    
    if not baby:
        return jsonify({'error': 'Baby not found'}), 404
    
    # Check if this is first time setup (no areas exist yet)
    existing_areas = database.get_development_areas(baby['id'])
    
    if not existing_areas:
        # First visit: Generate areas with AI
        development_goals = json.loads(baby['development_goals'])
        areas = ai_service.generate_development_areas(
            baby['baby_name'],
            baby['age_months'],
            development_goals
        )
        
        # Save areas with initial unique now_playing numbers
        for area in areas:
            database.save_development_area(
                baby['id'],
                area['name'],
                area['type'],
                area['age_min'],
                area['age_max'],
                area['emoji'],
                area['color'],
                area['description'],
                area['activity_count']
            )
        
        # Get saved areas and initialize unique now_playing numbers
        existing_areas = database.get_development_areas(baby['id'])
        refresh_all_area_now_playing(baby['id'])
        
        # Generate challenge templates if they don't exist
        challenges = database.get_all_challenges()
        if not challenges:
            challenge_templates = ai_service.generate_challenge_templates()
            for template in challenge_templates:
                database.save_challenge(
                    template['duration'],
                    template['title'],
                    template['tagline'],
                    template['description'],
                    template['emoji'],
                    template['development_types']
                )
    
    return jsonify({'success': True, 'ready': True})

@app.route('/logout')
def logout():
    """Clear all session data and return to parent entry"""
    session.clear()
    flash('You\'ve been logged out. Enter your details to continue! 👋', 'success')
    return redirect(url_for('index'))

@app.route('/home')
def home():
    """
    Show areas screen (homepage) with development areas and challenges for the baby.
    Generate UNIQUE 'Now Playing' number for EACH area on each visit.
    """
    baby_uuid = session.get('baby_uuid')
    parent_id = session.get('parent_id')
    
    if not baby_uuid or not parent_id:
        return redirect(url_for('create_profile'))
    
    baby = database.get_baby_by_uuid(baby_uuid)
    
    if not baby:
        return redirect(url_for('create_profile'))
    
    # Security check: verify baby belongs to current parent
    if baby['parent_id'] and baby['parent_id'] != parent_id:
        session.clear()
        flash('Session mismatch. Please log in again.', 'error')
        return redirect(url_for('index'))
    
    existing_areas = database.get_development_areas(baby['id'])
    
    # Refresh 'now playing' numbers with UNIQUE values on each visit
    if existing_areas:
        refresh_all_area_now_playing(baby['id'])
        existing_areas = database.get_development_areas(baby['id'])
    
    # Get challenges (should already be generated in loading phase)
    challenges = database.get_all_challenges()
    
    # Get parent's active challenges
    active_challenges = database.get_active_challenges_for_baby(baby['id'])
    
    return render_template('areas.html', 
                         baby=baby, 
                         areas=existing_areas,
                         challenges=challenges,
                         active_challenges=active_challenges)


@app.route('/activities/<int:area_id>')
def view_activities(area_id):
    """
    Show task list page with minimal info (icon, title, short description, duration)
    """
    baby_uuid = session.get('baby_uuid')
    if not baby_uuid:
        return redirect(url_for('create_profile'))
    
    baby = database.get_baby_by_uuid(baby_uuid)
    if not baby:
        return redirect(url_for('create_profile'))
    
    area = database.get_area_by_id(area_id)
    
    if not area or area['baby_id'] != baby['id']:
        flash('Area not found', 'error')
        return redirect(url_for('home'))
    
    existing_activities = database.get_area_activities(area_id)
    
    if not existing_activities:
        activities = ai_service.generate_activities_for_area(
            area['area_name'],
            area['description'],
            area['development_type'],
            area['age_range_min'],
            area['age_range_max']
        )
        
        for activity in activities:
            database.save_area_activity(
                area_id,
                activity['title'],
                activity['short_description'],
                json.dumps(activity.get('materials', [])),
                json.dumps(activity.get('how_to', [])),
                activity.get('duration_min', 10),
                activity.get('why_it_helps', ''),
                activity.get('safety_notes', ''),
                activity.get('reflection_prompt', ''),
                activity.get('icon', '🎯')
            )
        
        existing_activities = database.get_area_activities(area_id)
    
    # Get completed tasks for today to show checkmarks
    completed_tasks = database.get_completed_task_ids_today(baby['id'])
    
    return render_template('tasks_list.html', area=area, activities=existing_activities, baby=baby, completed_tasks=completed_tasks)

@app.route('/activity/<int:activity_id>')
def view_activity_detail(activity_id):
    """
    Show full task detail page with timer functionality and completion status.
    """
    if not session.get('baby_uuid'):
        return redirect(url_for('create_profile'))
    
    baby = database.get_baby_by_uuid(session.get('baby_uuid'))
    if not baby:
        return redirect(url_for('onboarding'))
    
    activity = database.get_area_activity_by_id(activity_id)
    
    if not activity:
        flash('Activity not found', 'error')
        return redirect(url_for('home'))
    
    area = database.get_area_by_id(activity['area_id'])
    
    if not area or area['baby_id'] != baby['id']:
        flash('Activity not found', 'error')
        return redirect(url_for('home'))
    
    # Check if this task is completed today
    completed_today = database.is_task_completed_today(baby['id'], activity_id)
    
    return render_template('task_detail.html', activity=activity, area=area, baby=baby, completed_today=completed_today)

@app.route('/timer/<int:activity_id>')
def start_timer(activity_id):
    """
    Show timer screen for activity.
    """
    if not session.get('baby_uuid'):
        return redirect(url_for('create_profile'))
    
    baby = database.get_baby_by_uuid(session.get('baby_uuid'))
    if not baby:
        return redirect(url_for('onboarding'))
    
    activity = database.get_area_activity_by_id(activity_id)
    
    if not activity:
        flash('Activity not found', 'error')
        return redirect(url_for('home'))
    
    area = database.get_area_by_id(activity['area_id'])
    
    if not area or area['baby_id'] != baby['id']:
        flash('Activity not found', 'error')
        return redirect(url_for('home'))
    
    duration_seconds = activity['duration_min'] * 60
    
    return render_template('timer.html',
                         activity=activity,
                         area=area,
                         baby=baby,
                         duration_seconds=duration_seconds,
                         duration_minutes=activity['duration_min'])


@app.route('/api/mark-task-complete/<int:activity_id>', methods=['POST'])
def api_mark_task_complete(activity_id):
    """
    API endpoint to mark task as completed.
    Called when parent finishes timer.
    """
    if not session.get('baby_uuid'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    baby = database.get_baby_by_uuid(session.get('baby_uuid'))
    if not baby:
        return jsonify({'status': 'error', 'message': 'No baby found'}), 404
    
    activity = database.get_area_activity_by_id(activity_id)
    
    if not activity:
        return jsonify({'status': 'error', 'message': 'Activity not found'}), 404
    
    area = database.get_area_by_id(activity['area_id'])
    
    if not area or area['baby_id'] != baby['id']:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Mark task as complete
    database.mark_task_complete(baby['id'], activity_id, activity['area_id'])
    
    # Get updated completion count
    completed_count = database.get_completed_tasks_count_today(baby['id'])
    
    return jsonify({
        'status': 'success',
        'message': 'Task marked as complete!',
        'completed_today': completed_count
    })


@app.route('/challenge/<int:challenge_id>')
def view_challenge(challenge_id):
    """
    Get challenge details for modal display.
    Returns JSON with challenge info and sample activities.
    """
    if not session.get('baby_uuid'):
        return redirect(url_for('create_profile'))
    
    baby = database.get_baby_by_uuid(session.get('baby_uuid'))
    if not baby:
        return redirect(url_for('onboarding'))
    
    challenge = database.get_challenge_by_id(challenge_id)
    
    if not challenge:
        flash('Challenge not found', 'error')
        return redirect(url_for('home'))
    
    # Get or generate sample activities (first 10 days for preview)
    activities = database.get_challenge_activities(challenge_id, limit=10)
    
    if not activities:
        # Generate sample activities with AI
        sample_activities = ai_service.generate_challenge_daily_activities(
            challenge['duration_days'],
            challenge['title'],
            baby['age_months'],
            num_days=10
        )
        
        for activity in sample_activities:
            database.save_challenge_activity(
                challenge_id,
                activity['day_number'],
                activity['title'],
                activity['description'],
                json.dumps(activity['materials']),
                json.dumps(activity['how_to']),
                activity['why_it_helps'],
                activity['duration_min']
            )
        
        activities = database.get_challenge_activities(challenge_id, limit=10)
    
    # Check if already enrolled
    enrolled = database.get_active_challenges_for_baby(baby['id'])
    is_enrolled = any(e['challenge_id'] == challenge_id for e in enrolled)
    
    return render_template('challenge_detail.html',
                         challenge=challenge,
                         activities=activities,
                         baby=baby,
                         is_enrolled=is_enrolled)


@app.route('/api/enroll-challenge/<int:challenge_id>', methods=['POST'])
def api_enroll_challenge(challenge_id):
    """
    API endpoint to enroll baby in a challenge.
    """
    if not session.get('baby_uuid'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    baby = database.get_baby_by_uuid(session.get('baby_uuid'))
    if not baby:
        return jsonify({'status': 'error', 'message': 'No baby found'}), 404
    
    challenge = database.get_challenge_by_id(challenge_id)
    
    if not challenge:
        return jsonify({'status': 'error', 'message': 'Challenge not found'}), 404
    
    # Enroll in challenge
    enrollment_id = database.enroll_in_challenge(baby['id'], challenge_id)
    
    return jsonify({
        'status': 'success',
        'message': f"Enrolled in {challenge['title']}!",
        'enrollment_id': enrollment_id
    })


@app.route('/coming-soon')
def coming_soon():
    return render_template('coming_soon.html')

@app.route('/debug/now-playing')
def debug_now_playing():
    """Show current 'Now Playing' number"""
    now_playing = get_now_playing()
    return jsonify({
        'now_playing': now_playing,
        'range': '101-999',
        'refreshes_on': 'Each page visit',
        'purpose': 'Social proof + urgency'
    })


@app.route('/debug/now-playing/refresh')
def debug_refresh_now_playing():
    """Manually refresh to see it change"""
    new_number = refresh_now_playing_if_needed()
    return jsonify({
        'new_now_playing': new_number,
        'message': 'Refreshed! Number changed.'
    })


@app.route('/debug/now-playing/set/<int:number>')
def debug_set_now_playing(number):
    """Set a specific number (for testing)"""
    if not (101 <= number <= 999):
        return jsonify({'error': 'Number must be between 101-999'}), 400
    
    conn = database.get_db_connection()
    conn.execute(
        'UPDATE app_state SET current_now_playing = ? WHERE id = 1',
        (number,)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'now_playing': number,
        'message': 'Set to specific number'
    })


@app.route('/debug/area-now-playing')
def debug_area_now_playing():
    """
    Show 'now playing' numbers for all areas (per-area unique numbers)
    """
    if not session.get('baby_uuid'):
        return jsonify({'error': 'Must be logged in'}), 401
    
    baby = database.get_baby_by_uuid(session.get('baby_uuid'))
    
    if not baby:
        return jsonify({'error': 'No baby found'}), 400
    
    areas = database.get_development_areas(baby['id'])
    
    result = []
    for area in areas:
        result.append({
            'area_name': area['area_name'],
            'now_playing': area['now_playing'],
            'development_type': area['development_type']
        })
    
    return jsonify({
        'baby_name': baby['baby_name'],
        'areas': result,
        'total_areas': len(result)
    })


@app.route('/debug/area-now-playing/refresh')
def debug_refresh_area_now_playing():
    """
    Manually refresh area now playing numbers (for testing)
    Shows before and after values to verify unique numbers
    """
    if not session.get('baby_uuid'):
        return jsonify({'error': 'Must be logged in'}), 401
    
    baby = database.get_baby_by_uuid(session.get('baby_uuid'))
    
    if not baby:
        return jsonify({'error': 'No baby found'}), 400
    
    # Get before values
    areas_before = database.get_development_areas(baby['id'])
    before = [{'name': a['area_name'], 'now_playing': a['now_playing']} for a in areas_before]
    
    # Refresh
    refresh_all_area_now_playing(baby['id'])
    
    # Get after values
    areas_after = database.get_development_areas(baby['id'])
    after = [{'name': a['area_name'], 'now_playing': a['now_playing']} for a in areas_after]
    
    return jsonify({
        'status': 'refreshed',
        'baby_name': baby['baby_name'],
        'before': before,
        'after': after,
        'total_areas': len(after)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
