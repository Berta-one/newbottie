class EnhancedDashboard {
    constructor() {
        this.apiUrl = 'https://bottie-1.onrender.com'; // Your API endpoint
        this.endpoints = [
            { name: 'equity', title: 'Portfolio Equity', icon: '💰', endpoint: '/status' },
            { name: 'trades', title: 'Trade History', icon: '📈', endpoint: '/trades' },
            { name: 'ml', title: 'ML Performance', icon: '🧠', endpoint: '/ml/status' },
            { name: 'quantum', title: 'Quantum Analysis', icon: '⚛️', endpoint: '/quantum/details' },
            { name: 'sentiment', title: 'Sentiment Analysis', icon: '📰', endpoint: '/sentiment/articles' },
            { name: 'brierscore', title: 'Brier Score Analysis', icon: '📊', endpoint: '/ml/performance' },
            { name: 'signals', title: 'Trading Signals', icon: '🎯', endpoint: '/signals' },
            { name: 'positions', title: 'Current Positions', icon: '💼', endpoint: '/positions' },
            { name: 'backtest', title: 'Backtest Results', icon: '⏮️', endpoint: '/backtest/results' },
            { name: 'logs', title: 'System Logs', icon: '📋', endpoint: '/logs/last' },
            { name: 'health', title: 'System Health', icon: '🔋', endpoint: '/health' },
            { name: 'grid', title: 'Cross-Pair Matrix', icon: '🌐', endpoint: '/grid/matrix' }
        ];
        this.endpointData = {};
        this.init();
    }

    async init() {
        await this.loadAllEndpoints();
        this.renderSlates();
        this.updateConnectionStatus();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.loadAllEndpoints();
            this.updateSlateMetrics();
        }, 30000);
    }

    async loadAllEndpoints() {
        const promises = this.endpoints.map(endpoint => this.loadEndpoint(endpoint));
        await Promise.allSettled(promises);
    }

    async loadEndpoint(endpoint) {
        try {
            const response = await fetch(`${this.apiUrl}${endpoint.endpoint}`);
            const data = await response.json();
            this.endpointData[endpoint.name] = {
                ...data,
                status: response.ok ? 'success' : 'error',
                lastUpdate: new Date().toISOString()
            };
        } catch (error) {
            this.endpointData[endpoint.name] = {
                status: 'error',
                error: error.message,
                lastUpdate: new Date().toISOString()
            };
        }
    }

    renderSlates() {
        const container = document.getElementById('slates-container');
        container.innerHTML = this.endpoints.map(endpoint => this.createSlate(endpoint)).join('');
    }

    createSlate(endpoint) {
        const data = this.endpointData[endpoint.name] || {};
        const metrics = this.getEndpointMetrics(endpoint.name, data);
        const status = this.getEndpointStatus(data);

        return `
            <div class="slate" onclick="dashboard.generateReport('${endpoint.name}')">
                <div class="slate-header">
                    <div class="slate-title">
                        <span class="slate-icon">${endpoint.icon}</span>
                        ${endpoint.title}
                    </div>
                    <div class="slate-status ${status.class}">${status.text}</div>
                </div>
                <div class="slate-metrics">
                    ${metrics.map(metric => `
                        <div class="metric">
                            <div class="metric-value ${metric.class || ''}">${metric.value}</div>
                            <div class="metric-label">${metric.label}</div>
                        </div>
                    `).join('')}
                </div>
                <div class="slate-description">
                    ${this.getEndpointDescription(endpoint.name, data)}
                </div>
            </div>
        `;
    }

    getEndpointMetrics(name, data) {
        switch (name) {
            case 'equity':
                return [
                    { label: 'Current Equity', value: `$${(data.equity || 0).toFixed(2)}`, class: data.equity > 0 ? 'positive' : 'neutral' },
                    { label: 'Positions', value: Object.keys(data.positions || {}).length }
                ];
            case 'trades':
                const trades = data.trades || [];
                return [
                    { label: 'Total Trades', value: trades.length },
                    { label: 'Today', value: trades.filter(t => this.isToday(t.timestamp)).length }
                ];
            case 'ml':
                return [
                    { label: 'Accuracy', value: `${((data.accuracy || 0) * 100).toFixed(1)}%`, class: data.accuracy > 0.7 ? 'positive' : 'neutral' },
                    { label: 'Sample Count', value: data.sample_count || 0 }
                ];
            case 'quantum':
                return [
                    { label: 'Q-Score', value: (data.quantum_score || 0).toFixed(3) },
                    { label: 'Enabled', value: data.enabled ? 'Yes' : 'No', class: data.enabled ? 'positive' : 'negative' }
                ];
            case 'sentiment':
                const articles = data.articles || [];
                const avgSentiment = articles.length > 0 ? articles.reduce((sum, a) => sum + (a.sentiment || 0), 0) / articles.length : 0;
                return [
                    { label: 'Avg Sentiment', value: avgSentiment.toFixed(2), class: avgSentiment > 0 ? 'positive' : avgSentiment < 0 ? 'negative' : 'neutral' },
                    { label: 'Articles', value: articles.length }
                ];
            case 'brierscore':
                return [
                    { label: 'Brier Score', value: (data.brier_score || 0).toFixed(3), class: data.brier_score < 0.2 ? 'positive' : 'neutral' },
                    { label: 'Timeframe', value: data.timeframe || '24h' }
                ];
            case 'signals':
                const signals = data.signals || [];
                return [
                    { label: 'Active Signals', value: signals.length },
                    { label: 'Avg Confidence', value: signals.length > 0 ? (signals.reduce((sum, s) => sum + (s.confidence || 0), 0) / signals.length).toFixed(2) : '0.00' }
                ];
            default:
                return [
                    { label: 'Status', value: data.status === 'success' ? 'OK' : 'Error', class: data.status === 'success' ? 'positive' : 'negative' },
                    { label: 'Last Update', value: data.lastUpdate ? new Date(data.lastUpdate).toLocaleTimeString() : 'Never' }
                ];
        }
    }

    getEndpointStatus(data) {
        if (data.status === 'error') {
            return { class: 'status-error', text: 'Error' };
        }
        
        // Add custom status logic based on data quality
        switch (data.status) {
            case 'success':
                return { class: 'status-excellent', text: 'Active' };
            default:
                return { class: 'status-loading', text: 'Loading' };
        }
    }

    getEndpointDescription(name, data) {
        const descriptions = {
            equity: `Monitor your portfolio value and asset allocation across all trading pairs.`,
            trades: `Complete history of executed trades with P&L calculations and performance metrics.`,
            ml: `Machine learning model performance, accuracy metrics, and prediction confidence scores.`,
            quantum: `Quantum-inspired algorithmic analysis and portfolio optimization insights.`,
            sentiment: `Real-time market sentiment analysis from news sources and social media.`,
            brierscore: `Statistical accuracy measure for probabilistic predictions and model calibration.`,
            signals: `Live trading signals with confidence levels and recommended actions.`,
            positions: `Current open positions, unrealized P&L, and risk exposure analysis.`,
            backtest: `Historical strategy performance testing and optimization results.`,
            logs: `System activity logs, errors, and operational status information.`,
            health: `Overall system health monitoring and component status checks.`,
            grid: `Cross-pair trading opportunities matrix and correlation analysis.`
        };
        
        return descriptions[name] || 'Comprehensive data analysis and reporting for this component.';
    }

    async generateReport(endpointName) {
        const endpoint = this.endpoints.find(e => e.name === endpointName);
        if (!endpoint) return;

        // Show modal
        const modal = document.getElementById('report-modal');
        const title = document.getElementById('report-title');
        const icon = document.getElementById('report-icon');
        const name = document.getElementById('report-name');
        const body = document.getElementById('report-body');

        icon.textContent = endpoint.icon;
        name.textContent = `${endpoint.title} Report`;
        modal.style.display = 'flex';

        // Show loading state
        body.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <div class="loading-spinner" style="width: 40px; height: 40px;"></div>
                <p style="margin-top: 1rem; color: #8892b0;">Generating comprehensive report...</p>
            </div>
        `;

        // Generate report content
        setTimeout(() => {
            body.innerHTML = this.createReportContent(endpointName, this.endpointData[endpointName] || {});
        }, 1500);
    }

    createReportContent(endpointName, data) {
        const timestamp = new Date().toLocaleString();
        
        return `
            <div class="report-section">
                <div class="section-title">
                    📋 Report Summary
                </div>
                <div class="data-grid">
                    <div class="data-card">
                        <div class="data-label">Generated</div>
                        <div class="data-value">${timestamp}</div>
                    </div>
                    <div class="data-card">
                        <div class="data-label">Data Source</div>
                        <div class="data-value">${this.endpoints.find(e => e.name === endpointName)?.endpoint || 'Unknown'}</div>
                    </div>
                    <div class="data-card">
                        <div class="data-label">Status</div>
                        <div class="data-value ${data.status === 'success' ? 'positive' : 'negative'}">${data.status === 'success' ? 'Online' : 'Error'}</div>
                    </div>
                    <div class="data-card">
                        <div class="data-label">Last Update</div>
                        <div class="data-value">${data.lastUpdate ? new Date(data.lastUpdate).toLocaleString() : 'Never'}</div>
                    </div>
                </div>
            </div>

            <div class="report-section">
                <div class="section-title">
                    📊 Key Metrics & Analysis
                </div>
                ${this.createDetailedAnalysis(endpointName, data)}
            </div>

            <div class="report-section">
                <div class="section-title">
                    📄 Raw Data & Logs
                </div>
                <div class="logs-container">
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                </div>
            </div>

            <div class="export-buttons">
                <button class="export-btn" onclick="dashboard.exportReport('${endpointName}', 'json')">
                    💾 Export JSON
                </button>
                <button class="export-btn" onclick="dashboard.exportReport('${endpointName}', 'csv')">
                    📊 Export CSV
                </button>
                <button class="export-btn" onclick="dashboard.printReport()">
                    🖨️ Print Report
                </button>
            </div>
        `;
    }

    createDetailedAnalysis(endpointName, data) {
        switch (endpointName) {
            case 'equity':
                return this.createEquityAnalysis(data);
            case 'trades':
                return this.createTradesAnalysis(data);
            case 'ml':
                return this.createMLAnalysis(data);
            case 'quantum':
                return this.createQuantumAnalysis(data);
            case 'sentiment':
                return this.createSentimentAnalysis(data);
            case 'brierscore':
                return this.createBrierAnalysis(data);
            default:
                return `<div class="data-card"><div class="data-label">Analysis</div><div class="data-value">No specific analysis available for this endpoint.</div></div>`;
        }
    }

    updateConnectionStatus() {
        const statusEl = document.getElementById('connection-status');
        const hasErrors = Object.values(this.endpointData).some(data => data.status === 'error');
        
        if (hasErrors) {
            statusEl.innerHTML = '<span>🟡</span><span>Partial Connection</span>';
            statusEl.className = 'status-badge status-warning';
        } else {
            statusEl.innerHTML = '<span>🟢</span><span>All Systems Online</span>';
            statusEl.className = 'status-badge status-online';
        }
    }

    updateSlateMetrics() {
        this.renderSlates();
    }

    isToday(timestamp) {
        const today = new Date();
        const date = new Date(timestamp);
        return date.toDateString() === today.toDateString();
    }
}

// Global functions
function closeReport() {
    document.getElementById('report-modal').style.display = 'none';
}

// Initialize dashboard
const dashboard = new EnhancedDashboard();

// Close modal when clicking outside
document.getElementById('report-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeReport();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeReport();
    }
});
