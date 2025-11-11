# Image Generation Integration Guide

## Current Status (MVP)

✅ **Image System Ready**: The application gracefully handles both illustrated and non-illustrated activities
✅ **Sample Images Generated**: 3 demonstration images created using AI
✅ **Template Support**: Activity detail pages show images when available, beautiful placeholders when not

## Generated Sample Images

The following AI-generated images demonstrate the feature working:

1. **Peek-a-Boo Play** (6-12 months)
   - Path: `attached_assets/generated_images/Parent_and_baby_peek-a-boo_22b76780.png`
   - Shows parent and infant playing peek-a-boo with warm, pastel colors

2. **Tummy Time with Toys** (0-6 months)
   - Path: `attached_assets/generated_images/Baby_tummy_time_with_parent_3492281a.png`
   - Shows newborn on tummy time mat with encouraging parent

3. **Singing and Rhymes Together** (1-2 years)
   - Path: `attached_assets/generated_images/Parent_and_toddler_reading_together_083e600e.png`
   - Shows parent and toddler reading together on couch

## How It Currently Works

When activities are generated (in `app.py`):

1. **Prompt Generation**: AI creates detailed illustration prompts via `ai_service.generate_activity_illustration()`
2. **Image Generation**: `ai_service.generate_activity_image()` is called (currently returns empty string)
3. **Database Storage**: `illustration_url` field stores the image path (or empty string for placeholder)
4. **Template Display**: 
   - If `illustration_url` exists and is valid → shows actual image
   - If empty or invalid → shows beautiful gradient placeholder

## Production Integration Options

### Option A: OpenAI DALL-E Integration (Recommended)

**Why**: Best quality for parenting illustrations, easy integration via Replit

**Steps**:
1. Search for OpenAI integration via Replit integrations
2. Add DALL-E API credentials securely
3. Update `ai_service.generate_activity_image()`:

```python
import openai
import os

def generate_activity_image(illustration_prompt, activity_title):
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Generate image using DALL-E
        response = client.images.generate(
            model="dall-e-3",
            prompt=illustration_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Download and save the image
        import requests
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        
        # Save to attached_assets
        filename = f"{activity_title.replace(' ', '_')}_{hash(illustration_prompt)}.png"
        filepath = f"attached_assets/activity_images/{filename}"
        
        os.makedirs("attached_assets/activity_images", exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filepath
    except Exception as e:
        print(f"Image generation failed: {e}")
        return ""  # Falls back to placeholder
```

### Option B: Stability AI Integration

**Why**: More control over style, potentially lower cost

**Steps**:
1. Get Stability AI API key
2. Add to environment secrets
3. Similar implementation to Option A using Stability SDK

### Option C: Async Background Processing (Best for Scale)

**Why**: Prevents user-facing latency, handles failures gracefully

**Architecture**:
1. **Immediate Response**: Save activity with empty `illustration_url`
2. **Background Job**: Queue image generation task
3. **Update on Complete**: Update database when image ready
4. **User Experience**: User sees placeholder initially, real image appears on refresh

**Implementation with Celery** (example):

```python
# In worker.py
from celery import Celery
import ai_service
import database

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def generate_activity_image_async(activity_id, illustration_prompt, activity_title):
    image_path = ai_service.generate_activity_image(illustration_prompt, activity_title)
    if image_path:
        database.update_activity_illustration(activity_id, image_path)
```

```python
# In app.py (generate_activities route)
from worker import generate_activity_image_async

# After saving activity
activity_id = database.save_personalized_activity(...)
generate_activity_image_async.delay(activity_id, illustration_prompt, activity_title)
```

## Testing the System

### Manual Test with Sample Images

To test with the generated sample images:

```python
# In Python shell or script
import database
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Update an activity to use a sample image
cursor.execute("""
    UPDATE personalized_activities 
    SET illustration_url = 'attached_assets/generated_images/Parent_and_baby_peek-a-boo_22b76780.png'
    WHERE id = 1
""")

conn.commit()
conn.close()
```

Then view the activity detail page to see the real image displayed!

## Cost Considerations

**DALL-E 3 Pricing** (as of 2024):
- Standard: $0.040 per image (1024x1024)
- HD: $0.080 per image (1024x1024)

**Example**: Generating 5 activities per user = $0.20 per user (standard quality)

**Optimization Tips**:
1. Cache images by illustration prompt hash (reuse similar activities)
2. Pre-generate images for common activities
3. Use standard quality for MVP, HD for premium features
4. Implement rate limiting to prevent abuse

## Security Best Practices

1. ✅ Use Replit integrations for API key management
2. ✅ Never commit API keys to repository
3. ✅ Validate image content before storing (content moderation)
4. ✅ Implement rate limiting on image generation endpoints
5. ✅ Use secure file storage with access controls

## Next Steps

1. Choose integration option (recommend Option A for MVP)
2. Set up OpenAI integration via Replit
3. Implement `generate_activity_image()` function
4. Test with a few activities
5. Monitor costs and performance
6. Consider async processing for scale (Option C)
