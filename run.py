# ============================================================
# CRITICAL: gevent monkey_patch MUST be the very first thing
# before ANY other import — including Flask, logging, os, etc.
# ============================================================
from gevent import monkey
monkey.patch_all()

# ── Only now is it safe to import everything else ──
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    logger.info("Starting Mzizibet application initialization...")

    from app import create_app

    config_name = os.environ.get("FLASK_ENV", "production")
    logger.info(f"Using configuration: {config_name}")

    app = create_app(config_name)
    logger.info("✓ Flask app created successfully")
    logger.info("✓ Mzizibet application ready for gunicorn")

except ImportError as e:
    logger.critical(f"❌ Import error during app initialization: {e}")
    logger.critical(f"Python path: {sys.path}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"❌ Unexpected error during app initialization: {e}")
    import traceback
    logger.critical(traceback.format_exc())
    sys.exit(1)

# Gunicorn entry point — 'run:app'
if __name__ == "__main__":
    logger.warning("⚠️  Running in development mode. Use gunicorn for production.")
    from app.extensions import socketio
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
