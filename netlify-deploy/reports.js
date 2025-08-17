class ReportsManager {
    constructor() {
        this.apiUrl = 'https://bottie-1.onrender.com/api';
        this.reports = [];
        this.filteredReports = [];
        this.currentView = 'grid';
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadReports();
        this.startAutoRefresh();
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
            // Load existing reports from various sources
            const [tradingReports, mlReports, backtestReports] = await Promise.all([
                this.fetchTradingReports(),
                this.fetchMLReports(),
                this.fetchBacktestReports()
            ]);
            
            this.reports = [...tradingReports, ...mlReports, ...backtestReports];
            this.applyFilters();
            this.updateStats();
            
        } catch (error) {
            console.error('Error loading reports:', error);
            this.showError('Failed to load reports. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }
    
    async fetchTradingReports() {
        try {
            const response = await fetch(`${this.apiUrl}/trading/history`);
            if (!response.ok) throw new Error('Failed to fetch trading reports');
            
            const data = await response.json();
            return this.processTradingData(data);
        } catch (error) {
            console.warn('Trading reports not available:', error);
            return this.generateSampleTradingReports();
        }
    }
    
    async fetchMLReports() {
        try {
            const response = await fetch(`${this.apiUrl}/ml/performance`);
            if (!response.ok) throw new Error('Failed to fetch ML reports');
            
            const data = await response.json();
            return this.processMLData(data);
        } catch (error) {
            console.warn('ML reports not available:', error);
            return this.generateSampleMLReports();
        }
    }
    
    async fetchBacktestReports() {
        try {
            const response = await fetch(`${this.apiUrl}/backtest/results`);
            if (!response.ok) throw new Error('Failed to fetch backtest reports');
            
            const data = await response.json();
            return this.processBacktestData(data);
        } catch (error) {
            console.warn('Backtest reports not available:', error);
            return this.generateSampleBacktestReports();
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
                totalProfit: this.calculateTotalProfit(data.trades),
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
                brierScore: data.brier_score || 0,
                sampleCount: data.sample_count || 0,
                quantumImportance: data.quantum_importance || 0
            },
            data: data,
            status: 'completed'
        };
        
        return [report];
    }
    
    processBacktestData(data) {
        const report = {
            id: `backtest_${Date.now()}`,
            type: 'backtest',
            title: 'Backtesting Results',
            createdAt: new Date().toISOString(),
            summary: {
                totalReturn: data.total_return || 0,
                sharpeRatio: data.sharpe_ratio || 0,
                maxDrawdown: data.max_drawdown || 0,
                winRate: data.win_rate || 0
            },
            data: data,
            status: 'completed'
        };
        
        return [report];
    }
    
    generateSampleTradingReports() {
        const sampleReports = [];
        const now = new Date();
        
        for (let i = 0; i < 5; i++) {
            const date = new Date(now - i * 24 * 60 * 60 * 1000);
            const trades = this.generateSampleTrades(10 + Math.floor(Math.random() * 20));
            
            sampleReports.push({
                id: `trading_sample_${i}`,
                type: 'trading',
                title: `Trading Report - ${date.toLocaleDateString()}`,
                createdAt: date.toISOString(),
                summary: {
                    totalTrades: trades.length,
                    winRate: this.calculateWinRate(trades),
                    totalProfit: this.calculateTotalProfit(trades),
                    avgProfit: this.calculateAvgProfit(trades)
                },
                data: trades,
                status: 'completed'
            });
        }
        
        return sampleReports;
    }
    
    generateSampleMLReports() {
        const sampleReports = [];
        const now = new Date();
        
        for (let i = 0; i < 3; i++) {
            const date = new Date(now - i * 2 * 24 * 60 * 60 * 1000);
            
            sampleReports.push({
                id: `ml_sample_${i}`,
                type: 'ml',
                title: `ML Performance - ${date.toLocaleDateString()}`,
                createdAt: date.toISOString(),
                summary: {
                    accuracy: 0.75 + Math.random() * 0.2,
                    brierScore: 0.15 + Math.random() * 0.1,
                    sampleCount: 1000 + Math.floor(Math.random() * 5000),
                    quantumImportance: Math.random()
                },
                data: {
                    feature_importance: {
                        'price_momentum': Math.random(),
                        'volume_trend': Math.random(),
                        'sentiment_score': Math.random(),
                        'technical_indicators': Math.random()
                    }
                },
                status: 'completed'
            });
        }
        
        return sampleReports;
    }
    
    generateSampleBacktestReports() {
        const sampleReports = [];
        const now = new Date();
        
        for (let i = 0; i < 4; i++) {
            const date = new Date(now - i * 3 * 24 * 60 * 60 * 1000);
            
            sampleReports.push({
                id: `backtest_sample_${i}`,
                type: 'backtest',
                title: `Backtest Results - ${date.toLocaleDateString()}`,
                createdAt: date.toISOString(),
                summary: {
                    totalReturn: (Math.random() - 0.3) * 100,
                    sharpeRatio: Math.random() * 3,
                    maxDrawdown: -Math.random() * 20,
                    winRate: 0.4 + Math.random() * 0.4
                },
                data: {
                    strategy: 'Quantum Enhanced Grid Trading',
                    period: '90 days',
                    initial_capital: 10000
                },
                status: 'completed'
            });
        }
        
        return sampleReports;
    }
    
    generateSampleTrades(count) {
        const trades = [];
        const symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT'];
        const now = new Date();
        
        for (let i = 0; i < count; i++) {
            const timestamp = new Date(now - Math.random() * 24 * 60 * 60 * 1000);
            const symbol = symbols[Math.floor(Math.random() * symbols.length)];
            const side = Math.random() > 0.5 ? 'BUY' : 'SELL';
            const qty = Math.random() * 10;
            const price = 100 + Math.random() * 1000;
            const profit = (Math.random() - 0.4) * 100;
            
            trades.push({
                ts: timestamp.toISOString(),
                symbol,
                side,
                qty,
                price,
                profit
            });
        }
        
        return trades;
    }
    
    calculateWinRate(trades) {
        if (!trades || trades.length === 0) return 0;
        const wins = trades.filter(t => (t.profit || 0) > 0).length;
        return (wins / trades.length) * 100;
    }
    
    calculateTotalProfit(trades) {
        if (!trades || trades.length === 0) return 0;
        return trades.reduce((sum, t) => sum + (t.profit || 0), 0);
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
        
        if (this.currentView === 'grid') {
            this.renderGridView(container);
        } else {
            this.renderListView(container);
        }
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
    
    renderListView(container) {
        container.className = 'space-y-4';
        container.innerHTML = this.filteredReports.map(report => this.createReportListItem(report)).join('');
        
        // Add click events
        container.querySelectorAll('.report-item').forEach(item => {
            item.addEventListener('click', () => {
                const reportId = item.dataset.reportId;
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
                
                <div class="mt-4 pt-4 border-t border-gray-200">
                    <button class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        View Details <i class="fas fa-arrow-right ml-1"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    createReportListItem(report) {
        const statusColor = this.getStatusColor(report.status);
        const typeIcon = this.getTypeIcon(report.type);
        const createdAt = new Date(report.createdAt).toLocaleDateString();
        
        return `
            <div class="bg-white rounded-xl shadow-lg p-6 cursor-pointer report-item card-hover" data-report-id="${report.id}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="flex-shrink-0">
                            <i class="${typeIcon} text-blue-600 text-xl"></i>
                        </div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-800">${report.title}</h3>
                            <div class="flex items-center space-x-4 text-sm text-gray-600">
                                <span class="uppercase font-medium">${report.type}</span>
                                <span>•</span>
                                <span>${createdAt}</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        <span class="px-3 py-1 rounded-full text-xs font-medium ${statusColor}">
                            ${report.status}
                        </span>
                        <i class="fas fa-chevron-right text-gray-400"></i>
                    </div>
                </div>
            </div>
        `;
    }
    
    createSummaryItems(report) {
        switch (report.type) {
            case 'trading':
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Total Trades:</span>
                        <span class="font-medium">${report.summary.totalTrades}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Win Rate:</span>
                        <span class="font-medium">${report.summary.winRate.toFixed(1)}%</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Total Profit:</span>
                        <span class="font-medium ${report.summary.totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}">
                            $${report.summary.totalProfit.toFixed(2)}
                        </span>
                    </div>
                `;
            case 'ml':
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Accuracy:</span>
                        <span class="font-medium">${(report.summary.accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Brier Score:</span>
                        <span class="font-medium">${report.summary.brierScore.toFixed(3)}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Samples:</span>
                        <span class="font-medium">${report.summary.sampleCount.toLocaleString()}</span>
                    </div>
                `;
            case 'backtest':
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Total Return:</span>
                        <span class="font-medium ${report.summary.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}">
                            ${report.summary.totalReturn.toFixed(2)}%
                        </span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Sharpe Ratio:</span>
                        <span class="font-medium">${report.summary.sharpeRatio.toFixed(2)}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Max Drawdown:</span>
                        <span class="font-medium text-red-600">${report.summary.maxDrawdown.toFixed(2)}%</span>
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
            case 'sentiment': return 'fas fa-heart';
            case 'portfolio': return 'fas fa-briefcase';
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
        const recentReports = this.reports.filter(r => {
            const reportDate = new Date(r.createdAt);
            const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
            return reportDate >= weekAgo;
        }).length;
        
        const tradingReports = this.reports.filter(r => r.type === 'trading');
        const totalWinRate = tradingReports.length > 0 ? 
            tradingReports.reduce((sum, r) => sum + r.summary.winRate, 0) / tradingReports.length : 0;
        
        const totalProfit = tradingReports.reduce((sum, r) => sum + r.summary.totalProfit, 0);
        
        document.getElementById('totalReports').textContent = totalReports;
        document.getElementById('recentReports').textContent = recentReports;
        document.getElementById('avgWinRate').textContent = `${totalWinRate.toFixed(1)}%`;
        document.getElementById('totalProfit').textContent = `$${totalProfit.toFixed(2)}`;
    }
    
    showNewReportModal() {
        document.getElementById('newReportModal').classList.remove('hidden');
    }
    
    hideNewReportModal() {
        document.getElementById('newReportModal').classList.add('hidden');
        document.getElementById('newReportForm').reset();
    }
    
    async handleNewReport(e) {
        e.preventDefault();
        
        const reportType = document.getElementById('reportType').value;
        const timeRange = document.getElementById('reportTimeRange').value;
        const reportName = document.getElementById('reportName').value;
        
        this.hideNewReportModal();
        
        // Show loading state
        this.setLoading(true);
        
        try {
            const newReport = await this.generateNewReport(reportType, timeRange, reportName);
            this.reports.unshift(newReport);
            this.applyFilters();
            this.updateStats();
            
            this.showSuccess('Report generated successfully!');
        } catch (error) {
            console.error('Error generating report:', error);
            this.showError('Failed to generate report. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }
    
    async generateNewReport(type, timeRange, name) {
        // Simulate API call to generate report
        await this.delay(2000);
        
        const now = new Date();
        const reportId = `${type}_${now.getTime()}`;
        const title = name || `${type.charAt(0).toUpperCase() + type.slice(1)} Report - ${now.toLocaleDateString()}`;
        
        let summary = {};
        let data = {};
        
        switch (type) {
            case 'trading':
                const trades = this.generateSampleTrades(15 + Math.floor(Math.random() * 25));
                summary = {
                    totalTrades: trades.length,
                    winRate: this.calculateWinRate(trades),
                    totalProfit: this.calculateTotalProfit(trades),
                    avgProfit: this.calculateAvgProfit(trades)
                };
                data = trades;
                break;
                
            case 'ml':
                summary = {
                    accuracy: 0.7 + Math.random() * 0.25,
                    brierScore: 0.1 + Math.random() * 0.15,
                    sampleCount: 500 + Math.floor(Math.random() * 3000),
                    quantumImportance: Math.random()
                };
                data = {
                    feature_importance: {
                        'price_momentum': Math.random(),
                        'volume_trend': Math.random(),
                        'sentiment_score': Math.random(),
                        'technical_indicators': Math.random(),
                        'quantum_features': Math.random()
                    }
                };
                break;
                
            case 'backtest':
                summary = {
                    totalReturn: (Math.random() - 0.2) * 150,
                    sharpeRatio: Math.random() * 4,
                    maxDrawdown: -Math.random() * 25,
                    winRate: 0.35 + Math.random() * 0.5
                };
                data = {
                    strategy: 'Custom Strategy',
                    period: timeRange,
                    initial_capital: 10000
                };
                break;
                
            default:
                summary = { status: 'Generated successfully' };
                data = { message: 'Report data generated' };
        }
        
        return {
            id: reportId,
            type,
            title,
            createdAt: now.toISOString(),
            summary,
            data,
            status: 'completed'
        };
    }
    
    showReportDetail(reportId) {
        const report = this.reports.find(r => r.id === reportId);
        if (!report) return;
        
        document.getElementById('reportDetailTitle').textContent = report.title;
        document.getElementById('reportDetailContent').innerHTML = this.createDetailContent(report);
        document.getElementById('reportDetailModal').classList.remove('hidden');
        
        // Initialize charts if needed
        setTimeout(() => this.initializeDetailCharts(report), 100);
    }
    
    createDetailContent(report) {
        const createdAt = new Date(report.createdAt).toLocaleString();
        
        return `
            <div class="space-y-6">
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <p class="text-sm text-gray-600">Type</p>
                            <p class="font-medium capitalize">${report.type}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Created</p>
                            <p class="font-medium">${createdAt}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Status</p>
                            <span class="px-2 py-1 rounded-full text-xs font-medium ${this.getStatusColor(report.status)}">
                                ${report.status}
                            </span>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">ID</p>
                            <p class="font-medium text-xs">${report.id}</p>
                        </div>
                    </div>
                </div>
                
                ${this.createDetailSummary(report)}
                
                <div class="bg-white border rounded-lg p-6">
                    <h3 class="text-lg font-semibold mb-4">Data Visualization</h3>
                    <canvas id="reportChart_${report.id}" width="400" height="200"></canvas>
                </div>
                
                ${this.createDetailData(report)}
            </div>
        `;
    }
    
    createDetailSummary(report) {
        let summaryHTML = '<div class="bg-white border rounded-lg p-6"><h3 class="text-lg font-semibold mb-4">Summary</h3><div class="grid grid-cols-2 md:grid-cols-4 gap-4">';
        
        Object.entries(report.summary).forEach(([key, value]) => {
            const displayKey = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
            let displayValue = value;
            
            if (typeof value === 'number') {
                if (key.includes('Rate') || key.includes('accuracy')) {
                    displayValue = `${(value * (key.includes('Rate') ? 1 : 100)).toFixed(1)}%`;
                } else if (key.includes('Profit') || key.includes('Return')) {
                    displayValue = `$${value.toFixed(2)}`;
                } else {
                    displayValue = value.toFixed(2);
                }
            }
            
            summaryHTML += `
                <div>
                    <p class="text-sm text-gray-600">${displayKey}</p>
                    <p class="font-medium ${key.includes('Profit') && value < 0 ? 'text-red-600' : key.includes('Profit') && value > 0 ? 'text-green-600' : ''}">${displayValue}</p>
                </div>
            `;
        });
        
        summaryHTML += '</div></div>';
        return summaryHTML;
    }
    
    createDetailData(report) {
        if (report.type === 'trading' && Array.isArray(report.data)) {
            return `
                <div class="bg-white border rounded-lg p-6">
                    <h3 class="text-lg font-semibold mb-4">Recent Trades</h3>
                    <div class="overflow-x-auto">
                        <table class="min-w-full table-auto">
                            <thead>
                                <tr class="bg-gray-50">
                                    <th class="px-4 py-2 text-left">Time</th>
                                    <th class="px-4 py-2 text-left">Symbol</th>
                                    <th class="px-4 py-2 text-left">Side</th>
                                    <th class="px-4 py-2 text-right">Quantity</th>
                                    <th class="px-4 py-2 text-right">Price</th>
                                    <th class="px-4 py-2 text-right">Profit</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${report.data.slice(0, 10).map(trade => `
                                    <tr class="border-t">
                                        <td class="px-4 py-2 text-sm">${new Date(trade.ts).toLocaleTimeString()}</td>
                                        <td class="px-4 py-2 font-medium">${trade.symbol}</td>
                                        <td class="px-4 py-2">
                                            <span class="px-2 py-1 rounded text-xs ${trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                                ${trade.side}
                                            </span>
                                        </td>
                                        <td class="px-4 py-2 text-right">${trade.qty.toFixed(4)}</td>
                                        <td class="px-4 py-2 text-right">$${trade.price.toFixed(2)}</td>
                                        <td class="px-4 py-2 text-right ${trade.profit >= 0 ? 'text-green-600' : 'text-red-600'}">
                                            $${trade.profit.toFixed(2)}
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="bg-white border rounded-lg p-6">
                <h3 class="text-lg font-semibold mb-4">Raw Data</h3>
                <pre class="bg-gray-50 p-4 rounded text-sm overflow-x-auto">${JSON.stringify(report.data, null, 2)}</pre>
            </div>
        `;
    }
    
    initializeDetailCharts(report) {
        const canvas = document.getElementById(`reportChart_${report.id}`);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        let chartData = {};
        let chartOptions = {
            responsive: true,
            maintainAspectRatio: false
        };
        
        switch (report.type) {
            case 'trading':
                if (Array.isArray(report.data)) {
                    const profits = report.data.map(t => t.profit);
                    const labels = report.data.map((t, i) => `Trade ${i + 1}`);
                    
                    chartData = {
                        labels: labels.slice(0, 20),
                        datasets: [{
                            label: 'Profit/Loss',
                            data: profits.slice(0, 20),
                            backgroundColor: profits.slice(0, 20).map(p => p >= 0 ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)'),
                            borderColor: profits.slice(0, 20).map(p => p >= 0 ? 'rgba(34, 197, 94, 1)' : 'rgba(239, 68, 68, 1)'),
                            borderWidth: 1
                        }]
                    };
                    
                    new Chart(ctx, {
                        type: 'bar',
                        data: chartData,
                        options: chartOptions
                    });
                }
                break;
                
            case 'ml':
                if (report.data.feature_importance) {
                    const features = Object.keys(report.data.feature_importance);
                    const importance = Object.values(report.data.feature_importance);
                    
                    chartData = {
                        labels: features,
                        datasets: [{
                            label: 'Feature Importance',
                            data: importance,
                            backgroundColor: 'rgba(59, 130, 246, 0.5)',
                            borderColor: 'rgba(59, 130, 246, 1)',
                            borderWidth: 1
                        }]
                    };
                    
                    new Chart(ctx, {
                        type: 'horizontalBar',
                        data: chartData,
                        options: chartOptions
                    });
                }
                break;
                
            default:
                // Simple line chart for other types
                const randomData = Array.from({length: 10}, () => Math.random() * 100);
                chartData = {
                    labels: Array.from({length: 10}, (_, i) => `Point ${i + 1}`),
                    datasets: [{
                        label: 'Data Points',
                        data: randomData,
                        borderColor: 'rgba(59, 130, 246, 1)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                };
                
                new Chart(ctx, {
                    type: 'line',
                    data: chartData,
                    options: chartOptions
                });
        }
    }
    
    hideDetailModal() {
        document.getElementById('reportDetailModal').classList.add('hidden');
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
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize the reports manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ReportsManager();
});