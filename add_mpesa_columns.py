"""
Run once against an EXISTING deployed database to add the new M-Pesa
correlation columns to the transactions table.

This project boots with db.create_all(), which only creates tables that
don't exist yet — it never ALTERs an existing table. On a brand new
database you don't need this at all (create_all() already includes these
columns from app/models/wallet.py). On a database that already has a
transactions table from before this update, run:

    python add_mpesa_columns.py

Safe to run more than once — every ALTER is guarded by a column-existence
check first.
"""
import logging

from app import create_app
from app.extensions import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEW_COLUMNS = {
    "phone_number": "VARCHAR(15)",
    "checkout_request_id": "VARCHAR(64)",
    "merchant_request_id": "VARCHAR(64)",
    "conversation_id": "VARCHAR(64)",
    "originator_conversation_id": "VARCHAR(64)",
    "result_desc": "VARCHAR(255)",
    "updated_at": "TIMESTAMP",
}


def run():
    app = create_app("production")
    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name

        with engine.connect() as conn:
            existing = {
                row[0]
                for row in conn.execute(db.text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'transactions'"
                ))
            } if dialect == "postgresql" else {
                row[1] for row in conn.execute(db.text("PRAGMA table_info(transactions)"))
            }

            for column, coltype in NEW_COLUMNS.items():
                if column in existing:
                    logger.info("✓ transactions.%s already present, skipping", column)
                    continue
                logger.info("Adding transactions.%s %s ...", column, coltype)
                conn.execute(db.text(f"ALTER TABLE transactions ADD COLUMN {column} {coltype}"))
                conn.commit()

            # Helpful lookups on the callback-matching columns.
            index_stmts = [
                "CREATE INDEX IF NOT EXISTS ix_transactions_checkout_request_id "
                "ON transactions (checkout_request_id)",
                "CREATE INDEX IF NOT EXISTS ix_transactions_conversation_id "
                "ON transactions (conversation_id)",
            ]
            for stmt in index_stmts:
                try:
                    conn.execute(db.text(stmt))
                    conn.commit()
                except Exception as e:  # SQLite/Postgres syntax differences, non-fatal
                    logger.warning("Index creation skipped: %s", e)

    logger.info("✓ Done.")


if __name__ == "__main__":
    run()
