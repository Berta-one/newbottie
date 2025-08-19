class ReportsManager {
    constructor() {
        this.apiUrl = '/api';
        this.reports = [];
        this.filteredReports = [];
        this.currentView = 'grid';
        this.isLoading = false;
        this.version = 'v2024-08-19-NO-RETRY-LOOP';
        this.retryCount = 0;
        this.maxRetries = 3;
        
        console.log('🚀 ReportsManager (No Retry Loop) initialized, version:', this.version, 'API URL:', this.apiUrl);
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadReports();
        // Remove auto-refresh to prevent endless loops
        // this.startAutoRefresh();
    }
    
    async fetchWithFallback(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        console.log(`🔍 Fetching (attempt ${this.retryCount + 1}): ${url}`);
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    ...options.headers
                }
            });
            
            console.log(`📊 Response: ${response.status} ${response.statusText}`);
            
            if (response.ok) {
                console.log(`✅ Success from ${url}`);
                this.retryCount = 0; // Reset retry count on success
                return response;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.log(`💥 Error from ${url}:`, error.message);
            this.retryCount++;
            
            if (this.retryCount >= this.maxRetries) {
                console.log(`🛑 Max retries (${this.maxRetries}) reached for ${endpoint}`);
                throw new Error(`Max retries exceeded for ${endpoint}`);
            }
            
            throw error;
        }
    }
    
    bindEvents() {
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.retryCount = 0; // Reset retry count on manual refresh
            this.loadReports();
        });
        
        // Add other event listeners as needed
        if (document.getElementById('newReportBtn')) {
            document.getElementById('newReportBtn').addEventListener('click', () => this.showNewReportModal());
        }
    }
    
    async loadReports() {
        if (this.isLoading) {
            console.log('🔄 Already loading, skipping...');
            return;
        }
        
        this.setLoading(true);
        try {
            console.log('🔄 Loading reports...');
            
            // Try to load reports with error handling
            const tradingReports = await this.fetchTradingReports();
            const mlReports = await this.fetchMLReports();
            
            this.reports = [...tradingReports, ...mlReports];
            this.applyFilters();
            this.updateStats();
            
            console.log(`✅ Reports loaded: ${this.reports.length} total`);
            
        } catch (error) {
            console.error('❌ Error loading reports:', error);
            this.showError('API endpoints temporarily unavailable. Service may be restarting after configuration changes.');
        } finally {
            this.setLoading(false);
        }
    }
    
    async fetchTradingReports() {
        try {
            const response = await this.fetchWithFallback('/trades');
            const data = await response.json();
            console.log('📈 Trading data received:', data.trades?.length || 0, 'trades');
            return this.processTradingData(data);
        } catch (error) {
            console.warn('⚠️ Trading endpoint not available:', error.message);
            return [];
        }
    }
    
    async fetchMLReports() {
        try {
            const response = await this.fetchWithFallback('/ml/status');
            const data = await response.json();
            console.log('🧠 ML data received:', data);
            return this.processMLData(data);
        } catch (error) {
            console.warn('⚠️ ML endpoint not available:', error.message);
            return [];
        }
    }
    
    processTradingData(data) {
        if (!data || !Array.isArray(data.trades)) return [];
        
        const backendSummary = data.summary || {};
        
        const report = {
            id: `trading_${Date.now()}`,
            type: 'trading',
            title: 'Trading Performance Report',
            createdAt: new Date().toISOString(),
            summary: {
                total_trades: data.trades.length,
                win_rate: backendSummary.win_rate || this.calculateWinRate(data.trades),
                net_pnl: backendSummary.net_pnl || backendSummary.realized_pnl || this.calculateTotalProfit(data.trades),
                realized_pnl: backendSummary.realized_pnl || 0,
                total_volume: backendSummary.total_volume || 0,
                profit_factor: this.calculateProfitFactor(data.trades),
                sharpe_ratio: this.calculateSharpeRatio(data.trades),
                max_drawdown: this.calculateMaxDrawdown(data.trades),
                volatility: this.calculateVolatility(data.trades)
            },
            data: data.trades,
            status: 'completed'
        };
        
        return [report];
    }
    
    processMLData(data) {
        const report = {
            id: `ml_${Date.now()}`,
            type: 'ml',
            title: 'ML Performance Analysis',
            createdAt: new Date().toISOString(),
            summary: {
                accuracy: data.accuracy || 0,
                brier_score: data.brier_score || this.calculateBrierScore(data) || 0,
                confidence: data.confidence || 0,
                total_predictions: data.total_predictions || 0,
                successful_predictions: data.successful_predictions || 0
            },
            data: data,
            status: 'completed'
        };
        
        return [report];
    }
    
    calculateWinRate(trades) {
        if (!trades || trades.length === 0) return 0;
        const wins = trades.filter(t => (t.profit || t.pnl || 0) > 0).length;
        return (wins / trades.length) * 100;
    }
    
    calculateTotalProfit(trades) {
        if (!trades || trades.length === 0) return 0;
        return trades.reduce((sum, t) => sum + (t.profit || t.pnl || 0), 0);
    }
    
    calculateProfitFactor(trades) {
        if (!trades || trades.length === 0) return 0;
        const profits = trades.filter(t => (t.pnl || 0) > 0).reduce((sum, t) => sum + (t.pnl || 0), 0);
        const losses = Math.abs(trades.filter(t => (t.pnl || 0) < 0).reduce((sum, t) => sum + (t.pnl || 0), 0));
        return losses > 0 ? profits / losses : (profits > 0 ? 999 : 0);
    }
    
    calculateSharpeRatio(trades) {
        if (!trades || trades.length < 2) return 0;
        const returns = trades.map(t => t.pnl || 0);
        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
        const stdDev = Math.sqrt(variance);
        return stdDev > 0 ? avgReturn / stdDev : 0;
    }
    
    calculateMaxDrawdown(trades) {
        if (!trades || trades.length === 0) return 0;
        let peak = 0;
        let maxDrawdown = 0;
        let runningPnL = 0;
        
        for (const trade of trades) {
            runningPnL += (trade.pnl || 0);
            if (runningPnL > peak) peak = runningPnL;
            const drawdown = peak > 0 ? (peak - runningPnL) / peak : 0;
            if (drawdown > maxDrawdown) maxDrawdown = drawdown;
        }
        
        return maxDrawdown;
    }
    
    calculateVolatility(trades) {
        if (!trades || trades.length < 2) return 0;
        const returns = trades.map(t => t.pnl || 0);
        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
        const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
        return Math.sqrt(variance);
    }
    
    calculateBrierScore(mlData) {
        if (mlData.accuracy && mlData.total_predictions) {
            const accuracy = mlData.accuracy;
            return (1 - accuracy) * 0.25; // Rough approximation
        }
        return 0;
    }
    
    applyFilters() {
        this.filteredReports = [...this.reports];
        this.renderReports();
    }
    
    renderReports() {
        const container = document.getElementById('reportsContainer');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const emptyState = document.getElementById('emptyState');
        
        if (this.isLoading) {
            container.innerHTML = '';
            loadingSpinner.classList.remove('hidden');
            emptyState.classList.add('hidden');
            return;
        }
        
        loadingSpinner.classList.add('hidden');
        
        if (this.filteredReports.length === 0) {
            container.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                    <i class="fas fa-exclamation-triangle text-yellow-500 text-4xl mb-4"></i>
                    <h3 class="text-lg font-semibold text-yellow-800 mb-2">API Endpoints Unavailable</h3>
                    <p class="text-yellow-600 mb-4">The trading API is temporarily unavailable. This may be due to:</p>
                    <ul class="text-sm text-yellow-600 text-left max-w-md mx-auto">
                        <li>• Service restarting after API key changes</li>
                        <li>• Binance API connection issues</li>
                        <li>• Network connectivity problems</li>
                    </ul>
                    <button onclick="window.location.reload()" class="mt-4 bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg">
                        Retry
                    </button>
                </div>
            `;
            emptyState.classList.add('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');
        this.renderGridView(container);
    }
    
    renderGridView(container) {
        container.className = 'report-grid';
        container.innerHTML = this.filteredReports.map(report => this.createReportCard(report)).join('');
    }
    
    createReportCard(report) {
        const createdAt = new Date(report.createdAt).toLocaleDateString();
        const typeIcon = report.type === 'trading' ? 'fa-chart-line' : 'fa-brain';
        
        return `
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center space-x-2">
                        <i class="fas ${typeIcon} text-blue-600"></i>
                        <span class="text-sm font-medium text-gray-600 uppercase">${report.type}</span>
                    </div>
                    <span class="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        completed
                    </span>
                </div>
                
                <h3 class="text-lg font-semibold text-gray-800 mb-2">${report.title}</h3>
                <p class="text-gray-600 text-sm mb-4">Created: ${createdAt}</p>
                
                <div class="space-y-2">
                    ${this.createSummaryItems(report)}
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
                    <span class="font-medium">${(s.profit_factor || 0).toFixed(2)}</span>
                </div>
            `;
        } else if (report.type === 'ml') {
            const s = report.summary;
            return `
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Accuracy:</span>
                    <span class="font-medium">${((s.accuracy || 0) * 100).toFixed(1)}%</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Confidence:</span>
                    <span class="font-medium">${((s.confidence || 0) * 100).toFixed(1)}%</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Predictions:</span>
                    <span class="font-medium">${s.total_predictions || 0}</span>
                </div>
            `;
        }
        return '';
    }
    
    updateStats() {
        const totalReports = this.reports.length;
        document.getElementById('totalReports').textContent = totalReports;
        
        // Trading stats
        const tradingReports = this.reports.filter(r => r.type === 'trading');
        if (tradingReports.length > 0) {
            const report = tradingReports[0];
            const s = report.summary;
            
            document.getElementById('totalProfit').textContent = `$${(s.net_pnl || 0).toFixed(2)}`;
            document.getElementById('totalProfit').className = `text-3xl font-bold ${(s.net_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`;
            document.getElementById('avgWinRate').textContent = `${(s.win_rate || 0).toFixed(1)}%`;
            
            // Advanced metrics
            if (document.getElementById('profitFactor')) {
                document.getElementById('profitFactor').textContent = (s.profit_factor || 0).toFixed(2);
                document.getElementById('sharpeRatio').textContent = (s.sharpe_ratio || 0).toFixed(2);
                document.getElementById('maxDrawdown').textContent = `${((s.max_drawdown || 0) * 100).toFixed(1)}%`;
                document.getElementById('volatility').textContent = (s.volatility || 0).toFixed(2);
            }
        }
        
        // ML stats
        const mlReports = this.reports.filter(r => r.type === 'ml');
        if (mlReports.length > 0) {
            const report = mlReports[0];
            const s = report.summary;
            
            document.getElementById('avgAccuracy').textContent = `${((s.accuracy || 0) * 100).toFixed(1)}%`;
            document.getElementById('avgAccuracy').className = `text-3xl font-bold ${(s.accuracy || 0) >= 0.7 ? 'text-green-600' : (s.accuracy || 0) >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`;
            
            if (document.getElementById('brierScore')) {
                document.getElementById('brierScore').textContent = `Brier: ${(s.brier_score || 0).toFixed(3)}`;
            }
        }
        
        // Update last report time
        if (this.reports.length > 0) {
            document.getElementById('lastReportTime').textContent = new Date().toLocaleTimeString();
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            if (loading) {
                spinner.classList.remove('hidden');
            } else {
                spinner.classList.add('hidden');
            }
        }
    }
    
    showError(message) {
        console.error('❌', message);
        const container = document.getElementById('reportsContainer');
        if (container) {
            container.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
                    <h3 class="text-lg font-semibold text-red-800 mb-2">API Connection Error</h3>
                    <p class="text-red-600 mb-4">${message}</p>
                    <button onclick="window.reportsManager.loadReports()" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
    
    // Placeholder methods
    showNewReportModal() { console.log('New report modal'); }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 Starting Reports Dashboard (No Retry Loop)...');
    window.reportsManager = new ReportsManager();
});