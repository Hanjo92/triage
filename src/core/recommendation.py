import random

def determine_user_mode(energy: str, state: str, missed_days: int) -> str:
    """Determine the user's mode based on current physical/mental state and missed days."""
    if missed_days >= 2:
        return 'recovery'
    if energy == 'low' or state in ['tired', 'stressed', 'distracted']:
        return 'start'
    return 'maintain'

def recommend_actions(db, energy: str, available_time: str, state: str, missed_days: int, domain_preference: str = None):
    """
    Recommend 3 actions based on user's current context.
    Returns: (mode, [Action, Action, Action])
    """
    from src.db.models import Action
    
    current_mode = determine_user_mode(energy, state, missed_days)
    
    # Load all active actions (Efficient enough for < 1000 items in MVP)
    all_actions = db.query(Action).filter(Action.is_active == True).all()
    
    candidates = []
    
    for action in all_actions:
        # Safety filter for recovery mode
        if current_mode == 'recovery' and not action.recovery_safe:
            continue
            
        score = 0
        
        # Mode match (+40)
        mode_tags = action.mode_tags or []
        if current_mode in mode_tags:
            score += 40
            
        # Time match (+25)
        time_tags = action.time_tags or []
        # Convert times like '3m' or '3' to integers for comparison
        clean_avail_time = int(''.join(filter(str.isdigit, available_time)) or 0)
        
        action_time_ints = []
        for t in time_tags:
            t_int = int(''.join(filter(str.isdigit, str(t))) or 0)
            if t_int > 0:
                action_time_ints.append(t_int)
        
        # If the action requires strictly more time than available, skip it
        if action_time_ints and clean_avail_time > 0 and clean_avail_time < min(action_time_ints):
            continue
            
        if any(t_int <= clean_avail_time for t_int in action_time_ints):
            score += 25

        # Energy match (+15)
        energy_tags = action.energy_tags or []
        if energy in energy_tags:
            score += 15
            
        # State match (+10)
        state_tags = action.state_tags or []
        if state in state_tags:
            score += 10
            
        # Domain match (+5)
        domain_tags = action.domain_tags or []
        if domain_preference and domain_preference in domain_tags:
            score += 5
            
        candidates.append({'action': action, 'score': score})
        
    # Sort candidates by score descending
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # We want top 3, but let's add some randomization from the top 5~10 to avoid repetition
    top_candidates = candidates[:10]
    
    # Instead of completely random, we can weight by score or just shuffle top items.
    top_actions = [c['action'] for c in top_candidates]
    random.shuffle(top_actions)
    
    return current_mode, top_actions[:3]
