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

/**
 * Fast manager summary - uses SQL aggregation for performance
 */
async function getManagerSummary() {
    return await apiGet('/api/manager/summary');
}

/**
 * Fast engineer summary - uses SQL aggregation for performance
 */
async function getEngineerSummary(engineerId) {
    return await apiGet(`/api/engineer/${engineerId}/summary`);
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
    
    const allCases = casesData.cases || casesData || [];
    
    // Separate active and resolved cases
    const activeCases = allCases.filter(c => c.status === 'active');
    const resolvedCases = allCases.filter(c => c.status === 'resolved');
    
    state.cases = allCases;
    
    // Calculate CSAT risk metrics for ACTIVE cases only
    const critical = activeCases.filter(c => (c.sentiment_score || 0.5) < 0.35).length;
    const atRisk = activeCases.filter(c => {
        const score = c.sentiment_score || 0.5;
        return score >= 0.35 && score < 0.55;
    }).length;
    const healthy = activeCases.length - critical - atRisk;
    
    // Calculate average sentiment for ACTIVE cases only
    const avgSentiment = activeCases.length > 0 
        ? activeCases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / activeCases.length 
        : 0.5;
    
    // Find top negative indicators from ACTIVE cases
    const negativeIndicators = analyzeNegativeIndicators(activeCases);
    
    // Render personal analytics
    renderPersonalAnalytics(avgSentiment, negativeIndicators, activeCases);
    
    // Render alerts - ONLY for ACTIVE cases with critical risk
    if (critical > 0) {
        document.getElementById('alerts-container').innerHTML = `
            <div class="alert-banner danger">
                🚨 <strong>CSAT Alert:</strong> ${critical} active case${critical > 1 ? 's' : ''} with critical customer satisfaction risk - immediate attention needed
            </div>
        `;
    } else if (atRisk > 0) {
        document.getElementById('alerts-container').innerHTML = `
            <div class="alert-banner warning">
                ⚠️ <strong>CSAT Warning:</strong> ${atRisk} active case${atRisk > 1 ? 's' : ''} showing signs of declining customer satisfaction
            </div>
        `;
    }
    
    // Render metrics - CSAT focused on ACTIVE cases
    document.getElementById('metrics-container').innerHTML = `
        <div class="metric-card">
            <div class="metric-value">${activeCases.length}</div>
            <div class="metric-label">Active Cases</div>
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
        <div class="metric-card">
            <div class="metric-value">${resolvedCases.length}</div>
            <div class="metric-label">Resolved</div>
        </div>
    `;
    
    // Render cases in separate sections
    document.getElementById('cases-container').innerHTML = `
        <!-- Active Cases Section -->
        <h3 class="mt-lg mb-md">📋 Active Cases (${activeCases.length})</h3>
        ${activeCases.length > 0 ? `
            <div class="table-container mb-lg">
                <table>
                    <thead>
                        <tr>
                            <th>Case ID</th>
                            <th>Title</th>
                            <th>Severity</th>
                            <th>Customer</th>
                            <th>CSAT Risk</th>
                            <th>Sentiment</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${activeCases.map(c => renderCaseRow(c, false)).join('')}
                    </tbody>
                </table>
            </div>
        ` : '<p class="text-muted mb-lg">No active cases - great job!</p>'}
        
        <!-- Resolved Cases Section -->
        <h3 class="mt-lg mb-md">✅ Resolved Cases (${resolvedCases.length})</h3>
        ${resolvedCases.length > 0 ? `
            <div class="table-container">
                <table class="resolved-table">
                    <thead>
                        <tr>
                            <th>Case ID</th>
                            <th>Title</th>
                            <th>Severity</th>
                            <th>Customer</th>
                            <th>Final Sentiment</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${resolvedCases.map(c => renderCaseRow(c, true)).join('')}
                    </tbody>
                </table>
            </div>
        ` : '<p class="text-muted">No resolved cases yet this quarter.</p>'}
    `;
}

function renderCaseRow(caseData, isResolved = false) {
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
    
    // Simplified row for resolved cases
    if (isResolved) {
        return `
            <tr class="clickable resolved-row" onclick="viewCase('${caseData.id}')">
                <td><strong>${caseData.id}</strong></td>
                <td>${caseData.title || 'Untitled'}</td>
                <td><span class="badge ${sevClass}">Sev ${sevLetter}</span></td>
                <td>${caseData.customer?.company || 'Unknown'}</td>
                <td>
                    <div class="sentiment-indicator">
                        <span class="sentiment-dot sentiment-${sentimentClass}"></span>
                        ${Math.round(sentiment * 100)}%
                    </div>
                </td>
            </tr>
        `;
    }
    
    // Full row for active cases
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
    state.selectedDateRange = state.selectedDateRange || '30d';
    showLoading(true);
    
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="content-header">
            <div class="flex justify-between items-center">
                <div>
                    <h1>Team Performance</h1>
                    <p class="subtitle">Empowering your team through data-driven coaching insights</p>
                </div>
                <div class="date-range-selector">
                    <button class="date-btn ${state.selectedDateRange === '7d' ? 'active' : ''}" onclick="updateDateRange('7d')">7 Days</button>
                    <button class="date-btn ${state.selectedDateRange === '30d' ? 'active' : ''}" onclick="updateDateRange('30d')">30 Days</button>
                    <button class="date-btn ${state.selectedDateRange === '90d' ? 'active' : ''}" onclick="updateDateRange('90d')">Quarter</button>
                </div>
            </div>
        </div>
        <div id="team-summary" class="team-summary-section"></div>
        <div id="team-container">
            <div class="loading"><div class="spinner"></div></div>
        </div>
    `;
    updateBreadcrumb([{ text: 'Team Performance' }]);
    
    // Use fast summary endpoint for performance (avoids N+1 queries)
    const summaryData = await getManagerSummary();
    
    showLoading(false);
    
    // Debug log to see what we're getting
    console.log('Manager summary data:', summaryData);
    
    // Check if we got USEFUL data (not just empty engineer list)
    // The slow fallback returns engineers but with active_cases=0 and no stats
    const hasUsefulData = summaryData && 
        summaryData.engineers && 
        summaryData.engineers.length > 0 &&
        summaryData.stats &&
        (summaryData.stats.total_active_cases > 0 || summaryData.stats.total_cases > 0);
    
    if (hasUsefulData) {
        state.engineers = summaryData.engineers;
        state.managerStats = summaryData.stats || {};
    } else {
        // Fast endpoint returned incomplete data, use slow method to load all cases
        console.log('Fast endpoint returned incomplete data, falling back to slow method');
        const [engineersData, casesData] = await Promise.all([
            getEngineers(),
            getCases()
        ]);
        
        const engineers = engineersData?.engineers || engineersData || [];
        const allCases = casesData?.cases || casesData || [];
        const activeCases = allCases.filter(c => c.status === 'active');
        const resolvedCases = allCases.filter(c => c.status === 'resolved');
        
        state.managerStats = {
            total_engineers: engineers.length,
            total_active_cases: activeCases.length,
            total_resolved_cases: resolvedCases.length,
            total_cases: allCases.length
        };
        
        // Compute metrics per engineer from the cases data
        state.engineers = engineers.map(eng => {
            const engActiveCases = activeCases.filter(c => c.owner?.id === eng.id);
            const engResolvedCases = resolvedCases.filter(c => c.owner?.id === eng.id);
            
            // Calculate average sentiment for this engineer's active cases
            const avgSentiment = engActiveCases.length > 0
                ? engActiveCases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / engActiveCases.length
                : null;  // null means no active cases to measure
            
            // Determine risk level based on sentiment - only if they have active cases
            let riskLevel = 'no_cases';  // Default for engineers with no active cases
            if (engActiveCases.length > 0) {
                if (engActiveCases.some(c => (c.sentiment_score || 0.5) < 0.35)) {
                    riskLevel = 'critical';
                } else if (engActiveCases.some(c => (c.sentiment_score || 0.5) < 0.55)) {
                    riskLevel = 'at_risk';
                } else {
                    riskLevel = 'healthy';
                }
            }
            
            return {
                ...eng,
                active_cases: engActiveCases.length,
                resolved_cases: engResolvedCases.length,
                risk_level: riskLevel,
                avg_sentiment: avgSentiment
            };
        });
    }
    
    renderTeamDashboardContent();
}

function updateDateRange(range) {
    state.selectedDateRange = range;
    // Update button states
    document.querySelectorAll('.date-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(
            range === '7d' ? '7' : range === '30d' ? '30' : 'Quarter'
        ));
    });
    renderTeamDashboardContent();
}

function renderTeamDashboardContent() {
    const teamSummaryEl = document.getElementById('team-summary');
    const teamContainerEl = document.getElementById('team-container');
    
    // Guard against race condition where elements don't exist yet
    if (!teamSummaryEl || !teamContainerEl) {
        console.warn('Team dashboard elements not ready, skipping render');
        return;
    }
    
    const engineers = state.engineers;
    const stats = state.managerStats || {};
    const range = state.selectedDateRange;
    
    const rangeLabel = range === '7d' ? 'Past 7 Days' : range === '30d' ? 'Past 30 Days' : 'Past Quarter';
    
    // Calculate date cutoff based on range selection
    const now = new Date();
    const cutoffDays = range === '7d' ? 7 : range === '30d' ? 30 : 90;
    const cutoffDate = new Date(now.getTime() - cutoffDays * 24 * 60 * 60 * 1000);
    
    // Note: Since we're using summary endpoint, we show all active cases
    // The date range affects the "period" label but active cases are always current
    // In a real implementation, you'd have historical data to filter
    
    // Use pre-computed stats from fast endpoint
    const totalActiveCases = stats.total_active_cases || engineers.reduce((sum, e) => sum + (e.active_cases || 0), 0);
    const totalResolvedCases = stats.total_resolved_cases || engineers.reduce((sum, e) => sum + (e.resolved_cases || 0), 0);
    const totalCases = stats.total_cases || (totalActiveCases + totalResolvedCases);
    
    // Calculate risk metrics from engineer summaries (fast endpoint provides risk_level)
    const healthyEngineers = engineers.filter(e => e.risk_level === 'healthy').length;
    const atRiskEngineers = engineers.filter(e => e.risk_level === 'at_risk').length;
    const criticalEngineers = engineers.filter(e => e.risk_level === 'critical').length;
    
    // Estimate sentiment distribution from ACTIVE cases only
    const excellentCount = engineers.reduce((sum, e) => sum + (e.risk_level === 'healthy' ? (e.active_cases || 0) : 0), 0);
    const goodCount = engineers.reduce((sum, e) => sum + (e.risk_level === 'at_risk' ? Math.floor((e.active_cases || 0) / 2) : 0), 0);
    const opportunityCount = engineers.reduce((sum, e) => sum + (e.risk_level === 'critical' ? (e.active_cases || 0) : (e.risk_level === 'at_risk' ? Math.ceil((e.active_cases || 0) / 2) : 0)), 0);
    
    // Calculate team average sentiment based on risk distribution
    const totalForAvg = excellentCount + goodCount + opportunityCount;
    const teamAvgSentiment = totalForAvg > 0
        ? (excellentCount * 0.8 + goodCount * 0.6 + opportunityCount * 0.35) / totalForAvg
        : 0.5;
    
    // Team summary with visual chart
    teamSummaryEl.innerHTML = `
        <div class="summary-grid">
            <div class="summary-card highlight">
                <div class="summary-header">
                    <span class="summary-icon">📊</span>
                    <span class="summary-title">Team Sentiment Overview</span>
                    <span class="summary-period">${rangeLabel}</span>
                </div>
                <div class="sentiment-chart-container">
                    <div class="sentiment-donut">
                        <svg viewBox="0 0 100 100" class="donut-chart">
                            ${renderDonutChart(excellentCount, goodCount, opportunityCount, totalActiveCases)}
                        </svg>
                        <div class="donut-center">
                            <span class="donut-value">${Math.round(teamAvgSentiment * 100)}%</span>
                            <span class="donut-label">Team Avg</span>
                        </div>
                    </div>
                    <div class="chart-legend">
                        <div class="legend-item">
                            <span class="legend-dot excellent"></span>
                            <span class="legend-label">Excellent (70%+)</span>
                            <span class="legend-value">${excellentCount}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-dot good"></span>
                            <span class="legend-label">Good (55-70%)</span>
                            <span class="legend-value">${goodCount}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-dot opportunity"></span>
                            <span class="legend-label">Growth Opportunity</span>
                            <span class="legend-value">${opportunityCount}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-header">
                    <span class="summary-icon">👥</span>
                    <span class="summary-title">Team at a Glance</span>
                </div>
                <div class="glance-metrics">
                    <div class="glance-item">
                        <span class="glance-value">${engineers.length}</span>
                        <span class="glance-label">Engineers</span>
                    </div>
                    <div class="glance-item">
                        <span class="glance-value">${totalActiveCases}</span>
                        <span class="glance-label">Active Cases</span>
                    </div>
                    <div class="glance-item">
                        <span class="glance-value">${totalResolvedCases}</span>
                        <span class="glance-label">Resolved (${rangeLabel})</span>
                    </div>
                    <div class="glance-item">
                        <span class="glance-value">${Math.round(totalActiveCases / Math.max(engineers.length, 1))}</span>
                        <span class="glance-label">Avg Active/Engineer</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Engineer cards - using data from fast summary endpoint
    const teamHtml = engineers.map(eng => {
        // Use pre-computed risk_level from fast endpoint
        const riskLevel = eng.risk_level || 'no_cases';
        const activeCases = eng.active_cases || 0;
        const maxDaysComm = eng.max_days_since_comm || 0;
        const avgDaysComm = eng.avg_days_since_comm || 0;
        
        // Use actual sentiment if available, otherwise estimate from risk level
        // null sentiment means no active cases
        const engAvgSentiment = eng.avg_sentiment !== null && eng.avg_sentiment !== undefined
            ? eng.avg_sentiment 
            : (riskLevel === 'critical' ? 0.35 : riskLevel === 'at_risk' ? 0.55 : riskLevel === 'healthy' ? 0.75 : null);
        
        // Supportive status badges based on risk_level
        let statusBadge, statusClass;
        if (riskLevel === 'no_cases' || activeCases === 0) {
            statusBadge = '📋 No Active Cases';
            statusClass = 'badge-neutral';
        } else if (riskLevel === 'healthy') {
            statusBadge = '⭐ Top Performer';
            statusClass = 'badge-excellent';
        } else if (riskLevel === 'at_risk') {
            statusBadge = '⚠️ Needs Attention';
            statusClass = 'badge-good';
        } else if (riskLevel === 'critical') {
            statusBadge = '🚨 Coaching Opportunity';
            statusClass = 'badge-opportunity';
        } else {
            statusBadge = '✓ On Track';
            statusClass = 'badge-good';
        }
        
        // Show communication staleness indicator (only if they have active cases)
        const stalenessIndicator = activeCases > 0 && maxDaysComm >= 7 
            ? `<span class="staleness-warning">⏰ ${maxDaysComm}d since comm</span>`
            : activeCases > 0 && maxDaysComm >= 4
                ? `<span class="staleness-caution">📅 ${maxDaysComm}d since comm</span>`
                : '';
        
        // Sentiment display - show N/A if no active cases
        const sentimentDisplay = engAvgSentiment !== null 
            ? `${Math.round(engAvgSentiment * 100)}%`
            : 'N/A';
        const sentimentWidth = engAvgSentiment !== null ? Math.round(engAvgSentiment * 100) : 0;
        
        return `
            <div class="engineer-card-modern" onclick="viewEngineerDetail('${eng.id}')">
                <div class="eng-card-left">
                    <div class="engineer-avatar-modern">${(eng.name || 'Unknown').split(' ').map(n => n[0]).join('')}</div>
                    <div class="eng-card-info">
                        <div class="eng-card-name">${eng.name || 'Unknown'}</div>
                        <div class="eng-card-meta">${activeCases} active cases • ${eng.team || 'Support'}</div>
                        ${stalenessIndicator}
                    </div>
                </div>
                <div class="eng-card-middle">
                    <div class="eng-sentiment-visual">
                        <div class="eng-sentiment-bar-bg">
                            <div class="eng-sentiment-bar-fill ${engAvgSentiment !== null ? getSentimentClass(engAvgSentiment) : 'neutral'}" style="width: ${sentimentWidth}%"></div>
                        </div>
                        <span class="eng-sentiment-value">${sentimentDisplay}</span>
                    </div>
                    <div class="eng-case-summary">
                        <span class="case-count-badge">${activeCases} active</span>
                        ${(eng.resolved_cases || 0) > 0 ? `<span class="case-count-badge resolved">${eng.resolved_cases} resolved</span>` : ''}
                    </div>
                </div>
                <div class="eng-card-right">
                    <span class="status-badge ${statusClass}">${statusBadge}</span>
                    <span class="view-insights">View Insights →</span>
                </div>
            </div>
        `;
    }).join('');
    
    teamContainerEl.innerHTML = `
        <div class="team-section-header">
            <h3>Team Members</h3>
            <p class="text-muted">Select an engineer to view personalized coaching insights</p>
        </div>
        <div class="engineer-cards-list">
            ${teamHtml || '<p class="text-muted">No team members found.</p>'}
        </div>
    `;
}

function renderDonutChart(excellent, good, opportunity, total) {
    if (total === 0) return '<circle cx="50" cy="50" r="40" fill="none" stroke="#3a3a3a" stroke-width="12"/>';
    
    const excellentPct = excellent / total;
    const goodPct = good / total;
    const opportunityPct = opportunity / total;
    
    const circumference = 2 * Math.PI * 40;
    
    const excellentDash = excellentPct * circumference;
    const goodDash = goodPct * circumference;
    const opportunityDash = opportunityPct * circumference;
    
    let offset = 0;
    const segments = [];
    
    if (excellent > 0) {
        segments.push(`<circle cx="50" cy="50" r="40" fill="none" stroke="#107c10" stroke-width="12" 
            stroke-dasharray="${excellentDash} ${circumference}" 
            stroke-dashoffset="${-offset}" transform="rotate(-90 50 50)"/>`);
        offset += excellentDash;
    }
    if (good > 0) {
        segments.push(`<circle cx="50" cy="50" r="40" fill="none" stroke="#ffb900" stroke-width="12" 
            stroke-dasharray="${goodDash} ${circumference}" 
            stroke-dashoffset="${-offset}" transform="rotate(-90 50 50)"/>`);
        offset += goodDash;
    }
    if (opportunity > 0) {
        segments.push(`<circle cx="50" cy="50" r="40" fill="none" stroke="#0078d4" stroke-width="12" 
            stroke-dasharray="${opportunityDash} ${circumference}" 
            stroke-dashoffset="${-offset}" transform="rotate(-90 50 50)"/>`);
    }
    
    return segments.join('');
}

/**
 * View individual engineer details (for managers)
 * Uses fast engineer summary endpoint for performance
 */
async function viewEngineerDetail(engineerId) {
    state.currentView = 'engineer-detail';
    showLoading(true);
    
    const main = document.getElementById('main-content');
    main.innerHTML = `<div class="loading"><div class="spinner"></div></div>`;
    
    // Use fast engineer summary endpoint
    const summaryData = await getEngineerSummary(engineerId);
    
    if (!summaryData || !summaryData.engineer) {
        showLoading(false);
        main.innerHTML = `
            <div class="card">
                <p class="text-muted">Unable to load engineer details.</p>
                <button class="btn btn-secondary mt-md" onclick="navigateTo('manager')">← Back to Team</button>
            </div>
        `;
        return;
    }
    
    const engineer = summaryData.engineer;
    const allCases = summaryData.cases || [];
    const summary = summaryData.summary || {};
    
    // Separate active vs resolved cases
    const activeCases = allCases.filter(c => c.status === 'active');
    const resolvedCases = allCases.filter(c => c.status === 'resolved');
    
    // For coaching and analysis, focus on ACTIVE cases only
    const engCases = activeCases;
    
    state.selectedEngineer = engineer;
    const dateRange = state.selectedDateRange || '30d';
    const rangeLabel = dateRange === '7d' ? 'Past 7 Days' : dateRange === '30d' ? 'Past 30 Days' : 'Past Quarter';
    
    // Calculate metrics from ACTIVE cases only
    // Map risk_level to sentiment scores for display
    const avgSentiment = activeCases.length > 0
        ? activeCases.reduce((sum, c) => {
            const riskScore = c.risk_level === 'breach' ? 0.25 : c.risk_level === 'at_risk' ? 0.5 : 0.8;
            return sum + riskScore;
        }, 0) / activeCases.length
        : 0.5;
    
    // Count ACTIVE cases by risk level for distribution
    const excellentCases = activeCases.filter(c => c.risk_level === 'healthy');
    const goodCases = activeCases.filter(c => c.risk_level === 'at_risk');
    const opportunityCases = activeCases.filter(c => c.risk_level === 'breach');
    
    // Generate personalized coaching based on actual case data
    const personalizedCoaching = generatePersonalizedCoachingFromSummary(engCases, engineer.name.split(' ')[0]);
    
    // Generate trend data (simulated for demo - would come from API in production)
    const trendData = generateTrendData(engCases, dateRange);
    
    const sentimentClass = getSentimentClass(avgSentiment);
    const firstName = engineer.name.split(' ')[0];
    
    showLoading(false);
    
    main.innerHTML = `
        <div class="content-header">
            <button class="btn btn-ghost mb-sm" onclick="navigateTo('manager')">← Back to Team</button>
            <div class="engineer-profile-header">
                <div class="engineer-avatar-xl">${engineer.name.split(' ').map(n => n[0]).join('')}</div>
                <div class="engineer-profile-info">
                    <h1>${engineer.name}</h1>
                    <p class="subtitle">${engineer.email} • ${engineer.team || 'Support'}</p>
                    <div class="profile-badges">
                        <span class="period-badge">${rangeLabel}</span>
                        <span class="case-count-badge">${activeCases.length} active</span>
                        <span class="case-count-badge resolved">${resolvedCases.length} resolved</span>
                        ${avgSentiment >= 0.7 ? '<span class="achievement-badge">⭐ Top Performer</span>' : ''}
                    </div>
                </div>
                <div class="profile-score">
                    <div class="score-ring ${sentimentClass}">
                        <svg viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="45" fill="none" stroke="#3a3a3a" stroke-width="8"/>
                            <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="8"
                                stroke-dasharray="${avgSentiment * 283} 283" 
                                stroke-linecap="round" transform="rotate(-90 50 50)"/>
                        </svg>
                        <span class="score-text">${Math.round(avgSentiment * 100)}%</span>
                    </div>
                    <span class="score-label">Active Case Sentiment</span>
                </div>
            </div>
        </div>
        
        <!-- Case Summary Cards -->
        <div class="case-summary-row mb-lg">
            <div class="case-summary-card active">
                <div class="summary-number">${activeCases.length}</div>
                <div class="summary-label">Active Cases</div>
                <div class="summary-detail">${opportunityCases.length} need attention</div>
            </div>
            <div class="case-summary-card resolved">
                <div class="summary-number">${resolvedCases.length}</div>
                <div class="summary-label">Resolved</div>
                <div class="summary-detail">This quarter</div>
            </div>
            <div class="case-summary-card total">
                <div class="summary-number">${allCases.length}</div>
                <div class="summary-label">Total Assigned</div>
                <div class="summary-detail">All time</div>
            </div>
        </div>
        
        <!-- Trend Chart Section -->
        <div class="card trend-card mb-lg">
            <div class="trend-header">
                <h3>📈 Sentiment Trend (Active Cases)</h3>
                <span class="trend-period">${rangeLabel}</span>
            </div>
            <div class="trend-chart-container">
                ${renderTrendChart(trendData)}
            </div>
            <div class="trend-summary">
                <div class="trend-stat">
                    <span class="trend-stat-value ${trendData.change >= 0 ? 'positive' : 'negative'}">
                        ${trendData.change >= 0 ? '↑' : '↓'} ${Math.abs(trendData.change)}%
                    </span>
                    <span class="trend-stat-label">vs Previous Period</span>
                </div>
                <div class="trend-stat">
                    <span class="trend-stat-value">${trendData.highPoint}%</span>
                    <span class="trend-stat-label">Period High</span>
                </div>
                <div class="trend-stat">
                    <span class="trend-stat-value">${trendData.lowPoint}%</span>
                    <span class="trend-stat-label">Period Low</span>
                </div>
            </div>
        </div>
        
        <div class="two-column">
            <div class="main-column">
                <!-- Personalized Coaching Section -->
                <div class="card coaching-card-main mb-lg">
                    <div class="coaching-header">
                        <h3>💡 Personalized Coaching Insights</h3>
                        <p class="text-muted">Based on ${firstName}'s specific case interactions during ${rangeLabel.toLowerCase()}</p>
                    </div>
                    
                    ${personalizedCoaching.length > 0 ? `
                        <div class="coaching-insights-list">
                            ${personalizedCoaching.map((insight, i) => `
                                <div class="coaching-insight-card">
                                    <div class="insight-header">
                                        <span class="insight-icon">${insight.icon}</span>
                                        <span class="insight-category">${insight.category}</span>
                                        ${insight.caseId ? `<span class="insight-case-ref">Case: ${insight.caseId}</span>` : ''}
                                    </div>
                                    <div class="insight-observation">
                                        <strong>Observation:</strong> ${insight.observation}
                                    </div>
                                    <div class="insight-suggestion">
                                        <strong>Coaching Point:</strong> ${insight.suggestion}
                                    </div>
                                    ${insight.example ? `
                                        <div class="insight-example">
                                            <strong>Try saying:</strong> <em>"${insight.example}"</em>
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div class="no-coaching-needed">
                            <span class="success-icon">✨</span>
                            <h4>${firstName} is doing great!</h4>
                            <p>No specific coaching points needed. Consider recognizing their excellent customer interactions.</p>
                        </div>
                    `}
                </div>
                
                <!-- 1:1 Conversation Guide -->
                <div class="card mb-lg">
                    <h3>🗣️ 1:1 Conversation Guide</h3>
                    <div class="conversation-guide mt-md">
                        ${generateConversationGuide(firstName, personalizedCoaching, avgSentiment, engCases)}
                    </div>
                </div>
            </div>
            
            <div class="sidebar">
                <!-- Case Distribution -->
                <div class="card mb-lg">
                    <h3>📊 Active Case Distribution</h3>
                    <p class="text-muted text-small">${activeCases.length} active cases</p>
                    <div class="distribution-visual mt-md">
                        <div class="dist-bar">
                            <div class="dist-segment excellent" style="width: ${(excellentCases.length / Math.max(activeCases.length, 1)) * 100}%"></div>
                            <div class="dist-segment good" style="width: ${(goodCases.length / Math.max(activeCases.length, 1)) * 100}%"></div>
                            <div class="dist-segment opportunity" style="width: ${(opportunityCases.length / Math.max(activeCases.length, 1)) * 100}%"></div>
                        </div>
                        <div class="dist-legend">
                            <div class="dist-item">
                                <span class="dist-dot excellent"></span>
                                <span>Healthy: ${excellentCases.length}</span>
                            </div>
                            <div class="dist-item">
                                <span class="dist-dot good"></span>
                                <span>At Risk: ${goodCases.length}</span>
                            </div>
                            <div class="dist-item">
                                <span class="dist-dot opportunity"></span>
                                <span>Breach: ${opportunityCases.length}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Strengths & Recognition -->
                <div class="card mb-lg">
                    <h3>🌟 Strengths to Recognize</h3>
                    <div class="strengths-list mt-md">
                        ${generateStrengths(activeCases, firstName)}
                    </div>
                </div>
                
                <!-- Quick Stats -->
                <div class="card">
                    <h3>📈 Quick Stats</h3>
                    <div class="quick-stats mt-md">
                        <div class="stat-row">
                            <span class="stat-label">Active Cases</span>
                            <span class="stat-value">${activeCases.length}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Resolved This Quarter</span>
                            <span class="stat-value">${resolvedCases.length}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Avg Response Time</span>
                            <span class="stat-value">${calculateAvgResponseTime(activeCases)}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Cases 70%+ Sentiment</span>
                            <span class="stat-value">${excellentCases.length}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    updateBreadcrumb([
        { text: 'Team Performance', action: "navigateTo('manager')" },
        { text: engineer.name }
    ]);
    
    showLoading(false);
}

/**
 * Generate personalized coaching insights based on actual case data
 */
function generatePersonalizedCoaching(cases, firstName) {
    const insights = [];
    
    // Analyze cases for specific patterns
    const slowResponseCases = cases.filter(c => (c.days_since_last_outbound || c.days_since_comm || 0) > 2);
    const staleNotesCases = cases.filter(c => (c.days_since_last_note || c.days_since_note || 0) > 5);
    const lowSentimentCases = cases.filter(c => (c.sentiment_score || 0.5) < 0.4 || c.risk_level === 'breach');
    const highSevDelayed = cases.filter(c => {
        const sev = formatSeverity(c.severity || c.priority);
        return (sev === 'A' || sev === 'B') && (c.days_open || 0) > 7;
    });
    
    // Generate specific insights with case references
    if (slowResponseCases.length > 0) {
        const worstCase = slowResponseCases.sort((a, b) => (b.days_since_last_outbound || b.days_since_comm || 0) - (a.days_since_last_outbound || a.days_since_comm || 0))[0];
        const daysComm = worstCase.days_since_last_outbound || worstCase.days_since_comm || 0;
        insights.push({
            icon: '⏰',
            category: 'Response Timeliness',
            caseId: worstCase.id,
            observation: `${slowResponseCases.length} case${slowResponseCases.length > 1 ? 's have' : ' has'} gone ${Math.round(daysComm)}+ days without customer communication. ${worstCase.customer?.company || worstCase.customer_name || 'The customer'} on case ${worstCase.id} may be wondering about status.`,
            suggestion: `Discuss with ${firstName} about setting daily check-in reminders. Even a brief "still investigating" update maintains customer confidence.`,
            example: `I noticed case ${worstCase.id} hasn't had a customer touchpoint recently. What's blocking progress there? How can I help?`
        });
    }
    
    if (lowSentimentCases.length > 0) {
        const lowestCase = lowSentimentCases[0];
        const sentimentPct = lowestCase.sentiment_score ? Math.round(lowestCase.sentiment_score * 100) : (lowestCase.risk_level === 'breach' ? 25 : 40);
        insights.push({
            icon: '💬',
            category: 'Customer Sentiment',
            caseId: lowestCase.id,
            observation: `Case ${lowestCase.id} (${lowestCase.customer?.company || lowestCase.customer_name || 'customer'}) shows ${sentimentPct}% sentiment. The customer may be experiencing frustration with "${lowestCase.title?.substring(0, 50) || 'their issue'}".`,
            suggestion: `Explore what's driving the frustration. Sometimes acknowledging the customer's situation directly can help reset the relationship.`,
            example: `Tell me about ${lowestCase.id} - I see the customer might be struggling. What's happening from your perspective?`
        });
    }
    
    if (staleNotesCases.length > 0) {
        const stalestCase = staleNotesCases.sort((a, b) => (b.days_since_last_note || b.days_since_note || 0) - (a.days_since_last_note || a.days_since_note || 0))[0];
        const daysNote = stalestCase.days_since_last_note || stalestCase.days_since_note || 0;
        insights.push({
            icon: '📝',
            category: 'Documentation',
            caseId: stalestCase.id,
            observation: `${staleNotesCases.length} case${staleNotesCases.length > 1 ? 's' : ''} with notes older than 5 days. Case ${stalestCase.id} hasn't been updated in ${Math.round(daysNote)} days.`,
            suggestion: `Current notes help with handoffs and compliance. Consider end-of-day note updates as a habit.`,
            example: `How's your case documentation going? I want to make sure you're set up for success if you need to hand anything off.`
        });
    }
    
    if (highSevDelayed.length > 0) {
        const oldestHighSev = highSevDelayed.sort((a, b) => (b.days_open || 0) - (a.days_open || 0))[0];
        insights.push({
            icon: '🎯',
            category: 'Priority Management',
            caseId: oldestHighSev.id,
            observation: `Sev ${formatSeverity(oldestHighSev.severity || oldestHighSev.priority)} case ${oldestHighSev.id} has been open ${Math.round(oldestHighSev.days_open || 0)} days. High-severity cases benefit from accelerated focus.`,
            suggestion: `Review if there are blockers preventing resolution. Consider if escalation or additional resources would help.`,
            example: `I see ${oldestHighSev.id} is a Sev ${formatSeverity(oldestHighSev.severity || oldestHighSev.priority)} that's been open a while. Are you blocked on anything? Do you need me to pull in anyone else?`
        });
    }
    
    return insights.slice(0, 4); // Max 4 insights
}

/**
 * Generate personalized coaching from fast summary endpoint data
 * Works with the simplified case objects from /api/engineer/{id}/summary
 */
function generatePersonalizedCoachingFromSummary(cases, firstName) {
    const insights = [];
    
    // Filter to only active cases
    const activeCases = cases.filter(c => c.status === 'active');
    
    // Analyze cases using summary endpoint fields
    const slowResponseCases = activeCases.filter(c => (c.days_since_comm || 0) > 2);
    const staleNotesCases = activeCases.filter(c => (c.days_since_note || 0) > 5);
    const breachCases = activeCases.filter(c => c.risk_level === 'breach');
    const atRiskCases = activeCases.filter(c => c.risk_level === 'at_risk');
    
    // Generate specific insights
    if (slowResponseCases.length > 0) {
        const worstCase = slowResponseCases.sort((a, b) => (b.days_since_comm || 0) - (a.days_since_comm || 0))[0];
        insights.push({
            icon: '⏰',
            category: 'Response Timeliness',
            caseId: worstCase.id,
            observation: `${slowResponseCases.length} case${slowResponseCases.length > 1 ? 's have' : ' has'} gone ${worstCase.days_since_comm}+ days without customer communication. ${worstCase.customer_name || 'The customer'} on case ${worstCase.id} may be wondering about status.`,
            suggestion: `Discuss with ${firstName} about setting daily check-in reminders. Even a brief "still investigating" update maintains customer confidence.`,
            example: `I noticed case ${worstCase.id} hasn't had a customer touchpoint recently. What's blocking progress there? How can I help?`
        });
    }
    
    if (breachCases.length > 0) {
        const worstCase = breachCases[0];
        insights.push({
            icon: '🚨',
            category: 'Critical Attention Needed',
            caseId: worstCase.id,
            observation: `Case ${worstCase.id} (${worstCase.customer_name || 'customer'}) is in breach state - ${worstCase.days_since_comm || worstCase.days_since_note || 7}+ days without activity. This needs immediate attention.`,
            suggestion: `Prioritize reaching out to this customer today. Even a brief status update can prevent escalation.`,
            example: `I see ${worstCase.id} needs urgent attention. What do you need from me to unblock this?`
        });
    }
    
    if (staleNotesCases.length > 0) {
        const stalestCase = staleNotesCases.sort((a, b) => (b.days_since_note || 0) - (a.days_since_note || 0))[0];
        insights.push({
            icon: '📝',
            category: 'Documentation',
            caseId: stalestCase.id,
            observation: `${staleNotesCases.length} case${staleNotesCases.length > 1 ? 's' : ''} with notes older than 5 days. Case ${stalestCase.id} hasn't been updated in ${stalestCase.days_since_note} days.`,
            suggestion: `Current notes help with handoffs and compliance. Consider end-of-day note updates as a habit.`,
            example: `How's your case documentation going? I want to make sure you're set up for success if you need to hand anything off.`
        });
    }
    
    if (atRiskCases.length > 0 && insights.length < 4) {
        insights.push({
            icon: '⚠️',
            category: 'At Risk Cases',
            observation: `${atRiskCases.length} case${atRiskCases.length > 1 ? 's are' : ' is'} approaching SLA thresholds. Cases: ${atRiskCases.slice(0, 3).map(c => c.id).join(', ')}${atRiskCases.length > 3 ? '...' : ''}`,
            suggestion: `Review these cases together and identify any blockers. Proactive updates now can prevent customer frustration.`,
            example: `Let's look at your at-risk cases together. Are there any patterns or blockers I can help with?`
        });
    }
    
    return insights.slice(0, 4); // Max 4 insights
}

/**
 * Generate trend data for visualization
 */
function generateTrendData(cases, dateRange) {
    const points = dateRange === '7d' ? 7 : dateRange === '30d' ? 6 : 12;
    const avgSentiment = cases.length > 0
        ? cases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / cases.length
        : 0.5;
    
    // Simulate trend data (in production, this would come from historical API data)
    const data = [];
    let baseValue = avgSentiment * 100;
    
    for (let i = 0; i < points; i++) {
        const variance = (Math.random() - 0.5) * 15;
        const value = Math.max(20, Math.min(95, baseValue + variance));
        data.push(Math.round(value));
        baseValue = value; // Random walk
    }
    
    return {
        points: data,
        change: data.length > 1 ? data[data.length - 1] - data[0] : 0,
        highPoint: Math.max(...data),
        lowPoint: Math.min(...data),
        labels: dateRange === '7d' 
            ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            : dateRange === '30d'
            ? ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6']
            : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].slice(0, 12)
    };
}

/**
 * Render SVG trend chart
 */
function renderTrendChart(trendData) {
    const width = 600;
    const height = 150;
    const padding = 30;
    const points = trendData.points;
    const labels = trendData.labels;
    
    if (points.length === 0) return '<p class="text-muted">No trend data available</p>';
    
    const xStep = (width - padding * 2) / (points.length - 1);
    const yScale = (height - padding * 2) / 100;
    
    // Generate path
    const pathPoints = points.map((val, i) => {
        const x = padding + i * xStep;
        const y = height - padding - (val * yScale);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
    
    // Generate gradient area
    const areaPath = pathPoints + ` L ${padding + (points.length - 1) * xStep} ${height - padding} L ${padding} ${height - padding} Z`;
    
    // Generate dots and labels
    const dotsAndLabels = points.map((val, i) => {
        const x = padding + i * xStep;
        const y = height - padding - (val * yScale);
        return `
            <circle cx="${x}" cy="${y}" r="4" fill="#0078d4"/>
            <text x="${x}" y="${height - 5}" text-anchor="middle" class="chart-label">${labels[i] || ''}</text>
        `;
    }).join('');
    
    return `
        <svg viewBox="0 0 ${width} ${height}" class="trend-chart-svg">
            <defs>
                <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#0078d4;stop-opacity:0.3"/>
                    <stop offset="100%" style="stop-color:#0078d4;stop-opacity:0"/>
                </linearGradient>
            </defs>
            <!-- Grid lines -->
            <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="#3a3a3a" stroke-width="1"/>
            <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#3a3a3a" stroke-width="1"/>
            <!-- Area fill -->
            <path d="${areaPath}" fill="url(#trendGradient)"/>
            <!-- Line -->
            <path d="${pathPoints}" fill="none" stroke="#0078d4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <!-- Dots and labels -->
            ${dotsAndLabels}
        </svg>
    `;
}

/**
 * Generate conversation guide for 1:1s
 */
function generateConversationGuide(firstName, insights, avgSentiment, cases) {
    const sections = [];
    
    // Opening
    if (avgSentiment >= 0.7) {
        sections.push(`
            <div class="guide-section positive">
                <h4>🎉 Start with Recognition</h4>
                <p>"${firstName}, I wanted to start by saying your customer sentiment scores have been excellent. Your customers clearly appreciate your work. What do you think is working well?"</p>
            </div>
        `);
    } else if (avgSentiment >= 0.5) {
        sections.push(`
            <div class="guide-section neutral">
                <h4>👋 Opening</h4>
                <p>"${firstName}, thanks for making time for our 1:1. I'd like to talk about your caseload and see how I can better support you. How are things going from your perspective?"</p>
            </div>
        `);
    } else {
        sections.push(`
            <div class="guide-section supportive">
                <h4>🤝 Supportive Opening</h4>
                <p>"${firstName}, I appreciate you. I know you've had some challenging cases lately, and I want to make sure you have the support you need. Let's talk about what's going on and how I can help."</p>
            </div>
        `);
    }
    
    // Specific discussion points from insights
    if (insights.length > 0) {
        const discussionPoints = insights.slice(0, 2).map(i => `
            <li><strong>${i.category}:</strong> "${i.example}"</li>
        `).join('');
        
        sections.push(`
            <div class="guide-section discussion">
                <h4>💬 Discussion Points</h4>
                <ul>${discussionPoints}</ul>
            </div>
        `);
    }
    
    // Closing
    sections.push(`
        <div class="guide-section closing">
            <h4>✅ Closing</h4>
            <p>"What's one thing I can do this week to help you be more successful? And what's one thing you're going to focus on?"</p>
        </div>
    `);
    
    return sections.join('');
}

/**
 * Generate strengths based on case performance
 */
function generateStrengths(cases, firstName) {
    const strengths = [];
    
    const excellentCases = cases.filter(c => (c.sentiment_score || 0.5) >= 0.7);
    const quickResponders = cases.filter(c => (c.days_since_last_outbound || 0) <= 1);
    const wellDocumented = cases.filter(c => (c.days_since_last_note || 0) <= 2);
    
    if (excellentCases.length >= cases.length * 0.5) {
        strengths.push({ icon: '⭐', text: 'Consistently high customer satisfaction' });
    }
    if (quickResponders.length >= cases.length * 0.6) {
        strengths.push({ icon: '⚡', text: 'Excellent response timeliness' });
    }
    if (wellDocumented.length >= cases.length * 0.5) {
        strengths.push({ icon: '📋', text: 'Strong case documentation habits' });
    }
    if (cases.length > 5) {
        strengths.push({ icon: '💪', text: 'Managing high case volume effectively' });
    }
    
    if (strengths.length === 0) {
        strengths.push({ icon: '🌱', text: 'Growing and developing skills' });
    }
    
    return strengths.map(s => `
        <div class="strength-item">
            <span class="strength-icon">${s.icon}</span>
            <span class="strength-text">${s.text}</span>
        </div>
    `).join('');
}

/**
 * Calculate average response time
 */
function calculateAvgResponseTime(cases) {
    if (cases.length === 0) return 'N/A';
    const avgDays = cases.reduce((sum, c) => sum + (c.days_since_last_outbound || 0), 0) / cases.length;
    if (avgDays < 1) return '< 1 day';
    return `${avgDays.toFixed(1)} days`;
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
        
        // Initialize feedback button listener
        initFeedbackSystem();
        
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

// =============================================================================
// Feedback System
// =============================================================================

let selectedFeedbackRating = null;

/**
 * Initialize the feedback system event listeners
 */
function initFeedbackSystem() {
    const feedbackBtn = document.getElementById('feedback-btn');
    if (feedbackBtn) {
        feedbackBtn.addEventListener('click', openFeedbackModal);
    }
    
    // Close modal on overlay click
    const modal = document.getElementById('feedback-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeFeedbackModal();
            }
        });
    }
    
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeFeedbackModal();
        }
    });
}

/**
 * Open the feedback modal
 */
function openFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Reset form
        selectedFeedbackRating = null;
        document.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
        document.getElementById('feedback-text').value = '';
        document.getElementById('feedback-category').value = 'general';
        document.getElementById('submit-feedback-btn').disabled = true;
    }
}

/**
 * Close the feedback modal
 */
function closeFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

/**
 * Select a feedback rating (thumbs up/down)
 */
function selectRating(rating) {
    selectedFeedbackRating = rating;
    
    // Update button states
    document.querySelectorAll('.rating-btn').forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.rating === rating);
    });
    
    // Enable submit button
    document.getElementById('submit-feedback-btn').disabled = false;
}

/**
 * Submit feedback to the API
 */
async function submitFeedback() {
    if (!selectedFeedbackRating) {
        alert('Please select a rating (thumbs up or down)');
        return;
    }
    
    const comment = document.getElementById('feedback-text').value.trim();
    const category = document.getElementById('feedback-category').value;
    
    const submitBtn = document.getElementById('submit-feedback-btn');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                rating: selectedFeedbackRating,
                comment: comment || null,
                category: category,
                page: state.currentView,
                engineer_id: state.currentEngineer?.id || null,
                user_agent: navigator.userAgent,
            }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit feedback');
        }
        
        const result = await response.json();
        
        // Show success message
        closeFeedbackModal();
        showToast('Thank you for your feedback! 🎉', 'success');
        
    } catch (error) {
        console.error('Error submitting feedback:', error);
        showToast('Failed to submit feedback. Please try again.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('toast-fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}
