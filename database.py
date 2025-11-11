import sqlite3
import json
import random
import uuid
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            parent_name TEXT,
            avatar_emoji TEXT DEFAULT '👤',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_type TEXT NOT NULL,
            contact_value TEXT NOT NULL,
            parent_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(contact_type, contact_value)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS babies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            baby_name TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            age_months INTEGER NOT NULL,
            avatar_emoji TEXT DEFAULT '👶',
            development_goals TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_title TEXT NOT NULL,
            description TEXT NOT NULL,
            age_range_min INTEGER NOT NULL,
            age_range_max INTEGER NOT NULL,
            development_type TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 10,
            icon TEXT DEFAULT '🌱',
            ai_tip TEXT,
            why_matters TEXT,
            how_to_adapt TEXT,
            what_baby_learns TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (baby_id) REFERENCES babies (id),
            FOREIGN KEY (activity_id) REFERENCES activities (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ability_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            question_text TEXT NOT NULL,
            age_range_min INTEGER NOT NULL,
            age_range_max INTEGER NOT NULL,
            difficulty_level TEXT DEFAULT 'medium',
            helpful_hint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ability_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            response TEXT NOT NULL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (baby_id) REFERENCES babies (id),
            FOREIGN KEY (question_id) REFERENCES ability_questions (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personalized_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            materials TEXT,
            how_to TEXT,
            why_it_helps TEXT,
            target_ability TEXT,
            target_domain TEXT,
            ability_state TEXT,
            duration_min INTEGER DEFAULT 10,
            illustration_url TEXT,
            safety_notes TEXT,
            reflection_prompt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (baby_id) REFERENCES babies (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS development_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id INTEGER NOT NULL,
            area_name TEXT NOT NULL,
            development_type TEXT NOT NULL,
            age_range_min INTEGER NOT NULL,
            age_range_max INTEGER NOT NULL,
            icon_emoji TEXT DEFAULT '🎯',
            background_color TEXT DEFAULT '#FDFAF5',
            description TEXT,
            activity_count INTEGER DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (baby_id) REFERENCES babies (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS area_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_id INTEGER NOT NULL,
            activity_title TEXT NOT NULL,
            short_description TEXT NOT NULL,
            materials TEXT,
            how_to TEXT,
            duration_min INTEGER DEFAULT 10,
            why_it_helps TEXT,
            safety_notes TEXT,
            reflection_prompt TEXT,
            activity_icon TEXT DEFAULT '🎯',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (area_id) REFERENCES development_areas (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY DEFAULT 1,
            current_now_playing INTEGER DEFAULT 101,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            area_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (baby_id) REFERENCES babies (id),
            FOREIGN KEY (activity_id) REFERENCES area_activities (id),
            FOREIGN KEY (area_id) REFERENCES development_areas (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duration_days INTEGER NOT NULL,
            title TEXT NOT NULL,
            tagline TEXT NOT NULL,
            description TEXT NOT NULL,
            cover_image TEXT DEFAULT '🎯',
            development_types TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenge_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            activity_title TEXT NOT NULL,
            activity_description TEXT NOT NULL,
            materials TEXT,
            how_to TEXT,
            why_it_helps TEXT,
            duration_min INTEGER DEFAULT 15,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (challenge_id) REFERENCES challenges (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenge_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_days INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (baby_id) REFERENCES babies (id),
            FOREIGN KEY (challenge_id) REFERENCES challenges (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenge_daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reflection_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (enrollment_id) REFERENCES challenge_enrollments (id),
            FOREIGN KEY (activity_id) REFERENCES challenge_activities (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id INTEGER NOT NULL,
            parent_id INTEGER NOT NULL,
            activity_date DATE NOT NULL,
            title TEXT NOT NULL,
            short_teaser TEXT NOT NULL,
            what_you_need TEXT NOT NULL,
            full_instructions TEXT NOT NULL,
            why_it_matters TEXT NOT NULL,
            tips TEXT,
            duration TEXT DEFAULT '10-15 min',
            age_range TEXT NOT NULL,
            goal_focus TEXT NOT NULL,
            domain TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(baby_id, activity_date),
            FOREIGN KEY (baby_id) REFERENCES babies (id),
            FOREIGN KEY (parent_id) REFERENCES parents (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            daily_activity_id INTEGER NOT NULL,
            baby_id INTEGER NOT NULL,
            parent_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (daily_activity_id) REFERENCES daily_activities (id),
            FOREIGN KEY (baby_id) REFERENCES babies (id),
            FOREIGN KEY (parent_id) REFERENCES parents (id),
            UNIQUE(daily_activity_id, parent_id)
        )
    ''')
    
    conn.commit()
    
    # Add age_group column to babies table if it doesn't exist
    try:
        cursor.execute('SELECT age_group FROM babies LIMIT 1')
        print("✓ 'age_group' column already exists")
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE babies ADD COLUMN age_group TEXT')
        conn.commit()
        print("✓ Added 'age_group' column to babies table")
    
    # Add baby_uuid column for session-based authentication
    try:
        cursor.execute('SELECT baby_uuid FROM babies LIMIT 1')
        print("✓ 'baby_uuid' column already exists")
    except sqlite3.OperationalError:
        # Add column without UNIQUE constraint (SQLite limitation)
        cursor.execute('ALTER TABLE babies ADD COLUMN baby_uuid TEXT')
        conn.commit()
        print("✓ Added 'baby_uuid' column to babies table")
        
        # Backfill UUIDs for existing babies
        existing_babies = cursor.execute('SELECT id FROM babies WHERE baby_uuid IS NULL').fetchall()
        for baby in existing_babies:
            new_uuid = str(uuid.uuid4())
            cursor.execute('UPDATE babies SET baby_uuid = ? WHERE id = ?', (new_uuid, baby['id']))
        conn.commit()
        if existing_babies:
            print(f"✓ Backfilled {len(existing_babies)} existing babies with UUIDs")
        
        # Create unique index on baby_uuid
        try:
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_baby_uuid ON babies(baby_uuid)')
            conn.commit()
            print("✓ Created unique index on baby_uuid")
        except sqlite3.Error as e:
            print(f"Note: Index creation error (may already exist): {e}")
    
    # Add 'now_playing' column for development_areas
    try:
        cursor.execute('SELECT now_playing FROM development_areas LIMIT 1')
        print("✓ 'now_playing' column already exists")
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE development_areas ADD COLUMN now_playing INTEGER')
        conn.commit()
        print("✓ Added 'now_playing' column to development_areas table")
    
    # Add 'parent_id' column to babies table
    try:
        cursor.execute('SELECT parent_id FROM babies LIMIT 1')
        print("✓ 'parent_id' column already exists")
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE babies ADD COLUMN parent_id INTEGER REFERENCES parents(id) ON DELETE SET NULL')
        conn.commit()
        print("✓ Added 'parent_id' column to babies table")
    
    # Migration: Add baby_id and parent_id to daily_activities table
    try:
        cursor.execute('SELECT baby_id FROM daily_activities LIMIT 1')
        print("✓ 'baby_id' column already exists in daily_activities")
    except sqlite3.OperationalError:
        # Need to add baby_id and parent_id - recreate table since they're NOT NULL
        print("⚠ Recreating daily_activities table with baby_id and parent_id columns...")
        cursor.execute('DROP TABLE IF EXISTS daily_activities')
        cursor.execute('''
            CREATE TABLE daily_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baby_id INTEGER NOT NULL,
                parent_id INTEGER NOT NULL,
                activity_date DATE NOT NULL,
                title TEXT NOT NULL,
                short_teaser TEXT NOT NULL,
                what_you_need TEXT NOT NULL,
                full_instructions TEXT NOT NULL,
                why_it_matters TEXT NOT NULL,
                tips TEXT,
                duration TEXT DEFAULT '10-15 min',
                age_range TEXT NOT NULL,
                goal_focus TEXT NOT NULL,
                domain TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(baby_id, activity_date),
                FOREIGN KEY (baby_id) REFERENCES babies (id),
                FOREIGN KEY (parent_id) REFERENCES parents (id)
            )
        ''')
        conn.commit()
        print("✓ Recreated daily_activities table with baby_id and parent_id")
    
    # Migration: Make user_id and date_of_birth nullable for session-based authentication
    # Check if migration is needed by trying to insert a test record with NULL user_id
    try:
        test_uuid = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO babies (user_id, baby_name, date_of_birth, age_months, baby_uuid, age_group) 
            VALUES (NULL, '__test__', NULL, 1, ?, '0–2 months')
        ''', (test_uuid,))
        # If this succeeds, migration already done - clean up test record
        cursor.execute('DELETE FROM babies WHERE baby_uuid = ?', (test_uuid,))
        conn.commit()
        print("✓ Babies table already supports nullable user_id and date_of_birth")
    except sqlite3.IntegrityError:
        # Migration needed - recreate table with nullable columns
        print("⟳ Migrating babies table to support session-based authentication...")
        
        # 1. Create new table with correct schema
        cursor.execute('''
            CREATE TABLE babies_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                baby_name TEXT NOT NULL,
                date_of_birth DATE,
                age_months INTEGER NOT NULL,
                avatar_emoji TEXT DEFAULT '👶',
                development_goals TEXT,
                age_group TEXT,
                baby_uuid TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Copy all existing data
        cursor.execute('''
            INSERT INTO babies_new (id, user_id, baby_name, date_of_birth, age_months, avatar_emoji, development_goals, age_group, baby_uuid, created_at)
            SELECT id, user_id, baby_name, date_of_birth, age_months, avatar_emoji, development_goals, age_group, baby_uuid, created_at
            FROM babies
        ''')
        
        # 3. Drop old table
        cursor.execute('DROP TABLE babies')
        
        # 4. Rename new table
        cursor.execute('ALTER TABLE babies_new RENAME TO babies')
        
        # 5. Recreate unique index on baby_uuid
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_baby_uuid ON babies(baby_uuid)')
        
        conn.commit()
        print("✓ Successfully migrated babies table")
    
    # Initialize app_state with random number if empty
    cursor.execute('SELECT COUNT(*) FROM app_state')
    if cursor.fetchone()[0] == 0:
        initial_number = random.randint(101, 999)
        cursor.execute(
            'INSERT INTO app_state (id, current_now_playing) VALUES (1, ?)',
            (initial_number,)
        )
        conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM activities')
    if cursor.fetchone()[0] == 0:
        seed_activities(conn)
    
    conn.close()

def seed_activities(conn):
    cursor = conn.cursor()
    
    activities = [
        {
            'title': 'Singing Time',
            'description': 'Sing nursery rhymes while making eye contact. Babies love rhythm and the connection to your voice. This builds language skills and emotional bonding. 💕',
            'age_min': 0,
            'age_max': 6,
            'dev_type': 'Linguistic',
            'duration': 10,
            'icon': '🎵',
            'ai_tip': 'Try this when your baby is calm and alert. Sing slowly and exaggerate your facial expressions!',
            'why_matters': 'At 0-6 months, babies are developing language recognition and bonding through familiar voices. Singing strengthens both!',
            'how_to_adapt': '0-3 months: Use gentle humming\n3-6 months: Add simple songs with repetition\n6+ months: Let baby vocalize along',
            'what_learns': '✓ Language recognition\n✓ Emotional bonding\n✓ Rhythm & timing\n✓ Parent-child synchrony'
        },
        {
            'title': 'Peek-a-Boo Magic',
            'description': 'Classic peek-a-boo builds trust, joy, and expectation. Repeat 5 times, celebrate each reveal with animated faces. This timeless game teaches object permanence and social connection.',
            'age_min': 6,
            'age_max': 12,
            'dev_type': 'Social-Emotional',
            'duration': 10,
            'icon': '👀',
            'ai_tip': 'Exaggerate your expressions for maximum baby delight! Make silly sounds when you reveal your face.',
            'why_matters': 'At 6-12 months, babies learn that things still exist even when they can\'t see them. This game makes learning joyful!',
            'how_to_adapt': '6-9 months: Use your hands to cover your face\n9-12 months: Hide behind a blanket or door\n12+ months: Let baby initiate the game',
            'what_learns': '✓ Object permanence\n✓ Social interaction\n✓ Cause and effect\n✓ Trust building'
        },
        {
            'title': 'Tummy Time Giggles',
            'description': 'Place baby on tummy. Make funny sounds & faces. This strengthens neck and shoulder muscles naturally while bonding through play.',
            'age_min': 0,
            'age_max': 6,
            'dev_type': 'Physical',
            'duration': 10,
            'icon': '🤸',
            'ai_tip': 'Do this when baby is alert and fed. Start with 3-5 minutes and gradually increase time.',
            'why_matters': 'Tummy time builds core strength needed for crawling, sitting, and walking. It prevents flat spots on baby\'s head too!',
            'how_to_adapt': '0-2 months: 2-3 minutes, several times daily\n2-4 months: 5-10 minutes sessions\n4-6 months: 15+ minutes with toys',
            'what_learns': '✓ Neck strength\n✓ Shoulder stability\n✓ Core muscles\n✓ Visual tracking'
        },
        {
            'title': 'Sensory Touch Time',
            'description': 'Let baby feel safe textures: soft fabric, wooden spoon, plastic bottle. Develops touch awareness and curiosity about the world.',
            'age_min': 6,
            'age_max': 12,
            'dev_type': 'Physical',
            'duration': 10,
            'icon': '✋',
            'ai_tip': 'Narrate what baby feels: "That\'s soft! That\'s smooth!" Your words help connect sensations to language.',
            'why_matters': 'Touch is baby\'s first way of learning about the world. Different textures build neural pathways and curiosity.',
            'how_to_adapt': '6-8 months: 2-3 safe textures\n8-10 months: 4-5 different textures\n10-12 months: Add temperature (warm/cool)',
            'what_learns': '✓ Tactile awareness\n✓ Fine motor skills\n✓ Curiosity\n✓ Sensory processing'
        },
        {
            'title': 'Story Snuggle',
            'description': 'Read colorful board books while pointing to pictures. Builds vocabulary through warm interaction and creates a love of reading.',
            'age_min': 12,
            'age_max': 24,
            'dev_type': 'Linguistic',
            'duration': 15,
            'icon': '📚',
            'ai_tip': 'Use different voices for characters. Make it theatrical! Let baby turn the pages even if they\'re not perfect.',
            'why_matters': 'Reading together builds vocabulary faster than any other activity. It also creates special bonding moments.',
            'how_to_adapt': '12-18 months: Point and name objects\n18-24 months: Ask "Where\'s the dog?"\n24+ months: Let them tell the story',
            'what_learns': '✓ Vocabulary expansion\n✓ Listening skills\n✓ Love of books\n✓ Bonding time'
        },
        {
            'title': 'Dance & Sway',
            'description': 'Put on music, hold baby, sway & clap together. Builds coordination, joy, and movement awareness through musical connection.',
            'age_min': 12,
            'age_max': 24,
            'dev_type': 'Physical',
            'duration': 10,
            'icon': '💃',
            'ai_tip': 'Try classical, jazz, or upbeat pop—babies love rhythm! Follow baby\'s energy level and dance accordingly.',
            'why_matters': 'Music and movement together develop coordination, rhythm, and body awareness. Plus it\'s pure joy!',
            'how_to_adapt': '12-18 months: Hold baby and sway gently\n18-24 months: Hold hands and bounce\n24+ months: Let them dance freely',
            'what_learns': '✓ Rhythm awareness\n✓ Gross motor skills\n✓ Body coordination\n✓ Joy & expression'
        },
        {
            'title': 'Mirror Play',
            'description': 'Point to baby\'s nose, ears in mirror. Say "That\'s your nose!" Builds self-awareness and identity through playful discovery.',
            'age_min': 12,
            'age_max': 24,
            'dev_type': 'Social-Emotional',
            'duration': 10,
            'icon': '🪞',
            'ai_tip': 'Play together: touch your nose, then baby\'s. Make it a game! Celebrate when they recognize themselves.',
            'why_matters': 'Self-recognition is a huge milestone! It\'s the foundation for understanding "me" and "you."',
            'how_to_adapt': '12-18 months: Point to body parts\n18-24 months: Ask "Where is your ear?"\n24+ months: Play silly faces together',
            'what_learns': '✓ Self-awareness\n✓ Body part names\n✓ Identity development\n✓ Social mirroring'
        },
        {
            'title': 'Problem Solver',
            'description': 'Hide a toy under a blanket. Encourage baby to find it. Builds object permanence and persistence through playful challenges.',
            'age_min': 18,
            'age_max': 36,
            'dev_type': 'Cognitive',
            'duration': 10,
            'icon': '🧩',
            'ai_tip': 'Make it easy at first, then gradually harder. Celebrate their effort, not just success!',
            'why_matters': 'Problem-solving skills develop when babies work through challenges. This builds confidence and thinking skills.',
            'how_to_adapt': '18-24 months: Hide partially visible\n24-30 months: Hide completely nearby\n30-36 months: Multiple hiding spots',
            'what_learns': '✓ Problem solving\n✓ Persistence\n✓ Memory skills\n✓ Spatial awareness'
        },
        {
            'title': 'Emotional Mirroring',
            'description': 'When baby cries/laughs, mirror the emotion: "You\'re happy! I\'m happy too!" Builds empathy and emotional literacy.',
            'age_min': 24,
            'age_max': 36,
            'dev_type': 'Social-Emotional',
            'duration': 10,
            'icon': '🤗',
            'ai_tip': 'Validate their emotions: "That made you sad. That\'s okay." Name feelings to build emotional vocabulary.',
            'why_matters': 'Emotional intelligence starts with recognizing and naming feelings. You\'re teaching lifelong skills!',
            'how_to_adapt': '24-30 months: Name basic emotions (happy, sad)\n30-36 months: Add more emotions (frustrated, excited)\n36+ months: Discuss why they feel that way',
            'what_learns': '✓ Emotion recognition\n✓ Empathy\n✓ Emotional vocabulary\n✓ Self-regulation'
        },
        {
            'title': 'Color Discovery',
            'description': 'Point around your home: red apple, blue cup, green plant. Repeat colors often. Builds vocabulary & pattern recognition.',
            'age_min': 24,
            'age_max': 36,
            'dev_type': 'Cognitive',
            'duration': 10,
            'icon': '🌈',
            'ai_tip': 'Start with primary colors: red, blue, yellow. Once mastered, add secondary colors!',
            'why_matters': 'Color recognition is a cognitive milestone that helps with categorization and pattern-finding skills.',
            'how_to_adapt': '24-30 months: Name colors for them\n30-33 months: Ask "What color?"\n33-36 months: Sort objects by color',
            'what_learns': '✓ Color recognition\n✓ Vocabulary\n✓ Categorization\n✓ Pattern recognition'
        },
        {
            'title': 'Stacking & Knocking',
            'description': 'Let baby stack soft blocks & knock them down. Builds fine motor skills & cause-effect understanding through playful destruction.',
            'age_min': 18,
            'age_max': 36,
            'dev_type': 'Physical',
            'duration': 10,
            'icon': '🏗️',
            'ai_tip': 'Celebrate each attempt, not just success! The knocking down is just as educational as building up.',
            'why_matters': 'Stacking requires hand-eye coordination, planning, and patience. Knocking down teaches cause and effect joyfully!',
            'how_to_adapt': '18-24 months: 2-3 blocks\n24-30 months: 4-6 blocks\n30-36 months: Create structures together',
            'what_learns': '✓ Hand-eye coordination\n✓ Fine motor skills\n✓ Cause and effect\n✓ Spatial reasoning'
        },
        {
            'title': 'Counting & Touch',
            'description': 'Count fingers, toes, toys: "One, two, three!" Point to each. Builds number awareness naturally during everyday moments.',
            'age_min': 24,
            'age_max': 36,
            'dev_type': 'Cognitive',
            'duration': 10,
            'icon': '1️⃣',
            'ai_tip': 'Do this during diaper changes or mealtimes. Repetition in daily routines helps learning stick!',
            'why_matters': 'Early math skills start with one-to-one correspondence. Counting body parts makes it personal and fun!',
            'how_to_adapt': '24-30 months: Count to 3\n30-33 months: Count to 5\n33-36 months: Count to 10',
            'what_learns': '✓ Number awareness\n✓ Counting skills\n✓ One-to-one correspondence\n✓ Math readiness'
        },
        {
            'title': 'Sound Exploration',
            'description': 'Give baby safe noisemakers: rattles, spoons on pots, bells. Encourage sound-making. Builds cause-effect & auditory skills.',
            'age_min': 6,
            'age_max': 12,
            'dev_type': 'Linguistic',
            'duration': 10,
            'icon': '🔔',
            'ai_tip': 'Narrate: "You made that sound! Again?" Your excitement encourages experimentation!',
            'why_matters': 'Babies learn they can make things happen! Sound-making develops cause-effect thinking and auditory processing.',
            'how_to_adapt': '6-8 months: One noisemaker at a time\n8-10 months: Two different sounds\n10-12 months: Let them experiment freely',
            'what_learns': '✓ Cause and effect\n✓ Auditory processing\n✓ Fine motor control\n✓ Experimentation'
        },
        {
            'title': 'Ball Rolling',
            'description': 'Roll a soft ball back and forth. Baby rolls it back (or tries!). Builds coordination, turn-taking, anticipation.',
            'age_min': 12,
            'age_max': 24,
            'dev_type': 'Physical',
            'duration': 10,
            'icon': '⚽',
            'ai_tip': 'Celebrate effort, not accuracy! Every attempt builds skills, even if the ball goes sideways.',
            'why_matters': 'Turn-taking games teach social skills and patience. Rolling builds hand-eye coordination naturally.',
            'how_to_adapt': '12-18 months: Roll gently, close distance\n18-21 months: Increase distance slightly\n21-24 months: Add gentle tosses',
            'what_learns': '✓ Hand-eye coordination\n✓ Turn-taking\n✓ Social skills\n✓ Motor planning'
        },
        {
            'title': 'Nature Walk Wonder',
            'description': 'Take a slow walk outside. Point to trees, birds, flowers. Name what you see. Builds vocabulary & sensory awareness.',
            'age_min': 24,
            'age_max': 36,
            'dev_type': 'Cognitive',
            'duration': 15,
            'icon': '🌳',
            'ai_tip': 'Go slowly. Let baby touch safe leaves, flowers. The journey is more important than the destination!',
            'why_matters': 'Nature provides endless learning opportunities! Every walk builds vocabulary, observation, and wonder.',
            'how_to_adapt': '24-30 months: Point and name things\n30-33 months: Ask them to find things\n33-36 months: Collect safe treasures',
            'what_learns': '✓ Vocabulary expansion\n✓ Observation skills\n✓ Nature connection\n✓ Sensory awareness'
        }
    ]
    
    for activity in activities:
        cursor.execute('''
            INSERT INTO activities (
                activity_title, description, age_range_min, age_range_max,
                development_type, duration_minutes, icon, ai_tip,
                why_matters, how_to_adapt, what_baby_learns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            activity['title'],
            activity['description'],
            activity['age_min'],
            activity['age_max'],
            activity['dev_type'],
            activity['duration'],
            activity['icon'],
            activity['ai_tip'],
            activity['why_matters'],
            activity['how_to_adapt'],
            activity['what_learns']
        ))
    
    conn.commit()

def create_user(email, password, parent_name='', avatar_emoji='👤'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash(password)
    
    try:
        cursor.execute(
            'INSERT INTO users (email, password, parent_name, avatar_emoji) VALUES (?, ?, ?, ?)',
            (email, hashed_password, parent_name, avatar_emoji)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def verify_password(user, password):
    return check_password_hash(user['password'], password)

def update_user_profile(user_id, parent_name, avatar_emoji):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE users SET parent_name = ?, avatar_emoji = ? WHERE id = ?',
        (parent_name, avatar_emoji, user_id)
    )
    
    conn.commit()
    conn.close()

def get_or_create_parent(contact_info):
    """Get or create a parent by contact info (email/mobile). Returns parent_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Determine contact type (simple validation)
    contact_type = 'email' if '@' in contact_info else 'mobile'
    
    # Check if parent exists
    parent = cursor.execute(
        'SELECT id FROM parents WHERE contact_type = ? AND contact_value = ?',
        (contact_type, contact_info)
    ).fetchone()
    
    if parent:
        conn.close()
        return parent['id']
    
    # Create new parent
    try:
        cursor.execute(
            'INSERT INTO parents (contact_type, contact_value) VALUES (?, ?)',
            (contact_type, contact_info)
        )
        conn.commit()
        parent_id = cursor.lastrowid
        conn.close()
        return parent_id
    except sqlite3.IntegrityError:
        # Handle race condition - parent was created between check and insert
        parent = cursor.execute(
            'SELECT id FROM parents WHERE contact_type = ? AND contact_value = ?',
            (contact_type, contact_info)
        ).fetchone()
        conn.close()
        return parent['id'] if parent else None

def get_babies_by_parent(parent_id):
    """Get all babies for a parent."""
    conn = get_db_connection()
    babies = conn.execute(
        'SELECT * FROM babies WHERE parent_id = ? ORDER BY created_at DESC',
        (parent_id,)
    ).fetchall()
    conn.close()
    return babies

def get_parent_by_id(parent_id):
    """Get parent by ID."""
    conn = get_db_connection()
    parent = conn.execute('SELECT * FROM parents WHERE id = ?', (parent_id,)).fetchone()
    conn.close()
    return parent

def age_group_to_months(age_group):
    """Convert age group string to approximate age in months (midpoint of range)"""
    age_map = {
        # New simplified age groups (6 categories)
        '0–3 Months': 2,
        '3–6 Months': 5,
        '6–12 Months': 9,
        '1–2 Years': 18,
        '2–4 Years': 36,
        '4–6 Years': 60,
        
        # Legacy age groups (backward compatibility for existing babies)
        '0–2 months': 1,
        '3–5 months': 4,
        '6–8 months': 7,
        '9–11 months': 10,
        '12–17 months': 14,
        '18–23 months': 20,
        '2–3 years': 30,
        '3–4 years': 42,
        '4–6 years': 60,
        '6–8 years': 84,
        '8–10 years': 108,
        '10–12 years': 132,
        '12+ years': 156
    }
    return age_map.get(age_group, 12)

def create_baby(user_id=None, parent_id=None, baby_name=None, date_of_birth=None, age_months=None, avatar_emoji='👶', development_goals=None, age_group=None):
    """Create a baby profile. Supports parent_id (new), user_id (legacy), and session-based UUID formats."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate unique UUID for this baby
    baby_uuid = str(uuid.uuid4())
    
    # Handle age_group (new format)
    if age_group:
        age_months = age_group_to_months(age_group)
        if not date_of_birth:
            # Generate approximate date_of_birth from age_months
            today = date.today()
            approx_year = today.year - (age_months // 12)
            approx_month = today.month - (age_months % 12)
            if approx_month <= 0:
                approx_month += 12
                approx_year -= 1
            date_of_birth = date(approx_year, approx_month, 1).isoformat()
    elif not age_months and date_of_birth:
        # Calculate age_months from date_of_birth (legacy)
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        today = date.today()
        age_months = (today.year - dob.year) * 12 + today.month - dob.month
        if today.day < dob.day:
            age_months -= 1
    
    # Default development_goals if not provided
    if development_goals is None:
        development_goals = []
    
    goals_json = json.dumps(development_goals)
    
    cursor.execute('''
        INSERT INTO babies (user_id, parent_id, baby_name, date_of_birth, age_months, avatar_emoji, development_goals, age_group, baby_uuid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, parent_id, baby_name, date_of_birth, age_months, avatar_emoji, goals_json, age_group, baby_uuid))
    
    conn.commit()
    baby_id = cursor.lastrowid
    conn.close()
    return baby_uuid  # Return UUID instead of baby_id for session-based flow

def get_baby_by_user(user_id):
    conn = get_db_connection()
    baby = conn.execute('SELECT * FROM babies WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,)).fetchone()
    conn.close()
    return baby

def get_baby_by_uuid(baby_uuid):
    """Get baby profile by UUID (for session-based authentication)"""
    conn = get_db_connection()
    baby = conn.execute('SELECT * FROM babies WHERE baby_uuid = ?', (baby_uuid,)).fetchone()
    conn.close()
    return baby

def update_baby_goals(baby_uuid, development_goals):
    """Update development goals for a baby by UUID"""
    conn = get_db_connection()
    goals_json = json.dumps(development_goals)
    conn.execute(
        'UPDATE babies SET development_goals = ? WHERE baby_uuid = ?',
        (goals_json, baby_uuid)
    )
    conn.commit()
    conn.close()

def get_activities_for_baby(age_months, development_goals=None):
    conn = get_db_connection()
    
    if development_goals and len(development_goals) > 0:
        placeholders = ','.join('?' * len(development_goals))
        query = f'''
            SELECT * FROM activities 
            WHERE age_range_min <= ? AND age_range_max >= ?
            AND development_type IN ({placeholders})
            ORDER BY RANDOM()
        '''
        params = [age_months, age_months] + development_goals
        activities = conn.execute(query, params).fetchall()
    else:
        activities = conn.execute('''
            SELECT * FROM activities 
            WHERE age_range_min <= ? AND age_range_max >= ?
            ORDER BY RANDOM()
        ''', (age_months, age_months)).fetchall()
    
    conn.close()
    return activities

def get_activity_by_id(activity_id):
    conn = get_db_connection()
    activity = conn.execute('SELECT * FROM activities WHERE id = ?', (activity_id,)).fetchone()
    conn.close()
    return activity

def complete_activity(baby_id, activity_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO completed_activities (baby_id, activity_id)
        VALUES (?, ?)
    ''', (baby_id, activity_id))
    
    conn.commit()
    conn.close()

def get_completed_activities_count(baby_id, development_type=None):
    conn = get_db_connection()
    
    if development_type:
        count = conn.execute('''
            SELECT COUNT(DISTINCT ca.activity_id) 
            FROM completed_activities ca
            JOIN activities a ON ca.activity_id = a.id
            WHERE ca.baby_id = ? AND a.development_type = ?
        ''', (baby_id, development_type)).fetchone()[0]
    else:
        count = conn.execute('''
            SELECT COUNT(*) FROM completed_activities WHERE baby_id = ?
        ''', (baby_id,)).fetchone()[0]
    
    conn.close()
    return count

def save_ability_question(domain, question_text, age_range_min, age_range_max, helpful_hint=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO ability_questions (domain, question_text, age_range_min, age_range_max, helpful_hint)
        VALUES (?, ?, ?, ?, ?)
    ''', (domain, question_text, age_range_min, age_range_max, helpful_hint))
    
    conn.commit()
    question_id = cursor.lastrowid
    conn.close()
    return question_id

def get_ability_assessments(baby_id):
    conn = get_db_connection()
    assessments = conn.execute('''
        SELECT aa.*, aq.domain, aq.question_text 
        FROM ability_assessments aa
        JOIN ability_questions aq ON aa.question_id = aq.id
        WHERE aa.baby_id = ?
        ORDER BY aa.answered_at DESC
    ''', (baby_id,)).fetchall()
    conn.close()
    return assessments

def save_ability_assessment(baby_id, question_id, response):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO ability_assessments (baby_id, question_id, response)
        VALUES (?, ?, ?)
    ''', (baby_id, question_id, response))
    
    conn.commit()
    assessment_id = cursor.lastrowid
    conn.close()
    return assessment_id

def check_assessment_today(baby_id):
    conn = get_db_connection()
    result = conn.execute('''
        SELECT COUNT(*) FROM ability_assessments 
        WHERE baby_id = ? AND DATE(answered_at) = DATE('now')
    ''', (baby_id,)).fetchone()[0]
    conn.close()
    return result > 0

def save_personalized_activity(baby_id, title, description, materials, how_to, 
                               why_it_helps, target_ability, target_domain, 
                               ability_state, duration_min, illustration_url='', 
                               safety_notes='', reflection_prompt=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO personalized_activities 
        (baby_id, title, description, materials, how_to, why_it_helps, 
         target_ability, target_domain, ability_state, duration_min, 
         illustration_url, safety_notes, reflection_prompt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (baby_id, title, description, materials, how_to, why_it_helps,
          target_ability, target_domain, ability_state, duration_min,
          illustration_url, safety_notes, reflection_prompt))
    
    conn.commit()
    activity_id = cursor.lastrowid
    conn.close()
    return activity_id

def get_personalized_activities(baby_id, limit=10):
    conn = get_db_connection()
    activities = conn.execute('''
        SELECT * FROM personalized_activities 
        WHERE baby_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (baby_id, limit)).fetchall()
    conn.close()
    return activities

def get_personalized_activity_by_id(activity_id):
    conn = get_db_connection()
    activity = conn.execute('SELECT * FROM personalized_activities WHERE id = ?', (activity_id,)).fetchone()
    conn.close()
    return activity

def complete_personalized_activity(baby_id, activity_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO completed_activities (baby_id, activity_id)
        VALUES (?, ?)
    ''', (baby_id, activity_id))
    
    conn.commit()
    conn.close()

def get_baby_by_id(baby_id):
    conn = get_db_connection()
    baby = conn.execute('SELECT * FROM babies WHERE id = ?', (baby_id,)).fetchone()
    conn.close()
    return baby

def get_development_areas(baby_id):
    conn = get_db_connection()
    areas = conn.execute('''
        SELECT * FROM development_areas 
        WHERE baby_id = ?
        ORDER BY development_type
    ''', (baby_id,)).fetchall()
    conn.close()
    return areas

def save_development_area(baby_id, area_name, development_type, age_range_min, 
                          age_range_max, icon_emoji, background_color, description, activity_count=4):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO development_areas 
        (baby_id, area_name, development_type, age_range_min, age_range_max,
         icon_emoji, background_color, description, activity_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (baby_id, area_name, development_type, age_range_min, age_range_max,
          icon_emoji, background_color, description, activity_count))
    
    conn.commit()
    area_id = cursor.lastrowid
    conn.close()
    return area_id

def get_area_by_id(area_id):
    conn = get_db_connection()
    area = conn.execute('SELECT * FROM development_areas WHERE id = ?', (area_id,)).fetchone()
    conn.close()
    return area

def get_area_activities(area_id):
    conn = get_db_connection()
    activities = conn.execute('''
        SELECT * FROM area_activities 
        WHERE area_id = ?
        ORDER BY created_at
    ''', (area_id,)).fetchall()
    conn.close()
    return activities

def get_area_activity_by_id(activity_id):
    conn = get_db_connection()
    activity = conn.execute('SELECT * FROM area_activities WHERE id = ?', (activity_id,)).fetchone()
    conn.close()
    return activity

def save_area_activity(area_id, activity_title, short_description, materials, how_to,
                       duration_min, why_it_helps, safety_notes='', reflection_prompt='', activity_icon='🎯'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO area_activities 
        (area_id, activity_title, short_description, materials, how_to,
         duration_min, why_it_helps, safety_notes, reflection_prompt, activity_icon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (area_id, activity_title, short_description, materials, how_to,
          duration_min, why_it_helps, safety_notes, reflection_prompt, activity_icon))
    
    conn.commit()
    activity_id = cursor.lastrowid
    conn.close()
    return activity_id

def mark_task_complete(baby_id, activity_id, area_id):
    """Mark a task as completed by parent. Store completion time in database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO task_completions (baby_id, activity_id, area_id, completed_at)
        VALUES (?, ?, ?, datetime('now'))
    ''', (baby_id, activity_id, area_id))
    
    conn.commit()
    conn.close()
    print(f"✓ Task completed: activity_id={activity_id}")

def is_task_completed_today(baby_id, activity_id):
    """Check if a task has been completed today by this baby."""
    conn = get_db_connection()
    
    result = conn.execute('''
        SELECT COUNT(*) as count FROM task_completions 
        WHERE baby_id = ? AND activity_id = ? 
        AND DATE(completed_at) = DATE('now')
    ''', (baby_id, activity_id)).fetchone()
    
    conn.close()
    return result['count'] > 0 if result else False

def get_completed_tasks_count_today(baby_id):
    """Get count of tasks completed TODAY by this baby."""
    conn = get_db_connection()
    
    result = conn.execute('''
        SELECT COUNT(*) as count FROM task_completions 
        WHERE baby_id = ? AND DATE(completed_at) = DATE('now')
    ''', (baby_id,)).fetchone()
    
    conn.close()
    return result['count'] if result else 0

def get_completed_task_ids_today(baby_id):
    """Get list of activity IDs completed today by this baby."""
    conn = get_db_connection()
    
    results = conn.execute('''
        SELECT DISTINCT activity_id FROM task_completions 
        WHERE baby_id = ? AND DATE(completed_at) = DATE('now')
    ''', (baby_id,)).fetchall()
    
    conn.close()
    return [row['activity_id'] for row in results] if results else []

def migrate_add_now_playing_column():
    """Add now_playing column to development_areas table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(development_areas)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'now_playing' not in columns:
        cursor.execute('ALTER TABLE development_areas ADD COLUMN now_playing INTEGER DEFAULT 0')
        conn.commit()
        print("✓ Added 'now_playing' column to development_areas table")
    else:
        print("✓ 'now_playing' column already exists")
    
    conn.close()

# ======================
# CHALLENGES HELPERS
# ======================

def get_all_challenges():
    """Get all challenge templates ordered by duration."""
    conn = get_db_connection()
    challenges = conn.execute('''
        SELECT * FROM challenges ORDER BY duration_days
    ''').fetchall()
    conn.close()
    return challenges

def get_challenge_by_id(challenge_id):
    """Get a specific challenge by ID."""
    conn = get_db_connection()
    challenge = conn.execute('''
        SELECT * FROM challenges WHERE id = ?
    ''', (challenge_id,)).fetchone()
    conn.close()
    return challenge

def save_challenge(duration_days, title, tagline, description, cover_image, development_types):
    """Save a new challenge template."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO challenges 
        (duration_days, title, tagline, description, cover_image, development_types)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (duration_days, title, tagline, description, cover_image, json.dumps(development_types)))
    
    conn.commit()
    challenge_id = cursor.lastrowid
    conn.close()
    return challenge_id

def get_challenge_activities(challenge_id, limit=None):
    """Get all activities for a challenge, optionally limited."""
    conn = get_db_connection()
    
    if limit:
        activities = conn.execute('''
            SELECT * FROM challenge_activities 
            WHERE challenge_id = ? 
            ORDER BY day_number
            LIMIT ?
        ''', (challenge_id, limit)).fetchall()
    else:
        activities = conn.execute('''
            SELECT * FROM challenge_activities 
            WHERE challenge_id = ? 
            ORDER BY day_number
        ''', (challenge_id,)).fetchall()
    
    conn.close()
    return activities

def save_challenge_activity(challenge_id, day_number, activity_title, activity_description,
                            materials, how_to, why_it_helps, duration_min=15):
    """Save a daily activity for a challenge."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO challenge_activities 
        (challenge_id, day_number, activity_title, activity_description, 
         materials, how_to, why_it_helps, duration_min)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (challenge_id, day_number, activity_title, activity_description,
          materials, how_to, why_it_helps, duration_min))
    
    conn.commit()
    activity_id = cursor.lastrowid
    conn.close()
    return activity_id

def enroll_in_challenge(baby_id, challenge_id):
    """Enroll a baby in a challenge."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if already enrolled in this challenge
    existing = conn.execute('''
        SELECT id FROM challenge_enrollments 
        WHERE baby_id = ? AND challenge_id = ? AND status = 'active'
    ''', (baby_id, challenge_id)).fetchone()
    
    if existing:
        conn.close()
        return existing['id']
    
    cursor.execute('''
        INSERT INTO challenge_enrollments 
        (baby_id, challenge_id, status, completed_days)
        VALUES (?, ?, 'active', 0)
    ''', (baby_id, challenge_id))
    
    conn.commit()
    enrollment_id = cursor.lastrowid
    conn.close()
    return enrollment_id

def get_active_challenges_for_baby(baby_id):
    """Get all active challenges for a baby."""
    conn = get_db_connection()
    
    enrollments = conn.execute('''
        SELECT ce.*, c.title, c.duration_days, c.tagline, c.cover_image
        FROM challenge_enrollments ce
        JOIN challenges c ON ce.challenge_id = c.id
        WHERE ce.baby_id = ? AND ce.status = 'active'
        ORDER BY ce.started_at DESC
    ''', (baby_id,)).fetchall()
    
    conn.close()
    return enrollments

def get_challenge_enrollment(enrollment_id):
    """Get specific challenge enrollment."""
    conn = get_db_connection()
    
    enrollment = conn.execute('''
        SELECT * FROM challenge_enrollments WHERE id = ?
    ''', (enrollment_id,)).fetchone()
    
    conn.close()
    return enrollment

def count_challenges():
    """Count total challenges in database."""
    conn = get_db_connection()
    result = conn.execute('SELECT COUNT(*) as count FROM challenges').fetchone()
    conn.close()
    return result['count'] if result else 0

def get_daily_activity(baby_id, activity_date=None):
    """Get daily activity for a specific baby and date (default: today)."""
    if activity_date is None:
        activity_date = date.today().isoformat()
    
    conn = get_db_connection()
    activity = conn.execute(
        'SELECT * FROM daily_activities WHERE baby_id = ? AND activity_date = ?',
        (baby_id, activity_date)
    ).fetchone()
    conn.close()
    return activity

def save_daily_activity(baby_id, parent_id, title, short_teaser, what_you_need, full_instructions, 
                       why_it_matters, tips, duration, age_range, goal_focus, domain, activity_date=None):
    """Save a generated daily activity for a specific baby."""
    if activity_date is None:
        activity_date = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO daily_activities 
        (baby_id, parent_id, activity_date, title, short_teaser, what_you_need, full_instructions, 
         why_it_matters, tips, duration, age_range, goal_focus, domain)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (baby_id, parent_id, activity_date, title, short_teaser, what_you_need, full_instructions,
          why_it_matters, tips, duration, age_range, goal_focus, domain))
    
    conn.commit()
    activity_id = cursor.lastrowid
    conn.close()
    return activity_id

def complete_daily_activity(daily_activity_id, baby_id, parent_id):
    """Mark a daily activity as completed by a parent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO activity_completions 
            (daily_activity_id, baby_id, parent_id)
            VALUES (?, ?, ?)
        ''', (daily_activity_id, baby_id, parent_id))
        conn.commit()
        completion_id = cursor.lastrowid
        conn.close()
        return completion_id
    except sqlite3.IntegrityError:
        # Already completed by this parent today
        conn.close()
        return None

def get_daily_activity_completion_count(daily_activity_id):
    """Get count of unique parents who completed today's activity."""
    conn = get_db_connection()
    result = conn.execute('''
        SELECT COUNT(DISTINCT parent_id) as count 
        FROM activity_completions 
        WHERE daily_activity_id = ?
    ''', (daily_activity_id,)).fetchone()
    conn.close()
    return result['count'] if result else 0

def has_completed_daily_activity(daily_activity_id, parent_id):
    """Check if a parent has already completed today's activity."""
    conn = get_db_connection()
    result = conn.execute('''
        SELECT id FROM activity_completions 
        WHERE daily_activity_id = ? AND parent_id = ?
    ''', (daily_activity_id, parent_id)).fetchone()
    conn.close()
    return result is not None

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
