# CSAT Guardian

> **Customer Satisfaction Guardian** - Proactive CSAT Risk Detection and Intervention

## Overview

CSAT Guardian is an AI-powered system that monitors support cases to proactively identify at-risk customer satisfaction situations before they escalate.

> **⚠️ Azure Government Cloud**
> 
> This application is deployed in **Azure Government** (not Azure Commercial).  
> All Azure endpoints use `.us` domains. See [Azure Government docs](docs/AZURE_GOVERNMENT.md).

### Key Features

- **🔍 Sentiment Analysis**: AI-powered detection of frustrated or unhappy customer communications
- **⏰ Compliance Monitoring**: Tracks 7-day case note requirements and alerts before breaches
- **📊 Trend Detection**: Identifies declining sentiment patterns across case timelines
- **🚨 Proactive Alerts**: Sends timely alerts to engineers and managers via Teams
- **💬 Conversational AI**: Engineers can ask questions about their cases

## Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| **Azure Government** | All components run in Azure Gov cloud |
| **No Secrets in Code** | Azure Key Vault for all credentials |
| **API-Based Access** | Even sample data accessed via API patterns |
| **Infrastructure as Code** | Bicep templates for all Azure resources |
| **CI/CD Automation** | GitHub Actions with Gov environment |
| **FedRAMP Compliant** | Azure Government meets federal requirements |

## Quick Links

| Document | Description |
|----------|-------------|
| [Project Plan](docs/PROJECT_PLAN.md) | SDLC methodology, branching strategy |
| [Architecture](docs/ARCHITECTURE.md) | System design, data flows |
| [File Reference](docs/FILE_REFERENCE.md) | Cheat sheet for all files |
| [Azure Government](docs/AZURE_GOVERNMENT.md) | Gov-specific endpoints and configuration |
| [Security Review](docs/APPLICATION_SECURITY_REVIEW.md) | API approval documentation |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              CSAT Guardian System (Azure Government)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐     │
│   │   DfM API   │────▶│   Monitor   │────▶│  Alert Service  │     │
│   │   (or Mock) │     │   Service   │     │                 │     │
│   └─────────────┘     └──────┬──────┘     └────────┬────────┘     │
│                              │                     │               │
│                              ▼                     ▼               │
│                       ┌─────────────┐     ┌─────────────────┐     │
│                       │  Sentiment  │     │   Teams Bot     │     │
│                       │  Analysis   │     │   (graph.us)    │     │
│                       │ (azure.us)  │     └─────────────────┘     │
│                       └─────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## POC Mode

This POC runs with:
- ✅ **Real Azure OpenAI** - For sentiment analysis (`.openai.azure.us`)
- 🔄 **Mock DfM Client** - Returns sample data from Azure SQL Database
- 🔄 **Mock Teams Client** - Prints alerts to console (can send to real Teams)
- 📊 **Sample Data** - 6 test cases covering different scenarios in Azure SQL

## Getting Started

### Prerequisites

- Python 3.11+
- Azure OpenAI access (Azure Government)
- Git
- Azure CLI configured for Government: `az cloud set --name AzureUSGovernment`

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd csat-guardian
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure OpenAI credentials
   ```

5. **Initialize and run**:
   ```bash
   cd src
   python main.py setup  # Create sample data
   python main.py scan   # Run monitoring scan
   ```

## Usage

### Commands

```bash
# Initialize database with sample data
python main.py setup

# Run a single monitoring scan
python main.py scan

# Start continuous monitoring (every 60 minutes)
python main.py monitor

# Start continuous monitoring (custom interval)
python main.py monitor --interval 30

# Start interactive chat
python main.py chat

# Chat as a specific engineer
python main.py chat --engineer eng-002
```

### Interactive Chat Examples

```
[John Smith] You: list my cases
[CSAT Guardian] 📂 Your Cases (3 total)

[John Smith] You: tell me about case 12345
[CSAT Guardian] 📋 Case Summary: 12345...

[John Smith] You: analyze case 12345
[CSAT Guardian] 🎭 Sentiment Analysis...

[John Smith] You: recommendations for case 12345
[CSAT Guardian] 💡 Recommendations...
```

## Project Structure

```
csat-guardian/
├── .env.example           # Environment configuration template
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── data/                  # SQLite database (created at runtime)
│   └── csat_guardian.db
└── src/
    ├── main.py            # Application entry point
    ├── config.py          # Configuration management
    ├── logger.py          # Logging setup
    ├── models.py          # Pydantic data models
    ├── database.py        # SQLAlchemy ORM
    ├── sample_data.py     # POC test data
    ├── monitor.py         # Case monitoring orchestrator
    ├── agent/
    │   └── guardian_agent.py  # Conversational AI agent
    ├── clients/
    │   ├── dfm_client.py      # DfM data client (mock/real)
    │   └── teams_client.py    # Teams notification client (mock/real)
    └── services/
        ├── sentiment_service.py  # Azure OpenAI sentiment analysis
        └── alert_service.py      # Alert generation and delivery
```

## Sample Data Scenarios

The POC includes 6 test cases:

| Case ID | Scenario | Expected Behavior |
|---------|----------|-------------------|
| case-001 | Happy Customer | No alerts |
| case-002 | Frustrated Customer | Negative sentiment alert |
| case-003 | Neutral Customer | No alerts |
| case-004 | At-Risk (Declining) | Trend alert |
| case-005 | 7-Day Warning | Compliance warning alert |
| case-006 | 7-Day Breach | Compliance breach alert |

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (default: gpt-4o) | No |
| `USE_MOCK_DFM` | Use mock DfM client (default: true) | No |
| `USE_MOCK_TEAMS` | Use mock Teams client (default: true) | No |
| `LOG_LEVEL` | Logging level (default: INFO) | No |

### Alert Thresholds

```python
negative_sentiment_threshold = 0.3    # Alert if score < 0.3
trend_change_threshold = -0.2         # Alert if trend drops by 0.2
days_until_warning = 5.0              # Warn 5 days after last note
days_until_breach = 7.0               # Breach at 7 days
```

## Swapping Mock for Real Services

When DfM and Teams APIs are approved:

1. **Set environment flags**:
   ```
   USE_MOCK_DFM=false
   USE_MOCK_TEAMS=false
   ```

2. **Configure real API credentials**:
   ```
   DFM_API_BASE_URL=https://...
   TEAMS_BOT_ID=...
   ```

3. **Implement real clients** in:
   - `src/clients/dfm_client.py` → `RealDfMClient`
   - `src/clients/teams_client.py` → `RealTeamsClient`

## Security Notes

- All case access is scoped to the authenticated engineer
- No customer data is stored permanently (only analysis results)
- Azure OpenAI calls use managed identity (production)
- Teams bot requires proper AAD registration

## License

Internal Microsoft Use Only

## Support

Contact: CSS Escalations Team
