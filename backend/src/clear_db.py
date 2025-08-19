from backend.src.db import Session, Reel, Config, engine
from sqlalchemy import delete

session = Session()

try:
    # Delete all reels
    session.execute(delete(Reel))

    # Optionnel : delete all config entries (si tu veux garder certaines, saute cette ligne)
    # session.execute(delete(Config))

    session.commit()
    print("Database cleaned successfully")
except Exception as e:
    session.rollback()
    print(f"Failed to clean database: {e}")
finally:
    session.close()
