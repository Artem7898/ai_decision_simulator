from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class DecisionType(str, enum.Enum):
    RELOCATION = "relocation"
    PURCHASE = "purchase"
    JOB = "job"
    INVESTMENT = "investment"


class SimulationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scenarios = relationship("Scenario", back_populates="user")


class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    decision_type = Column(SQLEnum(DecisionType), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="scenarios")
    simulations = relationship("Simulation", back_populates="scenario")


class Simulation(Base):
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    input_data = Column(JSON, nullable=False)  # Structured input from LLM
    result_json = Column(JSON)  # Simulation results
    status = Column(SQLEnum(SimulationStatus), default=SimulationStatus.PENDING)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    scenario = relationship("Scenario", back_populates="simulations")


class CachedData(Base):
    """Cache for external API data (cost of living, taxes, etc.)"""
    __tablename__ = "cached_data"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    data = Column(JSON, nullable=False)
    source = Column(String(100))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
