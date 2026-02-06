/**
 * CSAT Guardian - Frontend Application
 * Microsoft Learn-inspired UI for CSAT case management
 * ULTRA PREMIUM EDITION - Mobile, Filtering, Export, WOW Effects
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
    filteredCases: [],  // For filtered view
    engineers: [],
    isLoading: false,
    backendStatus: 'checking',  // checking, online, offline
    chatHistory: [],
    theme: localStorage.getItem('csat-theme') || 'dark',
    mobileMenuOpen: false,
    // Filter state
    filters: {
        search: '',
        severity: 'all',
        sentiment: 'all',
        daysInactive: 'all',
        status: 'all'
    },
    particles: [],
};

// =============================================================================
// Theme Management
// =============================================================================

/**
 * Initialize theme based on stored preference
 */
function initializeTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeToggle();
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('csat-theme', state.theme);
    updateThemeToggle();
    
    // Add a little celebration effect
    createRippleEffect(document.querySelector('.theme-toggle-nav'));
}

/**
 * Update theme toggle button appearance
 */
function updateThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    const mobileIcon = document.getElementById('mobile-theme-icon');
    const mobileLabel = document.getElementById('mobile-theme-label');
    
    if (toggle) {
        toggle.innerHTML = `<span class="theme-icon">${state.theme === 'dark' ? '☀️' : '🌙'}</span>`;
        toggle.title = state.theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
    }
    
    if (mobileIcon) {
        mobileIcon.textContent = state.theme === 'dark' ? '☀️' : '🌙';
    }
    
    if (mobileLabel) {
        mobileLabel.textContent = state.theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
}

// =============================================================================
// Mobile Menu Management
// =============================================================================

/**
 * Toggle mobile menu
 */
function toggleMobileMenu() {
    state.mobileMenuOpen = !state.mobileMenuOpen;
    
    const menuBtn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    const overlay = document.getElementById('mobile-nav-overlay');
    
    if (menuBtn) menuBtn.classList.toggle('active', state.mobileMenuOpen);
    if (menu) menu.classList.toggle('active', state.mobileMenuOpen);
    if (overlay) overlay.classList.toggle('active', state.mobileMenuOpen);
    
    // Prevent body scroll when menu is open
    document.body.style.overflow = state.mobileMenuOpen ? 'hidden' : '';
}

/**
 * Close mobile menu
 */
function closeMobileMenu() {
    if (state.mobileMenuOpen) {
        toggleMobileMenu();
    }
}

// =============================================================================
// Particle System - WOW Effect
// =============================================================================

/**
 * Initialize particle canvas
 */
function initParticles() {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let animationId;
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    function createParticle() {
        return {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 2 + 0.5,
            speedX: (Math.random() - 0.5) * 0.5,
            speedY: (Math.random() - 0.5) * 0.5,
            opacity: Math.random() * 0.5 + 0.2,
            hue: Math.random() * 60 + 180 // Blue to cyan range
        };
    }
    
    // Create initial particles
    for (let i = 0; i < 50; i++) {
        state.particles.push(createParticle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        state.particles.forEach((particle, index) => {
            // Update position
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            
            // Wrap around edges
            if (particle.x < 0) particle.x = canvas.width;
            if (particle.x > canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = canvas.height;
            if (particle.y > canvas.height) particle.y = 0;
            
            // Draw particle
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${particle.hue}, 70%, 60%, ${particle.opacity})`;
            ctx.fill();
            
            // Draw connections to nearby particles
            state.particles.forEach((other, otherIndex) => {
                if (index === otherIndex) return;
                const dx = particle.x - other.x;
                const dy = particle.y - other.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 150) {
                    ctx.beginPath();
                    ctx.moveTo(particle.x, particle.y);
                    ctx.lineTo(other.x, other.y);
                    ctx.strokeStyle = `hsla(${particle.hue}, 70%, 60%, ${0.1 * (1 - distance / 150)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            });
        });
        
        animationId = requestAnimationFrame(animate);
    }
    
    resize();
    window.addEventListener('resize', resize);
    animate();
    
    // Cleanup function
    return () => {
        cancelAnimationFrame(animationId);
        window.removeEventListener('resize', resize);
    };
}

/**
 * Create ripple effect on element
 */
function createRippleEffect(element) {
    if (!element) return;
    
    const ripple = document.createElement('span');
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        pointer-events: none;
        animation: ripple 0.6s linear;
    `;
    
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = '50%';
    ripple.style.top = '50%';
    ripple.style.transform = 'translate(-50%, -50%) scale(0)';
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
}

/**
 * Create celebration confetti
 */
function celebrateSuccess() {
    const colors = ['#0078d4', '#50e6ff', '#00d26a', '#a855f7', '#ffb900'];
    const container = document.createElement('div');
    container.className = 'success-celebration';
    document.body.appendChild(container);
    
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti-piece';
        confetti.style.cssText = `
            left: ${Math.random() * 100}%;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            animation-delay: ${Math.random() * 0.5}s;
            animation-duration: ${2 + Math.random() * 2}s;
        `;
        container.appendChild(confetti);
    }
    
    setTimeout(() => container.remove(), 4000);
}

// =============================================================================
// CSAT Prediction Engine
// =============================================================================

/**
 * Calculate predicted CSAT score for a case
 * Uses multiple signals to estimate likely CSAT outcome
 */
function calculateCSATPrediction(caseData) {
    // Base score from current sentiment (40% weight)
    const sentiment = caseData.sentiment_score || 0.5;
    let score = sentiment * 4; // Scale 0-1 to 0-4
    
    // Adjustment factors
    const factors = [];
    
    // Response time factor (20% weight)
    const daysComm = caseData.days_since_last_outbound || 0;
    if (daysComm <= 1) {
        score += 0.4;
        factors.push({ text: 'Fast response time', positive: true });
    } else if (daysComm > 3) {
        score -= 0.3 * Math.min(daysComm - 3, 3);
        factors.push({ text: `${daysComm} days since last communication`, positive: false });
    }
    
    // Severity handling factor (15% weight)
    const sev = formatSeverity(caseData.severity);
    const daysOpen = caseData.days_open || caseData.days_since_creation || 0;
    if (sev === 'A' && daysOpen > 3) {
        score -= 0.5;
        factors.push({ text: 'Sev A case open longer than expected', positive: false });
    } else if (sev === 'A' && daysOpen <= 3) {
        factors.push({ text: 'Sev A handled promptly', positive: true });
    }
    
    // Sentiment trend factor (15% weight)
    if (caseData.sentiment_trend === 'improving') {
        score += 0.3;
        factors.push({ text: 'Customer sentiment improving', positive: true });
    } else if (caseData.sentiment_trend === 'declining') {
        score -= 0.4;
        factors.push({ text: 'Customer sentiment declining', positive: false });
    }
    
    // Note freshness factor (10% weight)
    const daysNote = caseData.days_since_last_note || 0;
    if (daysNote > 7) {
        score -= 0.2;
        factors.push({ text: 'Case notes need updating', positive: false });
    }
    
    // Clamp score to 1-5 range
    score = Math.max(1, Math.min(5, score + 1));
    
    // Determine confidence level
    let confidence = 'Medium';
    if (sentiment > 0.7 || sentiment < 0.3) {
        confidence = 'High';
    }
    if (daysOpen < 2) {
        confidence = 'Low'; // Not enough history
    }
    
    return {
        score: Math.round(score * 10) / 10,
        factors: factors.slice(0, 4),
        confidence,
        trend: caseData.sentiment_trend || 'stable'
    };
}

/**
 * Render CSAT prediction card for case detail view
 */
function renderCSATPrediction(caseData) {
    const prediction = calculateCSATPrediction(caseData);
    const scoreClass = prediction.score >= 4 ? 'success' : prediction.score >= 3 ? 'warning' : 'danger';
    
    return `
        <div class="csat-prediction">
            <div class="csat-prediction-header">
                <span>🔮</span>
                <span>Predicted CSAT Score</span>
                <span class="badge badge-${prediction.confidence === 'High' ? 'success' : prediction.confidence === 'Medium' ? 'info' : 'neutral'}">${prediction.confidence} Confidence</span>
            </div>
            <div class="csat-prediction-score">
                <span class="csat-prediction-value" style="color: var(--accent-${scoreClass})">${prediction.score}</span>
                <span class="csat-prediction-max">/ 5</span>
            </div>
            <div class="csat-prediction-label">Based on current sentiment and case activity</div>
            ${prediction.factors.length > 0 ? `
                <div class="csat-prediction-factors">
                    ${prediction.factors.map(f => `
                        <div class="prediction-factor ${f.positive ? 'positive' : 'negative'}">
                            <span>${f.positive ? '✓' : '✗'}</span>
                            <span>${f.text}</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// =============================================================================
// Success Story Detection
// =============================================================================

/**
 * Detect if a case qualifies as a success story
 * Success stories show significant improvement or exemplary handling
 */
function isSuccessStory(caseData) {
    // Criteria for success story:
    // 1. Current sentiment >= 0.75
    // 2. Sentiment improved OR consistently high
    // 3. Case handled within expected timeframe for severity
    
    const sentiment = caseData.sentiment_score || 0.5;
    const trend = caseData.sentiment_trend || 'stable';
    const daysOpen = caseData.days_open || caseData.days_since_creation || 0;
    const sev = formatSeverity(caseData.severity);
    
    if (sentiment < 0.7) return false;
    
    // Significant improvement
    if (trend === 'improving' && sentiment >= 0.75) return true;
    
    // Consistently excellent handling
    if (sentiment >= 0.85 && trend !== 'declining') return true;
    
    // Fast resolution of high-severity case
    if ((sev === 'A' || sev === 'B') && daysOpen <= 5 && sentiment >= 0.7) return true;
    
    return false;
}

/**
 * Get success story details
 */
function getSuccessStoryDetails(caseData) {
    const sentiment = caseData.sentiment_score || 0.5;
    const trend = caseData.sentiment_trend || 'stable';
    const daysOpen = caseData.days_open || caseData.days_since_creation || 0;
    const sev = formatSeverity(caseData.severity);
    
    let reason = '';
    if (trend === 'improving') {
        reason = 'Customer sentiment significantly improved during this case - great recovery!';
    } else if (sentiment >= 0.85) {
        reason = 'Consistently high customer satisfaction throughout the case lifecycle.';
    } else if ((sev === 'A' || sev === 'B') && daysOpen <= 5) {
        reason = `Quick resolution of Severity ${sev} case with excellent customer satisfaction.`;
    }
    
    return {
        sentimentStart: Math.round((sentiment - 0.15) * 100), // Estimate
        sentimentEnd: Math.round(sentiment * 100),
        improvement: trend === 'improving' ? '+15%' : 'Stable',
        reason
    };
}

/**
 * Render success story highlight card
 */
function renderSuccessStoryCard(caseData) {
    if (!isSuccessStory(caseData)) return '';
    
    const details = getSuccessStoryDetails(caseData);
    
    return `
        <div class="success-story-card">
            <div class="success-story-header">
                <span>🌟</span>
                <span>Success Story</span>
                <span class="badge badge-success-story">Exemplary Case</span>
            </div>
            <div class="success-story-metrics">
                <div class="success-metric">
                    <div class="success-metric-value" style="color: var(--accent-success)">${details.sentimentEnd}%</div>
                    <div class="success-metric-label">Final Sentiment</div>
                </div>
                <div class="success-metric">
                    <div class="success-metric-value" style="color: var(--accent-info)">${details.improvement}</div>
                    <div class="success-metric-label">Improvement</div>
                </div>
            </div>
            <div class="success-story-detail">${details.reason}</div>
        </div>
    `;
}

// =============================================================================
// Live Sentiment Indicators
// =============================================================================

/**
 * Get live pulse class for sentiment-based animations
 */
function getLivePulseClass(caseData) {
    const sentiment = caseData.sentiment_score || 0.5;
    const trend = caseData.sentiment_trend || 'stable';
    
    // Critical: Low sentiment AND declining
    if (sentiment < 0.35 && trend === 'declining') {
        return 'live-pulse-critical';
    }
    
    // Warning: Low sentiment OR declining from moderate
    if (sentiment < 0.4 || (sentiment < 0.55 && trend === 'declining')) {
        return 'live-pulse-warning';
    }
    
    return '';
}

// =============================================================================
// Filter & Search System
// =============================================================================

/**
 * Render the filter bar for case list
 */
function renderFilterBar(cases) {
    const activeCases = cases.filter(c => c.status === 'active');
    const criticalCount = activeCases.filter(c => (c.sentiment_score || 0.5) < 0.35).length;
    const atRiskCount = activeCases.filter(c => {
        const s = c.sentiment_score || 0.5;
        return s >= 0.35 && s < 0.55;
    }).length;
    const healthyCount = activeCases.length - criticalCount - atRiskCount;
    
    return `
        <div class="filter-bar">
            <div class="filter-group search-group">
                <label class="filter-label">Search Cases</label>
                <div class="search-input-wrapper">
                    <span class="search-icon">🔍</span>
                    <input type="text" 
                           class="filter-input" 
                           id="filter-search" 
                           placeholder="Search by case ID, title, or customer..."
                           value="${state.filters.search}"
                           onkeyup="applyFilters()">
                </div>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">Severity</label>
                <select class="filter-select" id="filter-severity" onchange="applyFilters()">
                    <option value="all" ${state.filters.severity === 'all' ? 'selected' : ''}>All Severities</option>
                    <option value="A" ${state.filters.severity === 'A' ? 'selected' : ''}>Sev A (Critical)</option>
                    <option value="B" ${state.filters.severity === 'B' ? 'selected' : ''}>Sev B (High)</option>
                    <option value="C" ${state.filters.severity === 'C' ? 'selected' : ''}>Sev C (Standard)</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">Sentiment Status</label>
                <select class="filter-select" id="filter-sentiment" onchange="applyFilters()">
                    <option value="all" ${state.filters.sentiment === 'all' ? 'selected' : ''}>All Statuses</option>
                    <option value="critical" ${state.filters.sentiment === 'critical' ? 'selected' : ''}>🚨 Critical (&lt;35%)</option>
                    <option value="at-risk" ${state.filters.sentiment === 'at-risk' ? 'selected' : ''}>⚠️ At Risk (35-55%)</option>
                    <option value="healthy" ${state.filters.sentiment === 'healthy' ? 'selected' : ''}>✅ Healthy (&gt;55%)</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">Days Inactive</label>
                <select class="filter-select" id="filter-days" onchange="applyFilters()">
                    <option value="all" ${state.filters.daysInactive === 'all' ? 'selected' : ''}>All</option>
                    <option value="3" ${state.filters.daysInactive === '3' ? 'selected' : ''}>&gt;3 days</option>
                    <option value="5" ${state.filters.daysInactive === '5' ? 'selected' : ''}>&gt;5 days</option>
                    <option value="7" ${state.filters.daysInactive === '7' ? 'selected' : ''}>&gt;7 days</option>
                </select>
            </div>
            
            <div class="filter-actions">
                <button class="filter-btn" onclick="clearFilters()" title="Clear all filters">
                    ✕ Clear
                </button>
                <button class="filter-btn btn-glow" onclick="openExportModal()" title="Export cases">
                    📊 Export
                </button>
            </div>
        </div>
        
        <div class="quick-filters">
            <button class="quick-filter-pill ${state.filters.sentiment === 'all' ? 'active' : ''}" onclick="quickFilter('all')">
                All <span class="count">${activeCases.length}</span>
            </button>
            <button class="quick-filter-pill ${state.filters.sentiment === 'critical' ? 'active' : ''}" onclick="quickFilter('critical')">
                🚨 Critical <span class="count">${criticalCount}</span>
            </button>
            <button class="quick-filter-pill ${state.filters.sentiment === 'at-risk' ? 'active' : ''}" onclick="quickFilter('at-risk')">
                ⚠️ At Risk <span class="count">${atRiskCount}</span>
            </button>
            <button class="quick-filter-pill ${state.filters.sentiment === 'healthy' ? 'active' : ''}" onclick="quickFilter('healthy')">
                ✅ Healthy <span class="count">${healthyCount}</span>
            </button>
        </div>
    `;
}

/**
 * Apply filters to the case list
 */
function applyFilters() {
    // Get filter values
    state.filters.search = (document.getElementById('filter-search')?.value || '').toLowerCase();
    state.filters.severity = document.getElementById('filter-severity')?.value || 'all';
    state.filters.sentiment = document.getElementById('filter-sentiment')?.value || 'all';
    state.filters.daysInactive = document.getElementById('filter-days')?.value || 'all';
    
    // Filter cases
    const activeCases = state.cases.filter(c => c.status === 'active');
    
    state.filteredCases = activeCases.filter(caseData => {
        // Search filter
        if (state.filters.search) {
            const searchStr = state.filters.search;
            const matchesSearch = 
                (caseData.id?.toLowerCase().includes(searchStr)) ||
                (caseData.title?.toLowerCase().includes(searchStr)) ||
                (caseData.customer?.company?.toLowerCase().includes(searchStr));
            if (!matchesSearch) return false;
        }
        
        // Severity filter
        if (state.filters.severity !== 'all') {
            if (formatSeverity(caseData.severity) !== state.filters.severity) return false;
        }
        
        // Sentiment filter
        const sentiment = caseData.sentiment_score || 0.5;
        if (state.filters.sentiment !== 'all') {
            if (state.filters.sentiment === 'critical' && sentiment >= 0.35) return false;
            if (state.filters.sentiment === 'at-risk' && (sentiment < 0.35 || sentiment >= 0.55)) return false;
            if (state.filters.sentiment === 'healthy' && sentiment < 0.55) return false;
        }
        
        // Days inactive filter
        if (state.filters.daysInactive !== 'all') {
            const daysComm = caseData.days_since_last_outbound || 0;
            const threshold = parseInt(state.filters.daysInactive);
            if (daysComm <= threshold) return false;
        }
        
        return true;
    });
    
    // Re-render the cases table
    renderFilteredCasesTable();
}

/**
 * Quick filter shortcut
 */
function quickFilter(sentiment) {
    state.filters.sentiment = sentiment;
    
    // Update the dropdown to match
    const sentimentSelect = document.getElementById('filter-sentiment');
    if (sentimentSelect) {
        sentimentSelect.value = sentiment;
    }
    
    applyFilters();
    
    // Update quick filter buttons
    document.querySelectorAll('.quick-filter-pill').forEach(pill => {
        pill.classList.remove('active');
    });
    event.target.closest('.quick-filter-pill')?.classList.add('active');
}

/**
 * Clear all filters
 */
function clearFilters() {
    state.filters = {
        search: '',
        severity: 'all',
        sentiment: 'all',
        daysInactive: 'all',
        status: 'all'
    };
    
    // Reset form elements
    const searchInput = document.getElementById('filter-search');
    const severitySelect = document.getElementById('filter-severity');
    const sentimentSelect = document.getElementById('filter-sentiment');
    const daysSelect = document.getElementById('filter-days');
    
    if (searchInput) searchInput.value = '';
    if (severitySelect) severitySelect.value = 'all';
    if (sentimentSelect) sentimentSelect.value = 'all';
    if (daysSelect) daysSelect.value = 'all';
    
    applyFilters();
    
    // Reset quick filter buttons
    document.querySelectorAll('.quick-filter-pill').forEach((pill, index) => {
        pill.classList.toggle('active', index === 0);
    });
}

/**
 * Render filtered cases table
 */
function renderFilteredCasesTable() {
    const container = document.getElementById('filtered-cases-table');
    if (!container) return;
    
    const cases = state.filteredCases;
    
    if (cases.length === 0) {
        container.innerHTML = `
            <div class="card text-center" style="padding: var(--spacing-2xl);">
                <div style="font-size: 3rem; margin-bottom: var(--spacing-md);">🔍</div>
                <h3>No cases match your filters</h3>
                <p class="text-muted">Try adjusting your search criteria or <a href="#" onclick="clearFilters(); return false;">clear all filters</a></p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Case ID</th>
                        <th>Title</th>
                        <th>Severity</th>
                        <th>Customer</th>
                        <th>CSAT Risk</th>
                        <th>Sentiment</th>
                        <th>Last Comm</th>
                    </tr>
                </thead>
                <tbody>
                    ${cases.map(c => renderEnhancedCaseRow(c)).join('')}
                </tbody>
            </table>
        </div>
        <div class="text-muted text-small mt-md" style="text-align: center;">
            Showing ${cases.length} of ${state.cases.filter(c => c.status === 'active').length} active cases
        </div>
    `;
}

/**
 * Render enhanced case row with more details
 */
function renderEnhancedCaseRow(caseData) {
    const sentiment = caseData.sentiment_score || 0.5;
    const csatRisk = caseData.csat_risk || 'healthy';
    const daysComm = Math.round(caseData.days_since_last_outbound || 0);
    
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
    const sevLetter = formatSeverity(caseData.severity);
    const sevClass = getSeverityBadgeClass(caseData.severity);
    const pulseClass = getLivePulseClass(caseData);
    
    const daysCommClass = daysComm > 5 ? 'danger' : daysComm > 3 ? 'warning' : '';
    
    return `
        <tr class="clickable ${pulseClass}" onclick="viewCase('${caseData.id}')">
            <td><strong>${caseData.id}</strong></td>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${caseData.title || 'Untitled'}</td>
            <td><span class="badge ${sevClass}">Sev ${sevLetter}</span></td>
            <td>${caseData.customer?.company || 'Unknown'}</td>
            <td>${riskIcon} <span class="badge ${riskBadge}">${riskLabel}</span></td>
            <td>
                <div class="sentiment-indicator">
                    <span class="sentiment-dot sentiment-${sentimentClass}"></span>
                    ${Math.round(sentiment * 100)}%
                </div>
            </td>
            <td class="${daysCommClass}">${daysComm}d</td>
        </tr>
    `;
}

// =============================================================================
// Export System
// =============================================================================

/**
 * Open export modal
 */
function openExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close export modal
 */
function closeExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

/**
 * Export to CSV
 */
function exportToCSV() {
    const dateRange = document.getElementById('export-date-range')?.value || '30';
    const cases = getCasesForExport(dateRange);
    
    if (cases.length === 0) {
        showToast('No cases to export for the selected date range.', 'error');
        return;
    }
    
    // Build CSV
    const headers = ['Case ID', 'Title', 'Status', 'Severity', 'Customer', 'Sentiment Score', 'CSAT Risk', 'Days Since Comm', 'Days Open', 'Owner', 'Created Date'];
    const rows = cases.map(c => [
        c.id,
        `"${(c.title || '').replace(/"/g, '""')}"`,
        c.status,
        formatSeverity(c.severity),
        `"${(c.customer?.company || 'Unknown').replace(/"/g, '""')}"`,
        Math.round((c.sentiment_score || 0.5) * 100) + '%',
        c.csat_risk || 'N/A',
        c.days_since_last_outbound || 0,
        c.days_open || c.days_since_creation || 0,
        `"${(c.owner?.name || 'Unassigned').replace(/"/g, '""')}"`,
        c.created_on ? new Date(c.created_on).toLocaleDateString() : 'N/A'
    ]);
    
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    
    downloadFile(csvContent, `csat-guardian-export-${new Date().toISOString().split('T')[0]}.csv`, 'text/csv');
    
    closeExportModal();
    showToast(`Successfully exported ${cases.length} cases to CSV!`, 'success');
    celebrateSuccess();
}

/**
 * Export to PDF (generates HTML for print)
 */
function exportToPDF() {
    const dateRange = document.getElementById('export-date-range')?.value || '30';
    const cases = getCasesForExport(dateRange);
    
    if (cases.length === 0) {
        showToast('No cases to export for the selected date range.', 'error');
        return;
    }
    
    // Calculate summary stats
    const activeCases = cases.filter(c => c.status === 'active');
    const criticalCount = activeCases.filter(c => (c.sentiment_score || 0.5) < 0.35).length;
    const atRiskCount = activeCases.filter(c => {
        const s = c.sentiment_score || 0.5;
        return s >= 0.35 && s < 0.55;
    }).length;
    const avgSentiment = cases.length > 0 
        ? Math.round(cases.reduce((sum, c) => sum + (c.sentiment_score || 0.5), 0) / cases.length * 100) 
        : 0;
    
    // Generate printable HTML
    const printContent = `
<!DOCTYPE html>
<html>
<head>
    <title>CSAT Guardian Report</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 40px; color: #333; }
        h1 { color: #0078d4; border-bottom: 3px solid #0078d4; padding-bottom: 10px; }
        h2 { color: #0078d4; margin-top: 30px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }
        .stat { background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; min-width: 120px; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #0078d4; }
        .stat-label { font-size: 0.8rem; color: #666; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #0078d4; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f9f9f9; }
        .critical { color: #d13438; font-weight: bold; }
        .at-risk { color: #ffb900; font-weight: bold; }
        .healthy { color: #107c10; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.8rem; }
        @media print { body { margin: 20px; } }
    </style>
</head>
<body>
    <h1>🛡️ CSAT Guardian Report</h1>
    <p>Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}</p>
    <p>Date Range: Last ${dateRange === 'all' ? 'All Time' : dateRange + ' Days'}</p>
    
    <h2>Executive Summary</h2>
    <div class="summary">
        <div class="stat">
            <div class="stat-value">${cases.length}</div>
            <div class="stat-label">Total Cases</div>
        </div>
        <div class="stat">
            <div class="stat-value">${activeCases.length}</div>
            <div class="stat-label">Active Cases</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #d13438;">${criticalCount}</div>
            <div class="stat-label">Critical Risk</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #ffb900;">${atRiskCount}</div>
            <div class="stat-label">At Risk</div>
        </div>
        <div class="stat">
            <div class="stat-value">${avgSentiment}%</div>
            <div class="stat-label">Avg Sentiment</div>
        </div>
    </div>
    
    <h2>Case Details</h2>
    <table>
        <thead>
            <tr>
                <th>Case ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Sev</th>
                <th>Customer</th>
                <th>Sentiment</th>
                <th>Risk</th>
            </tr>
        </thead>
        <tbody>
            ${cases.map(c => {
                const sentiment = c.sentiment_score || 0.5;
                const sentimentClass = sentiment < 0.35 ? 'critical' : sentiment < 0.55 ? 'at-risk' : 'healthy';
                return `
                    <tr>
                        <td>${c.id}</td>
                        <td>${c.title || 'Untitled'}</td>
                        <td>${c.status}</td>
                        <td>${formatSeverity(c.severity)}</td>
                        <td>${c.customer?.company || 'Unknown'}</td>
                        <td class="${sentimentClass}">${Math.round(sentiment * 100)}%</td>
                        <td>${c.csat_risk || 'N/A'}</td>
                    </tr>
                `;
            }).join('')}
        </tbody>
    </table>
    
    <div class="footer">
        <p>CSAT Guardian &copy; 2026 EngOps / GSX • AI-Powered Customer Satisfaction Monitoring</p>
        <p>Powered by Azure OpenAI, Semantic Kernel, FastAPI</p>
    </div>
</body>
</html>
    `;
    
    // Open in new window for printing
    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
    
    closeExportModal();
    showToast('PDF report generated! Print dialog opened.', 'success');
}

/**
 * Export to JSON
 */
function exportToJSON() {
    const dateRange = document.getElementById('export-date-range')?.value || '30';
    const cases = getCasesForExport(dateRange);
    
    if (cases.length === 0) {
        showToast('No cases to export for the selected date range.', 'error');
        return;
    }
    
    const exportData = {
        exportDate: new Date().toISOString(),
        dateRange: dateRange,
        totalCases: cases.length,
        cases: cases.map(c => ({
            id: c.id,
            title: c.title,
            status: c.status,
            severity: formatSeverity(c.severity),
            customer: c.customer?.company,
            sentimentScore: c.sentiment_score,
            csatRisk: c.csat_risk,
            daysSinceComm: c.days_since_last_outbound,
            daysOpen: c.days_open || c.days_since_creation,
            owner: c.owner?.name,
            createdOn: c.created_on
        }))
    };
    
    const jsonContent = JSON.stringify(exportData, null, 2);
    downloadFile(jsonContent, `csat-guardian-export-${new Date().toISOString().split('T')[0]}.json`, 'application/json');
    
    closeExportModal();
    showToast(`Successfully exported ${cases.length} cases to JSON!`, 'success');
    celebrateSuccess();
}

/**
 * Get cases for export based on date range
 */
function getCasesForExport(dateRange) {
    if (dateRange === 'all') {
        return state.cases;
    }
    
    const days = parseInt(dateRange);
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return state.cases.filter(c => {
        if (!c.created_on) return true;
        return new Date(c.created_on) >= cutoffDate;
    });
}

/**
 * Download file helper
 */
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// =============================================================================
// UI Enhancement Functions - Animations & Visual Effects
// =============================================================================

/**
 * Animate a number counting up from 0 to target
 */
function animateCounter(element, targetValue, duration = 1000, suffix = '') {
    const startTime = performance.now();
    const startValue = 0;
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out cubic)
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.round(startValue + (targetValue - startValue) * easeOut);
        
        element.textContent = currentValue + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    requestAnimationFrame(updateCounter);
}

/**
 * Initialize all animated counters on the page
 */
function initAnimatedCounters() {
    const counters = document.querySelectorAll('[data-animate-count]');
    counters.forEach(counter => {
        const target = parseFloat(counter.dataset.animateCount);
        const suffix = counter.dataset.suffix || '';
        const duration = parseInt(counter.dataset.duration) || 1000;
        animateCounter(counter, target, duration, suffix);
    });
}

/**
 * Create an animated sentiment ring SVG
 */
function createSentimentRing(score, size = 'normal') {
    const percentage = Math.round(score * 100);
    const circumference = 251.2; // 2 * PI * 40 (radius)
    const offset = circumference - (circumference * score);
    const sentimentClass = getSentimentClass(score);
    
    const sizeClass = size === 'mini' ? 'sentiment-ring-mini' : 'sentiment-ring';
    const showValue = size !== 'mini';
    
    return `
        <div class="${sizeClass}">
            <svg viewBox="0 0 100 100">
                <defs>
                    <linearGradient id="gradientSuccess" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#107c10"/>
                        <stop offset="100%" style="stop-color:#6ccb5f"/>
                    </linearGradient>
                    <linearGradient id="gradientWarning" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#ff8c00"/>
                        <stop offset="100%" style="stop-color:#ffb900"/>
                    </linearGradient>
                    <linearGradient id="gradientDanger" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#d13438"/>
                        <stop offset="100%" style="stop-color:#ff6b6b"/>
                    </linearGradient>
                </defs>
                <circle class="sentiment-ring-bg" cx="50" cy="50" r="40"/>
                <circle class="sentiment-ring-fill ${sentimentClass}" cx="50" cy="50" r="40" 
                    style="stroke-dashoffset: ${offset}"/>
            </svg>
            ${showValue ? `
                <div class="sentiment-ring-value">
                    <div class="sentiment-ring-number" data-animate-count="${percentage}" data-suffix="%">${percentage}%</div>
                    <div class="sentiment-ring-label">Sentiment</div>
                </div>
            ` : `
                <div class="sentiment-ring-value">${percentage}%</div>
            `}
        </div>
    `;
}

/**
 * Create skeleton loading placeholder
 */
function createSkeleton(type = 'card', count = 1) {
    const skeletons = {
        card: '<div class="skeleton skeleton-card"></div>',
        metric: '<div class="skeleton skeleton-metric"></div>',
        row: '<div class="skeleton skeleton-row"></div>',
        text: '<div class="skeleton skeleton-text medium"></div>',
        textShort: '<div class="skeleton skeleton-text short"></div>',
    };
    
    return Array(count).fill(skeletons[type] || skeletons.card).join('');
}

/**
 * Create skeleton loading for metrics row
 */
function createMetricsSkeleton(count = 4) {
    return `
        <div class="metrics-row">
            ${Array(count).fill('<div class="metric-card skeleton skeleton-metric" style="height: 100px;"></div>').join('')}
        </div>
    `;
}

/**
 * Create skeleton loading for table
 */
function createTableSkeleton(rows = 5) {
    return `
        <div class="table-container">
            <div style="padding: var(--spacing-md);">
                ${Array(rows).fill('<div class="skeleton skeleton-row"></div>').join('')}
            </div>
        </div>
    `;
}

/**
 * Add page transition animation class
 */
function animatePageTransition(element) {
    element.classList.add('page-enter');
    // Remove class after animation completes
    setTimeout(() => element.classList.remove('page-enter'), 600);
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Toggle collapsible section visibility
 */
function toggleSection(sectionId) {
    const content = document.getElementById(`${sectionId}-content`);
    const icon = document.getElementById(`${sectionId}-icon`);
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.textContent = content.classList.contains('collapsed') ? '▶' : '▼';
    }
}

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
    // Build URL with optional date filter
    let url = '/api/manager/summary';
    if (state.selectedDateRange) {
        url += `?days=${state.selectedDateRange}`;
    }
    return await apiGet(url);
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
            <div class="hero-badge shimmer-overlay">
                <span>✨ AI-Powered</span>
            </div>
            <h1 class="hero-title">
                <span class="hero-icon float-animation">🛡️</span>
                <span class="gradient-text-animated">CSAT Guardian</span>
            </h1>
            <p class="subtitle hero-subtitle">AI-Powered Customer Satisfaction Monitoring & Proactive Coaching for Support Engineers</p>
            
            <div class="hero-buttons" data-stagger>
                <div class="card mode-card card-clickable hover-lift neon-border" onclick="navigateTo('engineer')">
                    <div class="mode-icon">👨‍💻</div>
                    <div class="mode-title">Engineer Mode</div>
                    <p class="mode-description">View your cases, get AI analysis and coaching recommendations</p>
                    <div class="mode-arrow">→</div>
                </div>
                
                <div class="card mode-card card-clickable hover-lift neon-border" onclick="navigateTo('manager')">
                    <div class="mode-icon">👥</div>
                    <div class="mode-title">Manager Mode</div>
                    <p class="mode-description">Team overview, CSAT health metrics, and intervention alerts</p>
                    <div class="mode-arrow">→</div>
                </div>
            </div>
            
            <div class="hero-features">
                <div class="hero-feature">
                    <span class="feature-icon">🔍</span>
                    <span>Smart Search & Filters</span>
                </div>
                <div class="hero-feature">
                    <span class="feature-icon">📊</span>
                    <span>Export Reports</span>
                </div>
                <div class="hero-feature">
                    <span class="feature-icon">📱</span>
                    <span>Mobile Friendly</span>
                </div>
                <div class="hero-feature">
                    <span class="feature-icon">🤖</span>
                    <span>AI Coaching</span>
                </div>
            </div>
        </div>
        
        <div class="tech-stack-section">
            <h3 class="tech-stack-title">Powered by Azure AI</h3>
            <div class="tech-stack-badges">
                <span class="tech-stack-badge pulse-ring">Azure OpenAI GPT-4o</span>
                <span class="tech-stack-badge">Semantic Kernel</span>
                <span class="tech-stack-badge">Azure SQL</span>
                <span class="tech-stack-badge">FastAPI</span>
            </div>
            <p class="tech-stack-subtitle">Built with ❤️ using Claude Opus 4.5</p>
        </div>
    `;
    updateBreadcrumb([]);
    animatePageTransition(main);
}

async function renderEngineerDashboard() {
    state.currentView = 'engineer';
    showLoading(true);
    
    const main = document.getElementById('main-content');
    // Show skeleton loading first
    main.innerHTML = `
        <div class="content-header page-enter">
            <h1>My Dashboard</h1>
            <p class="subtitle">Your CSAT performance insights and case management</p>
        </div>
        <div id="alerts-container"></div>
        
        <!-- Personal Analytics Section - Skeleton -->
        <div id="analytics-section" class="card mb-lg">
            ${createSkeleton('metric', 1)}
            <div class="skeleton skeleton-text long mt-md"></div>
            <div class="skeleton skeleton-text medium"></div>
        </div>
        
        <div id="metrics-container" class="metrics-row">
            ${createMetricsSkeleton(4).replace('<div class="metrics-row">', '').replace('</div>', '')}
        </div>
        
        <!-- My Cases Section - Skeleton -->
        <div id="cases-container">
            ${createTableSkeleton(5)}
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
        <div class="metric-card hover-lift">
            <div class="metric-value">${activeCases.length}</div>
            <div class="metric-label">Active Cases</div>
        </div>
        <div class="metric-card hover-lift">
            <div class="metric-value danger">${critical}</div>
            <div class="metric-label">Critical CSAT</div>
        </div>
        <div class="metric-card hover-lift">
            <div class="metric-value warning">${atRisk}</div>
            <div class="metric-label">At Risk</div>
        </div>
        <div class="metric-card hover-lift">
            <div class="metric-value success">${healthy}</div>
            <div class="metric-label">Healthy</div>
        </div>
        <div class="metric-card hover-lift">
            <div class="metric-value">${resolvedCases.length}</div>
            <div class="metric-label">Resolved</div>
        </div>
    `;
    
    // Initialize filtered cases
    state.filteredCases = [...activeCases];
    
    // Render cases with filter bar
    document.getElementById('cases-container').innerHTML = `
        <!-- Filter Bar -->
        ${renderFilterBar(allCases)}
        
        <!-- Filtered Active Cases Table -->
        <div id="filtered-cases-table">
            ${activeCases.length > 0 ? `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Case ID</th>
                                <th>Title</th>
                                <th>Severity</th>
                                <th>Customer</th>
                                <th>CSAT Risk</th>
                                <th>Sentiment</th>
                                <th>Last Comm</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${activeCases.map(c => renderEnhancedCaseRow(c)).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="text-muted text-small mt-md" style="text-align: center;">
                    Showing ${activeCases.length} of ${activeCases.length} active cases
                </div>
            ` : '<p class="text-muted mb-lg">No active cases - great job!</p>'}
        </div>
        
        <!-- Resolved Cases Section (Collapsible, collapsed by default) -->
        <div class="collapsible-section mt-xl" id="resolved-cases-section">
            <h3 class="collapsible-header mb-md" onclick="toggleSection('resolved-cases')">
                <span class="collapse-icon" id="resolved-cases-icon">▶</span>
                ✅ Resolved Cases (${resolvedCases.length})
            </h3>
            <div class="collapsible-content collapsed" id="resolved-cases-content">
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
            </div>
        </div>
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
    
    // Live pulse class for critical/declining sentiment
    const pulseClass = getLivePulseClass(caseData);
    
    // Success story badge
    const successBadge = isSuccessStory(caseData) ? '<span class="badge badge-success-story">🌟</span>' : '';
    
    // Simplified row for resolved cases
    if (isResolved) {
        return `
            <tr class="clickable resolved-row ${pulseClass}" onclick="viewCase('${caseData.id}')">
                <td><strong>${caseData.id}</strong></td>
                <td>${caseData.title || 'Untitled'} ${successBadge}</td>
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
        <tr class="clickable ${pulseClass}" onclick="viewCase('${caseData.id}')">
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
    
    // Determine if this is a resolved case
    const isResolved = caseData.status === 'resolved' || caseData.status === 'cancelled';
    
    // Fetch analysis in parallel
    const analysisPromise = analyzeCase(caseId);
    
    // Render case detail structure - Clean layout without full timeline
    const daysNote = Math.round(caseData.days_since_last_note || 0);
    const daysComm = Math.round(caseData.days_since_last_outbound || 0);
    const csatRisk = caseData.csat_risk || 'healthy';
    const sentimentScore = caseData.sentiment_score || 0.5;
    const daysOpen = Math.round(caseData.days_open || caseData.days_since_creation || 0);
    
    // Different header for resolved vs active cases
    const headerMetrics = isResolved ? `
        <div style="display: flex; gap: 24px; text-align: right;">
            <div>
                <div class="metric-value">${daysOpen}</div>
                <div class="metric-label">Days to Resolution</div>
            </div>
            <div>
                <span class="badge badge-success" style="font-size: 1rem; padding: 8px 16px;">✅ RESOLVED</span>
            </div>
        </div>
    ` : `
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
    `;
    
    // Different main content for resolved vs active cases
    const mainContent = isResolved ? `
        <!-- Post-Closure Analysis Section for Resolved Cases -->
        <div id="analysis-section" class="analysis-section mb-lg">
            <div class="loading"><div class="spinner"></div></div>
            <p class="text-center text-muted">Analyzing case history...</p>
        </div>
        
        <!-- Success Story Highlight (if applicable) -->
        ${renderSuccessStoryCard(caseData)}
        
        <!-- Case History Summary -->
        <div id="actions-section" class="card mb-lg" style="display: none;">
            <h3>📚 Case Review & Learnings</h3>
            <div id="actions-content" class="mt-md"></div>
        </div>
        
        <!-- Chat Section for asking about resolved case -->
        <div class="card">
            <h3>💬 Ask CSAT Guardian About This Case</h3>
            <p class="text-muted text-small mt-sm">Ask questions about how this case was handled or what could be improved.</p>
            <div id="chat-container" class="mt-md">
                <div id="chat-messages" style="max-height: 350px; overflow-y: auto; margin-bottom: var(--spacing-md); padding: var(--spacing-sm);">
                    <div class="chat-message">
                        <div class="chat-avatar">🤖</div>
                        <div class="chat-bubble">
                            <p>This case has been resolved. I can help you review it for learnings. You can ask me:</p>
                            <ul style="margin: 8px 0 0 16px; font-size: 0.9rem;">
                                <li>What went well on this case?</li>
                                <li>What could have been done differently?</li>
                                <li>How was the customer sentiment throughout?</li>
                                <li>Summarize the resolution</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="flex gap-sm">
                    <input type="text" id="chat-input" class="form-input" placeholder="Ask a question about this resolved case..." onkeypress="handleChatKeypress(event)">
                    <button class="btn btn-primary" onclick="sendChatMessage()">Send</button>
                </div>
            </div>
        </div>
    ` : `
        <!-- AI Sentiment Analysis Section -->
        <div id="analysis-section" class="analysis-section mb-lg">
            <div class="loading"><div class="spinner"></div></div>
            <p class="text-center text-muted">Analyzing case with Azure OpenAI...</p>
        </div>
        
        <!-- CSAT Prediction Card -->
        ${renderCSATPrediction(caseData)}
        
        <!-- Success Story Highlight (if applicable) -->
        ${renderSuccessStoryCard(caseData)}
        
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
    `;
    
    main.innerHTML = `
        <div class="content-header flex justify-between items-center">
            <div>
                <button class="btn btn-ghost mb-sm" onclick="navigateTo('engineer')">← Back to Cases</button>
                <h1>${caseData.title || caseId}</h1>
                <p class="subtitle">${caseData.id} • ${caseData.customer?.company || 'Unknown Customer'} (${caseData.customer?.tier || 'Standard'})</p>
            </div>
            ${headerMetrics}
        </div>
        
        <div class="two-column">
            <div class="sidebar">
                <!-- Case Info Card -->
                <div class="card mb-lg">
                    <h3>📋 Case Details</h3>
                    <div class="mt-md">
                        <div class="text-small text-muted">Status</div>
                        <div><span class="badge ${isResolved ? 'badge-success' : 'badge-info'}">${caseData.status || 'Active'}</span></div>
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
                        <div class="text-small text-muted">${isResolved ? 'Time to Resolution' : 'Days Open'}</div>
                        <div>${daysOpen} days</div>
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
                ${mainContent}
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
    
    // Check if this is a resolved case
    const isResolved = caseData?.status === 'resolved' || caseData?.status === 'cancelled';
    
    if (!analysis) {
        container.innerHTML = `
            <h3>🤖 ${isResolved ? 'Case History Analysis' : 'AI Sentiment Analysis'}</h3>
            <p class="text-muted mt-md">Unable to analyze case. AI service may be unavailable.</p>
        `;
        return;
    }
    
    const sentiment = analysis.sentiment || {};
    // Use the sentiment score from the case list (calculated consistently) if available
    // This ensures the list and detail views show the same number
    const score = caseData?.sentiment_score || sentiment.score || 0.5;
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
    
    // Build sentiment evidence showing the "story" - key communications that show sentiment trajectory
    let evidenceHtml = '';
    if (customerMessages.length > 0) {
        // Analyze all customer messages and find the most story-telling ones
        const frustrationWords = ['frustrated', 'disappointed', 'unacceptable', 'urgent', 'escalate', 'waiting', 'still no', 'again', 'issue', 'problem', 'not working', 'furious', 'terrible', 'nightmare'];
        const positiveWords = ['thank', 'great', 'appreciate', 'helpful', 'excellent', 'resolved', 'perfect', 'amazing', 'wonderful', 'awesome'];
        
        // Score each message
        const scoredMessages = customerMessages.map((msg, idx) => {
            const content = msg.content || '';
            const contentLower = content.toLowerCase();
            const foundFrustration = frustrationWords.filter(w => contentLower.includes(w));
            const foundPositive = positiveWords.filter(w => contentLower.includes(w));
            
            let msgScore = 0.5;
            let sentiment = 'neutral';
            if (foundFrustration.length > foundPositive.length) {
                msgScore = Math.max(0.1, 0.5 - (foundFrustration.length * 0.1));
                sentiment = 'negative';
            } else if (foundPositive.length > 0) {
                msgScore = Math.min(0.95, 0.7 + (foundPositive.length * 0.05));
                sentiment = 'positive';
            }
            
            return { ...msg, msgScore, sentiment, foundFrustration, foundPositive, index: idx };
        });
        
        // Find key story points: first, last, highest, lowest, and any sentiment changes
        const storyMessages = [];
        
        // Always show first customer message (sets the scene)
        if (scoredMessages.length > 0) {
            storyMessages.push({ ...scoredMessages[0], reason: 'Initial contact' });
        }
        
        // Find sentiment changes (transitions)
        for (let i = 1; i < scoredMessages.length; i++) {
            const prev = scoredMessages[i - 1];
            const curr = scoredMessages[i];
            
            // Detect significant sentiment change
            if (prev.sentiment !== curr.sentiment && curr.sentiment !== 'neutral') {
                storyMessages.push({ ...curr, reason: prev.sentiment === 'positive' ? '📉 Sentiment dropped' : '📈 Sentiment improved' });
            }
        }
        
        // Always show most recent message if not already included
        const lastMsg = scoredMessages[scoredMessages.length - 1];
        if (!storyMessages.find(m => m.index === lastMsg.index)) {
            storyMessages.push({ ...lastMsg, reason: 'Most recent' });
        }
        
        // Sort by chronological order and limit to 5 for display
        const displayMessages = storyMessages
            .sort((a, b) => a.index - b.index)
            .slice(0, 5);
        
        const totalAnalyzed = customerMessages.length;
        evidenceHtml = `
            <div class="mt-lg">
                <h4>📧 Sentiment Journey (${totalAnalyzed} total communications analyzed)</h4>
                <div class="mt-md" style="display: flex; flex-direction: column; gap: 12px;">
                    ${displayMessages.map(msg => {
                        const content = msg.content || '';
                        let indicator = '➡️ Neutral';
                        let bgColor = 'var(--background-tertiary)';
                        if (msg.sentiment === 'negative') {
                            indicator = '⚠️ Signs of frustration';
                            bgColor = 'rgba(209, 52, 56, 0.1)';
                        } else if (msg.sentiment === 'positive') {
                            indicator = '✅ Positive tone';
                            bgColor = 'rgba(16, 124, 16, 0.1)';
                        }
                        
                        let snippet = content.substring(0, 200);
                        if (content.length > 200) snippet += '...';
                        
                        const borderColor = msg.sentiment === 'negative' ? 'var(--accent-danger)' : msg.sentiment === 'positive' ? 'var(--accent-success)' : 'var(--border-subtle)';
                        
                        return `
                            <div style="background: ${bgColor}; padding: 12px; border-radius: 8px; border-left: 3px solid ${borderColor};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: 600; color: var(--text-primary);">${indicator}</span>
                                    <div style="text-align: right;">
                                        <span style="font-size: 0.7rem; color: var(--accent-primary); display: block;">${msg.reason}</span>
                                        <span style="font-size: 0.75rem; color: var(--text-tertiary);">${formatDateShort(msg.created_on)}</span>
                                    </div>
                                </div>
                                <div style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5; font-style: italic;">"${snippet}"</div>
                                ${msg.foundFrustration.length > 0 ? `<div style="margin-top: 8px; font-size: 0.75rem; color: var(--accent-warning);">Detected: ${msg.foundFrustration.join(', ')}</div>` : ''}
                                ${msg.foundPositive.length > 0 ? `<div style="margin-top: 8px; font-size: 0.75rem; color: var(--accent-success);">Detected: ${msg.foundPositive.join(', ')}</div>` : ''}
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
    
    // Different display for resolved vs active cases
    if (isResolved) {
        // Resolved case: Show case history analysis
        const daysToResolve = Math.round(caseData?.days_open || caseData?.days_since_creation || 0);
        const finalSentiment = score >= 0.6 ? 'Positive' : score >= 0.4 ? 'Neutral' : 'Negative';
        const outcome = score >= 0.6 ? '✅ Successful resolution - customer satisfied' : 
                       score >= 0.4 ? '➡️ Neutral outcome - room for improvement' : 
                       '⚠️ Customer may have been unsatisfied';
        
        container.innerHTML = `
            <h3>📊 Case History Analysis</h3>
            
            <div class="analysis-header mt-lg">
                <div class="analysis-score ${sentimentClass}">${Math.round(score * 100)}%</div>
                <div class="analysis-details">
                    <div class="analysis-label">FINAL SENTIMENT: ${finalSentiment.toUpperCase()}</div>
                    <div class="analysis-trend">${outcome}</div>
                    <div style="font-size: 0.8rem; color: var(--text-tertiary); margin-top: 4px;">
                        Resolved in ${daysToResolve} days • ${customerMessages.length} customer interaction${customerMessages.length !== 1 ? 's' : ''}
                    </div>
                </div>
            </div>
            
            ${evidenceHtml}
            ${phrasesHtml}
        `;
        
        // Show learnings instead of actions
        actionsSection.style.display = 'block';
        
        // Generate learnings based on the case
        const learnings = [];
        if (score >= 0.6) {
            learnings.push('🌟 Customer expressed satisfaction - good communication maintained');
            if (daysToResolve < 14) learnings.push('⚡ Quick resolution time contributed to positive outcome');
            if (customerMessages.length >= 3) learnings.push('💬 Good engagement level with multiple touchpoints');
        } else if (score >= 0.4) {
            learnings.push('📝 Resolution achieved but customer sentiment was mixed');
            learnings.push('💡 Consider more proactive communication on similar cases');
        } else {
            learnings.push('⚠️ Customer showed signs of frustration during this case');
            learnings.push('💡 Earlier intervention on negative signals may help in future cases');
            if (trend === 'declining') learnings.push('📉 Sentiment declined over time - watch for early warning signs');
        }
        
        if (concerns.length > 0) {
            learnings.push(`📋 Key concerns raised: ${concerns.slice(0, 2).join(', ')}`);
        }
        
        actionsContent.innerHTML = `
            <ul class="recommendations-list">
                ${learnings.map((l, i) => `
                    <li class="recommendation-item">
                        <span class="recommendation-text">${l}</span>
                    </li>
                `).join('')}
            </ul>
        `;
    } else {
        // Active case: Show current analysis and recommendations
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
}

async function renderManagerDashboard() {
    state.currentView = 'manager';
    state.selectedDateRange = state.selectedDateRange || 30;  // Default to 30 days (numeric)
    showLoading(true);
    
    const main = document.getElementById('main-content');
    // Show skeleton loading first for instant feedback
    main.innerHTML = `
        <div class="content-header page-enter">
            <div class="flex justify-between items-center">
                <div>
                    <h1>Team Performance</h1>
                    <p class="subtitle">Empowering your team through data-driven coaching insights</p>
                </div>
                <div class="date-range-selector">
                    <button class="date-btn ${state.selectedDateRange === 7 ? 'active' : ''}" onclick="updateDateRange('7d')">7 Days</button>
                    <button class="date-btn ${state.selectedDateRange === 30 ? 'active' : ''}" onclick="updateDateRange('30d')">30 Days</button>
                    <button class="date-btn ${state.selectedDateRange === 90 ? 'active' : ''}" onclick="updateDateRange('90d')">Quarter</button>
                </div>
            </div>
        </div>
        <div id="team-summary" class="team-summary-section">
            ${createMetricsSkeleton(5)}
        </div>
        <div id="team-container">
            ${createTableSkeleton(6)}
        </div>
    `;
    updateBreadcrumb([{ text: 'Team Performance' }]);
    
    // Use fast summary endpoint for performance (avoids N+1 queries)
    const summaryData = await getManagerSummary();
    
    showLoading(false);
    
    // Debug log to see what we're getting
    console.log('Manager summary data:', summaryData);
    
    // Check if we got USEFUL data from the fast endpoint
    const hasUsefulData = summaryData && 
        summaryData.engineers && 
        summaryData.engineers.length > 0 &&
        summaryData.stats &&
        summaryData.stats.total_cases > 0;
    
    if (hasUsefulData) {
        console.log('✅ Using fast endpoint data');
        state.engineers = summaryData.engineers;
        state.managerStats = summaryData.stats || {};
    } else {
        // Fast endpoint returned incomplete data, use slow method to load all cases
        console.log('⚠️ Fast endpoint returned incomplete data, falling back to slow method');
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
    // Convert range string to days number
    const daysMap = { '7d': 7, '30d': 30, '90d': 90 };
    state.selectedDateRange = daysMap[range] || 90;
    
    // Update button states
    document.querySelectorAll('.date-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.includes(
            range === '7d' ? '7' : range === '30d' ? '30' : 'Quarter'
        ));
    });
    
    // Re-fetch data with new date filter
    refreshManagerData();
}

async function refreshManagerData() {
    try {
        showLoading(true);
        const summaryData = await getManagerSummary();
        state.engineers = summaryData.engineers || [];
        state.managerStats = summaryData.stats || {};
        renderTeamDashboardContent();
    } catch (error) {
        console.error('Failed to refresh manager data:', error);
    } finally {
        showLoading(false);
    }
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
    const range = state.selectedDateRange || 30;  // numeric days
    
    const rangeLabel = range === 7 ? 'Past 7 Days' : range === 30 ? 'Past 30 Days' : 'Past Quarter';
    
    // Use pre-computed stats from fast endpoint (already filtered by days)
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
            <div class="summary-card highlight card-glass">
                <div class="summary-header">
                    <span class="summary-icon">📊</span>
                    <span class="summary-title">Team Sentiment Overview</span>
                    <span class="summary-period">${rangeLabel}</span>
                </div>
                <div class="sentiment-chart-container">
                    <div class="sentiment-donut">
                        ${createSentimentRing(teamAvgSentiment)}
                    </div>
                    <div class="chart-legend">
                        <div class="legend-item">
                            <span class="legend-dot excellent"></span>
                            <span class="legend-label">Excellent (70%+)</span>
                            <span class="legend-value" data-animate-count="${excellentCount}">${excellentCount}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-dot good"></span>
                            <span class="legend-label">Good (55-70%)</span>
                            <span class="legend-value" data-animate-count="${goodCount}">${goodCount}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-dot opportunity"></span>
                            <span class="legend-label">Growth Opportunity</span>
                            <span class="legend-value" data-animate-count="${opportunityCount}">${opportunityCount}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="summary-card card-glass">
                <div class="summary-header">
                    <span class="summary-icon">👥</span>
                    <span class="summary-title">Team at a Glance</span>
                </div>
                <div class="glance-metrics">
                    <div class="glance-item">
                        <span class="glance-value" data-animate-count="${engineers.length}">${engineers.length}</span>
                        <span class="glance-label">Engineers</span>
                    </div>
                    <div class="glance-item">
                        <span class="glance-value" data-animate-count="${totalActiveCases}">${totalActiveCases}</span>
                        <span class="glance-label">Active Cases</span>
                    </div>
                    <div class="glance-item">
                        <span class="glance-value" data-animate-count="${totalResolvedCases}">${totalResolvedCases}</span>
                        <span class="glance-label">Resolved (${rangeLabel})</span>
                    </div>
                    <div class="glance-item">
                        <span class="glance-value" data-animate-count="${Math.round(totalActiveCases / Math.max(engineers.length, 1))}">${Math.round(totalActiveCases / Math.max(engineers.length, 1))}</span>
                        <span class="glance-label">Avg Active/Engineer</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Trigger counter animations
    setTimeout(() => initAnimatedCounters(), 100);
    
    // Animate the sentiment ring
    setTimeout(() => {
        const ring = teamSummaryEl.querySelector('.sentiment-ring-fill');
        if (ring) {
            const score = teamAvgSentiment;
            const circumference = 251.2;
            const offset = circumference - (circumference * score);
            ring.style.strokeDashoffset = offset;
        }
    }, 200);
    
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
    const dateRange = state.selectedDateRange || 30;  // numeric days
    const rangeLabel = dateRange === 7 ? 'Past 7 Days' : dateRange === 30 ? 'Past 30 Days' : 'Past Quarter';
    
    // Use the pre-calculated avg_sentiment from API (consistent with manager view)
    // Fall back to calculating from cases if not available
    let avgSentiment = summary.avg_sentiment;
    if (avgSentiment === null || avgSentiment === undefined) {
        avgSentiment = activeCases.length > 0
            ? activeCases.reduce((sum, c) => {
                if (c.sentiment_score !== undefined && c.sentiment_score !== null) {
                    return sum + c.sentiment_score;
                }
                return sum + 0.5;
            }, 0) / activeCases.length
            : null;
    }
    
    // Count ACTIVE cases by risk level for distribution
    const excellentCases = activeCases.filter(c => c.risk_level === 'healthy');
    const goodCases = activeCases.filter(c => c.risk_level === 'at_risk');
    const opportunityCases = activeCases.filter(c => c.risk_level === 'breach');
    
    // Determine engineer status (matching manager view logic)
    let engineerStatus = '✓ On Track';
    if (activeCases.length === 0) {
        engineerStatus = '📋 No Active Cases';
    } else if (avgSentiment >= 0.55) {
        engineerStatus = '⭐ Top Performer';
    } else if (avgSentiment >= 0.35) {
        engineerStatus = '⚠️ Needs Attention';
    } else {
        engineerStatus = '🚨 Coaching Opportunity';
    }
    
    // Generate personalized coaching based on actual case data
    const personalizedCoaching = generatePersonalizedCoachingFromSummary(engCases, engineer.name.split(' ')[0]);
    
    // Generate trend data (simulated for demo - would come from API in production)
    const trendData = generateTrendData(engCases, dateRange);
    
    const sentimentClass = getSentimentClass(avgSentiment || 0.5);
    const firstName = engineer.name.split(' ')[0];
    const sentimentPct = avgSentiment !== null ? Math.round(avgSentiment * 100) : 'N/A';
    const sentimentWidth = avgSentiment !== null ? Math.round(avgSentiment * 100) : 0;
    
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
                        <span class="achievement-badge">${engineerStatus}</span>
                    </div>
                </div>
                <div class="profile-score">
                    <div class="score-ring ${sentimentClass}">
                        <svg viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="45" fill="none" stroke="#3a3a3a" stroke-width="8"/>
                            <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="8"
                                stroke-dasharray="${sentimentWidth * 2.83} 283" 
                                stroke-linecap="round" transform="rotate(-90 50 50)"/>
                        </svg>
                        <span class="score-text">${sentimentPct}${avgSentiment !== null ? '%' : ''}</span>
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
    console.log('🛡️ CSAT Guardian ULTRA PREMIUM initializing...');
    
    try {
        // Initialize theme first (before any rendering)
        initializeTheme();
        
        // Initialize particle system for WOW effect
        initParticles();
        console.log('✨ Particle system initialized');
        
        // Initialize mobile menu handlers
        initMobileMenuHandlers();
        
        // Render landing page immediately (don't wait for health check)
        renderLandingPage();
        console.log('🏠 Landing page rendered');
        
        // Initialize feedback button listener
        initFeedbackSystem();
        
        // Initialize export modal handlers
        initExportModalHandlers();
        
        // Check backend health in background
        checkHealth().catch(e => console.warn('Health check failed:', e));
        
        // Periodic health check
        setInterval(() => checkHealth().catch(() => {}), 30000);
        
        console.log('🚀 CSAT Guardian ready!');
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

/**
 * Initialize mobile menu event handlers
 */
function initMobileMenuHandlers() {
    // Close menu when clicking overlay
    const overlay = document.getElementById('mobile-nav-overlay');
    if (overlay) {
        overlay.addEventListener('click', closeMobileMenu);
    }
    
    // Handle resize - close menu if screen becomes large
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && state.mobileMenuOpen) {
            closeMobileMenu();
        }
    });
    
    // Handle swipe to close (touch devices)
    let touchStartX = 0;
    const menu = document.getElementById('mobile-menu');
    if (menu) {
        menu.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
        }, { passive: true });
        
        menu.addEventListener('touchmove', (e) => {
            const touchX = e.touches[0].clientX;
            const diff = touchStartX - touchX;
            if (diff > 50) {
                closeMobileMenu();
            }
        }, { passive: true });
    }
}

/**
 * Initialize export modal event handlers
 */
function initExportModalHandlers() {
    const modal = document.getElementById('export-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeExportModal();
            }
        });
    }
    
    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeExportModal();
        }
    });
}

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
