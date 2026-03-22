from datetime import datetime
from sqlalchemy import desc

def get_completion_score(status: str, is_recovery_mode: bool) -> float:
    """
    Calculate the soft streak score based on action completion status.
    status: 'done', 'partial', 'fail', 'checkin_only'
    """
    if status == 'done':
        return 0.4 if is_recovery_mode else 1.0
    elif status == 'partial':
        return 0.7
    elif status == 'fail' or status == 'checkin_only':
        return 0.2
    return 0.0

def get_missed_days(db, user_id: str) -> int:
    """
    Calculate how many days the user has completely missed executing any action.
    This checks the latest completion that was at least a recovery or partial.
    """
    from src.db.models import Completion
    
    latest_successful_completion = db.query(Completion).filter(
        Completion.user_id == user_id,
        Completion.score >= 0.4  # At least a recovery completion
    ).order_by(desc(Completion.created_at)).first()
    
    if not latest_successful_completion:
        # If no completions yet, they are technically starting fresh, so 0 missed days.
        return 0
        
    delta = datetime.utcnow() - latest_successful_completion.created_at
    return delta.days
