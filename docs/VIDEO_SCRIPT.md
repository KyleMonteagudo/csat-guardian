# CSAT Guardian - 2 Minute Video Script

## Hackathon Submission Video
**Target Duration:** 2:00 minutes  
**Speaker:** Kyle Monteagudo  
**Last Updated:** February 3, 2026

---

## DEMO ENVIRONMENT

- **URL:** `https://app-csatguardian-dev.azurewebsites.net/ui`
- **Frontend:** Microsoft Learn-style static HTML/CSS/JS
- **Backend:** FastAPI + Semantic Kernel + Azure OpenAI GPT-4o

---

## SCRIPT

### Opening (0:00 - 0:15)
*[Open browser to /ui - show landing page with CSAT Guardian branding]*

> "Hi, I'm Kyle Monteagudo, and this is **CSAT Guardian** - an AI-powered solution that transforms reactive customer support into proactive customer success.
>
> The problem is simple: support teams only find out about unhappy customers AFTER they receive bad CSAT scores - when it's too late to fix it."

---

### The Solution (0:15 - 0:30)
*[Stay on landing page, highlight the three feature cards]*

> "CSAT Guardian solves this by analyzing customer communications in **real-time** using Azure OpenAI. We detect frustration as it happens, not after it's too late.
>
> Let me show you how it works for both support engineers and their managers."

---

### Engineer Mode Demo (0:30 - 1:05)
*[Click Engineer Mode button]*

> "First, let's look at the **Engineer Dashboard**."

*[Dashboard loads - point to alert banner and metrics cards]*

> "Immediately, I can see my case metrics - total cases, at-risk cases, and my average CSAT score. The dashboard shows all my active cases with their sentiment status - critical in red, at-risk in yellow, or positive in green."

*[Point to the sentiment indicators on case cards]*

> "For each case, our AI provides a real-time analysis. Here, we've detected that this customer is frustrated due to extended downtime."

*[Click Analyze button on a case]*

> "Clicking Analyze runs GPT-4o sentiment analysis in real-time. You can see the sentiment score, risk factors, and - most importantly - specific recommended actions to turn this situation around."

---

### Manager Mode Demo (1:05 - 1:40)
*[Click Back to Home, then Manager Mode]*

> "Now let's see the **Manager View**."

*[Dashboard loads with team overview]*

> "As a manager, I get a bird's eye view of my entire team's CSAT health. I can see team-wide metrics, and which engineers need support."

*[Point to engineer cards]*

> "Each engineer is shown with their case load and average CSAT. I can quickly identify who might need coaching or workload balancing."

*[Point to critical cases section]*

> "At the bottom, I see every critical case across my team, so I can prioritize where to intervene first."

---

### Tech & Close (1:40 - 2:00)
*[Show landing page or chat with AI feature]*

> "Under the hood, CSAT Guardian uses **Semantic Kernel** with **Azure OpenAI's GPT-4o** for sentiment analysis, and **Azure AI Content Safety** for enterprise-grade PII protection - ensuring customer data never reaches the AI unprotected.
>
> CSAT Guardian: Stop reacting to bad scores. Start preventing them.
>
> Thank you."

---

## TIMING BREAKDOWN

| Section | Duration | Cumulative |
|---------|----------|------------|
| Opening | 15 sec | 0:15 |
| Solution | 15 sec | 0:30 |
| Engineer Demo | 35 sec | 1:05 |
| Manager Demo | 35 sec | 1:40 |
| Tech & Close | 20 sec | 2:00 |

---

## DEMO CLICK PATH

1. **Start:** Landing page
2. **Click:** Engineer Mode
3. **Show:** Dashboard (pause on metrics + alert)
4. **Show:** At-risk cases with AI analysis
5. **Click:** View Details on critical case
6. **Show:** Case detail page (AI analysis, recommendations)
7. **Click:** Back to Dashboard
8. **Click:** Back to Home
9. **Click:** Manager Mode
10. **Show:** Team metrics + engineer cards
11. **Show:** Critical cases section
12. **End:** Back to landing page or banner

---

## KEY PHRASES TO EMPHASIZE

- "Real-time sentiment analysis"
- "Detect frustration as it happens"
- "AI-powered recommendations"
- "Enterprise-grade PII protection"
- "Stop reacting. Start preventing."

---

## RECORDING TIPS

1. **Practice the click path** 3-4 times before recording
2. **Speak slightly slower** than normal - 2 minutes goes fast
3. **Pause briefly** when transitioning between screens
4. **Keep mouse movements smooth** and deliberate
5. **Have the script visible** on a second monitor or phone
6. **Record in 1080p** or higher
7. **Use a good microphone** - audio quality matters

---

## BACKUP TALKING POINTS

If you have extra time or need to fill:

- "This was built in two weeks as a hackathon project"
- "The sample data you're seeing demonstrates various sentiment levels"
- "In production, this would integrate with your ticketing system"
- "Managers can drill down into any engineer's caseload"
- "The AI analysis updates in real-time as new customer messages arrive"
