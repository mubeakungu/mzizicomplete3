import json
import logging
import os

from app.extensions import db
from app.models.casino import GameCategory, Game

logger = logging.getLogger(__name__)

BASE_URL = "https://jantabets.co.ke"
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "games.json")

def normalize_thumbnail_url(url: str) -> str:
    """Ensure relative image URLs get prefixed with the full domain path."""
    if not url:
        return ""
    if url.startswith("/"):
        return f"{BASE_URL}{url}"
    return url

def slugify(text: str) -> str:
    """Helper to convert strings into URL-safe slugs."""
    return text.lower().replace(" ", "-").replace("&", "and")

def run(force=False):
    """Seed catalog database using the scraped games JSON payload."""
    if not force and Game.query.count() > 0:
        logger.info("⚠️ Catalog already populated. Pass force=True to re-seed.")
        return False

    if not os.path.exists(JSON_FILE_PATH):
        logger.error(f"❌ Could not find {JSON_FILE_PATH}. Run your Go scraper first.")
        return False

    with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
        scraped_games = json.load(f)

    # Track or create dynamic categories from scraped data
    category_cache = {}

    for index, game_data in enumerate(scraped_games):
        raw_category = game_data.get("category", "virtuals")
        cat_slug = slugify(raw_category)

        # 1. Get or Create GameCategory dynamically
        if cat_slug not in category_cache:
            cat = GameCategory.query.filter_by(slug=cat_slug).first()
            if not cat:
                cat = GameCategory(
                    name=raw_category.replace("-", " ").title(),
                    slug=cat_slug,
                    display_order=len(category_cache) + 1
                )
                db.session.add(cat)
                db.session.flush()
            category_cache[cat_slug] = cat
        else:
            cat = category_cache[cat_slug]

        game_id = game_data.get("id")
        game_name = game_data.get("name")
        image_url = normalize_thumbnail_url(game_data.get("thumbnailUrl"))

        # 2. Check for existing game entry
        existing_game = Game.query.filter_by(slug=game_id).first()

        if existing_game:
            if force:
                existing_game.name = game_name
                existing_game.thumbnail_url = image_url
                existing_game.category_id = cat.id
                existing_game.is_active = game_data.get("isEnabled", True)
        else:
            db.session.add(
                Game(
                    name=game_name,
                    slug=game_id,  # Using the API ID as the unique slug/identifier
                    category_id=cat.id,
                    badge="HOT" if raw_category == "crash" else None,
                    thumbnail_url=image_url,
                    display_order=index,
                    is_active=game_data.get("isEnabled", True),
                )
            )

    db.session.commit()
    return True

if __name__ == "__main__":
    from app import create_app

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    app = create_app("development")
    with app.app_context():
        db.create_all()
        if run(force=True):
            print("✅ Successfully seeded database with scraped games payload!")
        else:
            print("⚠️ Seeding skipped or failed.")
