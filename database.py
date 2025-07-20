from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()
import os

# Create database engine (PostgreSQL or SQLite fallback)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llm_lens.db")

# Configure engine based on database type
if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL)
else:
    # SQLite configuration
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class LLMRequestLog(Base):
    """
    SQLAlchemy model for logging LLM requests and responses.
    Stores comprehensive metrics for observability and monitoring.
    """
    __tablename__ = "llm_request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Enhanced fields for streaming and analytics
    is_streaming = Column(Boolean, default=False)
    time_to_first_token_ms = Column(Integer, nullable=True)
    tokens_per_second = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    request_metadata = Column(JSON, nullable=True)
    performance_score = Column(Float, nullable=True)  # Calculated performance metric
    
class AlertRule(Base):
    """
    Model for storing alert rules and thresholds.
    """
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    metric = Column(String, nullable=False)  # 'latency', 'error_rate', 'tokens_per_second'
    threshold = Column(Float, nullable=False)
    operator = Column(String, nullable=False)  # 'gt', 'lt', 'eq'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class AlertEvent(Base):
    """
    Model for storing triggered alert events.
    """
    __tablename__ = "alert_events"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False)
    rule_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class CostSettings(Base):
    """
    Model for storing cost configuration per model.
    """
    __tablename__ = "cost_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, unique=True)
    cost_per_1k_input_tokens = Column(Float, default=0.0)
    cost_per_1k_output_tokens = Column(Float, default=0.0)
    electricity_cost_per_hour = Column(Float, default=0.0)  # For local models
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Budget(Base):
    """
    Model for storing budget limits and tracking.
    """
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    budget_type = Column(String, nullable=False)  # 'daily', 'weekly', 'monthly'
    amount = Column(Float, nullable=False)
    current_usage = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reset_at = Column(DateTime, nullable=True)

class ModelComparison(Base):
    """
    Model for storing A/B testing results between different models.
    """
    __tablename__ = "model_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    comparison_name = Column(String, nullable=False)
    model_a = Column(String, nullable=False)
    model_b = Column(String, nullable=False)
    test_prompt = Column(Text, nullable=False)
    result_a_latency = Column(Float, nullable=True)
    result_b_latency = Column(Float, nullable=True)
    result_a_tokens = Column(Integer, nullable=True)
    result_b_tokens = Column(Integer, nullable=True)
    result_a_cost = Column(Float, nullable=True)
    result_b_cost = Column(Float, nullable=True)
    winner = Column(String, nullable=True)  # 'model_a', 'model_b', 'tie'
    created_at = Column(DateTime, default=datetime.utcnow)

class OptimizationSuggestion(Base):
    """
    Model for storing AI-powered optimization suggestions.
    """
    __tablename__ = "optimization_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    suggestion_type = Column(String, nullable=False)  # 'performance', 'parameter', 'hardware'
    model_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=False)  # 'high', 'medium', 'low'
    potential_improvement = Column(String, nullable=True)  # Expected improvement percentage
    is_implemented = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    implemented_at = Column(DateTime, nullable=True)

def init_database():
    """
    Initialize the database and create all tables if they don't exist.
    This function should be called once when the application starts.
    """
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
