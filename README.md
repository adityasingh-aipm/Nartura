# Nurtura - Parenting Copilot MVP

## Overview
Nurtura is an empathetic parenting application designed to help parents track child development and provide personalized, science-backed bonding activities for children aged 0-6 years. It aims to offer a supportive experience akin to consulting a pediatrician or parenting coach. The MVP is a web application focusing on matching age-appropriate developmental activities and tracking progress, with key capabilities including a two-screen flow for development areas and activities, AI-powered generation of personalized content, and mobile-first optimization. The project seeks to create a caring and supportive user experience with a strong emphasis on data privacy and security, with ambitions to create a "Netflix for Parenting" with data-driven insights and a supportive community.

## User Preferences
Preferred communication style: Simple, everyday language.
- **Tone**: Warm, empathetic, supportive - like a caring pediatrician/parenting coach
- **Visual Language**: Soft, pastel colors with generous spacing and rounded corners for a baby-friendly aesthetic
- **Interaction Style**: Gentle animations, encouraging feedback, emoji-rich communication
- **Privacy First**: Emphasis on data security and privacy for sensitive child information

## System Architecture

### Frontend Architecture
The application uses Flask's Jinja2 templating engine with a base template for consistent UI. A comprehensive CSS design system prioritizes emotional warmth and trust, featuring a pastel color palette, specific typography (Poppins, Inter, Nunito), 8px base unit spacing, and custom CSS animations. A mobile-first responsive design approach is implemented, with touch-friendly UIs, horizontal scroll tabs, and advanced mobile features like iPhone notch support. The UI includes unique "Now Playing" numbers per area card to create dynamic freshness. The design emphasizes a two-screen flow for tasks and activities, separating lists from detailed views. Onboarding has been streamlined to a single screen. Challenge sections and timer/task completion tracking are integrated with responsive designs.

### Backend Architecture
Nurtura is a Flask-based monolithic application with parent-authenticated multi-baby architecture. Parents enter their contact information (mobile or email) first, then create and manage multiple baby profiles. Route handlers manage both parent and baby flows, and session management uses secure Flask cookies storing `parent_id`, `parent_contact`, and `baby_uuid`. The `database.py` module provides abstraction over SQLite operations, including parent lookup/creation, baby UUID generation, and session-based profile retrieval. Server-side session storage maintains both parent context and active baby profile context, with ownership verification on all baby-related routes.

### Data Storage
A SQLite relational database (`database.db`) stores parent, baby, and activity data. The schema includes `parents`, `babies`, `development_areas`, `area_activities`, `challenges`, `challenge_activities`, `challenge_enrollments`, `challenge_daily_logs`, `task_completions`, and `app_state`. The `parents` table stores contact information (email or mobile) with auto-detected contact_type. The `babies` table includes a `parent_id` foreign key linking each baby to their parent, enabling multi-baby support per parent. Each baby has a unique UUID stored in the session for identification. The `babies` table has nullable `user_id` and `date_of_birth` columns (legacy from prior architecture). Age is derived from age groups (6 simplified ranges: 0–3 Months/Newborn Nurture, 3–6 Months/Curious Explorer, 6–12 Months/Little Discoverer, 1–2 Years/Tiny Talker, 2–4 Years/Playful Learner, 4–6 Years/Confident Creator) for activity matching.

### Parent-Authenticated Multi-Baby Architecture
The system uses a parent-first authentication approach with support for multiple babies per parent. Parents enter their contact info (mobile or email) on first visit, creating or retrieving their parent record. The system stores `parent_id`, `parent_contact`, and `baby_uuid` in the Flask session. When returning parents log in, the system automatically loads their most recent baby profile, allowing seamless continuation. Parents can manage multiple children using the "Add New Baby" button, which maintains parent context while creating new baby profiles. All baby-related routes verify ownership by checking that the baby's `parent_id` matches the session `parent_id`, preventing cross-parent access. The "Logout" button clears all session data. This approach provides frictionless entry while enabling multi-child tracking and data security.

### AI Personalization and Content Generation
A 3-tier AI personalization system uses Anthropic Claude for:
1. **Ability Assessment**: AI-generated questions tailored to the child's age and development goals (though simplified in current onboarding).
2. **Activity Generation**: Personalized activities based on assessment results, targeting specific developmental needs, with exactly 4 activities per area.
3. **Smart Home Dashboard**: Displays personalized activities, falling back to a generic library if none are available.
AI-generated development areas and activities are lazily generated on first visit and cached in the database. AI is also used to generate fun, playful area names and compelling challenge templates and activities.

### User Journey Flow
The user journey starts with parent authentication, followed by streamlined baby onboarding:

**For New Parents:**
1. **Parent Entry** (`/`): Enter mobile number or email (auto-detects format)
2. **Create Profile** (`/create-profile`): Enter child's name and select age group from 6 options with descriptive labels (e.g., "0–3 Months — Newborn Nurture")
3. **Select Goals** (`/select-goals`): Choose development goals (Linguistic, Physical, Social-Emotional, Cognitive)
4. **Home Dashboard** (`/home`): Access AI-generated development areas and age-matched activities

**For Returning Parents:**
1. **Parent Entry** (`/`): Enter their existing mobile/email
2. **Auto-Load** → System automatically loads their most recent baby profile
3. **Home Dashboard** (`/home`): Resume where they left off

**Multi-Baby Management:**
- **Add New Baby**: Click button in navigation to create additional child profiles while maintaining parent context
- **Logout**: Clear all session data and return to parent entry screen

The app flow is: `/` → `/parent-entry` → `/create-profile` → `/select-goals` → `/home`. Detailed task views offer educational rationale and tips. A timer and task completion system allows tracking of completed activities. No traditional signup/login required - authentication is frictionless via contact info entry.

## External Dependencies

### Third-Party Services
- **Google Fonts API**: For CDN-hosted typography (Poppins, Nunito, Inter).
- **Anthropic Claude**: Integrated via Replit's secure AI Integrations for AI personalization and content generation.

### Python Libraries
- **Flask**: Web framework for core application logic, templating, and session management.
- **Werkzeug**: Used for password hashing.
- **SQLite3**: Python's standard library database driver for file-based data storage.

### Deployment Platform
- **Replit**: Used for development and hosting, supporting auto-deployment and environment variables.

### Browser APIs
- **Standard HTML5 Features**: For date input, local form validation, and JavaScript-driven multi-step forms.
