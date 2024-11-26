from datetime import datetime
from app.models import Journal
from app import db


def log_journal_action(user_id, action_type, description, ingredient_name=None):
    entry = Journal(
        user_id=user_id,
        action_type=action_type,
        description=description,
        timestamp=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()  # Enregistrer le journal
