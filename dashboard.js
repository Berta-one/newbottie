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
            this.showError(`Unable to reach ${endpoint}`);
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
            const [tradingReports, mlReports, quantumReports, dailyReports, sentimentReports] = await Promise.all([
                this.fetchTradingReports(),
                this.fetchMLReports(),
                this.fetchQuantumReports(),
                this.fetchDailyReports(),
                this.fetchSentimentReports()
            ]);
            
            this.reports = [...tradingReports, ...mlReports, ...quantumReports, ...dailyReports, ...sentimentReports];
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
            this.showError('ML performance data unavailable. Using cached data.');
            return [];
        }
    }
    
    async fetchQuantumReports() {
        try {
            console.log('🔮 Fetching quantum analysis from /quantum/analysis...');
            const response = await this.fetchWithFallback('/quantum/analysis');
            const data = await response.json();
            console.log('🔮 Quantum data received:', data);
            return this.processQuantumData(data);
        } catch (error) {
            console.info('⚠️ Quantum analysis endpoint not available:', error.message);
            return [];
        }
    }
    
    async fetchDailyReports() {
        try {
            console.log('📊 Fetching daily reports from /reports/daily...');
            const response = await this.fetchWithFallback('/reports/daily');
            const data = await response.json();
            console.log('📊 Daily reports received:', data);
            return this.processDailyReports(data);
        } catch (error) {
            console.info('⚠️ Daily reports endpoint not available:', error.message);
            return [];
        }
    }
    
    async fetchSentimentReports() {
        try {
            console.log('😀 Fetching sentiment data from /sentiment...');
            const response = await this.fetchWithFallback('/sentiment');
            const data = await response.json();
            console.log('😀 Sentiment data received:', data);
            return this.processSentimentData(data);
        } catch (error) {
            console.info('⚠️ Sentiment endpoint not available:', error.message);
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
            explanation: `This report analyzes the performance of the machine learning model used for trading predictions. The model currently shows an accuracy of ${(data.accuracy * 100).toFixed(1)}% with a confidence level of ${(data.confidence * 100).toFixed(1)}%. The model is running in ${data.mode} mode and has made ${data.total_predictions || 0} predictions. The current equity value is $${data.equity?.toFixed(2) || 0}.`,
            status: 'completed'
        };
        
        return [report];
    }
    
    processQuantumData(data) {
        if (!data || !data.predictions || !Array.isArray(data.predictions)) {
            return [];
        }
        
        // Create a summary of quantum predictions
        const buyCount = data.predictions.filter(p => p.prediction === 'BUY').length;
        const sellCount = data.predictions.filter(p => p.prediction === 'SELL').length;
        const holdCount = data.predictions.filter(p => p.prediction === 'HOLD').length;
        
        // Calculate average confidence
        const avgConfidence = data.predictions.reduce((sum, p) => sum + p.confidence, 0) / data.predictions.length;
        
        const report = {
            id: `quantum_${Date.now()}`,
            type: 'quantum',
            title: 'Quantum Analysis Report',
            createdAt: new Date().toISOString(),
            summary: {
                totalPredictions: data.predictions.length,
                buySignals: buyCount,
                sellSignals: sellCount,
                holdSignals: holdCount,
                avgConfidence: avgConfidence
            },
            data: data,
            explanation: `This report contains quantum computing analysis of ${data.predictions.length} trading pairs. The quantum engine used ${data.qubits_used} qubits with a decoherence rate of ${data.decoherence_rate}. The analysis resulted in ${buyCount} BUY signals, ${sellCount} SELL signals, and ${holdCount} HOLD signals with an average confidence of ${(avgConfidence * 100).toFixed(1)}%. Each prediction is based on quantum probability calculations and entanglement scores that measure the correlation between different market factors.`,
            status: 'completed'
        };
        
        return [report];
    }
    
    processDailyReports(data) {
        if (!data || !data.reports || !Array.isArray(data.reports)) {
            return [];
        }
        
        return data.reports.map(report => {
            const createdAt = new Date(report.created_at);
            
            return {
                id: report.id,
                type: 'daily',
                title: report.title,
                createdAt: report.created_at,
                summary: {
                    totalTrades: report.summary.total_trades,
                    winRate: report.summary.win_rate,
                    profitLoss: report.summary.profit_loss,
                    topPerformer: report.summary.top_performer
                },
                data: report,
                explanation: `Daily trading report generated on ${createdAt.toLocaleDateString()} at 18:00 UTC. This report summarizes the trading activity for the day, showing a total of ${report.summary.total_trades} trades with a win rate of ${report.summary.win_rate.toFixed(1)}%. The overall profit/loss for the day was $${report.summary.profit_loss.toFixed(2)}. The top performing asset was ${report.summary.top_performer}. This report is automatically generated at the end of each trading day to provide a comprehensive overview of trading performance.`,
                status: report.status
            };
        });
    }
    
    processSentimentData(data) {
        if (!data || !data.scores || Object.keys(data.scores).length === 0) {
            return [];
        }
        
        // Extract sentiment scores
        const scores = data.scores;
        const symbols = Object.keys(scores);
        
        // Calculate average sentiment
        let totalSentiment = 0;
        let count = 0;
        
        for (const symbol of symbols) {
            if (scores[symbol] && typeof scores[symbol] === 'number') {
                totalSentiment += scores[symbol];
                count++;
            }
        }
        
        const avgSentiment = count > 0 ? totalSentiment / count : 0;
        
        // Find most positive and negative assets
        let mostPositive = { symbol: null, score: -Infinity };
        let mostNegative = { symbol: null, score: Infinity };
        
        for (const symbol of symbols) {
            const score = scores[symbol];
            if (score > mostPositive.score) {
                mostPositive = { symbol, score };
            }
            if (score < mostNegative.score) {
                mostNegative = { symbol, score };
            }
        }
        
        const report = {
            id: `sentiment_${Date.now()}`,
            type: 'sentiment',
            title: 'Market Sentiment Analysis',
            createdAt: new Date().toISOString(),
            summary: {
                avgSentiment: avgSentiment,
                mostPositive: mostPositive,
                mostNegative: mostNegative,
                totalAssets: symbols.length
            },
            data: data,
            explanation: `This report analyzes market sentiment across ${symbols.length} assets based on social media, news, and market data. The average sentiment score is ${avgSentiment.toFixed(2)} (range: -1 to +1). The most positive asset is ${mostPositive.symbol || 'none'} with a score of ${mostPositive.score?.toFixed(2) || 0}, while the most negative is ${mostNegative.symbol || 'none'} with a score of ${mostNegative.score?.toFixed(2) || 0}. Sentiment analysis helps identify market trends and potential trading opportunities based on public perception and news impact. The data was collected over a ${data.window_sec || 0} second window.`,
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
                    ${report.explanation ? `<div class="mt-3 text-xs text-gray-500">${report.explanation}</div>` : ''}
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
                    ${report.explanation ? `<div class="mt-3 text-xs text-gray-500">${report.explanation}</div>` : ''}
                `;
            case 'quantum':
                const qSummary = report.summary;
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Predictions:</span>
                        <span class="font-medium">${qSummary.totalPredictions || 0}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Signals:</span>
                        <span class="font-medium">
                            <span class="text-green-600">${qSummary.buySignals || 0} Buy</span> / 
                            <span class="text-red-600">${qSummary.sellSignals || 0} Sell</span> / 
                            <span class="text-gray-600">${qSummary.holdSignals || 0} Hold</span>
                        </span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Confidence:</span>
                        <span class="font-medium text-purple-600">${((qSummary.avgConfidence || 0) * 100).toFixed(1)}%</span>
                    </div>
                    ${report.explanation ? `<div class="mt-3 text-xs text-gray-500">${report.explanation}</div>` : ''}
                `;
            case 'daily':
                const dSummary = report.summary;
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Total Trades:</span>
                        <span class="font-medium">${dSummary.totalTrades || 0}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Win Rate:</span>
                        <span class="font-medium">${(dSummary.winRate || 0).toFixed(1)}%</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">P&L:</span>
                        <span class="font-medium ${(dSummary.profitLoss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">
                            $${(dSummary.profitLoss || 0).toFixed(2)}
                        </span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Top Asset:</span>
                        <span class="font-medium text-blue-600">${dSummary.topPerformer || 'None'}</span>
                    </div>
                    ${report.explanation ? `<div class="mt-3 text-xs text-gray-500">${report.explanation}</div>` : ''}
                `;
            case 'sentiment':
                const sSummary = report.summary;
                return `
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Assets:</span>
                        <span class="font-medium">${sSummary.totalAssets || 0}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Avg Sentiment:</span>
                        <span class="font-medium ${(sSummary.avgSentiment || 0) >= 0 ? 'text-green-600' : 'text-red-600'}">
                            ${(sSummary.avgSentiment || 0).toFixed(2)}
                        </span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Most Positive:</span>
                        <span class="font-medium text-green-600">${sSummary.mostPositive?.symbol || 'None'}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Most Negative:</span>
                        <span class="font-medium text-red-600">${sSummary.mostNegative?.symbol || 'None'}</span>
                    </div>
                    ${report.explanation ? `<div class="mt-3 text-xs text-gray-500">${report.explanation}</div>` : ''}
                `;
            default:
                return `
                    <div class="text-sm text-gray-600">No summary available</div>
                    ${report.explanation ? `<div class="mt-3 text-xs text-gray-500">${report.explanation}</div>` : ''}
                `;
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
            case 'quantum': return 'fas fa-atom';
            case 'daily': return 'fas fa-calendar-day';
            case 'sentiment': return 'fas fa-comment-dots';
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
