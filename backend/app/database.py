from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(String, nullable=True)  # or DateTime if you prefer
    status = Column(String, default="pending")
    owner = Column(String, nullable=True)  # Slack ID or email sender
    source = Column(String, nullable=False)  # "slack" or "email"
    created_at = Column(DateTime, server_default=func.now())  # Creation time


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Client name
    slack_id = Column(String, unique=True, nullable=True)  # Slack ID
    email = Column(String, unique=True, nullable=True)  # Email address
    created_at = Column(DateTime, server_default=func.now())

# Processed Messages table for Slack
class ProcessedMessage(Base):
    __tablename__ = "processed_messages"
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(String, unique=True, nullable=False)  # Slack message timestamp


# Processed Messages table for Gmail
class ProcessedEmail(Base):
    __tablename__ = "processed_emails"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, nullable=False)  # Gmail message ID

Base.metadata.create_all(bind=engine)
