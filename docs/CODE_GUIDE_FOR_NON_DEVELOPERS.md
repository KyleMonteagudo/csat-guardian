# CSAT Guardian - Code Guide for Non-Developers

> **Audience:** This document explains how to read Python code for people who have never programmed before. Use this as a reference when reading the source files.

---

## Table of Contents

1. [How to Read Python Code](#1-how-to-read-python-code)
2. [Common Patterns in This Codebase](#2-common-patterns-in-this-codebase)
3. [Understanding api.py](#3-understanding-apipy)
4. [Understanding models.py](#4-understanding-modelspy)
5. [Understanding services](#5-understanding-services)
6. [Understanding the Agent](#6-understanding-the-agent)

---

## 1. How to Read Python Code

### Comments - Lines the Computer Ignores

```python
# This is a comment - it's for humans, not the computer
# Comments start with a # symbol
# The computer completely ignores these lines

"""
This is a multi-line comment (called a docstring).
It can span multiple lines.
It's used to document what a function or class does.
"""
```

### Variables - Storing Information

```python
# A variable is a name that stores a value
name = "John"           # Stores the text "John"
age = 30                # Stores the number 30
is_active = True        # Stores a yes/no value (True or False)

# Variables can change
age = 31                # Now age is 31
```

### Functions - Reusable Actions

```python
def greet_customer(name):
    """
    This function creates a greeting message.
    
    Args:
        name: The customer's name (text)
        
    Returns:
        A greeting string
    """
    return f"Hello, {name}!"

# Using the function:
message = greet_customer("Alice")  # message = "Hello, Alice!"
```

**Key vocabulary:**
- `def` = "define" - we're creating a function
- The part in parentheses are "arguments" - inputs to the function
- `return` = what the function gives back

### Classes - Blueprints for Things

```python
class Case:
    """
    A support case - this is like a template.
    
    Think of it like a form with blank fields.
    Each Case we create fills in those fields.
    """
    
    def __init__(self, id, title, description):
        """
        Initialize a new case.
        
        This runs when you create a new Case.
        'self' refers to the case being created.
        """
        self.id = id                  # Store the ID
        self.title = title            # Store the title
        self.description = description # Store the description
    
    def get_summary(self):
        """Get a short summary of the case."""
        return f"{self.id}: {self.title}"

# Creating a case (making a real thing from the blueprint):
my_case = Case(id="case-001", title="Cannot login", description="...")
print(my_case.get_summary())  # Outputs: "case-001: Cannot login"
```

### Lists and Dictionaries - Collections

```python
# A LIST is an ordered collection (like a shopping list)
cases = ["case-001", "case-002", "case-003"]
first_case = cases[0]  # Get first item: "case-001"

# A DICTIONARY is a collection with labels (like a phone book)
engineer = {
    "id": "eng-001",
    "name": "John Smith",
    "email": "jsmith@microsoft.com"
}
name = engineer["name"]  # Get the name: "John Smith"
```

### If/Else - Making Decisions

```python
sentiment_score = 0.3

if sentiment_score < 0.4:
    # This runs if the score is below 0.4
    label = "negative"
elif sentiment_score < 0.6:
    # This runs if the score is between 0.4 and 0.6
    label = "neutral"
else:
    # This runs if the score is 0.6 or higher
    label = "positive"
```

### For Loops - Doing Something Repeatedly

```python
cases = ["case-001", "case-002", "case-003"]

# Do something for each case in the list
for case_id in cases:
    print(f"Processing {case_id}")
    # ... do work here ...
```

### Async/Await - Waiting Without Blocking

```python
# Normal function - blocks everything while waiting
def get_data():
    result = slow_database_query()  # Everything stops while waiting
    return result

# Async function - can do other things while waiting
async def get_data_async():
    result = await slow_database_query()  # Can do other work while waiting
    return result
```

**Why async matters:** When waiting for a database or AI service, the app can handle other requests instead of just sitting idle.

---

## 2. Common Patterns in This Codebase

### The Pydantic BaseModel Pattern

Throughout the code, you'll see classes that inherit from `BaseModel`:

```python
from pydantic import BaseModel

class Engineer(BaseModel):
    """
    Represents a support engineer.
    
    The fields below are like a form that MUST be filled out.
    Pydantic will reject any Engineer that's missing required fields.
    """
    id: str                      # Required: unique identifier
    name: str                    # Required: display name
    email: str                   # Required: email address
    teams_id: Optional[str] = None  # Optional: may or may not have this
```

**What this gives us:**
- **Automatic validation**: Wrong data type? Error immediately
- **Documentation**: The types ARE the documentation
- **JSON conversion**: Can turn into JSON and back automatically

### The Enum Pattern

Enums are fixed lists of valid values:

```python
class CaseSeverity(str, Enum):
    """Only these four values are allowed."""
    SEV_A = "sev_a"  # Critical
    SEV_B = "sev_b"  # High
    SEV_C = "sev_c"  # Medium
    SEV_D = "sev_d"  # Low

# This is valid:
severity = CaseSeverity.SEV_A

# This would error:
severity = "urgent"  # ERROR: "urgent" isn't a valid CaseSeverity
```

### The FastAPI Endpoint Pattern

```python
@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """
    GET /api/cases/{case_id} - Retrieve a specific case
    
    The @app.get decorator tells FastAPI:
    - This is a GET request (for retrieving data)
    - The URL is /api/cases/something
    - The {case_id} part is a variable
    
    Args:
        case_id: Extracted from the URL automatically
        
    Returns:
        The case data as JSON
    """
    case = await dfm_client.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
```

### The Service Pattern

Services are classes that do specific jobs:

```python
class SentimentAnalysisService:
    """
    This service analyzes text to determine emotional tone.
    
    It's separate from the API so that:
    1. The logic can be tested independently
    2. The same logic can be used by API and CLI
    3. The implementation can change without changing the API
    """
    
    def __init__(self):
        """Set up the service when created."""
        self.openai_client = get_openai_client()
    
    async def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of the given text.
        
        Args:
            text: The customer communication to analyze
            
        Returns:
            SentimentResult with score, label, and key phrases
        """
        # 1. First, scrub any PII
        clean_text = scrub_pii(text)
        
        # 2. Send to OpenAI for analysis
        response = await self.openai_client.chat(...)
        
        # 3. Parse and return the result
        return SentimentResult(...)
```

---

## 3. Understanding api.py

The `api.py` file is the heart of the application. Here's how to read it:

### Section 1: Imports

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
```

These lines bring in code from other places. Think of it like:
- "I need the FastAPI toolkit for web servers"
- "I need Pydantic for data validation"

### Section 2: Request/Response Models

```python
class ChatRequest(BaseModel):
    """What the client sends when they want to chat."""
    message: str                    # The question they're asking
    case_id: Optional[str] = None   # Which case (if any)
    engineer_id: str                # Who is asking
```

These define "the shape of the data" for requests and responses.

### Section 3: Application State

```python
class AppState:
    """Global state for the application."""
    dfm_client = None           # Will hold the data client
    sentiment_service = None    # Will hold the AI service
    initialized: bool = False   # Have we started up?
```

This is like a "storage box" for things the whole app needs.

### Section 4: Lifecycle Events

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP - This runs when the app starts
    logger.info("Starting up...")
    app_state.dfm_client = create_dfm_client()
    app_state.initialized = True
    
    yield  # The app runs here
    
    # SHUTDOWN - This runs when the app stops
    logger.info("Shutting down...")
    await app_state.dfm_client.close()
```

### Section 5: Endpoints

Each endpoint is a "door" into the application:

```python
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    
    What it does:
    1. Checks if database is reachable
    2. Checks if AI service is available
    3. Returns status of everything
    
    Used by:
    - Load balancers (to know if app is alive)
    - Monitoring systems (to track service health)
    - Developers (to verify deployment worked)
    """
    return {
        "status": "healthy",
        "database": "connected",
        "ai_service": "available"
    }
```

---

## 4. Understanding models.py

The `models.py` file defines all the data structures. Think of it as "all the forms and templates."

### Core Entities

```python
class Engineer(BaseModel):
    """
    A support engineer - someone who handles cases.
    
    This is like an employee record card.
    """
    id: str         # e.g., "eng-001"
    name: str       # e.g., "John Smith"
    email: str      # e.g., "jsmith@microsoft.com"
    teams_id: Optional[str] = None  # For Teams notifications

class Customer(BaseModel):
    """
    A customer who opened a support case.
    
    We store minimal info - just enough to track the case.
    """
    id: str         # e.g., "cust-001"
    name: str       # e.g., "Contoso Corp"
    contact_email: str

class Case(BaseModel):
    """
    A support case - THE central entity in CSAT Guardian.
    
    This represents one customer issue being worked on.
    It has:
    - Basic info (ID, title, description)
    - Status and severity
    - Who owns it and who requested it
    - A timeline of all activities
    """
    id: str
    title: str
    description: str
    status: CaseStatus           # active, resolved, etc.
    severity: CaseSeverity       # sev_a through sev_d
    created_on: datetime
    modified_on: datetime
    owner: Engineer              # Who's working on it
    customer: Customer           # Who opened it
    timeline: List[TimelineEntry]  # Everything that happened
```

### Computed Properties

```python
class Case(BaseModel):
    # ... fields from above ...
    
    @property
    def days_since_last_note(self) -> float:
        """
        Calculate how many days since the last case note.
        
        This is a "computed property" - it calculates a value
        from other data rather than storing it directly.
        
        The 7-day rule requires notes at least every 7 days.
        """
        notes = [e for e in self.timeline if e.entry_type == "note"]
        if not notes:
            return self.days_since_creation
        latest = max(notes, key=lambda x: x.created_on)
        delta = datetime.utcnow() - latest.created_on
        return delta.total_seconds() / 86400  # Convert to days
```

---

## 5. Understanding Services

Services are "workers" that do specific jobs. The code is organized so that:
- Each service does ONE thing well
- Services can be tested independently
- Services can be swapped out (e.g., mock for testing)

### privacy.py - The PII Scrubber

```python
class PrivacyService:
    """
    Removes personally identifiable information from text.
    
    WHY THIS EXISTS:
    We cannot send customer emails, phone numbers, or SSNs to 
    Azure OpenAI. This service removes them before any AI processing.
    
    TWO LAYERS:
    1. Regex (fast pattern matching) - catches emails, phones, SSNs
    2. Content Safety (AI-powered) - catches names and addresses
    """
    
    def scrub_text(self, text: str) -> str:
        """
        Remove all PII from the given text.
        
        EXAMPLE:
        Input:  "Hi, I'm John Smith at john@contoso.com, call 555-1234"
        Output: "Hi, I'm [NAME] at [EMAIL], call [PHONE]"
        """
        # First pass: regex patterns (fast)
        text = self._regex_scrub(text)
        
        # Second pass: AI detection (if enabled)
        if self.use_content_safety:
            text = self._content_safety_scrub(text)
        
        return text
```

### sentiment_service.py - The AI Analyzer

```python
class SentimentAnalysisService:
    """
    Analyzes customer communications to detect sentiment.
    
    This is the "AI brain" for sentiment - it:
    1. Takes case description and timeline entries
    2. Scrubs PII for safety
    3. Sends to GPT-4o with a specific prompt
    4. Parses the response into a structured result
    """
    
    async def analyze_case(self, case: Case) -> SentimentResult:
        """
        Analyze sentiment for an entire case.
        
        Returns:
            SentimentResult containing:
            - score: 0.0 (very negative) to 1.0 (very positive)
            - label: "negative", "neutral", or "positive"
            - key_phrases: Words indicating sentiment
            - concerns: Specific issues detected
        """
        # Build the text to analyze
        text = self._build_analysis_text(case)
        
        # Scrub PII before sending to AI
        clean_text = self.privacy_service.scrub_text(text)
        
        # Send to Azure OpenAI
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                {"role": "user", "content": clean_text}
            ]
        )
        
        # Parse the response
        return self._parse_response(response)
```

### alert_service.py - The Notification Generator

```python
class AlertService:
    """
    Generates alerts when cases need attention.
    
    Alert types:
    - SENTIMENT_ALERT: Customer frustration detected
    - COMMUNICATION_GAP: Too long since customer contact
    - SEVEN_DAY_WARNING: Case notes approaching deadline
    - SEVEN_DAY_BREACH: Case notes past deadline
    """
    
    def check_case(self, case: Case) -> List[Alert]:
        """
        Check a case and generate any needed alerts.
        
        This runs periodically to catch at-risk cases.
        """
        alerts = []
        
        # Check 7-day notes rule
        if case.days_since_last_note >= 7:
            alerts.append(Alert(
                type=AlertType.SEVEN_DAY_BREACH,
                message=f"Case {case.id} has not had notes in 7+ days",
                urgency=AlertUrgency.HIGH
            ))
        elif case.days_since_last_note >= 5:
            alerts.append(Alert(
                type=AlertType.SEVEN_DAY_WARNING,
                message=f"Case {case.id} notes due in {7 - case.days_since_last_note:.1f} days",
                urgency=AlertUrgency.MEDIUM
            ))
        
        # ... more rule checks ...
        
        return alerts
```

---

## 6. Understanding the Agent

The "agent" is the conversational AI - it understands natural language and can answer questions about cases.

### guardian_agent.py - The Conversation Handler

```python
class CSATGuardianAgent:
    """
    The AI agent that engineers chat with.
    
    BUILT ON: Microsoft Semantic Kernel
    
    How it works:
    1. Engineer asks a question in plain English
    2. Agent uses GPT-4o to understand the question
    3. Agent calls "plugins" to get data (cases, sentiment, rules)
    4. Agent generates a helpful response
    """
    
    async def chat(self, message: str, case_id: Optional[str] = None) -> str:
        """
        Process a chat message from an engineer.
        
        EXAMPLE CONVERSATION:
        
        Engineer: "How are my cases doing?"
        Agent: "You have 4 active cases. Case-002 needs attention - 
               no notes in 6 days. Case-001 is showing negative sentiment."
        
        Engineer: "What's wrong with case-002?"
        Agent: "Case-002 (Production SQL down) is Severity A. The customer
               has expressed frustration about response time. Last contact
               was 2 days ago. Recommendation: Send an update today."
        """
        # Add context to the prompt
        if case_id:
            context = await self._get_case_context(case_id)
        
        # Run the agent
        result = await self.kernel.invoke(
            self.chat_function,
            input=message,
            context=context
        )
        
        return str(result)
```

### csat_rules_plugin.py - The Rules Checker

```python
class CSATRulesPlugin:
    """
    Plugin that the agent can call to check CSAT rules.
    
    The agent doesn't have these rules built-in. Instead,
    it can CALL these functions when it needs to check rules.
    
    This separation means:
    - Rules can be updated without retraining AI
    - Rules are explicit and auditable
    - Same rules used by agent and monitoring
    """
    
    @kernel_function(
        name="check_seven_day_rule",
        description="Check if a case is compliant with the 7-day notes rule"
    )
    async def check_seven_day_rule(self, case_id: str) -> str:
        """
        Check if case notes are up to date.
        
        The @kernel_function decorator tells Semantic Kernel:
        - This function can be called by the AI
        - The 'name' is what the AI sees
        - The 'description' helps AI know when to use it
        """
        case = await self.dfm_client.get_case(case_id)
        days = case.days_since_last_note
        
        if days >= 7:
            return f"❌ BREACH: No notes for {days:.1f} days. Add notes immediately."
        elif days >= 5:
            return f"⚠️ WARNING: Notes due in {7-days:.1f} days."
        else:
            return f"✅ COMPLIANT: Notes updated {days:.1f} days ago."
```

---

## Summary: Reading Code Files

When you open a source file, look for:

1. **File header comment** - explains what the file does
2. **Imports** - what external code is used
3. **Class definitions** - the "things" in the file
4. **Method definitions** - the "actions" those things can do
5. **Docstrings** - the explanations inside `"""triple quotes"""`

The most important files to understand:

| File | What It Is | Start Here If... |
|------|------------|------------------|
| `api.py` | The web server | You want to see all endpoints |
| `models.py` | Data structures | You want to understand the data |
| `guardian_agent.py` | The AI | You want to see how chat works |
| `privacy.py` | PII scrubbing | You care about security |

---

*Last Updated: January 28, 2026*
