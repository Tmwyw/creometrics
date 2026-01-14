#!/usr/bin/env python3
"""
Simple database initialization script without heavy dependencies
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Import only database models (no workers)
from database.models import Base, UniquificationPreset

def init_database():
    """Initialize database tables"""
    print("[*] Connecting to database...")
    print(f"    Host: {settings.DB_HOST}")
    print(f"    Database: {settings.DB_NAME}")

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )

    print("\n[*] Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("[+] Tables created successfully!")

    # Check if presets already exist
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        existing_presets = session.query(UniquificationPreset).count()

        if existing_presets > 0:
            print(f"\n[!] Found {existing_presets} existing presets. Skipping preset initialization.")
            print("    To reinitialize presets, delete them first or run init_presets.py")
        else:
            print("\n[*] Creating default presets...")
            create_default_presets(session)
            print("[+] Presets created successfully!")

    finally:
        session.close()

    print("\n[+] Database initialization complete!")
    print("\nCreated tables:")
    print("  - users")
    print("  - action_logs")
    print("  - uniquification_presets")
    print("  - broadcast_messages")
    print("  - bot_settings")

def create_default_presets(session):
    """Create default uniquification presets"""

    # Preset 1: Light uniquification
    light_preset = UniquificationPreset(
        name="Легкая уникализация",
        description="Минимальные изменения, почти незаметные",
        is_default=True,
        is_active=True,
        methods_config=json.dumps({
            "noise": {"enabled": True, "intensity": 0.01},
            "sparkles": {"enabled": True, "count": 3, "size": 2},
            "rotate": {"enabled": True, "max_degrees": 0.5},
            "brightness": {"enabled": True, "factor_range": [0.98, 1.02]}
        })
    )

    # Preset 2: Medium uniquification
    medium_preset = UniquificationPreset(
        name="Средняя уникализация",
        description="Умеренные изменения, баланс между заметностью и уникальностью",
        is_default=False,
        is_active=True,
        methods_config=json.dumps({
            "noise": {"enabled": True, "intensity": 0.03},
            "sparkles": {"enabled": True, "count": 5, "size": 3},
            "lens_flare": {"enabled": True, "intensity": 0.3},
            "rotate": {"enabled": True, "max_degrees": 1.0},
            "brightness": {"enabled": True, "factor_range": [0.95, 1.05]},
            "contrast": {"enabled": True, "factor_range": [0.95, 1.05]}
        })
    )

    # Preset 3: Heavy uniquification
    heavy_preset = UniquificationPreset(
        name="Сильная уникализация",
        description="Заметные изменения для максимальной уникальности",
        is_default=False,
        is_active=True,
        methods_config=json.dumps({
            "noise": {"enabled": True, "intensity": 0.05},
            "sparkles": {"enabled": True, "count": 10, "size": 4},
            "lens_flare": {"enabled": True, "intensity": 0.5},
            "rotate": {"enabled": True, "max_degrees": 2.0},
            "brightness": {"enabled": True, "factor_range": [0.90, 1.10]},
            "contrast": {"enabled": True, "factor_range": [0.90, 1.10]},
            "hue": {"enabled": True, "shift_range": [-5, 5]},
            "blur": {"enabled": True, "radius": 0.5}
        })
    )

    session.add_all([light_preset, medium_preset, heavy_preset])
    session.commit()

    print(f"   ✓ {light_preset.name} (default)")
    print(f"   ✓ {medium_preset.name}")
    print(f"   ✓ {heavy_preset.name}")

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
