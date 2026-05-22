"""Initialize database schema."""

import argparse
import logging
from app.core.database import init_db, reset_db
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)


def main():
    """Initialize database."""
    parser = argparse.ArgumentParser(description="Initialize database schema")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables and recreate (WARNING: deletes data)",
    )

    args = parser.parse_args()

    try:
        if args.reset:
            logger.warning("Resetting database - this will delete all data!")
            response = input("Are you sure? Type 'yes' to confirm: ")
            if response.lower() != "yes":
                logger.info("Cancelled")
                return

            logger.info("Dropping all tables...")
            reset_db()
            logger.info("Database reset complete")
        else:
            logger.info("Initializing database...")
            init_db()
            logger.info("Database initialization complete")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
