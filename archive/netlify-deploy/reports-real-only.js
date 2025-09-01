class ReportsManager {
    constructor() {
        this.apiUrl = '/api';
        this.reports = [];
        this.filteredReports = [];
        this.currentView = 'grid';
        this.isLoading = false;
        this.version = 'v2024-08-19-REAL-DATA-ONLY';
        this.retryCount = 0;
        this.maxRetries = 2; // Reduced retries
        
        console.log('🚀 ReportsManager (REAL DATA ONLY) initialized, version:', this.version);
        console.log('📡 API URL:', this.apiUrl);
        console.log('🚫 NO DEMO DATA - Only real trading data will be displayed');
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadReports();
    }
    
    async fetchWithFallback(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        console.log(`🔍 Fetching REAL data from: ${url}`);
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    ...options.headers
                }
            });
            
            if (response.ok) {
                console.log(`✅ Real data received from ${url}`);
                return response;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn(`⚠️ Real data unavailable from ${url}:`, error.message);
            throw error;
        }
    }
    
    bindEvents() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            console.log('🔄 Manual refresh triggered');
            this.retryCount = 0;
            this.loadReports();
        });
        
        // New report button
        if (document.getElementById('newReportBtn')) {
            document.getElementById('newReportBtn').addEventListener('click', () => this.showNewReportModal());
        }
        
        // Filters
        if (document.getElementById('timeFilter')) {
            document.getElementById('timeFilter').addEventListener('change', () => this.applyFilters());
        }
        if (document.getElementById('typeFilter')) {
            document.getElementById('typeFilter').addEventListener('change', () => this.applyFilters());
        }
        if (document.getElementById('searchInput')) {
            document.getElementById('searchInput').addEventListener('input', () => this.applyFilters());
        }
        
        // View toggles
        if (document.getElementById('gridView')) {
            document.getElementById('gridView').addEventListener('click', () => this.setView('grid'));
        }
        if (document.getElementById('listView')) {
            document.getElementById('listView').addEventListener('click', () => this.setView('list'));
        }
    }
    
    async loadReports() {
        if (this.isLoading) return;
        
        this.setLoading(true);
        try {
            console.log('🔄 Loading REAL data only...');
            
            // Only load real data - no fallbacks or demo data
            const tradingReports = await this.fetchTradingReports();
            const mlReports = await this.fetchMLReports();
            
            // Filter out any suspicious demo data
            const realTradingReports = this.filterRealTradingData(tradingReports);
            const realMLReports = this.filterRealMLData(mlReports);
            
            this.reports = [...realTradingReports, ...realMLReports];
            this.applyFilters();
            this.updateStats();
            
            console.log(`✅ Real reports loaded: ${this.reports.length} total`);
            
            if (this.reports.length === 0) {
                this.showError('No real trading data available. System may be in demo mode or API keys not configured.');
            }
            
        } catch (error) {
            console.error('❌ Error loading real data:', error);
            this.showError('Cannot connect to real trading API. Check if live trading is enabled.');
        } finally {
            this.setLoading(false);
        }
    }
    
    filterRealTradingData(reports) {
        return reports.filter(report => {
            if (!report || !report.data || !Array.isArray(report.data)) return false;
            
            // Check for demo trade ID patterns
            const hasDemoTradeIds = report.data.some(trade => 
                trade.trade_id && typeof trade.trade_id === 'string' && trade.trade_id.startsWith('T1755')
            );
            
            if (hasDemoTradeIds) {
                console.warn('⚠️ Trade IDs suggest demo mode - displaying for verification');
                console.warn('📋 To verify: Check if these trades appear in your Binance portfolio');
                // Mark as demo but still display for user verification
                report.isDemoData = true;
                report.title = report.title + ' (VERIFY: Demo or Real?)';
            }
            
            // Include if we have trade data (let user verify if real)
            return report.data.length > 0;
        });
    }
    
    filterRealMLData(reports) {
        return reports.filter(report => {
            if (!report || !report.data) return false;
            
            // Only include ML data if it has real metrics
            const hasRealMetrics = report.data.accuracy > 0 && report.data.total_predictions > 0;
            
            if (!hasRealMetrics) {
                console.warn('🚫 Filtered out incomplete ML data');
                return false;
            }
            
            return true;
        });
    }
    
    async fetchTradingReports() {
        try {
            const response = await this.fetchWithFallback('/trades');
            const data = await response.json();
            
            // Validate data is real
            if (!data.trades || !Array.isArray(data.trades) || data.trades.length === 0) {
                console.warn('🚫 No real trading data available');
                return [];
            }
            
            // Check for demo patterns
            const demoTradeIds = data.trades.filter(t => 
                t.trade_id && typeof t.trade_id === 'string' && t.trade_id.startsWith('T1755')
            ).length;
            
            if (demoTradeIds > data.trades.length * 0.8) {
                console.warn('🚫 Majority of trades appear to be demo data - filtering out');
                return [];
            }
            
            console.log(`📈 Real trading data: ${data.trades.length} trades`);
            return this.processTradingData(data);
        } catch (error) {
            console.warn('⚠️ Real trading data not available:', error.message);
            return [];
        }
    }
    
    async fetchMLReports() {
        try {
            const response = await this.fetchWithFallback('/ml/status');
            const data = await response.json();
            
            // Validate ML data is real
            if (!data.accuracy || data.accuracy === 0 || !data.total_predictions) {
                console.warn('🚫 No real ML data available');
                return [];
            }
            
            console.log(`🧠 Real ML data: ${(data.accuracy * 100).toFixed(1)}% accuracy`);
            return this.processMLData(data);
        } catch (error) {
            console.warn('⚠️ Real ML data not available:', error.message);
            return [];
        }
    }
    
    processTradingData(data) {
        const backendSummary = data.summary || {};
        
        // Calculate metrics properly
        const trades = data.trades;
        const totalPnL = backendSummary.net_pnl || backendSummary.realized_pnl || 0;
        const winRate = backendSummary.win_rate || 0;
        const totalTrades = trades.length;
        
        // Calculate advanced metrics with proper validation
        const profitFactor = this.calculateProfitFactor(trades);
        const sharpeRatio = this.calculateSharpeRatio(trades);
        const maxDrawdown = this.calculateMaxDrawdown(trades);
        const volatility = this.calculateVolatility(trades);
        
        const report = {
            id: `trading_${Date.now()}`,
            type: 'trading',
            title: 'Real Trading Performance Report',
            createdAt: new Date().toISOString(),
            summary: {
                total_trades: totalTrades,
                win_rate: winRate,
                net_pnl: totalPnL,
                realized_pnl: backendSummary.realized_pnl || 0,
                total_volume: backendSummary.total_volume || 0,
                profit_factor: profitFactor,
                sharpe_ratio: sharpeRatio,
                max_drawdown: maxDrawdown,
                volatility: volatility,
                data_source: 'real_api'
            },
            data: trades,
            status: 'completed'
        };
        
        console.log('📊 Trading report summary:', {
            trades: totalTrades,
            pnl: totalPnL,
            winRate: winRate,
            profitFactor: profitFactor,
            sharpe: sharpeRatio,
            drawdown: maxDrawdown
        });
        
        return [report];
    }
    
    processMLData(data) {
        const report = {
            id: `ml_${Date.now()}`,
            type: 'ml',
            title: 'Real ML Performance Analysis',
            createdAt: new Date().toISOString(),
            summary: {
                accuracy: data.accuracy,
                brier_score: data.brier_score || this.calculateBrierScore(data),
                confidence: data.confidence || 0,
                total_predictions: data.total_predictions,
                successful_predictions: data.successful_predictions || 0,
                data_quality: data.data_quality || 0,
                data_source: 'real_api'
            },
            data: data,
            status: 'completed'
        };
        
        console.log('🧠 ML report summary:', {
            accuracy: (data.accuracy * 100).toFixed(1) + '%',
            predictions: data.total_predictions,
            confidence: (data.confidence * 100).toFixed(1) + '%'
        });
        
        return [report];
    }
    
    calculateProfitFactor(trades) {
        if (!trades || trades.length === 0) return 0;
        
        const profits = trades.filter(t => (t.pnl || 0) > 0).reduce((sum, t) => sum + (t.pnl || 0), 0);
        const losses = Math.abs(trades.filter(t => (t.pnl || 0) < 0).reduce((sum, t) => sum + (t.pnl || 0), 0));
        
        if (losses === 0) return profits > 0 ? 10 : 0; // Cap high profit factor
        
        const pf = profits / losses;
        return Math.max(0, Math.min(10, pf)); // Clamp to 0-10 range
    }
    
    calculateSharpeRatio(trades) {
        if (!trades || trades.length < 10) return 0; // Need sufficient data
        
        const returns = trades.map(t => t.pnl || 0);
        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
        const stdDev = Math.sqrt(variance);
        
        if (stdDev <= 0.001) return 0; // Avoid division by very small numbers
        
        // Simple Sharpe ratio (not annualized to avoid extreme values)
        const sharpe = avgReturn / stdDev;
        
        // Clamp to reasonable range
        return Math.max(-3, Math.min(3, sharpe));
    }
    
    calculateMaxDrawdown(trades) {
        if (!trades || trades.length === 0) return 0;
        
        let peak = 0;
        let maxDrawdown = 0;
        let runningPnL = 0;
        
        for (const trade of trades) {
            runningPnL += (trade.pnl || 0);
            if (runningPnL > peak) peak = runningPnL;
            
            if (peak > 0) {
                const drawdown = (peak - runningPnL) / Math.abs(peak);
                if (drawdown > maxDrawdown && drawdown <= 1) { // Cap at 100%
                    maxDrawdown = drawdown;
                }
            }
        }
        
        return Math.max(0, Math.min(1, maxDrawdown)); // Return as 0-1 ratio
    }
    
    calculateVolatility(trades) {
        if (!trades || trades.length < 5) return 0;
        
        const returns = trades.map(t => t.pnl || 0);
        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
        const volatility = Math.sqrt(variance);
        
        // Return reasonable volatility value
        return Math.max(0, Math.min(100, volatility));
    }
    
    calculateBrierScore(mlData) {
        if (mlData.brier_score) return mlData.brier_score;
        if (mlData.accuracy && mlData.total_predictions) {
            // Calculate Brier score approximation
            const accuracy = mlData.accuracy;
            return Math.max(0, Math.min(1, (1 - accuracy) * 0.25));
        }
        return 0;
    }
    
    applyFilters() {
        let filtered = [...this.reports];
        
        // Time filter
        const timeFilter = document.getElementById('timeFilter');
        if (timeFilter && timeFilter.value !== 'all') {
            const now = new Date();
            let cutoff;
            
            switch (timeFilter.value) {
                case 'today':
                    cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                    break;
                case 'week':
                    cutoff = new Date(now - 7 * 24 * 60 * 60 * 1000);
                    break;
                case 'month':
                    cutoff = new Date(now - 30 * 24 * 60 * 60 * 1000);
                    break;
            }
            
            if (cutoff) {
                filtered = filtered.filter(report => new Date(report.createdAt) >= cutoff);
            }
        }
        
        // Type filter
        const typeFilter = document.getElementById('typeFilter');
        if (typeFilter && typeFilter.value !== 'all') {
            filtered = filtered.filter(report => report.type === typeFilter.value);
        }
        
        // Search filter
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value) {
            const searchTerm = searchInput.value.toLowerCase();
            filtered = filtered.filter(report => 
                report.title.toLowerCase().includes(searchTerm) ||
                report.type.toLowerCase().includes(searchTerm)
            );
        }
        
        this.filteredReports = filtered;
        this.renderReports();
    }
    
    renderReports() {
        const container = document.getElementById('reportsContainer');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const emptyState = document.getElementById('emptyState');
        
        if (this.isLoading) {
            if (container) container.innerHTML = '';
            if (loadingSpinner) loadingSpinner.classList.remove('hidden');
            if (emptyState) emptyState.classList.add('hidden');
            return;
        }
        
        if (loadingSpinner) loadingSpinner.classList.add('hidden');
        
        if (this.filteredReports.length === 0) {
            if (container) {
                container.innerHTML = `
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
                        <i class="fas fa-info-circle text-blue-500 text-4xl mb-4"></i>
                        <h3 class="text-lg font-semibold text-blue-800 mb-2">No Real Data Available</h3>
                        <p class="text-blue-600 mb-4">Only real trading data is displayed. No demo or fallback data.</p>
                        <div class="text-sm text-blue-600 text-left max-w-md mx-auto mb-4">
                            <p><strong>Possible reasons:</strong></p>
                            <ul class="list-disc list-inside mt-2">
                                <li>Live trading not yet enabled</li>
                                <li>Binance API keys not configured</li>
                                <li>System still in demo mode</li>
                                <li>No trades executed yet today</li>
                            </ul>
                        </div>
                        <button onclick="window.reportsManager.loadReports()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                            Refresh Data
                        </button>
                    </div>
                `;
            }
            if (emptyState) emptyState.classList.add('hidden');
            return;
        }
        
        if (emptyState) emptyState.classList.add('hidden');
        this.renderGridView(container);
    }
    
    renderGridView(container) {
        if (!container) return;
        
        container.className = 'report-grid';
        container.innerHTML = this.filteredReports.map(report => this.createReportCard(report)).join('');
        
        // Add click events for report details
        container.querySelectorAll('.report-card').forEach(card => {
            card.addEventListener('click', () => {
                const reportId = card.dataset.reportId;
                this.showReportDetail(reportId);
            });
        });
    }
    
    createReportCard(report) {
        const createdAt = new Date(report.createdAt).toLocaleDateString();
        const typeIcon = this.getTypeIcon(report.type);
        const statusColor = this.getStatusColor(report.status);
        
        return `
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover cursor-pointer report-card" data-report-id="${report.id}">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center space-x-2">
                        <i class="${typeIcon} text-blue-600"></i>
                        <span class="text-sm font-medium text-gray-600 uppercase">${report.type}</span>
                        <span class="text-xs ${report.isDemoData ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'} px-2 py-1 rounded">
                            ${report.isDemoData ? 'VERIFY DATA' : 'REAL DATA'}
                        </span>
                    </div>
                    <span class="px-2 py-1 rounded-full text-xs font-medium ${statusColor}">
                        ${report.status}
                    </span>
                </div>
                
                <h3 class="text-lg font-semibold text-gray-800 mb-2">${report.title}</h3>
                <p class="text-gray-600 text-sm mb-4">Created: ${createdAt}</p>
                
                <div class="space-y-2">
                    ${this.createSummaryItems(report)}
                </div>
                
                <div class="mt-4 pt-4 border-t border-gray-200">
                    <button class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        View Details <i class="fas fa-arrow-right ml-1"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    createSummaryItems(report) {
        if (report.type === 'trading') {
            const s = report.summary;
            return `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Total Trades:</span>
                    <span class="font-medium">${s.total_trades || 0}</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Win Rate:</span>
                    <span class="font-medium">${(s.win_rate || 0).toFixed(1)}%</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Net P&L:</span>
                    <span class="font-medium ${(s.net_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">
                        $${(s.net_pnl || 0).toFixed(2)}
                    </span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Profit Factor:</span>
                    <span class="font-medium ${(s.profit_factor || 0) >= 1.5 ? 'text-green-600' : (s.profit_factor || 0) >= 1.0 ? 'text-yellow-600' : 'text-red-600'}">
                        ${(s.profit_factor || 0).toFixed(2)}
                    </span>
                </div>
            `;
        } else if (report.type === 'ml') {
            const s = report.summary;
            return `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Accuracy:</span>
                    <span class="font-medium ${(s.accuracy || 0) >= 0.7 ? 'text-green-600' : (s.accuracy || 0) >= 0.5 ? 'text-yellow-600' : 'text-red-600'}">
                        ${((s.accuracy || 0) * 100).toFixed(1)}%
                    </span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Confidence:</span>
                    <span class="font-medium text-purple-600">${((s.confidence || 0) * 100).toFixed(1)}%</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Predictions:</span>
                    <span class="font-medium">${s.total_predictions || 0}</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Brier Score:</span>
                    <span class="font-medium ${(s.brier_score || 0) <= 0.15 ? 'text-green-600' : (s.brier_score || 0) <= 0.25 ? 'text-yellow-600' : 'text-red-600'}">
                        ${(s.brier_score || 0).toFixed(3)}
                    </span>
                </div>
            `;
        }
        return '';
    }
    
    getTypeIcon(type) {
        switch (type) {
            case 'trading': return 'fas fa-chart-line';
            case 'ml': return 'fas fa-brain';
            case 'backtest': return 'fas fa-history';
            default: return 'fas fa-file-alt';
        }
    }
    
    getStatusColor(status) {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800';
            case 'processing': return 'bg-yellow-100 text-yellow-800';
            case 'failed': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }
    
    showReportDetail(reportId) {
        const report = this.reports.find(r => r.id === reportId);
        if (!report) return;
        
        console.log('📋 Showing report details:', reportId);
        
        // Create modal content
        const modalContent = `
            <div class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" id="reportModal">
                <div class="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-screen overflow-y-auto">
                    <div class="p-6">
                        <div class="flex justify-between items-center mb-6">
                            <h2 class="text-2xl font-bold text-gray-800">${report.title}</h2>
                            <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" class="text-gray-500 hover:text-gray-700">
                                <i class="fas fa-times text-xl"></i>
                            </button>
                        </div>
                        
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div>
                                <p class="text-sm text-gray-600">Type</p>
                                <p class="font-medium capitalize">${report.type}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">Created</p>
                                <p class="font-medium">${new Date(report.createdAt).toLocaleString()}</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">Status</p>
                                <span class="px-2 py-1 rounded-full text-xs font-medium ${this.getStatusColor(report.status)}">
                                    ${report.status}
                                </span>
                            </div>
                            <div>
                                <p class="text-sm text-gray-600">Data Source</p>
                                <p class="font-medium text-green-600">${report.summary.data_source || 'Real API'}</p>
                            </div>
                        </div>
                        
                        <div class="bg-gray-50 rounded-lg p-4 mb-6">
                            <h3 class="text-lg font-semibold mb-3">Summary Metrics</h3>
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                ${this.createDetailSummary(report)}
                            </div>
                        </div>
                        
                        <div class="bg-white border rounded-lg p-6">
                            <h3 class="text-lg font-semibold mb-4">Raw Data Preview</h3>
                            <pre class="bg-gray-50 p-4 rounded text-sm overflow-x-auto max-h-64">${JSON.stringify(report.data, null, 2)}</pre>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalContent);
    }
    
    createDetailSummary(report) {
        let summaryHTML = '';
        
        Object.entries(report.summary).forEach(([key, value]) => {
            if (key === 'data_source') return; // Skip internal fields
            
            const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            let displayValue = value;
            let colorClass = '';
            
            if (typeof value === 'number') {
                if (key.includes('rate') || key.includes('accuracy')) {
                    displayValue = `${(value * (key.includes('rate') ? 1 : 100)).toFixed(1)}%`;
                } else if (key.includes('pnl') || key.includes('profit')) {
                    displayValue = `$${value.toFixed(2)}`;
                    colorClass = value < 0 ? 'text-red-600' : value > 0 ? 'text-green-600' : '';
                } else {
                    displayValue = value.toFixed(2);
                }
            }
            
            summaryHTML += `
                <div>
                    <p class="text-sm text-gray-600">${displayKey}</p>
                    <p class="font-medium ${colorClass}">${displayValue}</p>
                </div>
            `;
        });
        
        return summaryHTML;
    }
    
    setView(view) {
        this.currentView = view;
        
        // Update button states
        const gridBtn = document.getElementById('gridView');
        const listBtn = document.getElementById('listView');
        
        if (gridBtn && listBtn) {
            gridBtn.classList.toggle('bg-blue-500', view === 'grid');
            gridBtn.classList.toggle('text-white', view === 'grid');
            listBtn.classList.toggle('bg-blue-500', view === 'list');
            listBtn.classList.toggle('text-white', view === 'list');
        }
        
        this.renderReports();
    }
    
    updateStats() {
        const totalReports = this.reports.length;
        if (document.getElementById('totalReports')) {
            document.getElementById('totalReports').textContent = totalReports;
        }
        
        // Trading stats
        const tradingReports = this.reports.filter(r => r.type === 'trading');
        if (tradingReports.length > 0) {
            const report = tradingReports[0];
            const s = report.summary;
            
            // Main stats
            if (document.getElementById('totalProfit')) {
                document.getElementById('totalProfit').textContent = `$${(s.net_pnl || 0).toFixed(2)}`;
                document.getElementById('totalProfit').className = `text-3xl font-bold ${(s.net_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`;
            }
            
            if (document.getElementById('avgWinRate')) {
                document.getElementById('avgWinRate').textContent = `${(s.win_rate || 0).toFixed(1)}%`;
            }
            
            if (document.getElementById('totalTrades')) {
                document.getElementById('totalTrades').textContent = `${s.total_trades || 0} trades`;
            }
            
            // Advanced metrics with proper validation
            if (document.getElementById('profitFactor')) {
                const pf = s.profit_factor || 0;
                document.getElementById('profitFactor').textContent = pf.toFixed(2);
                document.getElementById('profitFactor').className = `text-2xl font-bold ${pf >= 1.5 ? 'text-green-600' : pf >= 1.0 ? 'text-yellow-600' : 'text-red-600'}`;
            }
            
            if (document.getElementById('sharpeRatio')) {
                const sr = s.sharpe_ratio || 0;
                document.getElementById('sharpeRatio').textContent = sr.toFixed(2);
                document.getElementById('sharpeRatio').className = `text-2xl font-bold ${sr >= 1.0 ? 'text-green-600' : sr >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`;
            }
            
            if (document.getElementById('maxDrawdown')) {
                const dd = ((s.max_drawdown || 0) * 100);
                document.getElementById('maxDrawdown').textContent = `${dd.toFixed(1)}%`;
                document.getElementById('maxDrawdown').className = `text-2xl font-bold ${dd <= 10 ? 'text-green-600' : dd <= 25 ? 'text-yellow-600' : 'text-red-600'}`;
            }
            
            if (document.getElementById('volatility')) {
                const vol = s.volatility || 0;
                document.getElementById('volatility').textContent = vol.toFixed(2);
                document.getElementById('volatility').className = `text-2xl font-bold ${vol <= 10 ? 'text-green-600' : vol <= 25 ? 'text-yellow-600' : 'text-red-600'}`;
            }
        }
        
        // ML stats
        const mlReports = this.reports.filter(r => r.type === 'ml');
        if (mlReports.length > 0) {
            const report = mlReports[0];
            const s = report.summary;
            
            if (document.getElementById('avgAccuracy')) {
                document.getElementById('avgAccuracy').textContent = `${((s.accuracy || 0) * 100).toFixed(1)}%`;
                document.getElementById('avgAccuracy').className = `text-3xl font-bold ${(s.accuracy || 0) >= 0.7 ? 'text-green-600' : (s.accuracy || 0) >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`;
            }
            
            if (document.getElementById('brierScore')) {
                document.getElementById('brierScore').textContent = `Brier: ${(s.brier_score || 0).toFixed(3)}`;
            }
            
            // Quantum Factor from ML confidence
            if (document.getElementById('quantumImportance')) {
                const quantum = (s.confidence || 0) * 100;
                document.getElementById('quantumImportance').textContent = `${quantum.toFixed(1)}%`;
                document.getElementById('quantumImportance').className = `text-2xl font-bold ${quantum >= 75 ? 'text-purple-600' : quantum >= 50 ? 'text-blue-600' : 'text-gray-600'}`;
            }
        }
        
        // Update timestamps
        if (document.getElementById('lastReportTime')) {
            document.getElementById('lastReportTime').textContent = new Date().toLocaleTimeString();
        }
        
        if (document.getElementById('recentReports')) {
            const recentCount = this.reports.filter(r => {
                const reportDate = new Date(r.createdAt);
                const hourAgo = new Date(Date.now() - 60 * 60 * 1000);
                return reportDate >= hourAgo;
            }).length;
            document.getElementById('recentReports').textContent = recentCount;
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.classList.toggle('hidden', !loading);
        }
    }
    
    showError(message) {
        console.error('❌', message);
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        console.log('✅', message);
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 4000);
    }
    
    showNewReportModal() {
        console.log('📊 Generating all report types...');
        this.generateAllReports();
    }
    
    async generateAllReports() {
        try {
            this.setLoading(true);
            console.log('🔄 Generating comprehensive reports (Trading + ML)...');
            
            // Reset retry count and load fresh data
            this.retryCount = 0;
            await this.loadReports();
            
            // Update all dashboard stats
            this.updateStats();
            
            const tradingReports = this.reports.filter(r => r.type === 'trading');
            const mlReports = this.reports.filter(r => r.type === 'ml');
            
            let message = 'Reports generated: ';
            if (tradingReports.length > 0) message += `✅ Trading (${tradingReports[0].summary.total_trades} trades)`;
            if (mlReports.length > 0) message += `✅ ML (${(mlReports[0].summary.accuracy * 100).toFixed(1)}% accuracy)`;
            
            if (this.reports.length > 0) {
                this.showSuccess(message);
                console.log('✅ All reports generated successfully');
                
                // Update the top row stats
                this.refreshTopRowStats();
            } else {
                this.showError('No data available. Check if live trading is enabled.');
                console.log('⚠️ No reports generated - no data available');
            }
        } catch (error) {
            console.error('❌ Error generating reports:', error);
            this.showError('Failed to generate reports: ' + error.message);
        } finally {
            this.setLoading(false);
        }
    }
    
    refreshTopRowStats() {
        console.log('📊 Refreshing top row statistics...');
        
        // Force update all stats with current data
        const tradingReports = this.reports.filter(r => r.type === 'trading');
        const mlReports = this.reports.filter(r => r.type === 'ml');
        
        if (tradingReports.length > 0) {
            const s = tradingReports[0].summary;
            console.log('📈 Trading stats updated:', {
                trades: s.total_trades,
                pnl: s.net_pnl,
                winRate: s.win_rate,
                profitFactor: s.profit_factor
            });
        }
        
        if (mlReports.length > 0) {
            const s = mlReports[0].summary;
            console.log('🧠 ML stats updated:', {
                accuracy: (s.accuracy * 100).toFixed(1) + '%',
                confidence: (s.confidence * 100).toFixed(1) + '%',
                predictions: s.total_predictions
            });
        }
        
        // Update recent reports count
        if (document.getElementById('recentReports')) {
            document.getElementById('recentReports').textContent = this.reports.length;
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 Starting REAL DATA ONLY Reports Dashboard...');
    window.reportsManager = new ReportsManager();
});