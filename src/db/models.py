import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(String, unique=True, index=True, nullable=True)
    discord_id = Column(String, unique=True, index=True, nullable=True)
    toss_id = Column(String, unique=True, index=True, nullable=True)
    preferred_intensity = Column(String, default='light')
    recovery_tone = Column(String, default='gentle')
    timezone = Column(String, default='Asia/Seoul')
    created_at = Column(DateTime, default=datetime.utcnow)

    checkins = relationship("DailyCheckin", back_populates="user")
    completions = relationship("Completion", back_populates="user")

class Action(Base):
    __tablename__ = "actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    label = Column(String, nullable=False)
    prompt_copy = Column(String, nullable=False)
    
    # JSON arrays for tags
    mode_tags = Column(JSON, nullable=False, default=list)      # start, maintain, recovery, micro_win
    energy_tags = Column(JSON, nullable=False, default=list)    # low, mid, high
    time_tags = Column(JSON, nullable=False, default=list)      # 1, 3, 10, 20, 30
    state_tags = Column(JSON, nullable=True, default=list)      # focused, distracted, tired, stressed
    domain_tags = Column(JSON, nullable=True, default=list)     # work, study, life
    
    difficulty = Column(Integer, nullable=False, default=1)
    recovery_safe = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    energy_level = Column(String, nullable=False)   # low, mid, high
    available_time = Column(String, nullable=False) # e.g., '3', '10', '30'
    mental_state = Column(String, nullable=False)   # stressed, distracted etc.
    mode = Column(String, nullable=False)           # recovery, start, maintain
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="checkins")

class Completion(Base):
    __tablename__ = "completions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action_id = Column(String, ForeignKey("actions.id"), nullable=False)
    status = Column(String, nullable=False)         # done, partial, fail
    score = Column(Float, nullable=False, default=0.0) # e.g. 1.0, 0.7, 0.4
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="completions")
    action = relationship("Action")
