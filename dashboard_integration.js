/**
 * BOTTIE ENHANCED DASHBOARD INTEGRATION
 * Optimized for the new reporting system with human-readable commentary
 */

class BottieDashboard {
    constructor(baseUrl = 'https://bottie-1.onrender.com') {
        this.baseUrl = baseUrl;
        this.cache = new Map();
        this.lastUpdate = 0;
        this.updateInterval = 30000; // 30 seconds instead of constant polling
        this.isBusinessHours = this.checkBusinessHours();
        
        console.log('🚀 Initializing Enhanced Bottie Dashboard...');
        this.init();
    }

    checkBusinessHours() {
        const now = new Date();
        const utcHour = now.getUTCHours();
        return utcHour >= 7 && utcHour < 18; // 7AM-6PM GMT
    }

    async init() {
        // Load initial data
        await this.loadAllData();
        
        // Set up automatic updates
        setInterval(() => {
            this.loadAllData();
        }, this.updateInterval);
        
        // Update business hours check every hour
        setInterval(() => {
            this.isBusinessHours = this.checkBusinessHours();
        }, 3600000);
    }

    async apiCall(endpoint) {
        const cacheKey = endpoint;
        const now = Date.now();
        
        // Use cache if recent (30 seconds)
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (now - cached.timestamp < 30000) {
                return cached.data;
            }
        }

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            
            // Cache the result
            this.cache.set(cacheKey, { data, timestamp: now });
            return data;
        } catch (error) {
            console.error(`❌ Error fetching ${endpoint}:`, error);
            return null;
        }
    }

    async loadAllData() {
        console.log('📊 Loading dashboard data...');
        
        // Load comprehensive report (this replaces multiple individual calls)
        const comprehensiveReport = await this.apiCall('/reports/comprehensive');
        if (comprehensiveReport) {
            this.updateComprehensiveView(comprehensiveReport);
        }

        // Load system status
        const reportStatus = await this.apiCall('/reports/status');
        if (reportStatus) {
            this.updateSystemStatus(reportStatus);
        }

        // Load only essential real-time data (reduce API calls)
        const essentialData = await Promise.all([
            this.apiCall('/trading/status'),
            this.apiCall('/health'),
            this.apiCall('/positions')
        ]);

        if (essentialData[0]) this.updateTradingStatus(essentialData[0]);
        if (essentialData[1]) this.updateHealthStatus(essentialData[1]);
        if (essentialData[2]) this.updatePositionsView(essentialData[2]);

        console.log('✅ Dashboard data loaded');
    }

    updateComprehensiveView(report) {
        const analysis = report.analysis;
        
        // Update main dashboard with formatted summary
        this.updateElement('comprehensive-report', report.formatted_summary);
        
        // Update individual sections with structured data
        this.updatePortfolioSummary(analysis.portfolio_summary);
        this.updateTradingActivity(analysis.trading_activity);
        this.updateInsights(analysis.commentary);
        this.updateRecommendations(analysis.recommendations);
        this.updateRiskAssessment(analysis.risk_assessment);
    }

    updatePortfolioSummary(portfolio) {
        const html = `
            <div class="portfolio-summary">
                <h3>💰 Portfolio Status</h3>
                <div class="metrics">
                    <div class="metric">
                        <span class="label">Total Equity</span>
                        <span class="value">$${portfolio.total_equity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Active Positions</span>
                        <span class="value">${portfolio.total_positions}</span>
                    </div>
                    <div class="metric ${portfolio.total_pnl >= 0 ? 'positive' : 'negative'}">
                        <span class="label">Total P&L</span>
                        <span class="value">$${portfolio.total_pnl.toFixed(2)} (${portfolio.total_pnl_percentage >= 0 ? '+' : ''}${portfolio.total_pnl_percentage.toFixed(1)}%)</span>
                    </div>
                    <div class="metric">
                        <span class="label">Winners / Losers</span>
                        <span class="value">${portfolio.profitable_positions} / ${portfolio.losing_positions}</span>
                    </div>
                </div>
            </div>
        `;
        this.updateElement('portfolio-summary', html);
    }

    updateTradingActivity(activity) {
        const html = `
            <div class="trading-activity">
                <h3>📈 Trading Activity (24h)</h3>
                <div class="metrics">
                    <div class="metric">
                        <span class="label">Trades Executed</span>
                        <span class="value">${activity.trades_24h}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Signals Generated</span>
                        <span class="value">${activity.signals_24h}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Actionable Signals</span>
                        <span class="value">${activity.actionable_signals}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Avg Confidence</span>
                        <span class="value">${(activity.avg_signal_confidence * 100).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
        `;
        this.updateElement('trading-activity', html);
    }

    updateInsights(commentary) {
        const html = `
            <div class="insights">
                <h3>🎯 Key Insights</h3>
                <ul class="insight-list">
                    ${commentary.map(insight => `<li class="insight-item">${insight}</li>`).join('')}
                </ul>
            </div>
        `;
        this.updateElement('insights', html);
    }

    updateRecommendations(recommendations) {
        const html = `
            <div class="recommendations">
                <h3>💡 Recommendations</h3>
                <ul class="recommendation-list">
                    ${recommendations.map(rec => `<li class="recommendation-item">${rec}</li>`).join('')}
                </ul>
            </div>
        `;
        this.updateElement('recommendations', html);
    }

    updateRiskAssessment(risk) {
        const riskClass = risk.level.toLowerCase();
        const html = `
            <div class="risk-assessment">
                <h3>⚠️ Risk Assessment</h3>
                <div class="risk-level ${riskClass}">
                    <span class="risk-label">Level:</span>
                    <span class="risk-value">${risk.level}</span>
                </div>
                <ul class="risk-factors">
                    ${risk.factors.map(factor => `<li class="risk-factor">${factor}</li>`).join('')}
                </ul>
                <div class="risk-metrics">
                    <div class="metric">
                        <span class="label">Diversification Score</span>
                        <span class="value">${risk.diversification_score}/10</span>
                    </div>
                    <div class="metric">
                        <span class="label">Max Position Size</span>
                        <span class="value">$${risk.max_position_size.toFixed(2)}</span>
                    </div>
                </div>
            </div>
        `;
        this.updateElement('risk-assessment', html);
    }

    updateSystemStatus(status) {
        const html = `
            <div class="system-status">
                <h3>📊 Reporting System</h3>
                <div class="status-info">
                    <div class="status-item">
                        <span class="label">Auto Reports:</span>
                        <span class="value ${status.auto_reports_enabled ? 'enabled' : 'disabled'}">
                            ${status.auto_reports_enabled ? '✅ Enabled' : '❌ Disabled'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="label">Business Hours:</span>
                        <span class="value">${status.business_hours ? '✅ Yes' : '❌ No'}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Report Frequency:</span>
                        <span class="value">${status.report_frequency}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Next Report:</span>
                        <span class="value">${status.next_report_in}</span>
                    </div>
                </div>
            </div>
        `;
        this.updateElement('system-status', html);
    }

    updateTradingStatus(status) {
        const html = `
            <div class="trading-status">
                <h3>🤖 Trading Engine</h3>
                <div class="status-grid">
                    <div class="status-item ${status.trade_enabled ? 'enabled' : 'disabled'}">
                        <span class="label">Trading:</span>
                        <span class="value">${status.trade_enabled ? '✅ Enabled' : '❌ Disabled'}</span>
                    </div>
                    <div class="status-item ${status.execution_enabled ? 'enabled' : 'disabled'}">
                        <span class="label">Execution:</span>
                        <span class="value">${status.execution_enabled ? '✅ Enabled' : '❌ Disabled'}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Recent Signals:</span>
                        <span class="value">${status.recent_signals}</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Recent Trades:</span>
                        <span class="value">${status.recent_trades}</span>
                    </div>
                </div>
            </div>
        `;
        this.updateElement('trading-status', html);
    }

    updateHealthStatus(health) {
        const isHealthy = health.ok;
        const html = `
            <div class="health-status ${isHealthy ? 'healthy' : 'unhealthy'}">
                <h3>💚 System Health</h3>
                <div class="health-indicator">
                    <span class="status-dot ${isHealthy ? 'green' : 'red'}"></span>
                    <span class="status-text">${isHealthy ? 'Healthy' : 'Issues Detected'}</span>
                </div>
                <div class="health-details">
                    <div class="detail">Mode: ${health.mode}</div>
                    <div class="detail">Exchange: ${health.exchange}</div>
                    <div class="detail">Equity: $${health.equity?.toFixed(2) || 'N/A'}</div>
                </div>
            </div>
        `;
        this.updateElement('health-status', html);
    }

    updatePositionsView(positions) {
        const positionList = Object.entries(positions.positions || {});
        const html = `
            <div class="positions-view">
                <h3>📊 Current Positions</h3>
                <div class="positions-list">
                    ${positionList.map(([symbol, position]) => `
                        <div class="position-item">
                            <div class="position-symbol">${symbol}</div>
                            <div class="position-details">
                                <span class="quantity">${position.quantity || 0}</span>
                                <span class="value">$${(position.market_value || 0).toFixed(2)}</span>
                                <span class="pnl ${(position.pnl || 0) >= 0 ? 'positive' : 'negative'}">
                                    ${(position.pnl_percentage || 0) >= 0 ? '+' : ''}${(position.pnl_percentage || 0).toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        this.updateElement('positions-view', html);
    }

    updateElement(elementId, content) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = content;
        } else {
            console.warn(`Element with ID '${elementId}' not found`);
        }
    }

    // Manual refresh methods
    async refreshComprehensiveReport() {
        console.log('🔄 Refreshing comprehensive report...');
        const report = await this.apiCall('/reports/on-demand');
        if (report) {
            this.updateComprehensiveView(report);
        }
    }

    async refreshDailyReport() {
        console.log('🔄 Refreshing daily report...');
        const report = await this.apiCall('/reports/daily');
        if (report) {
            const dailyData = report.reports[0];
            this.updateElement('daily-report', dailyData.formatted_report);
        }
    }

    // Utility methods
    formatTimestamp(timestamp) {
        return new Date(timestamp * 1000).toLocaleString();
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(amount);
    }

    formatPercentage(value) {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    }
}

// CSS Styles for the enhanced dashboard
const dashboardStyles = `
    .portfolio-summary, .trading-activity, .insights, .recommendations, 
    .risk-assessment, .system-status, .trading-status, .health-status, 
    .positions-view {
        margin-bottom: 20px;
        padding: 15px;
        border: 1px solid #e3e3e3;
        border-radius: 8px;
        background: #fafafa;
    }

    .metrics, .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 10px;
    }

    .metric, .status-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 12px;
        background: white;
        border-radius: 6px;
        border: 1px solid #e3e3e3;
    }

    .metric.positive .value { color: #16a34a; }
    .metric.negative .value { color: #dc2626; }

    .insight-list, .recommendation-list, .risk-factors {
        list-style: none;
        padding: 0;
        margin: 10px 0;
    }

    .insight-item, .recommendation-item, .risk-factor {
        padding: 8px 12px;
        margin: 5px 0;
        background: white;
        border-radius: 6px;
        border-left: 4px solid #3b82f6;
    }

    .risk-level.low { color: #16a34a; }
    .risk-level.medium { color: #f59e0b; }
    .risk-level.high { color: #dc2626; }

    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-dot.green { background: #16a34a; }
    .status-dot.red { background: #dc2626; }

    .position-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 12px;
        margin: 5px 0;
        background: white;
        border-radius: 6px;
        border: 1px solid #e3e3e3;
    }

    .position-details {
        display: flex;
        gap: 15px;
    }

    .pnl.positive { color: #16a34a; }
    .pnl.negative { color: #dc2626; }

    .enabled { color: #16a34a; }
    .disabled { color: #dc2626; }
`;

// Initialize dashboard when DOM is ready
if (typeof document !== 'undefined') {
    // Add styles
    const styleSheet = document.createElement('style');
    styleSheet.textContent = dashboardStyles;
    document.head.appendChild(styleSheet);

    // Initialize dashboard
    document.addEventListener('DOMContentLoaded', () => {
        window.bottieDashboard = new BottieDashboard();
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BottieDashboard;
}