"""Create admin user.

Run this script to manually create an admin user in the database.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, init_db
from database.models import User


def create_admin(telegram_id: int, username: str = None, first_name: str = None):
    """Create admin user.

    Args:
        telegram_id: Telegram user ID
        username: Telegram username (optional)
        first_name: First name (optional)
    """
    print("Initializing database...")
    init_db()

    db = SessionLocal()

    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if existing_user:
            # Update to admin
            existing_user.is_admin = True
            db.commit()
            print(f"✅ User {telegram_id} (@{existing_user.username}) updated to admin!")
        else:
            # Create new admin user
            admin = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name or "Admin",
                is_admin=True,
                is_subscribed=True
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin user {telegram_id} (@{username}) created!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_admin.py <telegram_id> [username] [first_name]")
        print("Example: python create_admin.py 123456789 admin_user Admin")
        sys.exit(1)

    telegram_id = int(sys.argv[1])
    username = sys.argv[2] if len(sys.argv) > 2 else None
    first_name = sys.argv[3] if len(sys.argv) > 3 else None

    create_admin(telegram_id, username, first_name)
