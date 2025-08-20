class ReportsManager {
    constructor() {
        // NUCLEAR FIX - Always use direct Render API endpoints
        this.apiUrl = 'https://bottie-1.onrender.com';  // NO /api prefix ever!
        
        this.reports = [];
        this.filteredReports = [];
        this.currentView = 'grid';
        this.isLoading = false;
        this.version = 'v2024-01-17-NUCLEAR-FIX';
        
        console.log('🚀 NUCLEAR FIX ReportsManager initialized, version:', this.version);
        console.log('📡 API URL (NO /api):', this.apiUrl);
        console.log('🌐 Current hostname:', window.location.hostname);
        console.log('📍 Current origin:', window.location.origin);
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadReports();
        this.startAutoRefresh();
    }
    
    // FIXED: Direct API calls only
    async fetchWithFallback(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;  // Direct endpoint, no /api
        console.log(`🔍 NUCLEAR FIX - Fetching from: ${url}`);
        
        try {
            const response = await fetch(url, {
                ...options,
                mode: 'cors',
                credentials: 'omit',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Origin': window.location.origin,
                    ...options.headers
                }
            });
            
            console.log(`📊 Response: ${response.status} ${response.statusText}`);
            
            if (response.ok) {
                console.log(`✅ SUCCESS from ${url}`);
                return response;
            } else {
                console.log(`❌ FAILED ${url}: ${response.status}`);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.log(`💥 ERROR from ${url}:`, error.message);
            throw error;
        }
    }
    
    bindEvents() {
        // Navigation buttons
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadReports());
        document.getElementById('newReportBtn').addEventListener('click', () => this.showNewReportModal());
        
        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => this.hideNewReportModal());
        document.getElementById('closeDetailModal').addEventListener('click', () => this.hideDetailModal());
        document.getElementById('cancelReport').addEventListener('click', () => this.hideNewReportModal());
        
        // Form submission
        document.getElementById('newReportForm').addEventListener('submit', (e) => this.handleNewReport(e));
        
        // Filters
        document.getElementById('timeFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('typeFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('searchInput').addEventListener('input', () => this.applyFilters());
        document.getElementById('searchBtn').addEventListener('click', () => this.applyFilters());
        
        // View toggles
        document.getElementById('gridView').addEventListener('click', () => this.setView('grid'));
        document.getElementById('listView').addEventListener('click', () => this.setView('list'));
        
        // Close modals on outside click
        document.getElementById('newReportModal').addEventListener('click', (e) => {
            if (e.target.id === 'newReportModal') this.hideNewReportModal();
        });
        document.getElementById('reportDetailModal').addEventListener('click', (e) => {
            if (e.target.id === 'reportDetailModal') this.hideDetailModal();
        });
    }
    
    async loadReports() {
        this.setLoading(true);
        try {
            console.log('🔄 Loading reports...');
            // Load existing reports from various sources
            const [tradingReports, mlReports] = await Promise.all([
                this.fetchTradingReports(),
                this.fetchMLReports()
            ]);
            
            this.reports = [...tradingReports, ...mlReports];
            this.applyFilters();
            this.updateStats();
            console.log('✅ Reports loaded successfully:', this.reports.length);
            
        } catch (error) {
            console.error('❌ Error loading reports:', error);
            this.showError('Failed to load reports. Check if the API server is running and accessible.');
        } finally {
            this.setLoading(false);
        }
    }
    
    async fetchTradingReports() {
        try {
            console.log('📈 Fetching trading reports from /trades...');
            const response = await this.fetchWithFallback('/trades');
            const data = await response.json();
            console.log('📈 Trading data received:', data);
            return this.processTradingData(data);
        } catch (error) {
            console.info('⚠️ Trading API endpoint not available:', error.message);
            return [];
        }
    }
    
    async fetchMLReports() {
        try {
            console.log('🧠 Fetching ML reports from /ml/status...');
            const response = await this.fetchWithFallback('/ml/status');
            const data = await response.json();
            console.log('🧠 ML data received:', data);
            return this.processMLData(data);
        } catch (error) {
            console.info('⚠️ ML performance endpoint not available:', error.message);
            return [];
        }
    }
    
    processTradingData(data) {
        if (!data || !Array.isArray(data.trades)) return [];
        
        const report = {
            id: `trading_${Date.now()}`,
            type: 'trading',
            title: 'Trading Performance Report',
            createdAt: new Date().toISOString(),
            summary: {
                totalTrades: data.trades.length,
                winRate: this.calculateWinRate(data.trades),
                totalProfit: data.summary?.net_pnl || this.calculateTotalProfit(data.trades),
                avgProfit: this.calculateAvgProfit(data.trades)
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
                confidence: data.confidence || 0,
                totalPredictions: data.total_predictions || 0
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
    
    calculateAvgProfit(trades) {
        if (!trades || trades.length === 0) return 0;
        return this.calculateTotalProfit(trades) / trades.length;
    }
    
    applyFilters() {
        let filtered = [...this.reports];
        
        // Time filter
        const timeFilter = document.getElementById('timeFilter').value;
        if (timeFilter !== 'all') {
            const now = new Date();
            let cutoff;
            
            switch (timeFilter) {
                case 'today':
                    cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                    break;
                case 'week':
                    cutoff = new Date(now - 7 * 24 * 60 * 60 * 1000);
                    break;
                case 'month':
                    cutoff = new Date(now - 30 * 24 * 60 * 60 * 1000);
                    break;
                case 'year':
                    cutoff = new Date(now - 365 * 24 * 60 * 60 * 1000);
                    break;
            }
            
            if (cutoff) {
                filtered = filtered.filter(report => new Date(report.createdAt) >= cutoff);
            }
        }
        
        // Type filter
        const typeFilter = document.getElementById('typeFilter').value;
        if (typeFilter !== 'all') {
            filtered = filtered.filter(report => report.type === typeFilter);
        }
        
        // Search filter
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        if (searchTerm) {
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
            container.innerHTML = '';
            loadingSpinner.classList.remove('hidden');
            emptyState.classList.add('hidden');
            return;
        }
        
        loadingSpinner.classList.add('hidden');
        
        if (this.filteredReports.length === 0) {
            container.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');
        this.renderGridView(container);
    }
    
    renderGridView(container) {
        container.className = 'report-grid';
        container.innerHTML = this.filteredReports.map(report => this.createReportCard(report)).join('');
        
        // Add click events
        container.querySelectorAll('.report-card').forEach(card => {
            card.addEventListener('click', () => {
                const reportId = card.dataset.reportId;
                this.showReportDetail(reportId);
            });
        });
    }
    
    createReportCard(report) {
        const statusColor = this.getStatusColor(report.status);
        const typeIcon = this.getTypeIcon(report.type);
        const createdAt = new Date(report.createdAt).toLocaleDateString();
        
        return `
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover cursor-pointer report-card" data-report-id="${report.id}">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center space-x-2">
                        <i class="${typeIcon} text-blue-600"></i>
                        <span class="text-sm font-medium text-gray-600 uppercase">${report.type}</span>
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
            </div>
        `;
    }
    
    createSummaryItems(report) {
        switch (report.type) {
            case 'trading':
                const summary = report.summary;
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Total Trades:</span>
                        <span class="font-medium">${summary.totalTrades || 0}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Win Rate:</span>
                        <span class="font-medium">${(summary.winRate || 0).toFixed(1)}%</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Total P&L:</span>
                        <span class="font-medium ${(summary.totalProfit || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">
                            $${(summary.totalProfit || 0).toFixed(2)}
                        </span>
                    </div>
                `;
            case 'ml':
                const accuracy = report.summary.accuracy || 0;
                const confidence = report.summary.confidence || 0;
                const totalPredictions = report.summary.totalPredictions || 0;
                
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Accuracy:</span>
                        <span class="font-medium ${accuracy >= 0.7 ? 'text-green-600' : accuracy >= 0.5 ? 'text-yellow-600' : 'text-red-600'}">${(accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Confidence:</span>
                        <span class="font-medium text-purple-600">${(confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Predictions:</span>
                        <span class="font-medium">${totalPredictions.toLocaleString()}</span>
                    </div>
                `;
            default:
                return '<div class="text-sm text-gray-600">No summary available</div>';
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
    
    getTypeIcon(type) {
        switch (type) {
            case 'trading': return 'fas fa-chart-line';
            case 'ml': return 'fas fa-brain';
            case 'backtest': return 'fas fa-history';
            default: return 'fas fa-file-alt';
        }
    }
    
    setView(view) {
        this.currentView = view;
        
        // Update button states
        document.getElementById('gridView').classList.toggle('bg-blue-500', view === 'grid');
        document.getElementById('gridView').classList.toggle('text-white', view === 'grid');
        document.getElementById('listView').classList.toggle('bg-blue-500', view === 'list');
        document.getElementById('listView').classList.toggle('text-white', view === 'list');
        
        this.renderReports();
    }
    
    updateStats() {
        const totalReports = this.reports.length;
        
        // Trading metrics
        const tradingReports = this.reports.filter(r => r.type === 'trading');
        let totalWinRate = 0;
        let totalProfit = 0;
        let totalTrades = 0;
        
        if (tradingReports.length > 0) {
            tradingReports.forEach(r => {
                totalWinRate += r.summary.winRate || 0;
                totalProfit += r.summary.totalProfit || 0;
                totalTrades += r.summary.totalTrades || 0;
            });
            
            totalWinRate /= tradingReports.length;
        }
        
        // ML metrics
        const mlReports = this.reports.filter(r => r.type === 'ml');
        let avgAccuracy = 0;
        
        if (mlReports.length > 0) {
            mlReports.forEach(r => {
                avgAccuracy += (r.summary.accuracy || 0) * 100;
            });
            
            avgAccuracy /= mlReports.length;
        }
        
        // Update main stats
        document.getElementById('totalReports').textContent = totalReports;
        document.getElementById('avgWinRate').textContent = `${totalWinRate.toFixed(1)}%`;
        document.getElementById('totalProfit').textContent = `$${totalProfit.toFixed(2)}`;
        document.getElementById('totalProfit').className = `text-3xl font-bold ${totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`;
        document.getElementById('avgAccuracy').textContent = `${avgAccuracy.toFixed(1)}%`;
        document.getElementById('avgAccuracy').className = `text-3xl font-bold ${avgAccuracy >= 70 ? 'text-green-600' : avgAccuracy >= 50 ? 'text-yellow-600' : 'text-red-600'}`;
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        if (loading) {
            this.renderReports();
        }
    }
    
    startAutoRefresh() {
        // Refresh every 5 minutes
        setInterval(() => {
            if (!this.isLoading) {
                this.loadReports();
            }
        }, 5 * 60 * 1000);
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // Placeholder methods for functionality not needed for basic testing
    showNewReportModal() { console.log('Show new report modal'); }
    hideNewReportModal() { console.log('Hide new report modal'); }
    hideDetailModal() { console.log('Hide detail modal'); }
    handleNewReport(e) { e.preventDefault(); console.log('Handle new report'); }
    showReportDetail(reportId) { console.log('Show report detail:', reportId); }
}

// Initialize the reports manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌟 Starting NUCLEAR FIX Reports Dashboard...');
    new ReportsManager();
});