"""Initialize default uniquification presets.

Run this script once after database initialization to create default presets.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, init_db
from database.models import UniquificationPreset, MediaType
from workers.uniquification.photo_uniquifier import create_default_photo_preset
from workers.uniquification.video_uniquifier import create_default_video_preset


def init_presets():
    """Initialize default presets."""
    print("Initializing database...")
    init_db()

    db = SessionLocal()

    try:
        # Check if presets already exist
        existing_photo = db.query(UniquificationPreset).filter(
            UniquificationPreset.name == "Default Photo",
            UniquificationPreset.media_type == MediaType.PHOTO
        ).first()

        existing_video = db.query(UniquificationPreset).filter(
            UniquificationPreset.name == "Default Video",
            UniquificationPreset.media_type == MediaType.VIDEO
        ).first()

        if existing_photo and existing_video:
            print("Default presets already exist!")
            return

        # Create photo preset
        if not existing_photo:
            print("Creating default photo preset...")
            photo_preset = UniquificationPreset(
                name="Default Photo",
                media_type=MediaType.PHOTO,
                is_active=True,
                is_default=True,
                config=create_default_photo_preset(),
                description="Пресет по умолчанию для уникализации фотографий. "
                           "Включает шумы, звездочки, блики и цветокоррекцию."
            )
            db.add(photo_preset)
            print("✓ Photo preset created")

        # Create video preset
        if not existing_video:
            print("Creating default video preset...")
            video_preset = UniquificationPreset(
                name="Default Video",
                media_type=MediaType.VIDEO,
                is_active=True,
                is_default=True,
                config=create_default_video_preset(),
                description="Пресет по умолчанию для уникализации видео. "
                           "Включает изменение скорости, яркости, контраста и шумы."
            )
            db.add(video_preset)
            print("✓ Video preset created")

        db.commit()
        print("\n✅ Default presets initialized successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    init_presets()
