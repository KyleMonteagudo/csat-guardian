# CSAT Guardian

> **Customer Satisfaction Guardian** - AI-Powered CSAT Risk Detection and Proactive Coaching for Support Engineers

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Try%20It%20Now-blue?style=for-the-badge)](https://app-csatguardian-dev.azurewebsites.net/ui)
[![CXP ACES AI Bash](https://img.shields.io/badge/Hackathon-CXP%20ACES%20AI%20Bash-purple?style=for-the-badge)](https://innovationstudio.microsoft.com/hackathons/CXP-ACES-AI-Bash/project/115573)

---

## 🎯 What is CSAT Guardian?

CSAT Guardian is an AI-powered assistant that helps support engineers maintain high customer satisfaction (CSAT) scores by:

- **🔍 Monitoring** open cases for early warning signs
- **🎭 Detecting** customer sentiment using Azure OpenAI
- **⚠️ Alerting** when cases approach risk thresholds (2-day, 7-day rules)
- **💬 Coaching** with personalized, actionable recommendations

### The Problem We're Solving

Support engineers often don't know a customer is frustrated until they receive a poor CSAT score—**after** the survey is sent. By then, it's too late to course-correct.

### Our Solution

> **"Shift from reactive CSAT recovery to proactive customer experience management."**

CSAT Guardian analyzes case timelines in real-time to detect declining sentiment and compliance risks **before** they become problems, empowering engineers to take action while they can still make a difference.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **📊 Engineer Dashboard** | See all your cases with AI-analyzed sentiment scores, risk indicators, and timeline insights |
| **👥 Manager Dashboard** | Team overview with drill-down into individual engineer performance and coaching opportunities |
| **🤖 AI Chat Assistant** | Ask case-specific questions and get personalized coaching recommendations |
| **📈 Sentiment Analysis** | Azure OpenAI-powered analysis of case communications |
| **📋 Case Timeline View** | Full history with detected phrases, sentiment trends, and risk factors |
| **💡 Personalized Coaching** | Context-aware suggestions based on actual case patterns |
| **📤 Export Capabilities** | CSV, PDF, and JSON export for reporting and integration |
| **🔒 Feedback System** | Built-in feedback collection for continuous improvement |

---

## 🎨 User Interface

The app features a modern **glassmorphism design** with:
- Mobile-responsive layout
- Animated sentiment rings and counters
- Category drill-down (Excellent/Good/Growth Opportunity)
- Smooth page transitions and micro-interactions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure Commercial Cloud                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  Virtual Network (VNet)                  │   │
│   │                                                          │   │
│   │   ┌──────────────────────────────────────────────────┐  │   │
│   │   │              App Service (Python 3.11)            │  │   │
│   │   │      FastAPI + Semantic Kernel + Static UI        │  │   │
│   │   └─────────────────────┬────────────────────────────┘  │   │
│   │                         │                                │   │
│   │   ┌─────────┬──────────┴──────────┬─────────────────┐   │   │
│   │   ▼         ▼                     ▼                 ▼   │   │
│   │ Azure   Azure SQL           Azure OpenAI      AI Content│   │
│   │ Key     Database            (GPT-4o)          Safety    │   │
│   │ Vault   (Private EP)        (AI Services)    (PII Det.) │   │
│   │                                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   🔐 All services use Managed Identity (no API keys/passwords)  │
│   🔒 Private Endpoints for all backend services                  │
│   🛡️ Local authentication DISABLED on all Azure services        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | HTML/CSS/JavaScript (no build step) |
| **Backend** | FastAPI (Python 3.11) |
| **AI** | Azure OpenAI GPT-4o, Semantic Kernel Agents |
| **Database** | Azure SQL with Managed Identity |
| **Security** | MSI Auth, Private Endpoints, No secrets in code |
| **Hosting** | Azure App Service with VNet Integration |

---

## 📚 Documentation

| Document | Audience | Description |
|----------|----------|-------------|
| [**Getting Started**](docs/GETTING_STARTED.md) | Everyone | Quick start guide |
| [Architecture](docs/ARCHITECTURE.md) | Developers | Technical deep-dive |
| [File Reference](docs/FILE_REFERENCE.md) | Developers | Complete code walkthrough |
| [Code Guide for Non-Developers](docs/CODE_GUIDE_FOR_NON_DEVELOPERS.md) | Non-programmers | How to read the code |
| [Quick Reference](docs/QUICK_REFERENCE.md) | Developers | API cheat sheet |
| [Deployment Guide](infrastructure/DEPLOYMENT_GUIDE.md) | DevOps | How to deploy |
| [Security Review](docs/APPLICATION_SECURITY_REVIEW.md) | Security | Security controls |
| [CSAT Requirements](docs/CSAT_REQUIREMENTS.md) | Product | Business rules |

---

## 🚀 Try It Now

**Live Demo:** [https://app-csatguardian-dev.azurewebsites.net/ui](https://app-csatguardian-dev.azurewebsites.net/ui)

### Quick Tour:
1. **Engineer Mode** - View case dashboard, analyze sentiment, chat with AI
2. **Manager Mode** - See team overview, drill into engineer performance
3. **Feedback Button** - Share your thoughts (top right corner)

---

## 📁 Project Structure

```
csat-guardian/
├── src/
│   ├── api.py                    # FastAPI REST endpoints
│   ├── config.py                 # Configuration management
│   ├── db_sync.py                # Azure SQL database client
│   ├── models.py                 # Data models
│   ├── static/                   # Frontend UI
│   │   ├── index.html            # Single-page app
│   │   ├── css/styles.css        # Styling
│   │   └── js/app.js             # Frontend logic
│   ├── agent/
│   │   ├── guardian_agent.py     # Semantic Kernel agent
│   │   └── csat_rules_plugin.py  # CSAT rules plugin
│   ├── services/
│   │   ├── sentiment_service.py  # Azure OpenAI integration
│   │   └── alert_service.py      # Alert generation
│   └── clients/
│       ├── azure_sql_adapter.py  # Azure SQL adapter
│       └── dfm_client_memory.py  # In-memory data client
├── infrastructure/
│   ├── bicep/                    # Infrastructure as Code
│   └── sql/                      # Database schemas
├── docs/                         # Documentation
└── README.md
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health status |
| `/api/cases` | GET | List cases with filters |
| `/api/cases/{id}` | GET | Get case with full timeline |
| `/api/analyze/{id}` | POST | AI sentiment analysis |
| `/api/chat` | POST | Chat with CSAT Guardian agent |
| `/api/feedback` | POST | Submit user feedback |

---

## 🧪 Test Scenarios

The demo includes 8 pre-configured test cases:

| Case | Scenario | Risk Level |
|------|----------|------------|
| case-001 | Happy, engaged customer | Healthy |
| case-002 | Frustrated customer | At Risk |
| case-003 | Neutral progress | Healthy |
| case-004 | Declining sentiment | At Risk |
| case-005 | 7-day warning approaching | At Risk |
| case-006 | 7-day compliance breach | Breach |
| case-007 | Technical complexity | Healthy |
| case-008 | Escalation scenario | At Risk |

---

## 🔮 Future Roadmap

- [ ] **DfM/Kusto Integration** - Connect to real case data
- [ ] **Teams Notifications** - Proactive alerts via Teams
- [ ] **CI/CD Pipeline** - Automated deployments
- [ ] **Real-time Updates** - WebSocket live refresh

---

## 🤝 Contributing

We welcome feedback and contributions! 

- **Try the app:** [Live Demo](https://app-csatguardian-dev.azurewebsites.net/ui)
- **Submit feedback:** Use the Feedback button in the app
- **Join the project:** [Innovation Studio](https://innovationstudio.microsoft.com/hackathons/CXP-ACES-AI-Bash/project/115573)

---

## 👨‍💻 Author

**Kyle Monteagudo**  
Government Support Engineer | GSX

*Built for the CXP ACES AI Bash Hackathon 2026*

---

## 📜 License

Internal Microsoft Use Only
