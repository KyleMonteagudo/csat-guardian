# =============================================================================
# CSAT Guardian - Database Module
# =============================================================================
# This module handles all database operations for the POC.
# 
# For the POC, we use SQLite to store:
# - Sample case data (mock DfM data)
# - Alert history
# - Configuration
# - Aggregate metrics
#
# In production, this would be replaced with Azure SQL or Cosmos DB,
# and the DfM data would come from real API calls instead of the database.
#
# The module uses SQLAlchemy for:
# - ORM mapping
# - Async database operations
# - Schema management
# =============================================================================

import os
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, DateTime, Float, Boolean, Integer, 
    ForeignKey, Enum as SQLEnum, create_engine
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.future import select

from logger import get_logger, log_api_call

# Get logger for this module
logger = get_logger(__name__)

# SQLAlchemy declarative base for ORM models
Base = declarative_base()


# =============================================================================
# Database ORM Models
# =============================================================================
# These models define the database schema. Note that these are SEPARATE from
# the Pydantic models in models.py - these are for database persistence only.

class DBEngineer(Base):
    """
    Database model for engineers.
    
    This table stores engineer information for routing notifications
    and tracking alert history.
    """
    __tablename__ = "engineers"
    
    # Primary key - unique engineer identifier
    id = Column(String(50), primary_key=True)
    
    # Engineer details
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    teams_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cases = relationship("DBCase", back_populates="owner")
    alerts = relationship("DBAlert", back_populates="recipient")


class DBCustomer(Base):
    """
    Database model for customers.
    
    NOTE: We store minimal customer data - just an ID and optional company.
    No PII like names, emails, or phone numbers.
    """
    __tablename__ = "customers"
    
    # Primary key - anonymized customer identifier
    id = Column(String(50), primary_key=True)
    
    # Customer details (minimal)
    company = Column(String(200), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cases = relationship("DBCase", back_populates="customer")


class DBCase(Base):
    """
    Database model for support cases.
    
    This is the primary table for POC case data. In production,
    this data would come from DfM API calls instead.
    """
    __tablename__ = "cases"
    
    # Primary key - case identifier
    id = Column(String(50), primary_key=True)
    
    # Case details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="active")
    priority = Column(String(20), nullable=False, default="medium")
    
    # Timestamps
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    modified_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign keys
    owner_id = Column(String(50), ForeignKey("engineers.id"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.id"), nullable=False)
    
    # Relationships
    owner = relationship("DBEngineer", back_populates="cases")
    customer = relationship("DBCustomer", back_populates="cases")
    timeline_entries = relationship("DBTimelineEntry", back_populates="case")


class DBTimelineEntry(Base):
    """
    Database model for case timeline entries.
    
    This stores notes, emails, phone call notes, etc. for each case.
    """
    __tablename__ = "timeline_entries"
    
    # Primary key
    id = Column(String(50), primary_key=True)
    
    # Foreign key to parent case
    case_id = Column(String(50), ForeignKey("cases.id"), nullable=False)
    
    # Entry details
    entry_type = Column(String(20), nullable=False)  # note, email, phone_call
    subject = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(200), nullable=False)
    direction = Column(String(20), nullable=True)  # inbound, outbound (for emails)
    is_customer_communication = Column(Boolean, default=False)
    
    # Relationships
    case = relationship("DBCase", back_populates="timeline_entries")


class DBAlert(Base):
    """
    Database model for alert history.
    
    This tracks all alerts sent by CSAT Guardian for auditing
    and to prevent duplicate notifications.
    """
    __tablename__ = "alerts"
    
    # Primary key
    id = Column(String(50), primary_key=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)
    urgency = Column(String(20), nullable=False)
    case_id = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # Foreign key to recipient
    recipient_id = Column(String(50), ForeignKey("engineers.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Relationships
    recipient = relationship("DBEngineer", back_populates="alerts")


class DBMetric(Base):
    """
    Database model for aggregate metrics.
    
    This stores anonymized metrics for dashboards and reporting.
    No PII is stored here - just counts and averages.
    """
    __tablename__ = "metrics"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Optional dimensions for filtering
    dimension_name = Column(String(100), nullable=True)
    dimension_value = Column(String(200), nullable=True)


# =============================================================================
# Database Manager Class
# =============================================================================

class DatabaseManager:
    """
    Manager class for all database operations.
    
    This class provides:
    - Database initialization and schema creation
    - CRUD operations for all entities
    - Async support for non-blocking operations
    - Conversion between DB models and Pydantic models
    
    Usage:
        db = DatabaseManager("data/csat_guardian.db")
        await db.initialize()
        
        cases = await db.get_active_cases()
        for case in cases:
            print(f"Case {case.id}: {case.title}")
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        logger.info(f"Initializing database manager with path: {db_path}")
        
        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.debug(f"Created database directory: {db_dir}")
        
        # Create async engine for SQLite
        # Note: aiosqlite is required for async SQLite operations
        self.db_path = db_path
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,  # Set to True for SQL debugging
        )
        
        # Create async session factory
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.debug("Database manager initialized successfully")
    
    async def initialize(self) -> None:
        """
        Initialize the database schema.
        
        This creates all tables if they don't exist. It's safe to call
        multiple times - existing tables won't be modified.
        """
        logger.info("Initializing database schema...")
        
        async with self.engine.begin() as conn:
            # Create all tables defined by the ORM models
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database schema initialized successfully")
    
    async def close(self) -> None:
        """
        Close the database connection.
        
        Call this when shutting down the application to ensure
        all connections are properly closed.
        """
        logger.info("Closing database connection...")
        await self.engine.dispose()
        logger.debug("Database connection closed")
    
    # -------------------------------------------------------------------------
    # Engineer Operations
    # -------------------------------------------------------------------------
    
    async def get_engineer(self, engineer_id: str) -> Optional[DBEngineer]:
        """
        Get an engineer by ID.
        
        Args:
            engineer_id: The engineer's unique identifier
            
        Returns:
            DBEngineer if found, None otherwise
        """
        logger.debug(f"Fetching engineer: {engineer_id}")
        
        async with self.async_session() as session:
            result = await session.execute(
                select(DBEngineer).where(DBEngineer.id == engineer_id)
            )
            engineer = result.scalar_one_or_none()
            
            if engineer:
                logger.debug(f"Found engineer: {engineer.name}")
            else:
                logger.debug(f"Engineer not found: {engineer_id}")
            
            return engineer
    
    async def create_engineer(
        self,
        engineer_id: str,
        name: str,
        email: str,
        teams_id: Optional[str] = None
    ) -> DBEngineer:
        """
        Create a new engineer record.
        
        Args:
            engineer_id: Unique identifier
            name: Full name
            email: Email address
            teams_id: Optional Teams user ID
            
        Returns:
            DBEngineer: The created engineer record
        """
        logger.info(f"Creating engineer: {name} ({email})")
        
        async with self.async_session() as session:
            engineer = DBEngineer(
                id=engineer_id,
                name=name,
                email=email,
                teams_id=teams_id,
            )
            session.add(engineer)
            await session.commit()
            
            logger.debug(f"Engineer created successfully: {engineer_id}")
            return engineer
    
    # -------------------------------------------------------------------------
    # Case Operations
    # -------------------------------------------------------------------------
    
    async def get_case(self, case_id: str) -> Optional[DBCase]:
        """
        Get a case by ID, including timeline entries.
        
        Args:
            case_id: The case identifier
            
        Returns:
            DBCase if found, None otherwise
        """
        logger.debug(f"Fetching case: {case_id}")
        
        async with self.async_session() as session:
            # Query case with eager loading of relationships
            result = await session.execute(
                select(DBCase)
                .where(DBCase.id == case_id)
            )
            case = result.scalar_one_or_none()
            
            if case:
                # Eagerly load relationships
                await session.refresh(case, ["owner", "customer", "timeline_entries"])
                logger.debug(f"Found case: {case.title}")
            else:
                logger.debug(f"Case not found: {case_id}")
            
            return case
    
    async def get_active_cases(self) -> list[DBCase]:
        """
        Get all active cases.
        
        This returns cases that are not resolved or cancelled,
        along with their timeline entries.
        
        Returns:
            list[DBCase]: List of active cases
        """
        logger.info("Fetching active cases...")
        
        async with self.async_session() as session:
            result = await session.execute(
                select(DBCase)
                .where(DBCase.status.in_(["active", "in_progress"]))
            )
            cases = result.scalars().all()
            
            # Eagerly load relationships for each case
            for case in cases:
                await session.refresh(case, ["owner", "customer", "timeline_entries"])
            
            logger.info(f"Found {len(cases)} active cases")
            return list(cases)
    
    async def get_cases_by_owner(self, owner_id: str) -> list[DBCase]:
        """
        Get all cases assigned to a specific engineer.
        
        Args:
            owner_id: The engineer's identifier
            
        Returns:
            list[DBCase]: List of cases assigned to the engineer
        """
        logger.debug(f"Fetching cases for engineer: {owner_id}")
        
        async with self.async_session() as session:
            result = await session.execute(
                select(DBCase)
                .where(DBCase.owner_id == owner_id)
            )
            cases = result.scalars().all()
            
            # Eagerly load relationships for each case
            for case in cases:
                await session.refresh(case, ["owner", "customer", "timeline_entries"])
            
            logger.debug(f"Found {len(cases)} cases for engineer {owner_id}")
            return list(cases)
    
    async def create_case(
        self,
        case_id: str,
        title: str,
        description: str,
        owner_id: str,
        customer_id: str,
        status: str = "active",
        priority: str = "medium",
    ) -> DBCase:
        """
        Create a new case record.
        
        Args:
            case_id: Unique case identifier
            title: Case title
            description: Case description
            owner_id: Assigned engineer ID
            customer_id: Customer ID
            status: Case status (default: "active")
            priority: Case priority (default: "medium")
            
        Returns:
            DBCase: The created case record
        """
        logger.info(f"Creating case: {case_id} - {title}")
        
        async with self.async_session() as session:
            case = DBCase(
                id=case_id,
                title=title,
                description=description,
                status=status,
                priority=priority,
                owner_id=owner_id,
                customer_id=customer_id,
            )
            session.add(case)
            await session.commit()
            
            logger.debug(f"Case created successfully: {case_id}")
            return case
    
    # -------------------------------------------------------------------------
    # Timeline Entry Operations
    # -------------------------------------------------------------------------
    
    async def add_timeline_entry(
        self,
        entry_id: str,
        case_id: str,
        entry_type: str,
        content: str,
        created_by: str,
        subject: Optional[str] = None,
        direction: Optional[str] = None,
        is_customer_communication: bool = False,
    ) -> DBTimelineEntry:
        """
        Add a timeline entry to a case.
        
        Args:
            entry_id: Unique entry identifier
            case_id: Parent case ID
            entry_type: Type of entry (note, email, phone_call)
            content: Entry content text
            created_by: Who created this entry
            subject: Optional subject line
            direction: For emails - inbound/outbound
            is_customer_communication: True if customer interaction
            
        Returns:
            DBTimelineEntry: The created entry
        """
        logger.debug(f"Adding timeline entry to case {case_id}: {entry_type}")
        
        async with self.async_session() as session:
            entry = DBTimelineEntry(
                id=entry_id,
                case_id=case_id,
                entry_type=entry_type,
                content=content,
                created_by=created_by,
                subject=subject,
                direction=direction,
                is_customer_communication=is_customer_communication,
            )
            session.add(entry)
            
            # Update case modified timestamp
            result = await session.execute(
                select(DBCase).where(DBCase.id == case_id)
            )
            case = result.scalar_one_or_none()
            if case:
                case.modified_on = datetime.utcnow()
            
            await session.commit()
            
            logger.debug(f"Timeline entry added: {entry_id}")
            return entry
    
    # -------------------------------------------------------------------------
    # Alert Operations
    # -------------------------------------------------------------------------
    
    async def create_alert(
        self,
        alert_id: str,
        alert_type: str,
        urgency: str,
        case_id: str,
        recipient_id: str,
        title: str,
        message: str,
    ) -> DBAlert:
        """
        Create a new alert record.
        
        Args:
            alert_id: Unique alert identifier
            alert_type: Type of alert (sentiment_alert, 7day_warning, etc.)
            urgency: Urgency level (high, medium, low)
            case_id: Related case ID
            recipient_id: Engineer to notify
            title: Alert title
            message: Full alert message
            
        Returns:
            DBAlert: The created alert record
        """
        logger.info(f"Creating alert: {alert_type} for case {case_id}")
        
        async with self.async_session() as session:
            alert = DBAlert(
                id=alert_id,
                alert_type=alert_type,
                urgency=urgency,
                case_id=case_id,
                recipient_id=recipient_id,
                title=title,
                message=message,
            )
            session.add(alert)
            await session.commit()
            
            logger.debug(f"Alert created: {alert_id}")
            return alert
    
    async def mark_alert_sent(self, alert_id: str) -> None:
        """
        Mark an alert as sent.
        
        Args:
            alert_id: The alert identifier
        """
        logger.debug(f"Marking alert as sent: {alert_id}")
        
        async with self.async_session() as session:
            result = await session.execute(
                select(DBAlert).where(DBAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            
            if alert:
                alert.sent_at = datetime.utcnow()
                await session.commit()
                logger.debug(f"Alert marked as sent: {alert_id}")
            else:
                logger.warning(f"Alert not found for marking as sent: {alert_id}")
    
    async def get_recent_alerts(
        self,
        case_id: str,
        alert_type: str,
        hours: int = 24
    ) -> list[DBAlert]:
        """
        Get recent alerts of a specific type for a case.
        
        This is used to prevent duplicate alerts - we don't want to
        send the same alert type multiple times in a short period.
        
        Args:
            case_id: The case identifier
            alert_type: Type of alert to check
            hours: How far back to look
            
        Returns:
            list[DBAlert]: List of recent alerts
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        async with self.async_session() as session:
            result = await session.execute(
                select(DBAlert)
                .where(DBAlert.case_id == case_id)
                .where(DBAlert.alert_type == alert_type)
                .where(DBAlert.created_at >= cutoff)
            )
            alerts = result.scalars().all()
            
            logger.debug(
                f"Found {len(alerts)} recent {alert_type} alerts for case {case_id}"
            )
            return list(alerts)
    
    # -------------------------------------------------------------------------
    # Metric Operations
    # -------------------------------------------------------------------------
    
    async def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        dimension_name: Optional[str] = None,
        dimension_value: Optional[str] = None,
    ) -> None:
        """
        Record an aggregate metric.
        
        Args:
            metric_name: Name of the metric (e.g., "negative_sentiment_count")
            metric_value: The metric value
            dimension_name: Optional dimension for filtering
            dimension_value: Dimension value
        """
        logger.debug(f"Recording metric: {metric_name} = {metric_value}")
        
        async with self.async_session() as session:
            metric = DBMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                dimension_name=dimension_name,
                dimension_value=dimension_value,
            )
            session.add(metric)
            await session.commit()
