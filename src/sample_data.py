# =============================================================================
# CSAT Guardian - Sample Data Population Script
# =============================================================================
# This script populates the database with realistic sample data for POC testing.
#
# The sample data includes:
# - Engineers with different cases assigned
# - Customers (anonymized)
# - Cases with various statuses, priorities, and sentiment scenarios
# - Timeline entries (notes, emails, phone call notes)
#
# Scenarios covered:
# 1. Happy customer - positive sentiment, good communication
# 2. Frustrated customer - negative sentiment, needs intervention
# 3. Neutral customer - standard case, no immediate concerns
# 4. At-risk customer - sentiment declining over time
# 5. 7-day compliance warning - case approaching update deadline
# 6. 7-day compliance breach - case past update deadline
#
# Usage:
#     python -m src.sample_data
# =============================================================================

import asyncio
import uuid
from datetime import datetime, timedelta

from database import DatabaseManager, DBEngineer, DBCustomer, DBCase, DBTimelineEntry
from logger import setup_logging, get_logger

# Set up logging
setup_logging(level="DEBUG", verbose=True)
logger = get_logger(__name__)


async def populate_sample_data(db: DatabaseManager) -> None:
    """
    Populate the database with sample data for POC testing.
    
    This creates a realistic set of cases that demonstrate all the
    scenarios CSAT Guardian is designed to handle.
    
    Args:
        db: The database manager instance
    """
    logger.info("=" * 60)
    logger.info("POPULATING SAMPLE DATA FOR POC")
    logger.info("=" * 60)
    
    # -------------------------------------------------------------------------
    # Create Engineers
    # -------------------------------------------------------------------------
    logger.info("Creating sample engineers...")
    
    engineers = [
        {"id": "eng-001", "name": "John Smith", "email": "jsmith@microsoft.com", "teams_id": "teams-001"},
        {"id": "eng-002", "name": "Sarah Johnson", "email": "sjohnson@microsoft.com", "teams_id": "teams-002"},
        {"id": "eng-003", "name": "Mike Chen", "email": "mchen@microsoft.com", "teams_id": "teams-003"},
    ]
    
    for eng in engineers:
        try:
            await db.create_engineer(**eng)
            logger.info(f"  ✓ Created engineer: {eng['name']}")
        except Exception as e:
            logger.warning(f"  ⚠ Engineer may already exist: {eng['name']} ({e})")
    
    # -------------------------------------------------------------------------
    # Create Customers (anonymized)
    # -------------------------------------------------------------------------
    logger.info("Creating sample customers...")
    
    customers = [
        {"id": "cust-001", "company": "Contoso Ltd"},
        {"id": "cust-002", "company": "Fabrikam Inc"},
        {"id": "cust-003", "company": "Adventure Works"},
        {"id": "cust-004", "company": "Northwind Traders"},
        {"id": "cust-005", "company": "Tailspin Toys"},
        {"id": "cust-006", "company": "Wide World Importers"},
    ]
    
    async with db.async_session() as session:
        for cust in customers:
            try:
                customer = DBCustomer(**cust)
                session.add(customer)
                logger.info(f"  ✓ Created customer: {cust['company']}")
            except Exception as e:
                logger.warning(f"  ⚠ Customer may already exist: {cust['company']} ({e})")
        await session.commit()
    
    # -------------------------------------------------------------------------
    # Create Cases with Various Scenarios
    # -------------------------------------------------------------------------
    logger.info("Creating sample cases...")
    
    now = datetime.utcnow()
    
    # CASE 1: Happy customer - positive sentiment, good communication
    case1 = await db.create_case(
        case_id="case-10001",
        title="Question about license renewal process",
        description="Hi, I need to understand the license renewal process for our Microsoft 365 subscription. Can you please guide me through the steps?",
        owner_id="eng-001",
        customer_id="cust-001",
        status="active",
        priority="low",
    )
    logger.info(f"  ✓ Created case: {case1.title}")
    
    # Timeline for Case 1 - Positive interactions
    await db.add_timeline_entry(
        entry_id="entry-10001-001",
        case_id="case-10001",
        entry_type="email",
        subject="RE: License renewal process",
        content="Thank you for your quick response! The documentation you shared was very helpful. I was able to start the renewal process. Just one quick question - can we add more licenses during renewal?",
        created_by="Customer",
        direction="inbound",
        is_customer_communication=True,
    )
    await db.add_timeline_entry(
        entry_id="entry-10001-002",
        case_id="case-10001",
        entry_type="note",
        subject="Internal note",
        content="Customer is happy with the guidance provided. Sent additional documentation about adding licenses during renewal.",
        created_by="John Smith",
        is_customer_communication=False,
    )
    
    # CASE 2: Frustrated customer - NEGATIVE sentiment, needs intervention
    case2_created = now - timedelta(days=3)
    async with db.async_session() as session:
        case2 = DBCase(
            id="case-10002",
            title="Unable to access shared mailbox after migration - URGENT",
            description="After the migration last week, I cannot access the shared mailbox. This is affecting our entire sales team. We've been unable to respond to customer inquiries!",
            status="active",
            priority="high",
            owner_id="eng-001",
            customer_id="cust-002",
            created_on=case2_created,
            modified_on=now - timedelta(days=1),
        )
        session.add(case2)
        await session.commit()
    logger.info(f"  ✓ Created case: Unable to access shared mailbox (FRUSTRATED)")
    
    # Timeline for Case 2 - Increasingly negative
    await db.add_timeline_entry(
        entry_id="entry-10002-001",
        case_id="case-10002",
        entry_type="email",
        subject="RE: Shared mailbox access",
        content="I've been waiting for 3 days now with no real update. This is unacceptable for a P1 issue. Our customers are complaining that we're not responding to their emails!",
        created_by="Customer",
        direction="inbound",
        is_customer_communication=True,
    )
    await db.add_timeline_entry(
        entry_id="entry-10002-002",
        case_id="case-10002",
        entry_type="email",
        subject="RE: Shared mailbox access",
        content="Another day, another excuse. I need to speak with your manager. This level of service is completely unacceptable.",
        created_by="Customer",
        direction="inbound",
        is_customer_communication=True,
    )
    await db.add_timeline_entry(
        entry_id="entry-10002-003",
        case_id="case-10002",
        entry_type="note",
        subject="Investigation note",
        content="Escalated to Exchange team for investigation. Waiting on response.",
        created_by="John Smith",
        is_customer_communication=False,
    )
    
    # CASE 3: Neutral customer - standard case
    case3 = await db.create_case(
        case_id="case-10003",
        title="How to configure conditional access policies",
        description="We're implementing conditional access and need guidance on best practices for our organization.",
        owner_id="eng-002",
        customer_id="cust-003",
        status="active",
        priority="medium",
    )
    logger.info(f"  ✓ Created case: {case3.title}")
    
    await db.add_timeline_entry(
        entry_id="entry-10003-001",
        case_id="case-10003",
        entry_type="email",
        subject="RE: Conditional access configuration",
        content="Thanks for the call today. I've reviewed the documentation you shared. We'll implement the suggested policies and let you know if we have questions.",
        created_by="Customer",
        direction="inbound",
        is_customer_communication=True,
    )
    
    # CASE 4: At-risk customer - sentiment declining over time
    case4_created = now - timedelta(days=5)
    async with db.async_session() as session:
        case4 = DBCase(
            id="case-10004",
            title="Performance issues with Teams after update",
            description="After the latest Teams update, we're experiencing significant lag and crashes. Multiple users affected.",
            status="active",
            priority="high",
            owner_id="eng-002",
            customer_id="cust-004",
            created_on=case4_created,
            modified_on=now - timedelta(hours=12),
        )
        session.add(case4)
        await session.commit()
    logger.info(f"  ✓ Created case: Teams performance issues (AT-RISK)")
    
    # Timeline showing declining sentiment
    await db.add_timeline_entry(
        entry_id="entry-10004-001",
        case_id="case-10004",
        entry_type="email",
        subject="Initial report",
        content="Hi, we've noticed some performance issues with Teams after the latest update. Could you please help us investigate?",
        created_by="Customer",
        direction="inbound",
        is_customer_communication=True,
    )
    await db.add_timeline_entry(
        entry_id="entry-10004-002",
        case_id="case-10004",
        entry_type="email",
        subject="RE: Teams performance",
        content="It's been 2 days and the issues are getting worse. More users are now affected. When can we expect a resolution?",
        created_by="Customer",
        direction="inbound",
        is_customer_communication=True,
    )
    await db.add_timeline_entry(
        entry_id="entry-10004-003",
        case_id="case-10004",
        entry_type="phone_call",
        subject="Customer call",
        content="Customer called expressing frustration. They mentioned their CEO is now aware of the issue and is asking for answers. Promised to provide update by EOD.",
        created_by="Sarah Johnson",
        is_customer_communication=True,
    )
    await db.add_timeline_entry(
        entry_id="entry-10004-004",
        case_id="case-10004",
        entry_type="email",
        subject="RE: Teams performance",
        content="I'm still waiting for that end-of-day update you promised. This is starting to feel like we're not being taken seriously.",
        created_by="Customer",
        direction="inbound",
        is_customer_communication=True,
    )
    
    # CASE 5: 7-day compliance WARNING - approaching deadline
    case5_created = now - timedelta(days=6)
    case5_modified = now - timedelta(days=5, hours=12)  # Last note ~5.5 days ago
    async with db.async_session() as session:
        case5 = DBCase(
            id="case-10005",
            title="Inquiry about Azure cost optimization",
            description="Looking for recommendations on optimizing our Azure spending.",
            status="active",
            priority="low",
            owner_id="eng-003",
            customer_id="cust-005",
            created_on=case5_created,
            modified_on=case5_modified,
        )
        session.add(case5)
        await session.commit()
    logger.info(f"  ✓ Created case: Azure cost optimization (7-DAY WARNING)")
    
    # Only one note, several days ago
    async with db.async_session() as session:
        entry = DBTimelineEntry(
            id="entry-10005-001",
            case_id="case-10005",
            entry_type="note",
            subject="Initial review",
            content="Reviewed customer's Azure usage. Need to schedule call to discuss recommendations.",
            created_by="Mike Chen",
            created_on=case5_modified,
            is_customer_communication=False,
        )
        session.add(entry)
        await session.commit()
    
    # CASE 6: 7-day compliance BREACH - past deadline
    case6_created = now - timedelta(days=10)
    case6_modified = now - timedelta(days=8)  # Last note 8 days ago
    async with db.async_session() as session:
        case6 = DBCase(
            id="case-10006",
            title="Security assessment for compliance audit",
            description="Need security assessment report for upcoming compliance audit.",
            status="active",
            priority="medium",
            owner_id="eng-003",
            customer_id="cust-006",
            created_on=case6_created,
            modified_on=case6_modified,
        )
        session.add(case6)
        await session.commit()
    logger.info(f"  ✓ Created case: Security assessment (7-DAY BREACH)")
    
    # Last note over 7 days ago
    async with db.async_session() as session:
        entry = DBTimelineEntry(
            id="entry-10006-001",
            case_id="case-10006",
            entry_type="note",
            subject="Initial assessment",
            content="Started security assessment. Gathering information from customer environment.",
            created_by="Mike Chen",
            created_on=case6_modified,
            is_customer_communication=False,
        )
        session.add(entry)
        await session.commit()
    
    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    logger.info("")
    logger.info("=" * 60)
    logger.info("SAMPLE DATA POPULATION COMPLETE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Created cases:")
    logger.info("  • case-10001: Happy customer (positive sentiment)")
    logger.info("  • case-10002: Frustrated customer (NEGATIVE sentiment - needs alert)")
    logger.info("  • case-10003: Neutral customer (standard case)")
    logger.info("  • case-10004: At-risk customer (declining sentiment)")
    logger.info("  • case-10005: 7-day WARNING (approaching update deadline)")
    logger.info("  • case-10006: 7-day BREACH (past update deadline)")
    logger.info("")
    logger.info("Engineers:")
    logger.info("  • eng-001 (John Smith): Cases 10001, 10002")
    logger.info("  • eng-002 (Sarah Johnson): Cases 10003, 10004")
    logger.info("  • eng-003 (Mike Chen): Cases 10005, 10006")
    logger.info("")


async def main():
    """Main entry point for sample data population."""
    # Initialize database
    db = DatabaseManager("data/csat_guardian.db")
    await db.initialize()
    
    try:
        # Populate sample data
        await populate_sample_data(db)
    finally:
        # Close database connection
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
