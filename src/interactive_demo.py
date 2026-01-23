# =============================================================================
# CSAT Guardian - Interactive Demo Mode
# =============================================================================
# A simplified interactive chat experience that emulates a Teams-like interface.
# This demonstrates the core POC capabilities without complex Semantic Kernel setup.
#
# Usage:
#   python interactive_demo.py
#   python interactive_demo.py --engineer eng-002
#
# =============================================================================

import asyncio
import sys
import os
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from database import DatabaseManager
from clients.dfm_client import get_dfm_client
from services.sentiment_service import get_sentiment_service
from models import Case, Engineer
from logger import get_logger

logger = get_logger(__name__)


class InteractiveDemo:
    """
    Interactive demo that emulates a Teams-like chat experience.
    
    Features:
    - List cases with SR numbers and titles (numbered for selection)
    - Select a case by number to review
    - Get case summary
    - Get sentiment analysis
    - Get recommendations
    """
    
    def __init__(self):
        self.config = None
        self.database = None
        self.dfm_client = None
        self.sentiment_service = None
        self.current_engineer: Optional[Engineer] = None
        self.cached_cases: List[Case] = []
    
    async def initialize(self, engineer_id: str = "eng-001"):
        """Initialize the demo with Azure connections."""
        print("\n" + "=" * 60)
        print("   CSAT GUARDIAN - Interactive Demo")
        print("   Powered by Azure OpenAI (Azure Government)")
        print("=" * 60)
        print("\nInitializing...")
        
        # Load config
        self.config = get_config()
        
        # Connect to Azure SQL
        print("  ▸ Connecting to Azure SQL Database...", end=" ")
        self.database = DatabaseManager(self.config.database.connection_string)
        await self.database.initialize()
        print("✓")
        
        # Initialize services
        print("  ▸ Initializing DfM client...", end=" ")
        self.dfm_client = await get_dfm_client(self.config, self.database)
        print("✓")
        
        print("  ▸ Initializing Azure OpenAI...", end=" ")
        self.sentiment_service = get_sentiment_service(self.config)
        print("✓")
        
        # Load engineer
        print(f"  ▸ Loading engineer profile ({engineer_id})...", end=" ")
        engineer_db = await self.database.get_engineer(engineer_id)
        if engineer_db:
            self.current_engineer = Engineer(
                id=engineer_db.id,
                name=engineer_db.name,
                email=engineer_db.email,
            )
            print("✓")
        else:
            print("✗")
            print(f"\nError: Engineer {engineer_id} not found. Available engineers:")
            # List available engineers
            print("  - eng-001 (John Smith)")
            print("  - eng-002 (Mike Chen)")
            print("  - eng-003 (Sarah Johnson)")
            return False
        
        print("\nReady! Type 'help' for commands.\n")
        return True
    
    def print_welcome(self):
        """Print welcome message."""
        print("-" * 60)
        print(f"Hello, {self.current_engineer.name}!")
        print("   I'm CSAT Guardian, here to help you manage your cases.")
        print("-" * 60)
        print("\nHow can I help you today?\n")
    
    def print_help(self):
        """Print available commands."""
        print("\n" + "=" * 60)
        print("   AVAILABLE COMMANDS")
        print("=" * 60)
        print("""
  VIEWING CASES:
    list / cases          List all your cases with numbers
    <number>              Select a case by its number (after listing)
  
  CASE ANALYSIS:
    summary               Get summary of selected case
    sentiment             Analyze sentiment of selected case
    recommendations       Get action recommendations
  
  GENERAL:
    help                  Show this help message
    quit / exit           End the session
""")
        print("=" * 60 + "\n")
    
    async def list_cases(self):
        """List all cases for the current engineer with numbers."""
        print("\n🔍 Loading your cases...")
        
        self.cached_cases = await self.dfm_client.get_cases_by_owner(
            self.current_engineer.id
        )
        
        if not self.cached_cases:
            print("\n   You don't have any cases assigned.\n")
            return
        
        print("\n" + "=" * 60)
        print(f"   YOUR CASES ({len(self.cached_cases)} total)")
        print("=" * 60)
        print()
        
        for i, case in enumerate(self.cached_cases, 1):
            # Status indicator
            if case.days_since_last_note >= 7:
                status_icon = "🚨"
                status_hint = "(OVERDUE)"
            elif case.days_since_last_note >= 5:
                status_icon = "⚠️"
                status_hint = "(Due soon)"
            else:
                status_icon = "✅"
                status_hint = ""
            
            print(f"  {i}. {status_icon} [{case.id}] {case.title[:40]}")
            print(f"     Priority: {case.priority.value} | Status: {case.status.value}")
            print(f"     Last update: {case.days_since_last_note:.0f} days ago {status_hint}")
            print()
        
        print("-" * 60)
        print("💡 Enter a number (1-{}) to select a case.".format(len(self.cached_cases)))
        print("-" * 60 + "\n")
    
    async def select_case(self, index: int) -> Optional[Case]:
        """Select a case by index."""
        if not self.cached_cases:
            print("\n⚠️ Please list cases first with 'list' command.\n")
            return None
        
        if index < 1 or index > len(self.cached_cases):
            print(f"\n⚠️ Invalid selection. Please enter 1-{len(self.cached_cases)}.\n")
            return None
        
        return self.cached_cases[index - 1]
    
    async def show_summary(self, case: Case):
        """Show a summary of the case."""
        print("\n" + "=" * 60)
        print(f"   CASE SUMMARY: {case.id}")
        print("=" * 60)
        print(f"""
  📋 Title:     {case.title}
  🏢 Customer:  {case.customer.company}
  📊 Status:    {case.status.value}
  🔥 Priority:  {case.priority.value}
  📅 Created:   {case.created_on.strftime('%Y-%m-%d')} ({case.days_since_creation:.0f} days ago)
  📝 Last Note: {case.days_since_last_note:.1f} days ago
  
  DESCRIPTION:
  {case.description[:500]}
  
  RECENT TIMELINE ({len(case.timeline)} entries):
""")
        
        for entry in case.timeline[-3:]:
            content_preview = entry.content[:80].replace('\n', ' ')
            print(f"    [{entry.entry_type.value}] {entry.created_on.strftime('%Y-%m-%d')}")
            print(f"      {content_preview}...")
            print()
        
        print("=" * 60 + "\n")
    
    async def analyze_sentiment(self, case: Case):
        """Perform sentiment analysis on the case."""
        print("\n🎭 Analyzing sentiment with Azure OpenAI...")
        
        try:
            analysis = await self.sentiment_service.analyze_case(case)
            
            # Sentiment display
            sentiment_emoji = {
                "positive": "😊",
                "neutral": "😐",
                "negative": "😞"
            }
            emoji = sentiment_emoji.get(analysis.overall_sentiment.label.value, "❓")
            
            print("\n" + "=" * 60)
            print(f"   SENTIMENT ANALYSIS: {case.id}")
            print("=" * 60)
            print(f"""
  {emoji} Overall Sentiment: {analysis.overall_sentiment.label.value.upper()}
  
  📊 Score:      {analysis.overall_sentiment.score:.2f} (0=negative → 1=positive)
  📈 Confidence: {analysis.overall_sentiment.confidence:.0%}
  📉 Trend:      {analysis.sentiment_trend}
  
  ⏰ COMPLIANCE STATUS: {analysis.compliance_status.upper()}
     Days since last note: {analysis.days_since_last_note:.1f}
""")
            
            if analysis.overall_sentiment.key_phrases:
                print("  🔑 KEY PHRASES:")
                for phrase in analysis.overall_sentiment.key_phrases[:5]:
                    print(f'     • "{phrase}"')
                print()
            
            if analysis.overall_sentiment.concerns:
                print("  ⚠️ CUSTOMER CONCERNS:")
                for concern in analysis.overall_sentiment.concerns[:5]:
                    print(f"     • {concern}")
                print()
            
            print("=" * 60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error analyzing sentiment: {e}\n")
    
    async def show_recommendations(self, case: Case):
        """Show recommendations for the case."""
        print("\n💡 Generating recommendations...")
        
        try:
            analysis = await self.sentiment_service.analyze_case(case)
            
            print("\n" + "=" * 60)
            print(f"   RECOMMENDATIONS: {case.id}")
            print("=" * 60)
            print()
            
            if analysis.recommendations:
                print("  Based on case analysis, here are suggested actions:")
                print()
                for i, rec in enumerate(analysis.recommendations, 1):
                    print(f"    {i}. {rec}")
                print()
            
            # Compliance-specific recommendations
            if analysis.compliance_status == "warning":
                print("  ⚠️ COMPLIANCE ALERT:")
                print("     This case is approaching the 7-day update requirement.")
                print("     → Add a case note within the next 2 days.\n")
            elif analysis.compliance_status == "breach":
                print("  🚨 COMPLIANCE ALERT:")
                print("     This case has exceeded the 7-day update requirement!")
                print("     → Add a case note IMMEDIATELY.\n")
            
            # Sentiment-specific recommendations
            if analysis.overall_sentiment.label.value == "negative":
                print("  ⚠️ SENTIMENT ALERT:")
                print("     Customer sentiment is negative. Consider:")
                print("     → Scheduling a call to address concerns directly")
                print("     → Escalating to a specialist if needed")
                print("     → Providing a detailed update on progress\n")
            
            print("=" * 60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error generating recommendations: {e}\n")
    
    async def run(self, engineer_id: str = "eng-001"):
        """Run the interactive demo."""
        # Initialize
        if not await self.initialize(engineer_id):
            return
        
        self.print_welcome()
        
        selected_case: Optional[Case] = None
        
        while True:
            try:
                # Get user input
                prompt = f"[{self.current_engineer.name}] > "
                user_input = input(prompt).strip().lower()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Exit commands
                if user_input in ["quit", "exit", "bye", "q"]:
                    print("\n👋 Goodbye! Have a great day.\n")
                    break
                
                # Help command
                if user_input == "help":
                    self.print_help()
                    continue
                
                # List cases
                if user_input in ["list", "cases", "list cases", "my cases"]:
                    await self.list_cases()
                    selected_case = None
                    continue
                
                # Case selection by number
                if user_input.isdigit():
                    index = int(user_input)
                    case = await self.select_case(index)
                    if case:
                        selected_case = case
                        print(f"\n✓ Selected: [{case.id}] {case.title[:50]}")
                        print("  Commands: summary, sentiment, recommendations\n")
                    continue
                
                # Commands requiring a selected case
                if user_input in ["summary", "sum", "s"]:
                    if selected_case:
                        await self.show_summary(selected_case)
                    else:
                        print("\n⚠️ No case selected. Use 'list' then select a number.\n")
                    continue
                
                if user_input in ["sentiment", "analyze", "a"]:
                    if selected_case:
                        await self.analyze_sentiment(selected_case)
                    else:
                        print("\n⚠️ No case selected. Use 'list' then select a number.\n")
                    continue
                
                if user_input in ["recommendations", "rec", "r"]:
                    if selected_case:
                        await self.show_recommendations(selected_case)
                    else:
                        print("\n⚠️ No case selected. Use 'list' then select a number.\n")
                    continue
                
                # Unknown command
                print(f"\n❓ Unknown command: '{user_input}'")
                print("   Type 'help' for available commands.\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session ended.\n")
                break
            except EOFError:
                print("\n\n👋 Session ended.\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logger.error(f"Demo error: {e}", exc_info=True)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CSAT Guardian Interactive Demo")
    parser.add_argument(
        "--engineer",
        default="eng-001",
        help="Engineer ID to simulate (default: eng-001)"
    )
    args = parser.parse_args()
    
    demo = InteractiveDemo()
    await demo.run(args.engineer)


if __name__ == "__main__":
    asyncio.run(main())
