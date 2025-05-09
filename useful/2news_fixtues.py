
def load_user_fixtures(output_dir):
    """Load user fixtures created by users_fixtures.py script."""
    user_fixtures = []
    student_profiles = []
    
    # Load auth users
    try:
        with open(os.path.join(output_dir, 'auth_users.json'), 'r', encoding='utf-8') as f:
            user_fixtures = json.load(f)
        print(f"✅ Loaded {len(user_fixtures)} user fixtures")
    except FileNotFoundError:
        print(f"❌ User fixtures not found. Run users_fixtures.py first.")
        sys.exit(1)
    
    # Load student profiles
    try:
        with open(os.path.join(output_dir, 'student_profiles.json'), 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
            student_profiles = [p for p in profile_data if p['model'].endswith('studentprofile')]
        print(f"✅ Loaded {len(student_profiles)} student profile fixtures")
    except FileNotFoundError:
        print(f"❌ Student profile fixtures not found. Run users_fixtures.py first.")
    
    return user_fixtures, student_profiles


def get_user_ids(user_fixtures):
    """Extract user IDs from user fixtures."""
    return [user['pk'] for user in user_fixtures 
            if user['fields']['is_active'] and not user['fields']['is_staff']]


def get_student_profile_ids(profile_fixtures):
    """Extract student profile IDs and user IDs from profile fixtures."""
    profile_ids = [profile['pk'] for profile in profile_fixtures]
    user_ids = [profile['fields']['user'] for profile in profile_fixtures]
    return profile_ids, user_ids


def create_category_fixtures(fake, media_dir):
    """Create fixtures for news categories."""
    categories = [
        {"name": "Technology", "description": "Latest tech news and innovations"},
        {"name": "Business", "description": "Business, economy and market updates"},
        {"name": "Science", "description": "Scientific discoveries and research"},
        {"name": "Health", "description": "Health, medicine and wellness news"},
        {"name": "Politics", "description": "Political news and policy updates"},
        {"name": "Environment", "description": "Climate change and environmental news"},
        {"name": "Education", "description": "Educational trends and academic research"},  
        {"name": "Culture", "description": "Arts, literature and cultural highlights"},
        {"name": "Sports", "description": "Sports news and athletic achievements"}
    ]
    
    category_fixtures = []
    category_slugs = set()
    
    for i, category in enumerate(categories, 1):
        name = category["name"]
        description = category["description"]
        
        # Create a unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        
        while slug in category_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        category_slugs.add(slug)
        
        # Generate a category image
        image_path = generate_category_image(name, media_dir)
        
        category_fixtures.append({
            "model": "news.category",
            "pk": i,
            "fields": {
                "name": name,
                "slug": slug,
                "description": description,
                "image": image_path
            }
        })
    
    print(f"✅ Created {len(category_fixtures)} category fixtures")
    return category_fixtures


def generate_category_image(category_name, media_dir):
    """Generate a simple placeholder image for a category."""
    width, height = 800, 400
    color = get_color_from_string(category_name)
    
    # Create the image
    image = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(image)
    
    # Add text to the center
    try:
        # Try to use a system font
        font = ImageFont.truetype("Arial", 60)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = category_name
    text_width, text_height = draw.textsize(text) if hasattr(draw, 'textsize') else (200, 40)  # Fallback for Pillow 9.0+
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill="white")
    
    # Save the image
    filename = f"categories/{slugify(category_name)}.jpg"
    filepath = os.path.join(media_dir, filename)
    image.save(filepath)
    
    return filename


def get_color_from_string(text):
    """Generate a consistent color based on a text string."""
    # Simple hash function to get consistent colors
    hash_value = 0
    for char in text:
        hash_value = (hash_value * 31 + ord(char)) & 0xFFFFFF
    
    # Return as RGB tuple
    r = (hash_value >> 16) & 255
    g = (hash_value >> 8) & 255
    b = hash_value & 255
    
    return (r, g, b)


def fetch_news_data(api_key, sources, articles_per_source):
    """Fetch news data from NewsAPI if API key is provided."""
    if not api_key:
        print("ℹ️ No NewsAPI key provided. Using generated fake content only.")
        return []
    
    all_articles = []
    API_URL = 'https://newsapi.org/v2/everything'
    
    for source in sources:
        params = {
            'apiKey': api_key,
            'sources': source,
            'sortBy': 'popularity',
            'pageSize': articles_per_source
        }
        
        try:
            response = requests.get(API_URL, params=params, timeout=15)
            data = response.json()
            
            if data.get('status') != 'ok':
                print(f"❌ Error fetching news from {source}: {data.get('message', 'Unknown error')}")
                continue
                
            articles = data.get('articles', [])
            if articles:
                print(f"✅ Fetched {len(articles)} articles from {source}")
                all_articles.extend(articles)
            else:
                print(f"ℹ️ No articles found for source: {source}")
        except Exception as e:
            print(f"❌ Error connecting to NewsAPI for {source}: {e}")
    
    return all_articles


def download_image(url, directory, filename_base):
    """Download an image from a URL and save it to the specified directory."""
    if not url:
        return ""
    
    # Extract file extension from URL or default to .jpg
    parsed_url = urlparse(url)
    path = parsed_url.path
    extension = os.path.splitext(path)[1].lower()
    if not extension or extension not in ['.jpg', '.jpeg', '.png', '.gif']:
        extension = '.jpg'
    
    filename = f"{filename_base}{extension}"
    filepath = os.path.join(directory, filename)
    
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return filepath.replace(os.path.commonprefix([directory, filepath]), '').lstrip('/')
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
    
    return ""


def generate_placeholder_image(text, directory, filename, width=800, height=400):
    """Generate a placeholder image with text."""
    image = Image.new('RGB', (width, height), get_color_from_string(text))
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("Arial", 40)
    except IOError:
        font = ImageFont.load_default()
    
    # Add text to the center
    text_width, text_height = draw.textsize(text) if hasattr(draw, 'textsize') else (width//2, height//4)
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill="white")
    
    # Save the image
    filepath = os.path.join(directory, filename)
    image.save(filepath)
    
    return filepath.replace(os.path.commonprefix([directory, filepath]), '').lstrip('/')


def clean_title(title, max_length=190):
    """Clean and truncate a title to prevent issues with database fields."""
    if not title:
        return "Untitled Article"
    
    # Remove any special characters that might cause issues
    cleaned = ''.join(c for c in title if c.isalnum() or c.isspace() or c in ',.;:-_')
    
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
        
    return cleaned


def generate_ckeditor_content(fake, title, content_text=None):
    """Generate rich HTML content for CKEditor5 field."""
    if not content_text:
        paragraphs = [fake.paragraph(nb_sentences=random.randint(5, 10)) for _ in range(random.randint(6, 12))]
        content_text = "\n\n".join(paragraphs)
    
    html_content = f"<h1>{title}</h1>\n"
    
    # Add a subtitle/lead paragraph in italics
    html_content += f"<p><em>{fake.paragraph(nb_sentences=2)}</em></p>\n"
    
    # Split content into paragraphs
    paragraphs = content_text.split('\n')
    
    # Process paragraphs with formatting
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue
            
        # Occasionally add subheadings
        if i > 0 and random.random() < 0.3:
            html_content += f"<h2>{fake.sentence().rstrip('.')}</h2>\n"
        
        # Format paragraph with occasional styling
        if random.random() < 0.15:
            # Add bold to some text
            words = paragraph.split()
            if len(words) > 5:
                start_pos = random.randint(0, len(words) - 3)
                end_pos = start_pos + random.randint(1, 3)
                phrase = " ".join(words[start_pos:end_pos])
                paragraph = paragraph.replace(phrase, f"<strong>{phrase}</strong>", 1)
        
        html_content += f"<p>{paragraph}</p>\n"
        
        # Occasionally add a blockquote
        if random.random() < 0.2:
            html_content += f'<blockquote><p>"{fake.sentence()}"</p></blockquote>\n'
            
        # Occasionally add a bullet list
        if random.random() < 0.15:
            html_content += "<ul>\n"
            for _ in range(random.randint(3, 5)):
                html_content += f"<li>{fake.sentence()}</li>\n"
            html_content += "</ul>\n"
    
    # Add a concluding paragraph
    html_content += f"<p>{fake.paragraph()}</p>\n"
    
    return html_content
#old_fixtures_generator.py
"""
Django Newsletter Website Fixtures Generator

This script generates realistic fixture data for a Django newsletter website, including:
- News Categories with images
- News Articles with CKEditor5 content
- News Media files 
- Comments on articles
- User messages and subscriptions

It builds upon user fixtures created by the users_fixtures.py script.

Usage:
    python newsletter_fixtures_generator.py [options]

Options:
    --output DIRECTORY    Directory to output fixture files (default: fixtures/)
    --media DIRECTORY     Directory for media files (default: media/)
    --articles NUM        Number of articles to generate per category (default: 10)
    --seed NUM            Random seed for reproducible results (default: None)
    --api-key KEY         NewsAPI key for real article data (optional)
"""

import argparse
import json
import os
import random
import requests
import shutil
import string
import sys
from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import urlparse

import pytz
from faker import Faker
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate Django newsletter website fixtures')
    parser.add_argument('--output', type=str, default='fixtures',
                        help='Output directory for fixture files (default: fixtures/)')
    parser.add_argument('--media', type=str, default='media',
                        help='Output directory for media files (default: media/)')
    parser.add_argument('--articles', type=int, default=10,
                        help='Number of articles per category (default: 10)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducible results')
    parser.add_argument('--api-key', type=str, default=None,
                        help='NewsAPI key for real article data (optional)')
    
    return parser.parse_args()


def setup_directories(output_dir, media_dir):
    """Set up output directories for fixtures and media files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create media subdirectories
    media_subdirs = [
        os.path.join(media_dir, 'news', 'images'),
        os.path.join(media_dir, 'news', 'media'),
        os.path.join(media_dir, 'categories'),
        os.path.join(media_dir, 'profiles')
    ]
    
    for directory in media_subdirs:
        os.makedirs(directory, exist_ok=True)
        
    print(f"✅ Created output directories")



def create_news_fixtures(fake, categories, api_articles, student_profiles, media_dir, articles_per_category):
    """Create fixtures for news articles, media files, and comments."""
    news_fixtures = []
    media_fixtures = []
    comment_fixtures = []
    tag_fixtures = []
    tagged_item_fixtures = []
    
    news_pk = 1
    media_pk = 1
    comment_pk = 1
    tag_pk = 1
    tagged_item_pk = 1
    
    # Track used slugs to ensure uniqueness
    used_slugs = set()
    
    # List of potential tags
    tags = [
        'technology', 'politics', 'business', 'climate', 'sports', 'education',
        'science', 'health', 'world', 'local', 'economy', 'innovation',
        'research', 'ai', 'machine learning', 'blockchain', 'cybersecurity', 
        'environment', 'sustainability', 'finance', 'startups', 'digital',
        'culture', 'art', 'music', 'literature', 'film', 'theater', 'social media'
    ]
    
    # Create a dictionary to track tag fixtures
    tag_dict = {}
    
    # Get student profile user IDs for authors
    if student_profiles:
        author_ids = [profile["pk"] for profile in student_profiles]
    else:
        # Fallback to random user IDs if no profiles available
        author_ids = list(range(1, 11))
    
    # Process articles for each category
    for category in categories:
        category_id = category["pk"]
        category_name = category["fields"]["name"]
        
        # Number of articles to create for this category
        num_articles = articles_per_category
        
        for article_idx in range(num_articles):
            # Try to use real article data if available
            api_article = None
            if api_articles:
                # Try to find an article that matches the category
                matching_articles = [a for a in api_articles if category_name.lower() in 
                                    (a.get('title', '').lower() + a.get('description', '').lower())]
                
                if matching_articles:
                    api_article = matching_articles.pop(0)
                    # Remove used article
                    api_articles.remove(api_article)
                elif api_articles:
                    # If no matching article, just take any available one
                    api_article = api_articles.pop(0)
            
            # Generate article data, using API data if available
            if api_article:
                title = clean_title(api_article.get('title', f"{category_name} News {article_idx+1}"))
                summary = api_article.get('description') or fake.paragraph()
                content_text = api_article.get('content') or None
            else:
                title = clean_title(f"{fake.sentence().rstrip('.')} - {category_name} Update")
                summary = fake.paragraph()
                content_text = None
            
            # Create a unique slug
            base_slug = slugify(title)
            if not base_slug:
                base_slug = f"news-{category_id}-{article_idx}"
                
            slug = base_slug
            counter = 1
            
            while slug in used_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            used_slugs.add(slug)
            
            # Get an author
            author_id = random.choice(author_ids)
            
            # Generate dates
            now = datetime.now(pytz.UTC)
            created_at = fake.date_time_between(start_date='-90d', end_date='-1d', tzinfo=pytz.UTC)
            updated_at = fake.date_time_between(start_date=created_at, end_date='now', tzinfo=pytz.UTC)
            publish_date = fake.date_time_between(start_date=created_at, end_date=updated_at, tzinfo=pytz.UTC)
            
            # Get or generate a featured image
            featured_image = ""
            if api_article and api_article.get('urlToImage'):
                image_dir = os.path.join(media_dir, 'news', 'images')
                featured_image = download_image(
                    api_article.get('urlToImage'),
                    image_dir,
                    slugify(title)[:50]
                )
                if featured_image:
                    featured_image = f"news/images/{os.path.basename(featured_image)}"
            
            # If download failed or no image URL, generate a placeholder
            if not featured_image:
                image_dir = os.path.join(media_dir, 'news', 'images')
                image_path = generate_placeholder_image(
                    title[:30],
                    image_dir,
                    f"{slugify(title)[:50]}.jpg"
                )
                featured_image = f"news/images/{os.path.basename(image_path)}"
            
            # Generate rich content for CKEditor5 field
            rich_content = generate_ckeditor_content(fake, title, content_text)
            
            # Determine if article is featured (20% chance)
            is_featured = random.random() < 0.2
            
            # Determine status (most published, some draft)
            status = "published" if random.random() < 0.9 else "draft"
            
            # Views count based on age of article
            days_since_publish = (now - publish_date).days
            base_views = random.randint(10, 200)
            views = int(base_views * (1 + days_since_publish / 10))
            
            # Create news article fixture
            news_fixtures.append({
                "model": "news.news",
                "pk": news_pk,
                "fields": {
                    "title": title,
                    "slug": slug,
                    "author": author_id,
                    "category": category_id,
                    "featured_image": featured_image,
                    "summary": summary,
                    "content": rich_content,
                    "is_featured": is_featured,
                    "status": status,
                    "created_at": created_at.isoformat(),
                    "updated_at": updated_at.isoformat(),
                    "publish_date": publish_date.isoformat(),
                    "views": views
                }
            })
            
            # Generate 1-3 media files for some articles (30% chance)
            if random.random() < 0.3:
                num_media = random.randint(1, 3)
                for media_idx in range(num_media):
                    media_type = random.choice(['image', 'document', 'audio', 'video'])
                    
                    # Generate appropriate file name based on type
                    if media_type == 'image':
                        file_extension = random.choice(['.jpg', '.png'])
                        media_dir_path = os.path.join(media_dir, 'news', 'media')
                        file_path = generate_placeholder_image(
                            f"{title} - Media {media_idx+1}",
                            media_dir_path,
                            f"{slugify(title)[:30]}-media-{media_idx+1}{file_extension}"
                        )
                    else:
                        # For other types, we just create dummy filenames
                        if media_type == 'document':
                            file_extension = random.choice(['.pdf', '.docx'])
                        elif media_type == 'audio':
                            file_extension = random.choice(['.mp3', '.wav'])
                        elif media_type == 'video':
                            file_extension = random.choice(['.mp4', '.mov'])
                            
                        file_path = f"news/media/{slugify(title)[:30]}-media-{media_idx+1}{file_extension}"
                    
                    media_title = f"{title} - {media_type.title()} {media_idx+1}"
                    
                    media_fixtures.append({
                        "model": "news.newsmedia",
                        "pk": media_pk,
                        "fields": {
                            "news": news_pk,
                            "media_type": media_type,
                            "file": file_path,
                            "title": media_title,
                            "description": fake.sentence(),
                            "is_featured": random.random() < 0.3,
                            "upload_date": created_at.isoformat(),
                            "order": media_idx + 1
                        }
                    })
                    media_pk += 1
            
            # Generate comments (0-8 per article)
            num_comments = random.randint(0, 8)
            for comment_idx in range(num_comments):
                # Comment date is after publish date
                comment_date = fake.date_time_between(
                    start_date=publish_date,
                    end_date='now',
                    tzinfo=pytz.UTC
                )
                
                # Random user ID for comment - can be any user
                user_id = random.randint(1, 15)  # Assumes at least 15 users from user fixtures
                
                comment_fixtures.append({
                    "model": "news.comment",
                    "pk": comment_pk,
                    "fields": {
                        "news": news_pk,
                        "user": user_id,
                        "content": fake.paragraph(nb_sentences=random.randint(1, 4)),
                        "created_at": comment_date.isoformat(),
                        "is_approved": random.random() < 0.9  # 90% approved
                    }
                })
                comment_pk += 1
            
            # Generate 2-5 tags for this article
            article_tag_count = random.randint(2, 5)
            selected_tags = random.sample(tags, article_tag_count)
            
            for tag_name in selected_tags:
                # Create tag if it doesn't exist
                if tag_name not in tag_dict:
                    tag_dict[tag_name] = tag_pk
                    tag_fixtures.append({
                        "model": "taggit.tag",
                        "pk": tag_pk,
                        "fields": {
                            "name": tag_name,
                            "slug": slugify(tag_name)
                        }
                    })
                    tag_pk += 1
                
                # Create tagged item
                tagged_item_fixtures.append({
                    "model": "taggit.taggeditem",
                    "pk": tagged_item_pk,
                    "fields": {
                        "tag": tag_dict[tag_name],
                        "content_type": 18,  # Content type ID for News model - adjust as needed
                        "object_id": news_pk
                    }
                })
                tagged_item_pk += 1
            
            news_pk += 1
    
    print(f"✅ Created {news_pk-1} news articles with {media_pk-1} media files and {comment_pk-1} comments")
    return news_fixtures, media_fixtures, comment_fixtures, tag_fixtures, tagged_item_fixtures


def create_contact_message_fixtures(fake, user_count):
    """Create fixtures for contact messages."""
    fixtures = []
    
    # Generate 20-50 contact messages
    num_messages = random.randint(20, 50)
    
    for i in range(1, num_messages + 1):
        # Some messages from registered users, some from non-registered
        is_registered_user = random.random() < 0.4
        
        if is_registered_user:
            user_id = random.randint(1, user_count)
            user = fake.name()
            email = f"user{user_id}@example.com"  # Simplified
        else:
            user = fake.name()
            email = fake.email()
            
        subject = fake.sentence(nb_words=random.randint(4, 8)).rstrip('.')
        message = fake.paragraphs(nb=random.randint(1, 3))
        message = '\n\n'.join(message)
        
        # Generate creation date within the last 180 days
        created_at = fake.date_time_between(
            start_date='-180d',
            end_date='now',
            tzinfo=pytz.UTC
        )
        
        fixtures.append({
            "model": "subscription.contactmessage",
            "pk": i,
            "fields": {
                "name": user,
                "email": email,
                "subject": subject,
                "message": message,
                "created_at": created_at.isoformat()
            }
        })
    
    print(f"✅ Created {len(fixtures)} contact message fixtures")
    return fixtures


def main():
    """Main function to generate and save fixtures."""
    args = parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        
    # Initialize faker
    global fake
    fake = Faker()
    if args.seed is not None:
        Faker.seed(args.seed)
    
    # Setup directories
    setup_directories(args.output, args.media)
    
    # Load user fixtures
    user_fixtures, student_profiles = load_user_fixtures(args.output)
    
    # Get user and profile IDs
    user_ids = get_user_ids(user_fixtures)
    
    # API sources for news data
    sources = ['bbc-news', 'cnn', 'the-verge', 'wired', 'bloomberg', 'ars-technica']
    
    # Fetch real article data if API key provided
    api_articles = []
    if args.api_key:
        api_articles = fetch_news_data(args.api_key, sources, args.articles)
    
    # Create category fixtures
    category_fixtures = create_category_fixtures(fake, args.media)
    
    # Create news fixtures
    news_fixtures, media_fixtures, comment_fixtures, tag_fixtures, tagged_item_fixtures = create_news_fixtures(
        fake, category_fixtures, api_articles, student_profiles, args.media, args.articles
    )
    
    # Create contact message fixtures
    contact_fixtures = create_contact_message_fixtures(fake, len(user_ids))
    
    # Save all fixtures
    fixtures_to_save = {
        'categories.json': category_fixtures,
        'news.json': news_fixtures,
        'news_media.json': media_fixtures,
        'comments.json': comment_fixtures,
        'tags.json': tag_fixtures,
        'tagged_items.json': tagged_item_fixtures,
        'contact_messages.json': contact_fixtures
    }
    
    for filename, data in fixtures_to_save.items():
        save_path = os.path.join(args.output, filename)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(data)} fixtures to {save_path}")
    
    # Print instructions
    print("\n✅ All newsletter fixtures generated successfully!")
    print("\nTo load fixtures into your Django project:")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'sites.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'auth_users.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'allauth_email.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'student_requests.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'student_profiles.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'categories.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'tags.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'news.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'tagged_items.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'news_media.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'comments.json')}")
    print(f"  python manage.py loaddata {os.path.join(args.output, 'contact_messages.json')}")


if __name__ == '__main__':
    main()