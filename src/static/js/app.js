/**
 * CSAT Guardian - Frontend Application
 * Microsoft Learn-inspired UI for CSAT case management
 */

// =============================================================================
// Configuration
// =============================================================================

const CONFIG = {
    // API Base URL - will be same origin when deployed
    API_BASE: window.location.origin,
    // Default engineer for demo
    DEFAULT_ENGINEER_ID: 'eng-001',
};

// =============================================================================
// State Management
// =============================================================================

const state = {
    currentView: 'landing',  // landing, engineer, manager, case-detail, engineer-detail
    currentEngineer: null,
    currentCase: null,
    selectedEngineer: null,  // For manager viewing an engineer's details
    cases: [],
    engineers: [],
    isLoading: false,
    backendStatus: 'checking',  // checking, online, offline
    chatHistory: [],
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Format severity from "sev_a", "sev_b" etc to just "A", "B", "C", "D"
 */
function formatSeverity(severity) {
    if (!severity) return 'C';
    const sev = severity.toLowerCase().replace('sev_', '').replace('sev', '').toUpperCase();
    return sev || 'C';
}

/**
 * Get severity badge class based on level
 */
function getSeverityBadgeClass(severity) {
    const sev = formatSeverity(severity);
    switch (sev) {
        case 'A': return 'badge-danger';
        case 'B': return 'badge-warning';
        case 'C': return 'badge-info';
        default: return 'badge-info';
    }
}

/**
 * Analyze negative indicators from a set of cases
 * Returns top 3 factors contributing to negative sentiment
 */
function analyzeNegativeIndicators(cases) {
    const indicators = {
        'Slow Response Time': 0,
        'Long Time Since Last Note': 0,
        'High Severity Case Delays': 0,
        'Customer Frustration Signals': 0,
        'Extended Case Duration': 0,
        'Declining Sentiment Trend': 0,
    };
    
    cases.forEach(c => {
        const sentiment = c.sentiment_score || 0.5;
        const daysComm = c.days_since_last_outbound || 0;
        const daysNote = c.days_since_last_note || 0;
        const daysOpen = c.days_open || c.days_since_creation || 0;
        const sev = formatSeverity(c.severity);
        
        // Only analyze cases with issues
        if (sentiment < 0.55) {
            if (daysComm > 2) indicators['Slow Response Time'] += (daysComm - 2);
            if (daysNote > 5) indicators['Long Time Since Last Note'] += (daysNote - 5);
            if ((sev === 'A' || sev === 'B') && daysOpen > 5) indicators['High Severity Case Delays'] += 1;
            if (sentiment < 0.35) indicators['Customer Frustration Signals'] += 1;
            if (daysOpen > 14) indicators['Extended Case Duration'] += 1;
            if (c.sentiment_trend === 'declining') indicators['Declining Sentiment Trend'] += 1;
        }
    });
    
    // Sort and return top 3
    return Object.entries(indicators)
        .filter(([_, v]) => v > 0)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([indicator, _]) => indicator);
}

/**
 * Generate coaching advice based on negative indicators
 */
function generateCoachingAdvice(indicators, avgSentiment) {
    const advice = [];
    
    indicators.forEach(indicator => {
        switch (indicator) {
            case 'Slow Response Time':
                advice.push({
                    issue: indicator,
                    suggestion: 'Consider setting daily check-in reminders to ensure customers hear from you within 24-48 hours',
                    icon: '⏰'
                });
                break;
            case 'Long Time Since Last Note':
                advice.push({
                    issue: indicator,
                    suggestion: 'Keep case notes current - even brief updates help with handoffs and compliance (7-day rule)',
                    icon: '📝'
                });
                break;
            case 'High Severity Case Delays':
                advice.push({
                    issue: indicator,
                    suggestion: 'Prioritize Sev A/B cases - consider blocking time each morning specifically for critical cases',
                    icon: '🎯'
                });
                break;
            case 'Customer Frustration Signals':
                advice.push({
                    issue: indicator,
                    suggestion: 'When customers show frustration, acknowledge their concerns directly and provide clear next steps with timelines',
                    icon: '🤝'
                });
                break;
            case 'Extended Case Duration':
                advice.push({
                    issue: indicator,
                    suggestion: 'For long-running cases, consider a case review or escalation to ensure forward progress',
                    icon: '📊'
                });
                break;
            case 'Declining Sentiment Trend':
                advice.push({
                    issue: indicator,
                    suggestion: 'Schedule proactive check-ins with customers showing declining satisfaction before issues escalate',
                    icon: '📉'
                });
                break;
        }
    });
    
    // Add general advice based on overall sentiment
    if (avgSentiment < 0.4 && advice.length < 3) {
        advice.push({
            issue: 'Overall CSAT Health',
            suggestion: 'Consider scheduling 1:1 time to review challenging cases and identify patterns',
            icon: '💡'
        });
    }
    
    return advice;
}

/**
 * Render personal analytics section for engineer dashboard
 */
function renderPersonalAnalytics(avgSentiment, indicators, cases) {
    const container = document.getElementById('analytics-section');
    const sentimentClass = getSentimentClass(avgSentiment);
    const coachingAdvice = generateCoachingAdvice(indicators, avgSentiment);
    
    container.innerHTML = `
        <h3>📊 My CSAT Performance (Last 30 Days)</h3>
        
        <div class="analytics-grid mt-lg">
            <!-- Sentiment Score -->
            <div class="analytics-score-card">
                <div class="score-circle ${sentimentClass}">
                    <span class="score-value">${Math.round(avgSentiment * 100)}%</span>
                </div>
                <div class="score-label">Average Sentiment</div>
                <div class="score-trend text-muted">Across ${cases.length} active cases</div>
            </div>
            
            <!-- Top Indicators -->
            <div class="analytics-indicators">
                <h4>🎯 Top Areas for Improvement</h4>
                ${indicators.length > 0 ? `
                    <div class="indicators-list mt-md">
                        ${indicators.map((ind, i) => `
                            <div class="indicator-item">
                                <span class="indicator-rank">${i + 1}</span>
                                <span class="indicator-text">${ind}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <p class="text-muted mt-md">✅ No significant improvement areas identified - keep up the great work!</p>
                `}
            </div>
        </div>
        
        ${coachingAdvice.length > 0 ? `
            <div class="coaching-section mt-lg">
                <h4>💡 Personalized Coaching Tips</h4>
                <div class="coaching-cards mt-md">
                    ${coachingAdvice.map(a => `
                        <div class="coaching-card">
                            <div class="coaching-icon">${a.icon}</div>
                            <div class="coaching-content">
                                <div class="coaching-issue">${a.issue}</div>
                                <div class="coaching-suggestion">${a.suggestion}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    `;
}

// =============================================================================
// API Functions
// =============================================================================

async function apiGet(endpoint) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API GET ${endpoint} failed:`, error);
        return null;
    }
}

async function apiPost(endpoint, data) {
    try {
        // Add timeout for chat requests (30 seconds)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`API POST ${endpoint} error: ${response.status} - ${errorText}`);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error(`API POST ${endpoint} timed out`);
            return { error: 'timeout', message: 'Request timed out. The AI service may be unavailable or slow. Please try again.' };
        }
        console.error(`API POST ${endpoint} failed:`, error);
        return { error: 'failed', message: error.message };
    }
}

async function checkHealth() {
    updateStatus('checking');
    const health = await apiGet('/api/health');
    if (health) {
        updateStatus('online');
        return health;
    }
    updateStatus('offline');
    return null;
}

async function getCases(engineerId = null) {
    const endpoint = engineerId ? `/api/cases?engineer_id=${engineerId}` : '/api/cases';
    return await apiGet(endpoint);
}

async function getCase(caseId) {
    return await apiGet(`/api/cases/${caseId}`);
}

async function getEngineers() {
    return await apiGet('/api/engineers');
}

async function analyzeCase(caseId) {
    return await apiPost(`/api/analyze/${caseId}`, { include_recommendations: true });
}

async function chatWithAgent(message, caseId = null) {
    return await apiPost('/api/chat', {
        message,
        case_id: caseId,
        engineer_id: CONFIG.DEFAULT_ENGINEER_ID,
    });
}

// =============================================================================
// UI Updates
// =============================================================================

function updateStatus(status) {
    state.backendStatus = status;
    const statusEl = document.getElementById('backend-status');
    if (statusEl) {
        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');
        dot.className = `status-dot ${status}`;
        text.textContent = status === 'online' ? 'Connected' : status === 'offline' ? 'Offline' : 'Checking...';
    }
}

function showLoading(show = true) {
    state.isLoading = show;
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.classList.toggle('hidden', !show);
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDateShort(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getSentimentClass(score) {
    if (score >= 0.7) return 'positive';
    if (score >= 0.4) return 'neutral';
    return 'negative';
}

function getSentimentBadgeClass(score) {
    if (score >= 0.7) return 'badge-success';
    if (score >= 0.4) return 'badge-warning';
    return 'badge-danger';
}

// =============================================================================
// View Rendering Functions
// =============================================================================

function renderLandingPage() {
    state.currentView = 'landing';
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="hero">
            <h1>🛡️ CSAT Guardian</h1>
            <p class="subtitle">AI-Powered Customer Satisfaction Monitoring & Proactive Coaching for Support Engineers</p>
            
            <div class="hero-buttons">
                <div class="card mode-card card-clickable" onclick="navigateTo('engineer')">
                    <div class="mode-icon">👨‍💻</div>
                    <div class="mode-title">Engineer Mode</div>
                    <p class="mode-description">View your cases, get AI analysis and coaching recommendations</p>
                </div>
                
                <div class="card mode-card card-clickable" onclick="navigateTo('manager')">
                    <div class="mode-icon">👥</div>
                    <div class="mode-title">Manager Mode</div>
                    <p class="mode-description">Team overview, CSAT health metrics, and intervention alerts</p>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-lg">
            <h3>Powered by Azure AI</h3>
            <p class="text-muted">Azure OpenAI • Azure SQL • Semantic Kernel • FastAPI</p>
        </div>
    `;
    updateBreadcrumb([]);
}

async function renderEngineerDashboard() {
    state.currentView = 'engineer';
    showLoading(true);
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="content-header">
            <h1>My Dashboard</h1>
            <p class="subtitle">Your CSAT performance insights and case management</p>
        </div>
        <div id="alerts-container"></div>
        
        <!-- Personal Analytics Section -->
        <div id="analytics-section" class="card mb-lg">
            <div class="loading"><div class="spinner"></div></div>
            <p class="text-center text-muted">Loading your performance analytics...</p>
        </div>
        
        <div id="metrics-container" class="metrics-row"></div>
        
        <!-- My Cases Section -->
        <h3 class="mt-lg mb-md">📋 My Cases</h3>
        <div id="cases-container">
            <div class="loading"><div class="spinner"></div></div>
        </div>
    `;
    updateBreadcrumb([{ text: 'Engineer Dashboard' }]);
    
    // Fetch cases
    const casesData = await getCases(CONFIG.DEFAULT_ENGINEER_ID);
    showLoading(false);
    
    if (!casesData) {
        document.getElementById('cases-container').innerHTML = `
            <div class="card">
                <p class="text-muted text-center">Unable to load cases. Please check your connection.</p>
            </div>
        `;
        return;
    }
    
    state.cases = casesData.cases || casesData || [];
    
    // Calculate CSAT risk metrics (focus on sentiment, not just days)
    const critical = state.cases.filter(c => (c.sentiment_score || 0.5) < 0.35).length;
    const atRisk = state.cases.filter(c => {
        const score = c.sentiment_score || 0.5;
        return score >= 0.35 && score < 0.55;
    }).length;
    const healthy = state.cases.length - critical - atRisk;
    
    // Calculate average sentiment
    const avgSentiment = state.cases.length > 0 
        ? state.cases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / state.cases.length 
        : 0.5;
    
    // Find top negative indicators
    const negativeIndicators = analyzeNegativeIndicators(state.cases);
    
    // Render personal analytics
    renderPersonalAnalytics(avgSentiment, negativeIndicators, state.cases);
    
    // Render alerts - focus on CSAT risk, not SLA
    if (critical > 0) {
        document.getElementById('alerts-container').innerHTML = `
            <div class="alert-banner danger">
                🚨 <strong>CSAT Alert:</strong> ${critical} case${critical > 1 ? 's' : ''} with critical customer satisfaction risk - immediate attention needed
            </div>
        `;
    } else if (atRisk > 0) {
        document.getElementById('alerts-container').innerHTML = `
            <div class="alert-banner warning">
                ⚠️ <strong>CSAT Warning:</strong> ${atRisk} case${atRisk > 1 ? 's' : ''} showing signs of declining customer satisfaction
            </div>
        `;
    }
    
    // Render metrics - CSAT focused
    document.getElementById('metrics-container').innerHTML = `
        <div class="metric-card">
            <div class="metric-value">${state.cases.length}</div>
            <div class="metric-label">Total Cases</div>
        </div>
        <div class="metric-card">
            <div class="metric-value danger">${critical}</div>
            <div class="metric-label">Critical CSAT</div>
        </div>
        <div class="metric-card">
            <div class="metric-value warning">${atRisk}</div>
            <div class="metric-label">At Risk</div>
        </div>
        <div class="metric-card">
            <div class="metric-value success">${healthy}</div>
            <div class="metric-label">Healthy</div>
        </div>
    `;
    
    // Render cases table
    if (state.cases.length === 0) {
        document.getElementById('cases-container').innerHTML = `
            <div class="card">
                <p class="text-muted text-center">No cases assigned to you.</p>
            </div>
        `;
        return;
    }
    
    document.getElementById('cases-container').innerHTML = `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Case ID</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Severity</th>
                        <th>Customer</th>
                        <th>CSAT Risk</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody>
                    ${state.cases.map(c => renderCaseRow(c)).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderCaseRow(caseData) {
    const sentiment = caseData.sentiment_score || 0.5;
    const csatRisk = caseData.csat_risk || 'healthy';
    
    // CSAT risk indicator (based on sentiment score)
    let riskBadge = 'badge-success';
    let riskIcon = '✅';
    let riskLabel = 'Healthy';
    if (csatRisk === 'critical' || sentiment < 0.35) {
        riskBadge = 'badge-danger';
        riskIcon = '🚨';
        riskLabel = 'Critical';
    } else if (csatRisk === 'at_risk' || sentiment < 0.55) {
        riskBadge = 'badge-warning';
        riskIcon = '⚠️';
        riskLabel = 'At Risk';
    }
    
    const sentimentClass = getSentimentClass(sentiment);
    const daysNote = Math.round(caseData.days_since_last_note || 0);
    const daysComm = Math.round(caseData.days_since_last_outbound || 0);
    
    const sevLetter = formatSeverity(caseData.severity);
    const sevClass = getSeverityBadgeClass(caseData.severity);
    
    return `
        <tr class="clickable" onclick="viewCase('${caseData.id}')">
            <td><strong>${caseData.id}</strong></td>
            <td>${caseData.title || 'Untitled'}</td>
            <td><span class="badge badge-info">${caseData.status || 'Active'}</span></td>
            <td><span class="badge ${sevClass}">Sev ${sevLetter}</span></td>
            <td>${caseData.customer?.company || 'Unknown'}</td>
            <td>
                ${riskIcon} <span class="badge ${riskBadge}">${riskLabel}</span>
            </td>
            <td>
                <div class="sentiment-indicator">
                    <span class="sentiment-dot sentiment-${sentimentClass}"></span>
                    ${Math.round(sentiment * 100)}%
                </div>
            </td>
        </tr>
    `;
}

async function viewCase(caseId) {
    state.currentView = 'case-detail';
    showLoading(true);
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="loading"><div class="spinner"></div></div>
    `;
    
    // Fetch case details
    const caseData = await getCase(caseId);
    if (!caseData) {
        main.innerHTML = `
            <div class="card">
                <p class="text-muted">Unable to load case details.</p>
                <button class="btn btn-secondary mt-md" onclick="navigateTo('engineer')">← Back to Cases</button>
            </div>
        `;
        showLoading(false);
        return;
    }
    
    state.currentCase = caseData;
    updateBreadcrumb([
        { text: 'Engineer Dashboard', action: "navigateTo('engineer')" },
        { text: caseId }
    ]);
    
    // Fetch analysis in parallel
    const analysisPromise = analyzeCase(caseId);
    
    // Render case detail structure - Clean layout without full timeline
    const daysNote = Math.round(caseData.days_since_last_note || 0);
    const daysComm = Math.round(caseData.days_since_last_outbound || 0);
    const csatRisk = caseData.csat_risk || 'healthy';
    const sentimentScore = caseData.sentiment_score || 0.5;
    
    main.innerHTML = `
        <div class="content-header flex justify-between items-center">
            <div>
                <button class="btn btn-ghost mb-sm" onclick="navigateTo('engineer')">← Back to Cases</button>
                <h1>${caseData.title || caseId}</h1>
                <p class="subtitle">${caseData.id} • ${caseData.customer?.company || 'Unknown Customer'} (${caseData.customer?.tier || 'Standard'})</p>
            </div>
            <div style="display: flex; gap: 24px; text-align: right;">
                <div>
                    <div class="metric-value ${daysComm > 2 ? 'danger' : daysComm > 1 ? 'warning' : ''}">${daysComm}</div>
                    <div class="metric-label">Days Since Comm</div>
                </div>
                <div>
                    <div class="metric-value ${daysNote >= 7 ? 'danger' : daysNote >= 5 ? 'warning' : ''}">${daysNote}</div>
                    <div class="metric-label">Days Since Note</div>
                </div>
            </div>
        </div>
        
        <div class="two-column">
            <div class="sidebar">
                <!-- Case Info Card -->
                <div class="card mb-lg">
                    <h3>📋 Case Details</h3>
                    <div class="mt-md">
                        <div class="text-small text-muted">Status</div>
                        <div><span class="badge badge-info">${caseData.status || 'Active'}</span></div>
                    </div>
                    <div class="mt-md">
                        <div class="text-small text-muted">Severity</div>
                        <div><span class="badge ${getSeverityBadgeClass(caseData.severity)}">Sev ${formatSeverity(caseData.severity)}</span></div>
                    </div>
                    <div class="mt-md">
                        <div class="text-small text-muted">Created</div>
                        <div>${formatDateShort(caseData.created_on)}</div>
                    </div>
                    <div class="mt-md">
                        <div class="text-small text-muted">Days Open</div>
                        <div>${Math.round(caseData.days_open || caseData.days_since_creation || 0)} days</div>
                    </div>
                    <div class="mt-md">
                        <div class="text-small text-muted">Owner</div>
                        <div>${caseData.owner?.name || 'Unassigned'}</div>
                    </div>
                    <div class="mt-md">
                        <div class="text-small text-muted">Customer</div>
                        <div>${caseData.customer?.company || 'Unknown'}</div>
                    </div>
                    <div class="mt-md">
                        <div class="text-small text-muted">Support Tier</div>
                        <div>${caseData.customer?.tier || 'Standard'}</div>
                    </div>
                </div>
                
                <!-- Description -->
                <div class="card mb-lg">
                    <h3>📝 Description</h3>
                    <p class="mt-md" style="font-size: 0.9rem; line-height: 1.6;">${caseData.description || 'No description available.'}</p>
                </div>
            </div>
            
            <div class="main-column">
                <!-- AI Sentiment Analysis Section -->
                <div id="analysis-section" class="analysis-section mb-lg">
                    <div class="loading"><div class="spinner"></div></div>
                    <p class="text-center text-muted">Analyzing case with Azure OpenAI...</p>
                </div>
                
                <!-- Suggested Actions Section -->
                <div id="actions-section" class="card mb-lg" style="display: none;">
                    <h3>💡 Suggested Actions</h3>
                    <div id="actions-content" class="mt-md"></div>
                </div>
                
                <!-- Chat Section -->
                <div class="card">
                    <h3>💬 Ask CSAT Guardian About This Case</h3>
                    <p class="text-muted text-small mt-sm">Ask questions about sentiment, customer concerns, or get coaching advice.</p>
                    <div id="chat-container" class="mt-md">
                        <div id="chat-messages" style="max-height: 350px; overflow-y: auto; margin-bottom: var(--spacing-md); padding: var(--spacing-sm);">
                            <div class="chat-message">
                                <div class="chat-avatar">🤖</div>
                                <div class="chat-bubble">
                                    <p>I've analyzed this case. What would you like to know? You can ask me:</p>
                                    <ul style="margin: 8px 0 0 16px; font-size: 0.9rem;">
                                        <li>Why is the customer frustrated?</li>
                                        <li>What should I do next?</li>
                                        <li>Is there any risk of low CSAT?</li>
                                        <li>Summarize the customer's concerns</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="flex gap-sm">
                            <input type="text" id="chat-input" class="form-input" placeholder="Ask a question about this case..." onkeypress="handleChatKeypress(event)">
                            <button class="btn btn-primary" onclick="sendChatMessage()">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    showLoading(false);
    
    // Wait for analysis and render
    const analysis = await analysisPromise;
    renderAnalysis(analysis, caseData);
}

function renderTimeline(timeline) {
    if (!timeline || timeline.length === 0) {
        return '<p class="text-muted">No timeline entries.</p>';
    }
    
    return `
        <div class="timeline">
            ${timeline.map(entry => {
                const isCustomer = entry.is_customer_communication || entry.created_by === 'Customer';
                const icon = entry.entry_type?.includes('email') ? '📧' : 
                            entry.entry_type?.includes('phone') ? '📞' : '📝';
                return `
                    <div class="timeline-item ${isCustomer ? 'customer' : ''}">
                        <div class="timeline-header">
                            <span class="timeline-type">${icon} ${(entry.entry_type || 'note').replace(/_/g, ' ')}</span>
                            <span class="timeline-date">${formatDate(entry.created_on)}</span>
                        </div>
                        <div class="timeline-author">${entry.created_by || 'Unknown'}</div>
                        ${entry.subject ? `<div class="text-small mt-sm"><strong>${entry.subject}</strong></div>` : ''}
                        <div class="timeline-content mt-sm">${entry.content || ''}</div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderAnalysis(analysis, caseData) {
    const container = document.getElementById('analysis-section');
    const actionsSection = document.getElementById('actions-section');
    const actionsContent = document.getElementById('actions-content');
    
    if (!analysis) {
        container.innerHTML = `
            <h3>🤖 AI Sentiment Analysis</h3>
            <p class="text-muted mt-md">Unable to analyze case. AI service may be unavailable.</p>
        `;
        return;
    }
    
    const sentiment = analysis.sentiment || {};
    const score = sentiment.score || 0.5;
    const label = sentiment.label || 'neutral';
    const trend = sentiment.trend || 'stable';
    const phrases = sentiment.key_phrases || [];
    const concerns = sentiment.concerns || [];
    const recommendations = analysis.recommendations || [];
    const timelineInsights = analysis.timeline_insights || [];
    
    const sentimentClass = getSentimentClass(score);
    
    // Extract evidence from timeline for verbose display
    const timeline = caseData?.timeline || [];
    const customerMessages = timeline.filter(e => e.is_customer_communication || e.created_by === 'Customer');
    
    // Build sentiment evidence from actual communications
    let evidenceHtml = '';
    if (customerMessages.length > 0) {
        const recentCustomerMsgs = customerMessages.slice(-3); // Last 3 customer messages
        evidenceHtml = `
            <div class="mt-lg">
                <h4>📧 Sentiment Evidence from Communications</h4>
                <div class="mt-md" style="display: flex; flex-direction: column; gap: 12px;">
                    ${recentCustomerMsgs.map(msg => {
                        // Detect sentiment indicators in message
                        const content = msg.content || '';
                        const contentLower = content.toLowerCase();
                        const frustrationWords = ['frustrated', 'disappointed', 'unacceptable', 'urgent', 'escalate', 'waiting', 'still no', 'again', 'issue', 'problem', 'not working'];
                        const positiveWords = ['thank', 'great', 'appreciate', 'helpful', 'excellent', 'resolved', 'perfect', 'amazing'];
                        
                        const foundFrustration = frustrationWords.filter(w => contentLower.includes(w));
                        const foundPositive = positiveWords.filter(w => contentLower.includes(w));
                        
                        let indicator = '➡️ Neutral';
                        let bgColor = 'var(--background-tertiary)';
                        if (foundFrustration.length > foundPositive.length) {
                            indicator = '⚠️ Signs of frustration';
                            bgColor = 'rgba(209, 52, 56, 0.1)';
                        } else if (foundPositive.length > 0) {
                            indicator = '✅ Positive tone';
                            bgColor = 'rgba(16, 124, 16, 0.1)';
                        }
                        
                        // Extract a relevant snippet (first 150 chars or first sentence)
                        let snippet = content.substring(0, 200);
                        if (content.length > 200) snippet += '...';
                        
                        return `
                            <div style="background: ${bgColor}; padding: 12px; border-radius: 8px; border-left: 3px solid ${foundFrustration.length > foundPositive.length ? 'var(--accent-danger)' : foundPositive.length > 0 ? 'var(--accent-success)' : 'var(--border-subtle)'};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: 600; color: var(--text-primary);">${indicator}</span>
                                    <span style="font-size: 0.75rem; color: var(--text-tertiary);">${formatDateShort(msg.created_on)}</span>
                                </div>
                                <div style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5; font-style: italic;">"${snippet}"</div>
                                ${foundFrustration.length > 0 ? `<div style="margin-top: 8px; font-size: 0.75rem; color: var(--accent-warning);">Detected: ${foundFrustration.join(', ')}</div>` : ''}
                                ${foundPositive.length > 0 ? `<div style="margin-top: 8px; font-size: 0.75rem; color: var(--accent-success);">Detected: ${foundPositive.join(', ')}</div>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    // Build concerns section with better formatting
    let concernsHtml = '';
    if (concerns.length > 0) {
        concernsHtml = `
            <div class="mt-lg">
                <h4>⚠️ Identified Customer Concerns</h4>
                <div class="mt-md" style="display: flex; flex-direction: column; gap: 8px;">
                    ${concerns.slice(0, 5).map(c => `
                        <div style="background: rgba(255, 185, 0, 0.1); padding: 10px 14px; border-radius: 6px; border-left: 3px solid var(--accent-warning); color: var(--text-primary); font-size: 0.9rem;">
                            ${c}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Key phrases with better styling
    let phrasesHtml = '';
    if (phrases.length > 0) {
        phrasesHtml = `
            <div class="mt-lg">
                <h4>🔍 Key Phrases from Customer</h4>
                <div class="key-phrases mt-md">
                    ${phrases.slice(0, 6).map(p => `<span class="key-phrase">"${p}"</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    container.innerHTML = `
        <h3>🤖 AI Sentiment Analysis</h3>
        
        <div class="analysis-header mt-lg">
            <div class="analysis-score ${sentimentClass}">${Math.round(score * 100)}%</div>
            <div class="analysis-details">
                <div class="analysis-label">${label.toUpperCase()}</div>
                <div class="analysis-trend">Trend: ${trend}</div>
                <div style="font-size: 0.8rem; color: var(--text-tertiary); margin-top: 4px;">
                    Based on ${customerMessages.length} customer communication${customerMessages.length !== 1 ? 's' : ''}
                </div>
            </div>
        </div>
        
        ${concernsHtml}
        ${evidenceHtml}
        ${phrasesHtml}
    `;
    
    // Render recommendations in the separate actions section
    if (recommendations.length > 0) {
        actionsSection.style.display = 'block';
        actionsContent.innerHTML = `
            <ul class="recommendations-list">
                ${recommendations.slice(0, 5).map((r, i) => `
                    <li class="recommendation-item">
                        <span class="recommendation-number">#${i + 1}</span>
                        <span class="recommendation-text">${r}</span>
                    </li>
                `).join('')}
            </ul>
        `;
    }
}

async function renderManagerDashboard() {
    state.currentView = 'manager';
    showLoading(true);
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="content-header">
            <h1>Team Overview</h1>
            <p class="subtitle">Click on an engineer to view their CSAT insights and coaching recommendations</p>
        </div>
        <div id="alerts-container"></div>
        <div id="metrics-container" class="metrics-row"></div>
        <div id="team-container">
            <div class="loading"><div class="spinner"></div></div>
        </div>
    `;
    updateBreadcrumb([{ text: 'Manager Dashboard' }]);
    
    // Fetch data
    const [engineersData, casesData] = await Promise.all([
        getEngineers(),
        getCases()
    ]);
    
    showLoading(false);
    
    state.engineers = engineersData?.engineers || engineersData || [];
    state.cases = casesData?.cases || casesData || [];
    
    const cases = state.cases;
    const engineers = state.engineers;
    
    // Calculate CSAT risk metrics
    const critical = cases.filter(c => (c.sentiment_score || 0.5) < 0.35).length;
    const atRisk = cases.filter(c => {
        const score = c.sentiment_score || 0.5;
        return score >= 0.35 && score < 0.55;
    }).length;
    
    // Calculate team average sentiment
    const teamAvgSentiment = cases.length > 0
        ? cases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / cases.length
        : 0.5;
    
    // Alerts - CSAT focused
    if (critical > 0) {
        document.getElementById('alerts-container').innerHTML = `
            <div class="alert-banner danger">
                🚨 <strong>Team CSAT Alert:</strong> ${critical} case${critical > 1 ? 's' : ''} with critical satisfaction risk require immediate attention
            </div>
        `;
    }
    
    // Metrics - CSAT focused
    document.getElementById('metrics-container').innerHTML = `
        <div class="metric-card">
            <div class="metric-value">${engineers.length}</div>
            <div class="metric-label">Team Members</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${cases.length}</div>
            <div class="metric-label">Total Cases</div>
        </div>
        <div class="metric-card">
            <div class="metric-value ${getSentimentClass(teamAvgSentiment)}">${Math.round(teamAvgSentiment * 100)}%</div>
            <div class="metric-label">Team Avg Sentiment</div>
        </div>
        <div class="metric-card">
            <div class="metric-value danger">${critical}</div>
            <div class="metric-label">Critical CSAT</div>
        </div>
    `;
    
    // Engineer cards - clickable for details
    const teamHtml = engineers.map(eng => {
        const engCases = cases.filter(c => c.owner?.id === eng.id);
        const engCritical = engCases.filter(c => (c.sentiment_score || 0.5) < 0.35).length;
        const engAtRisk = engCases.filter(c => {
            const score = c.sentiment_score || 0.5;
            return score >= 0.35 && score < 0.55;
        }).length;
        const engAvgSentiment = engCases.length > 0
            ? engCases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / engCases.length
            : 0.5;
        
        const statusBadge = engCritical > 0 ? '<span class="badge badge-danger">Needs Attention</span>' : 
                           engAtRisk > 0 ? '<span class="badge badge-warning">At Risk</span>' : 
                           '<span class="badge badge-success">Healthy</span>';
        
        return `
            <div class="card card-clickable engineer-card" onclick="viewEngineerDetail('${eng.id}')">
                <div class="card-header">
                    <div class="engineer-avatar">${eng.name.split(' ').map(n => n[0]).join('')}</div>
                    <div>
                        <div class="card-title">${eng.name}</div>
                        <div class="card-subtitle">${engCases.length} cases</div>
                    </div>
                    ${statusBadge}
                </div>
                <div class="card-body">
                    <div class="engineer-sentiment-bar">
                        <div class="sentiment-fill ${getSentimentClass(engAvgSentiment)}" style="width: ${Math.round(engAvgSentiment * 100)}%"></div>
                    </div>
                    <div class="flex justify-between mt-sm">
                        <span class="text-muted text-small">Avg Sentiment</span>
                        <span class="text-small ${getSentimentClass(engAvgSentiment)}">${Math.round(engAvgSentiment * 100)}%</span>
                    </div>
                </div>
                <div class="card-footer">
                    <span class="text-xs text-muted">Click for coaching insights →</span>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('team-container').innerHTML = `
        <h3 class="mb-lg">👥 Team Members</h3>
        <div class="card-grid">
            ${teamHtml || '<p class="text-muted">No team members found.</p>'}
        </div>
    `;
}

/**
 * View individual engineer details (for managers)
 */
async function viewEngineerDetail(engineerId) {
    state.currentView = 'engineer-detail';
    showLoading(true);
    
    const engineer = state.engineers.find(e => e.id === engineerId);
    const engCases = state.cases.filter(c => c.owner?.id === engineerId);
    
    if (!engineer) {
        showLoading(false);
        alert('Engineer not found');
        return;
    }
    
    state.selectedEngineer = engineer;
    
    const main = document.getElementById('main-content');
    
    // Calculate metrics
    const avgSentiment = engCases.length > 0
        ? engCases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / engCases.length
        : 0.5;
    const critical = engCases.filter(c => (c.sentiment_score || 0.5) < 0.35).length;
    const atRisk = engCases.filter(c => {
        const score = c.sentiment_score || 0.5;
        return score >= 0.35 && score < 0.55;
    }).length;
    const healthy = engCases.length - critical - atRisk;
    
    // Get negative indicators
    const indicators = analyzeNegativeIndicators(engCases);
    const coachingAdvice = generateCoachingAdvice(indicators, avgSentiment);
    
    const sentimentClass = getSentimentClass(avgSentiment);
    
    main.innerHTML = `
        <div class="content-header">
            <button class="btn btn-ghost mb-sm" onclick="navigateTo('manager')">← Back to Team</button>
            <div class="flex items-center gap-md">
                <div class="engineer-avatar-large">${engineer.name.split(' ').map(n => n[0]).join('')}</div>
                <div>
                    <h1>${engineer.name}</h1>
                    <p class="subtitle">${engineer.email} • ${engineer.team || 'CSS Support'}</p>
                </div>
            </div>
        </div>
        
        <div id="metrics-container" class="metrics-row">
            <div class="metric-card">
                <div class="metric-value">${engCases.length}</div>
                <div class="metric-label">Total Cases</div>
            </div>
            <div class="metric-card">
                <div class="metric-value ${sentimentClass}">${Math.round(avgSentiment * 100)}%</div>
                <div class="metric-label">Avg Sentiment</div>
            </div>
            <div class="metric-card">
                <div class="metric-value danger">${critical}</div>
                <div class="metric-label">Critical</div>
            </div>
            <div class="metric-card">
                <div class="metric-value success">${healthy}</div>
                <div class="metric-label">Healthy</div>
            </div>
        </div>
        
        <div class="two-column mt-lg">
            <div class="main-column">
                <!-- Coaching Section for Manager -->
                <div class="card mb-lg">
                    <h3>🎯 Coaching Insights for 1:1</h3>
                    <p class="text-muted text-small mt-sm">Use these insights when having coaching conversations with ${engineer.name.split(' ')[0]}</p>
                    
                    <!-- Top Indicators -->
                    <div class="mt-lg">
                        <h4>Top 3 Areas Affecting CSAT</h4>
                        ${indicators.length > 0 ? `
                            <div class="indicators-list mt-md">
                                ${indicators.map((ind, i) => `
                                    <div class="indicator-item highlight">
                                        <span class="indicator-rank">${i + 1}</span>
                                        <span class="indicator-text">${ind}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : `
                            <p class="text-muted mt-md">✅ No significant issues identified</p>
                        `}
                    </div>
                    
                    <!-- Coaching Advice -->
                    ${coachingAdvice.length > 0 ? `
                        <div class="mt-lg">
                            <h4>💬 Suggested Coaching Points</h4>
                            <div class="coaching-cards mt-md">
                                ${coachingAdvice.map(a => `
                                    <div class="coaching-card manager">
                                        <div class="coaching-icon">${a.icon}</div>
                                        <div class="coaching-content">
                                            <div class="coaching-issue">${a.issue}</div>
                                            <div class="coaching-suggestion">${a.suggestion}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Sample Talking Points -->
                    <div class="mt-lg">
                        <h4>📋 Sample Talking Points</h4>
                        <div class="talking-points mt-md">
                            ${generateTalkingPoints(engineer.name.split(' ')[0], indicators, avgSentiment)}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="sidebar">
                <!-- Case Summary -->
                <div class="card mb-lg">
                    <h3>📊 Case Breakdown</h3>
                    <div class="case-breakdown mt-md">
                        <div class="breakdown-item">
                            <span class="breakdown-dot danger"></span>
                            <span>Critical (${critical})</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-dot warning"></span>
                            <span>At Risk (${atRisk})</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-dot success"></span>
                            <span>Healthy (${healthy})</span>
                        </div>
                    </div>
                    
                    ${critical > 0 ? `
                        <div class="mt-lg">
                            <h4 class="text-danger">🚨 Critical Cases</h4>
                            <div class="critical-cases-list mt-md">
                                ${engCases.filter(c => (c.sentiment_score || 0.5) < 0.35).slice(0, 3).map(c => `
                                    <div class="critical-case-item">
                                        <div class="text-small"><strong>${c.id}</strong></div>
                                        <div class="text-xs text-muted">${c.title?.substring(0, 40)}${c.title?.length > 40 ? '...' : ''}</div>
                                        <div class="text-xs text-danger">${Math.round((c.sentiment_score || 0.5) * 100)}% sentiment</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Trend Indicator -->
                <div class="card">
                    <h3>📈 30-Day Trend</h3>
                    <div class="trend-indicator mt-md">
                        <div class="trend-visual ${sentimentClass}">
                            ${avgSentiment >= 0.6 ? '📈' : avgSentiment >= 0.4 ? '➡️' : '📉'}
                        </div>
                        <div class="trend-label">
                            ${avgSentiment >= 0.6 ? 'Positive trend' : avgSentiment >= 0.4 ? 'Stable' : 'Needs improvement'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    updateBreadcrumb([
        { text: 'Manager Dashboard', action: "navigateTo('manager')" },
        { text: engineer.name }
    ]);
    
    showLoading(false);
}

/**
 * Generate sample talking points for manager coaching
 */
function generateTalkingPoints(firstName, indicators, avgSentiment) {
    const points = [];
    
    // Opening
    if (avgSentiment < 0.4) {
        points.push(`"${firstName}, I wanted to check in on how things are going with your cases. I've noticed some customers may be having a tougher time than usual."`);
    } else if (avgSentiment < 0.6) {
        points.push(`"${firstName}, let's talk about your current caseload and see if there are areas where I can support you."`);
    } else {
        points.push(`"${firstName}, your customer sentiment looks great! Let's discuss what's working well so we can share with the team."`);
    }
    
    // Specific to indicators
    indicators.forEach(ind => {
        switch (ind) {
            case 'Slow Response Time':
                points.push(`"I noticed some customers haven't heard back in a while. Is there anything blocking you from responding more quickly?"`);
                break;
            case 'Long Time Since Last Note':
                points.push(`"Let's talk about keeping case notes current. It really helps with handoffs and audit compliance."`);
                break;
            case 'Customer Frustration Signals':
                points.push(`"A few customers seem frustrated. What's your read on the situation? How can I help?"`);
                break;
        }
    });
    
    // Closing
    points.push(`"What support do you need from me to help improve these areas?"`);
    
    return points.map(p => `<div class="talking-point">${p}</div>`).join('');
}

// =============================================================================
// Chat Functions
// =============================================================================

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    input.disabled = true;
    
    // Add user message
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML += `
        <div class="chat-message user">
            <div class="chat-avatar">You</div>
            <div class="chat-bubble">
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `;
    
    // Add loading indicator
    messagesContainer.innerHTML += `
        <div class="chat-message" id="chat-loading">
            <div class="chat-avatar">🤖</div>
            <div class="chat-bubble">
                <p><span class="spinner" style="width: 16px; height: 16px; display: inline-block;"></span> Thinking...</p>
            </div>
        </div>
    `;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Send to API
    const response = await chatWithAgent(message, state.currentCase?.id);
    
    // Remove loading
    document.getElementById('chat-loading')?.remove();
    
    // Handle response or error
    let responseText;
    if (response?.error) {
        if (response.error === 'timeout') {
            responseText = '⏱️ The AI service is taking too long to respond. This could be due to high load or the service being unavailable. Please try again in a moment.';
        } else {
            responseText = `❌ Sorry, I encountered an error: ${response.message || 'Unable to process your request'}. Please try again.`;
        }
    } else if (response?.response) {
        responseText = response.response;
    } else {
        responseText = '❌ Sorry, I couldn\'t get a response. The AI service may be unavailable. Please try again later.';
    }
    
    messagesContainer.innerHTML += `
        <div class="chat-message">
            <div class="chat-avatar">🤖</div>
            <div class="chat-bubble">
                <p>${formatChatResponse(responseText)}</p>
            </div>
        </div>
    `;
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    input.disabled = false;
    input.focus();
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function formatChatResponse(text) {
    // Convert markdown-like formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================================================
// Navigation
// =============================================================================

function navigateTo(view) {
    switch (view) {
        case 'landing':
            renderLandingPage();
            break;
        case 'engineer':
            renderEngineerDashboard();
            break;
        case 'manager':
            renderManagerDashboard();
            break;
        default:
            renderLandingPage();
    }
}

function updateBreadcrumb(items) {
    const breadcrumb = document.getElementById('breadcrumb');
    if (!breadcrumb) return;
    
    if (items.length === 0) {
        breadcrumb.innerHTML = '<span class="breadcrumb-current">Home</span>';
        return;
    }
    
    let html = `<a href="#" onclick="navigateTo('landing'); return false;">Home</a>`;
    items.forEach((item, index) => {
        html += '<span class="breadcrumb-separator">›</span>';
        if (index === items.length - 1) {
            html += `<span class="breadcrumb-current">${item.text}</span>`;
        } else {
            html += `<a href="#" onclick="${item.action}; return false;">${item.text}</a>`;
        }
    });
    
    breadcrumb.innerHTML = html;
}

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('CSAT Guardian initializing...');
    
    try {
        // Render landing page immediately (don't wait for health check)
        renderLandingPage();
        console.log('Landing page rendered');
        
        // Check backend health in background
        checkHealth().catch(e => console.warn('Health check failed:', e));
        
        // Periodic health check
        setInterval(() => checkHealth().catch(() => {}), 30000);
    } catch (e) {
        console.error('Initialization error:', e);
        document.getElementById('main-content').innerHTML = `
            <div class="card" style="margin: 2rem;">
                <h2>Error Loading Application</h2>
                <p>${e.message}</p>
            </div>
        `;
    }
});
