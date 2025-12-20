from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Float
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)

class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), default="pending")
    model_name = Column(String(50))
    epochs = Column(Integer)
    batch_size = Column(Integer)
    learning_rate = Column(String(20)) # Store as string just in case
    classes = Column(Integer) # Store number of classes
    augmentation = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    prediction_text = Column(Text)
    confidence = Column(Float)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
