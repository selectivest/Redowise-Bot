from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    MANAGER = "manager"
    MEMBER = "member"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True)
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    language_code = Column(String, default='en')  # Default language is English
    
    # Relationships
    teams = relationship("TeamMember", back_populates="user")
    created_tasks = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    members = relationship("TeamMember", back_populates="team")
    tasks = relationship("Task", back_populates="team")

class TeamMember(Base):
    __tablename__ = 'team_members'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    role = Column(String, nullable=False)  # e.g., "Manager", "Member"
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="teams")
    
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uix_team_user'),
    )

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    creator_id = Column(Integer, ForeignKey('users.id'))
    assignee_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # Values: pending, in_progress, done
    media_file_id = Column(String, nullable=True)  # Store Telegram file_id for media attachments
    
    # Relationships
    team = relationship("Team", back_populates="tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks") 