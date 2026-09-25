"""Creates the initial Admin account on first startup, if none exists yet.

Admin accounts are never exposed on the public signup form (per spec), so
the system needs one bootstrap account to log in and start approving/
creating other users. Change the seed password immediately after first
login in a real deployment (set SEED_ADMIN_PASSWORD in .env before first
run to avoid the default entirely).
"""

import logging

from sqlalchemy.orm import Session

from backend import config
from backend.models_db import User
from backend.security import hash_password

logger = logging.getLogger("seed")


def seed_admin(db: Session):
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        return

    admin = User(
        full_name="System Administrator",
        email=config.SEED_ADMIN_EMAIL,
        username=config.SEED_ADMIN_USERNAME,
        password_hash=hash_password(config.SEED_ADMIN_PASSWORD),
        role="admin",
        status="active",
    )
    db.add(admin)
    db.commit()
    logger.warning(
        "Seeded default admin account (username=%s). CHANGE THIS PASSWORD immediately.",
        config.SEED_ADMIN_USERNAME,
    )
