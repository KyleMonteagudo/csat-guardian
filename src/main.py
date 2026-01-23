# =============================================================================
# CSAT Guardian - Main Entry Point
# =============================================================================
# This is the main entry point for the CSAT Guardian application.
#
# The application can run in several modes:
# 1. scan     - Run a single monitoring scan
# 2. monitor  - Run continuous monitoring
# 3. chat     - Start an interactive chat session
# 4. setup    - Initialize the database with sample data
#
# Usage:
#   python main.py scan      # Run single scan
#   python main.py monitor   # Run continuous monitoring
#   python main.py chat      # Interactive chat mode
#   python main.py setup     # Initialize sample data
# =============================================================================

import asyncio
import argparse
import sys
from datetime import datetime

# =============================================================================
# Application Banner
# =============================================================================

BANNER = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██████╗███████╗ █████╗ ████████╗     ██████╗ ██╗   ██╗ █████╗ ██████╗      ║
║  ██╔════╝██╔════╝██╔══██╗╚══██╔══╝    ██╔════╝ ██║   ██║██╔══██╗██╔══██╗     ║
║  ██║     ███████╗███████║   ██║       ██║  ███╗██║   ██║███████║██████╔╝     ║
║  ██║     ╚════██║██╔══██║   ██║       ██║   ██║██║   ██║██╔══██║██╔══██╗     ║
║  ╚██████╗███████║██║  ██║   ██║       ╚██████╔╝╚██████╔╝██║  ██║██║  ██║     ║
║   ╚═════╝╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝     ║
║                                                                               ║
║              Customer Satisfaction Guardian - POC v0.1.0                      ║
║              Proactive CSAT Risk Detection and Intervention                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""


# =============================================================================
# Main Application Class
# =============================================================================

class CSATGuardianApp:
    """
    Main application orchestrator for CSAT Guardian.
    
    This class manages:
    - Application initialization
    - Configuration loading
    - Database setup
    - Running different modes (scan, monitor, chat)
    """
    
    def __init__(self):
        """Initialize the application (lazy loading of dependencies)."""
        self._config = None
        self._database = None
        self._dfm_client = None
        self._teams_client = None
        self._sentiment_service = None
        self._alert_service = None
        self._logger = None
    
    async def initialize(self):
        """
        Initialize the application and all its dependencies.
        
        This method:
        1. Loads configuration from environment
        2. Sets up logging
        3. Initializes the database
        4. Creates service instances
        """
        # Import here to avoid circular imports
        from config import get_config
        from logger import setup_logging, get_logger
        from database import DatabaseManager
        
        # Print banner
        print(BANNER)
        
        # Load configuration
        print("🔧 Loading configuration...")
        self._config = get_config()
        
        # Set up logging
        setup_logging(
            level=self._config.log_level,
        )
        self._logger = get_logger(__name__)
        self._logger.info("CSAT Guardian starting...")
        
        # Log configuration status
        self._logger.info(f"Using mock DfM client: {self._config.features.use_mock_dfm}")
        self._logger.info(f"Using mock Teams client: {self._config.features.use_mock_teams}")
        
        if self._config.azure_openai.endpoint:
            self._logger.info(f"Azure OpenAI configured: {self._config.azure_openai.endpoint}")
        else:
            self._logger.warning("Azure OpenAI NOT configured - limited functionality")
        
        # Initialize database
        print("💾 Initializing database...")
        self._database = DatabaseManager(self._config.database.connection_string)
        await self._database.initialize()
        self._logger.info("Database initialized")
        
        # Initialize clients and services
        print("🔌 Initializing services...")
        await self._init_services()
        
        print("✅ Initialization complete!\n")
        self._logger.info("CSAT Guardian initialization complete")
    
    async def _init_services(self):
        """Initialize all service dependencies."""
        from clients.dfm_client import get_dfm_client
        from clients.teams_client import get_teams_client
        from services.sentiment_service import get_sentiment_service
        from services.alert_service import AlertService
        
        # Initialize DfM client (mock or real based on config)
        # Pass our database so it uses Azure SQL, not a separate SQLite DB
        self._dfm_client = await get_dfm_client(config=self._config, db=self._database)
        self._logger.debug("DfM client initialized")
        
        # Initialize Teams client (mock or real based on config)
        self._teams_client = get_teams_client(config=self._config)
        self._logger.debug("Teams client initialized")
        
        # Initialize sentiment service
        self._sentiment_service = get_sentiment_service(config=self._config)
        self._logger.debug("Sentiment service initialized")
        
        # Initialize alert service
        self._alert_service = AlertService(
            db=self._database,
            teams_client=self._teams_client,
            config=self._config,
        )
        self._logger.debug("Alert service initialized")
    
    async def setup_sample_data(self):
        """
        Initialize the database with sample data for POC testing.
        """
        from sample_data import create_sample_data
        
        print("📊 Setting up sample data...")
        self._logger.info("Creating sample data for POC...")
        
        try:
            await create_sample_data(self._database)
            print("✅ Sample data created successfully!")
            self._logger.info("Sample data creation complete")
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            self._logger.error(f"Sample data creation failed: {e}", exc_info=True)
            raise
    
    async def run_scan(self):
        """
        Run a single monitoring scan.
        """
        from monitor import CaseMonitor
        
        print("🔍 Running case monitoring scan...\n")
        self._logger.info("Starting single scan mode")
        
        # Create monitor
        monitor = CaseMonitor(
            dfm_client=self._dfm_client,
            sentiment_service=self._sentiment_service,
            alert_service=self._alert_service,
            database=self._database,
            config=self._config,
        )
        
        # Run scan
        results = await monitor.run_scan()
        
        # Print results summary
        print("\n" + "=" * 60)
        print("SCAN RESULTS SUMMARY")
        print("=" * 60)
        print(f"  Scan ID:              {results['scan_id']}")
        print(f"  Total Cases:          {results['total_cases']}")
        print(f"  Negative Sentiment:   {results['negative_sentiment']}")
        print(f"  Declining Sentiment:  {results['declining_sentiment']}")
        print(f"  Compliance Warnings:  {results['compliance_warnings']}")
        print(f"  Compliance Breaches:  {results['compliance_breaches']}")
        print(f"  Alerts Sent:          {results['alerts_sent']}")
        print(f"  Errors:               {results['errors']}")
        print("=" * 60)
        
        return results
    
    async def run_continuous_monitor(self, interval_minutes: int = 60):
        """
        Run continuous monitoring.
        
        Args:
            interval_minutes: Minutes between scans
        """
        from monitor import CaseMonitor
        
        print(f"👁️ Starting continuous monitoring (every {interval_minutes} minutes)...")
        print("   Press Ctrl+C to stop\n")
        self._logger.info(f"Starting continuous monitoring mode (interval: {interval_minutes}m)")
        
        # Create monitor
        monitor = CaseMonitor(
            dfm_client=self._dfm_client,
            sentiment_service=self._sentiment_service,
            alert_service=self._alert_service,
            database=self._database,
            config=self._config,
        )
        
        try:
            await monitor.run_continuous(interval_minutes)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            monitor.stop()
    
    async def run_chat(self, engineer_id: str = "eng-001"):
        """
        Run interactive chat mode.
        
        Args:
            engineer_id: ID of the engineer to simulate
        """
        from agent.guardian_agent import create_agent
        from models import Engineer
        
        # Get engineer from database
        engineer_db = await self._database.get_engineer(engineer_id)
        
        if engineer_db is None:
            print(f"❌ Engineer {engineer_id} not found. Run 'setup' first to create sample data.")
            return
        
        # Create Engineer model
        engineer = Engineer(
            id=engineer_db.id,
            name=engineer_db.name,
            email=engineer_db.email,
        )
        
        print(f"💬 Starting chat as {engineer.name} ({engineer_id})")
        print("   Type 'quit' or 'exit' to end the session")
        print("   Type 'help' for available commands\n")
        print("-" * 60)
        
        self._logger.info(f"Starting chat mode for engineer: {engineer.name}")
        
        # Create agent
        agent = await create_agent(
            engineer=engineer,
            dfm_client=self._dfm_client,
            sentiment_service=self._sentiment_service,
            config=self._config,
        )
        
        # Chat loop
        while True:
            try:
                # Get user input
                user_input = input(f"\n[{engineer.name}] You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\n👋 Goodbye! Session ended.")
                    break
                
                # Check for help command
                if user_input.lower() == "help":
                    print("\n" + "=" * 60)
                    print("AVAILABLE COMMANDS")
                    print("=" * 60)
                    print("  'list my cases'  - Show all cases assigned to you")
                    print("  'tell me about case <ID>' - Get case summary")
                    print("  'analyze case <ID>' - Get sentiment analysis")
                    print("  'recommendations for case <ID>' - Get suggestions")
                    print("  'quit' or 'exit' - End the session")
                    print("=" * 60)
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Get response from agent
                print("\n🤔 Thinking...")
                response = await agent.chat(user_input)
                
                print(f"\n[CSAT Guardian] {response}")
                
            except KeyboardInterrupt:
                print("\n\n🛑 Chat ended")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                self._logger.error(f"Chat error: {e}", exc_info=True)
    
    async def cleanup(self):
        """
        Clean up resources before shutdown.
        """
        if self._logger:
            self._logger.info("CSAT Guardian shutting down...")
        
        # Close database connections
        # (SQLAlchemy handles this automatically, but explicit cleanup is good practice)
        
        if self._logger:
            self._logger.info("Cleanup complete")


# =============================================================================
# Command Line Interface
# =============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="CSAT Guardian - Customer Satisfaction Guardian System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py setup              # Initialize database with sample data
  python main.py scan               # Run a single monitoring scan
  python main.py monitor            # Start continuous monitoring
  python main.py monitor --interval 30  # Monitor every 30 minutes
  python main.py chat               # Start interactive chat
  python main.py chat --engineer eng-002  # Chat as specific engineer
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Initialize sample data")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Run a single scan")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Run continuous monitoring")
    monitor_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Minutes between scans (default: 60)"
    )
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")
    chat_parser.add_argument(
        "--engineer",
        type=str,
        default="eng-001",
        help="Engineer ID to chat as (default: eng-001)"
    )
    
    return parser.parse_args()


async def main():
    """
    Main application entry point.
    """
    # Parse arguments
    args = parse_arguments()
    
    # Create and initialize application
    app = CSATGuardianApp()
    
    try:
        # Initialize the application
        await app.initialize()
        
        # Run the appropriate command
        if args.command == "setup":
            await app.setup_sample_data()
            
        elif args.command == "scan":
            await app.run_scan()
            
        elif args.command == "monitor":
            await app.run_continuous_monitor(args.interval)
            
        elif args.command == "chat":
            await app.run_chat(args.engineer)
            
        else:
            # Default: show help and run setup + scan
            print("No command specified. Running setup and scan...\n")
            await app.setup_sample_data()
            print()
            await app.run_scan()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Application interrupted")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await app.cleanup()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
