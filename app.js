// Enhanced app.js with real data integration and ML learning visualization
// Replace your web/app.js with this enhanced version

class SntaxApp {
  constructor() {
    this.API = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
    this.authToken = localStorage.getItem('auth_token');
    this.refreshIntervals = {
      health: 5000,
      signals: 3000,
      grid: 15000,
      ml: 10000
    };
    this.intervalIds = {};
    this.mlData = {};
    this.isAuthenticated = !!this.authToken;
    
    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.updateUI();
    
    if (this.isAuthenticated) {
      await this.startDataRefresh();
    }
  }

  setupEventListeners() {
    // Modal close
    document.getElementById('close-modal')?.addEventListener('click', () => {
      document.getElementById('response-modal').style.display = 'none';
    });

    // Refresh controls
    document.getElementById('apply-intervals')?.addEventListener('click', () => {
      this.applyIntervals();
    });

    document.getElementById('refresh-all')?.addEventListener('click', () => {
      this.refreshAllData();
    });

    // Endpoint testing
    document.querySelectorAll('.endpoint-box').forEach(box => {
      box.addEventListener('click', async (e) => {
        const endpoint = box.dataset.endpoint;
        if (endpoint) {
          await this.testEndpoint(endpoint, box);
        }
      });
    });
  }

  updateUI() {
    // Update authentication state in UI if needed
    console.log('UI updated. Auth status:', this.isAuthenticated);
  }

  async authFetch(url, options = {}) {
    const fullUrl = url.startsWith('http') ? url : `${this.API}${url}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    const response = await fetch(fullUrl, { ...options, headers });
    
    if (response.status === 401) {
      this.clearAuthState();
      this.updateUI();
      throw new Error('Authentication expired');
    }
    
    return response;
  }

  async fetchJSON(url) {
    const response = await this.authFetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  clearAuthState() {
    this.authToken = null;
    this.isAuthenticated = false;
    localStorage.removeItem('auth_token');
    this.stopAllIntervals();
  }

  async startDataRefresh() {
    // Clear existing intervals
    this.stopAllIntervals();
    
    // Start new intervals
    this.intervalIds.health = setInterval(() => this.refreshHealth(), this.refreshIntervals.health);
    this.intervalIds.signals = setInterval(() => this.refreshSignals(), this.refreshIntervals.signals);
    this.intervalIds.grid = setInterval(() => this.refreshGrid(), this.refreshIntervals.grid);
    this.intervalIds.ml = setInterval(() => this.refreshMLStatus(), this.refreshIntervals.ml);
    
    // Initial load
    await this.refreshAllData();
  }

  stopAllIntervals() {
    Object.values(this.intervalIds).forEach(id => clearInterval(id));
    this.intervalIds = {};
  }

  async refreshAllData() {
    console.log('🔄 Refreshing all data...');
    
    try {
      await Promise.allSettled([
        this.refreshHealth(),
        this.refreshSignals(),
        this.refreshGrid(),
        this.refreshMLStatus(),
        this.refreshSentiment(),
        this.refreshPortfolio(),
        this.refreshAtomicSwaps()
      ]);
      console.log('✅ All data refreshed');
    } catch (error) {
      console.error('❌ Error refreshing data:', error);
    }
  }

  async refreshHealth() {
    try {
      const data = await this.fetchJSON('/health');
      this.updateHealthStatus(data);
    } catch (error) {
      console.error('Failed to refresh health:', error);
      this.updateEndpointStatus('/health', 'error');
    }
  }

  async refreshSignals() {
    try {
      const data = await this.fetchJSON('/signals');
      this.updateSignalsDisplay(data);
      this.updateEndpointStatus('/signals', 'success');
    } catch (error) {
      console.error('Failed to refresh signals:', error);
      this.updateEndpointStatus('/signals', 'error');
    }
  }

  async refreshGrid() {
    try {
      const data = await this.fetchJSON('/grid/matrix');
      this.updateGridDisplay(data);
      this.updateEndpointStatus('/grid/matrix', 'success');
    } catch (error) {
      console.error('Failed to refresh grid:', error);
      this.updateEndpointStatus('/grid/matrix', 'error');
    }
  }

  async refreshMLStatus() {
    try {
      const data = await this.fetchJSON('/ml/performance');
      this.mlData = data;
      this.updateMLDisplay(data);
      this.updateEndpointStatus('/ml/performance', 'success');
    } catch (error) {
      console.error('Failed to refresh ML status:', error);
      this.updateEndpointStatus('/ml/performance', 'error');
    }
  }

  async refreshSentiment() {
    try {
      const data = await this.fetchJSON('/sentiment/articles');
      this.updateSentimentDisplay(data);
      this.updateEndpointStatus('/sentiment/articles', 'success');
    } catch (error) {
      console.error('Failed to refresh sentiment:', error);
      this.updateEndpointStatus('/sentiment/articles', 'error');
    }
  }

  async refreshPortfolio() {
    try {
      const data = await this.fetchJSON('/portfolio/assets');
      this.updatePortfolioDisplay(data);
      this.updateEndpointStatus('/portfolio/assets', 'success');
    } catch (error) {
      console.error('Failed to refresh portfolio:', error);
      this.updateEndpointStatus('/portfolio/assets', 'error');
    }
  }

  async refreshAtomicSwaps() {
    try {
      const data = await this.fetchJSON('/atomic/opportunities');
      this.updateAtomicSwapsDisplay(data);
      this.updateEndpointStatus('/atomic/opportunities', 'success');
    } catch (error) {
      console.error('Failed to refresh atomic swaps:', error);
      this.updateEndpointStatus('/atomic/opportunities', 'error');
    }
  }

  updateHealthStatus(data) {
    // Update health indicators in the UI
    console.log('🏥 Health Status:', data.status);
    
    // Update service statuses
    if (data.services) {
      this.updateServiceStatus('ml-engine', data.services.ml_engine);
      this.updateServiceStatus('quantum-engine', data.services.quantum_engine);
      this.updateServiceStatus('sentiment-analysis', data.services.sentiment_analysis);
      this.updateServiceStatus('trading-engine', data.services.trading_engine);
    }
  }

  updateServiceStatus(serviceId, serviceData) {
    const element = document.getElementById(serviceId);
    if (element && serviceData) {
      element.className = `service-status ${serviceData.enabled ? 'enabled' : 'disabled'}`;
      element.textContent = `${serviceData.enabled ? '✅' : '❌'} ${serviceId.replace('-', ' ')}`;
    }
  }

  updateSignalsDisplay(signals) {
    console.log('📡 Signals:', signals.length);
    
    // Find signals container or create one
    let container = document.getElementById('signals-container');
    if (!container) {
      // Create signals display if it doesn't exist
      container = document.createElement('div');
      container.id = 'signals-container';
      container.innerHTML = '<h3>Trading Signals</h3>';
      document.body.appendChild(container);
    }
    
    // Clear existing signals
    const existingList = container.querySelector('.signals-list');
    if (existingList) {
      existingList.remove();
    }
    
    // Create new signals list
    const signalsList = document.createElement('div');
    signalsList.className = 'signals-list';
    
    if (signals && signals.length > 0) {
      signals.forEach((signal, index) => {
        const signalElement = document.createElement('div');
        signalElement.className = `signal-item signal-${signal.signal.toLowerCase()}`;
        signalElement.innerHTML = `
          <div class="signal-header">
            <span class="signal-symbol">${signal.symbol}</span>
            <span class="signal-type ${signal.signal.toLowerCase()}">${signal.signal}</span>
            <span class="signal-confidence">${(signal.conf * 100).toFixed(1)}%</span>
          </div>
          <div class="signal-details">
            <small>ML: ${(signal.features?.ml_confidence * 100 || 0).toFixed(0)}% | 
                  Quantum: ${(signal.features?.quantum_feature * 100 || 0).toFixed(0)}% | 
                  24h: ${signal.market_data?.price_change_24h || 0}%</small>
          </div>
        `;
        signalsList.appendChild(signalElement);
      });
    } else {
      signalsList.innerHTML = '<p class="no-signals">No signals available</p>';
    }
    
    container.appendChild(signalsList);
  }

  updateGridDisplay(data) {
    console.log('🏛️ Grid Matrix:', data.total_pairs, 'pairs');
    
    // Find grid container or create one
    let container = document.getElementById('grid-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'grid-container';
      container.innerHTML = '<h3>Professional Trading Grid</h3>';
      document.body.appendChild(container);
    }
    
    // Update grid stats
    let statsElement = container.querySelector('.grid-stats');
    if (!statsElement) {
      statsElement = document.createElement('div');
      statsElement.className = 'grid-stats';
      container.appendChild(statsElement);
    }
    
    statsElement.innerHTML = `
      <div class="grid-stat">
        <span class="stat-label">Portfolio Assets:</span>
        <span class="stat-value">${data.rows?.length || 0}</span>
      </div>
      <div class="grid-stat">
        <span class="stat-label">Volume Leaders:</span>
        <span class="stat-value">${data.cols?.length || 0}</span>
      </div>
      <div class="grid-stat">
        <span class="stat-label">Total Pairs:</span>
        <span class="stat-value">${data.total_pairs || 0}</span>
      </div>
      <div class="grid-stat">
        <span class="stat-label">Data Source:</span>
        <span class="stat-value">${data.data_source || 'mock'}</span>
      </div>
    `;
    
    // Create trading matrix display
    this.createTradingMatrix(container, data);
    
    // Process atomic swap opportunities from grid data
    if (data.atomic_swaps && data.atomic_swaps.length > 0) {
      this.updateAtomicSwapsDisplay({ opportunities: data.atomic_swaps });
    }
  }

  createTradingMatrix(container, data) {
    // Remove existing matrix
    const existingMatrix = container.querySelector('.trading-matrix');
    if (existingMatrix) {
      existingMatrix.remove();
    }
    
    if (!data.matrix || !data.rows || !data.cols) {
      return;
    }
    
    const matrixElement = document.createElement('div');
    matrixElement.className = 'trading-matrix';
    
    // Create header row
    const headerRow = document.createElement('div');
    headerRow.className = 'matrix-row matrix-header';
    headerRow.innerHTML = '<div class="matrix-cell header-cell">Portfolio</div>';
    
    // Add column headers (top volume cryptos)
    data.cols.slice(0, 10).forEach((col, index) => {
      const leader = data.volume_leaders?.find(l => l.symbol === col);
      const rank = leader?.rank || index + 1;
      headerRow.innerHTML += `
        <div class="matrix-cell header-cell" title="Volume Rank #${rank}">
          ${col}
          <small>#${rank}</small>
        </div>
      `;
    });
    
    matrixElement.appendChild(headerRow);
    
    // Create data rows
    data.rows.forEach(row => {
      const rowElement = document.createElement('div');
      rowElement.className = 'matrix-row';
      rowElement.innerHTML = `<div class="matrix-cell row-header">${row}</div>`;
      
      data.cols.slice(0, 10).forEach(col => {
        const cellData = data.matrix[row]?.[col];
        const cellElement = document.createElement('div');
        cellElement.className = `matrix-cell data-cell ${cellData?.signal?.toLowerCase() || 'none'}`;
        
        if (cellData) {
          cellElement.innerHTML = `
            <div class="cell-signal">${cellData.signal}</div>
            <div class="cell-conf">${(cellData.conf * 100).toFixed(0)}%</div>
          `;
          cellElement.title = `${row}/${col}: ${cellData.signal} (${(cellData.conf * 100).toFixed(1)}%)`;
        } else {
          cellElement.innerHTML = '<div class="cell-signal">—</div>';
          cellElement.title = `${row}/${col}: No signal`;
        }
        
        rowElement.appendChild(cellElement);
      });
      
      matrixElement.appendChild(rowElement);
    });
    
    container.appendChild(matrixElement);
  }

  updateMLDisplay(data) {
    console.log('🧠 ML Performance:', data.status);
    
    // Find ML container or create one
    let container = document.getElementById('ml-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ml-container';
      container.innerHTML = '<h3>Machine Learning Performance</h3>';
      document.body.appendChild(container);
    }
    
    // Update ML status
    let statusElement = container.querySelector('.ml-status');
    if (!statusElement) {
      statusElement = document.createElement('div');
      statusElement.className = 'ml-status';
      container.appendChild(statusElement);
    }
    
    const interpretation = data.interpretation || {};
    statusElement.innerHTML = `
      <div class="ml-health ${interpretation.class || 'ml-unknown'}">
        <span class="ml-emoji">${interpretation.emoji || '❓'}</span>
        <span class="ml-status-text">${interpretation.health || 'Unknown'}</span>
      </div>
      <div class="ml-description">${interpretation.description || 'No status available'}</div>
    `;
    
    // Update ML metrics
    this.updateMLMetrics(container, data);
    
    // Update feature importance
    this.updateFeatureImportance(container, data);
    
    // Update Brier score chart
    this.updateBrierScoreChart(container, data);
  }

  updateMLMetrics(container, data) {
    let metricsElement = container.querySelector('.ml-metrics');
    if (!metricsElement) {
      metricsElement = document.createElement('div');
      metricsElement.className = 'ml-metrics';
      container.appendChild(metricsElement);
    }
    
    const metrics = data.metrics || {};
    const learningStats = data.learning_stats || {};
    
    metricsElement.innerHTML = `
      <div class="metric-grid">
        <div class="metric-item">
          <span class="metric-label">Brier Score:</span>
          <span class="metric-value brier-score">${metrics.brier_score?.toFixed(3) || 'N/A'}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Sample Count:</span>
          <span class="metric-value">${metrics.sample_count || 0}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Accuracy:</span>
          <span class="metric-value">${(metrics.accuracy * 100).toFixed(1)}%</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Quantum Rank:</span>
          <span class="metric-value quantum-rank">#${metrics.quantum_rank || 'N/A'}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Learning Active:</span>
          <span class="metric-value">${metrics.learning_active ? '✅ Yes' : '❌ No'}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Recent Accuracy:</span>
          <span class="metric-value">${(learningStats.recent_accuracy * 100).toFixed(1)}%</span>
        </div>
      </div>
    `;
  }

  updateFeatureImportance(container, data) {
    let importanceElement = container.querySelector('.feature-importance');
    if (!importanceElement) {
      importanceElement = document.createElement('div');
      importanceElement.className = 'feature-importance';
      importanceElement.innerHTML = '<h4>Feature Importance</h4>';
      container.appendChild(importanceElement);
    }
    
    // Clear existing bars
    const existingBars = importanceElement.querySelector('.importance-bars');
    if (existingBars) {
      existingBars.remove();
    }
    
    if (!data.feature_importance) {
      return;
    }
    
    const barsContainer = document.createElement('div');
    barsContainer.className = 'importance-bars';
    
    // Sort features by importance
    const sortedFeatures = Object.entries(data.feature_importance)
      .sort(([,a], [,b]) => b - a);
    
    sortedFeatures.forEach(([feature, importance], index) => {
      const barElement = document.createElement('div');
      barElement.className = `importance-bar ${feature.includes('quantum') ? 'quantum' : ''}`;
      
      barElement.innerHTML = `
        <div class="bar-label">
          <span class="feature-name">${feature.replace('_', ' ')}</span>
          <span class="feature-rank">#${index + 1}</span>
        </div>
        <div class="bar-container">
          <div class="bar-fill" style="width: ${importance * 100}%"></div>
        </div>
        <div class="bar-value">${(importance * 100).toFixed(1)}%</div>
      `;
      
      barsContainer.appendChild(barElement);
    });
    
    importanceElement.appendChild(barsContainer);
  }

  updateBrierScoreChart(container, data) {
    let chartElement = container.querySelector('.brier-chart');
    if (!chartElement) {
      chartElement = document.createElement('div');
      chartElement.className = 'brier-chart';
      chartElement.innerHTML = '<h4>Brier Score History</h4>';
      container.appendChild(chartElement);
    }
    
    // Simple text-based chart for now
    // In a real implementation, you'd use a charting library like Chart.js
    let chartContent = chartElement.querySelector('.chart-content');
    if (!chartContent) {
      chartContent = document.createElement('div');
      chartContent.className = 'chart-content';
      chartElement.appendChild(chartContent);
    }
    
    if (data.chart_data && data.chart_data.length > 0) {
      const latest = data.chart_data[data.chart_data.length - 1];
      chartContent.innerHTML = `
        <div class="chart-summary">
          <div class="chart-item">
            <span class="chart-label">Latest Brier:</span>
            <span class="chart-value">${latest.brier_score.toFixed(3)}</span>
          </div>
          <div class="chart-item">
            <span class="chart-label">Trend:</span>
            <span class="chart-value">${data.chart_data.length > 1 ? 
              (latest.brier_score < data.chart_data[data.chart_data.length - 2].brier_score ? '📈 Improving' : '📉 Declining') 
              : '📊 Collecting'}</span>
          </div>
          <div class="chart-item">
            <span class="chart-label">Data Points:</span>
            <span class="chart-value">${data.chart_data.length}</span>
          </div>
        </div>
      `;
    } else {
      chartContent.innerHTML = '<p class="chart-placeholder">Collecting data for Brier score chart...</p>';
    }
  }

  updateSentimentDisplay(data) {
    console.log('📰 Sentiment:', data.enabled ? 'Enabled' : 'Disabled');
    
    let container = document.getElementById('sentiment-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'sentiment-container';
      container.innerHTML = '<h3>Sentiment Analysis</h3>';
      document.body.appendChild(container);
    }
    
    // Clear existing content
    const existingContent = container.querySelector('.sentiment-content');
    if (existingContent) {
      existingContent.remove();
    }
    
    const contentElement = document.createElement('div');
    contentElement.className = 'sentiment-content';
    
    if (data.enabled && data.articles && data.articles.length > 0) {
      contentElement.innerHTML = `
        <div class="sentiment-summary">
          <div class="sentiment-metric">
            <span class="metric-label">Overall Sentiment:</span>
            <span class="metric-value sentiment-${data.overall_sentiment > 0.5 ? 'positive' : data.overall_sentiment >= 0.3 ? 'neutral' : 'negative'}">
              ${(data.overall_sentiment * 100).toFixed(1)}%
            </span>
          </div>
          <div class="sentiment-metric">
            <span class="metric-label">Articles:</span>
            <span class="metric-value">${data.article_count}</span>
          </div>
          <div class="sentiment-metric">
            <span class="metric-label">Impact Score:</span>
            <span class="metric-value">${(data.sentiment_impact * 100).toFixed(1)}%</span>
          </div>
        </div>
      `;
      
      // Add articles list
      const articlesList = document.createElement('div');
      articlesList.className = 'articles-list';
      
      data.articles.forEach(article => {
        const articleElement = document.createElement('div');
        articleElement.className = `article-item sentiment-${article.sentiment > 0.5 ? 'positive' : article.sentiment >= 0.3 ? 'neutral' : 'negative'}`;
        
        const timeAgo = Math.floor((Date.now() / 1000 - article.timestamp) / 3600);
        
        articleElement.innerHTML = `
          <div class="article-title">${article.title}</div>
          <div class="article-meta">
            <span class="article-source">${article.source}</span>
            <span class="article-sentiment">${(article.sentiment * 100).toFixed(0)}% sentiment</span>
            <span class="article-time">${timeAgo}h ago</span>
          </div>
        `;
        
        articlesList.appendChild(articleElement);
      });
      
      contentElement.appendChild(articlesList);
    } else {
      contentElement.innerHTML = '<p class="sentiment-disabled">Sentiment analysis disabled or no articles available</p>';
    }
    
    container.appendChild(contentElement);
  }

  updatePortfolioDisplay(data) {
    console.log('💼 Portfolio:', data.asset_count, 'assets');
    
    let container = document.getElementById('portfolio-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'portfolio-container';
      container.innerHTML = '<h3>Portfolio Assets</h3>';
      document.body.appendChild(container);
    }
    
    // Clear existing content
    const existingContent = container.querySelector('.portfolio-content');
    if (existingContent) {
      existingContent.remove();
    }
    
    const contentElement = document.createElement('div');
    contentElement.className = 'portfolio-content';
    
    if (data.portfolio_details && data.portfolio_details.length > 0) {
      contentElement.innerHTML = `
        <div class="portfolio-summary">
          <div class="portfolio-metric">
            <span class="metric-label">Total Value:</span>
            <span class="metric-value">$${data.total_value_usdt.toLocaleString()}</span>
          </div>
          <div class="portfolio-metric">
            <span class="metric-label">Assets:</span>
            <span class="metric-value">${data.asset_count}</span>
          </div>
        </div>
      `;
      
      // Add assets list
      const assetsList = document.createElement('div');
      assetsList.className = 'assets-list';
      
      data.portfolio_details.forEach(asset => {
        const assetElement = document.createElement('div');
        assetElement.className = 'asset-item';
        
        assetElement.innerHTML = `
          <div class="asset-symbol">${asset.symbol}</div>
          <div class="asset-balance">${asset.balance}</div>
          <div class="asset-value">$${asset.value_usdt.toLocaleString()}</div>
          <div class="asset-allocation">${(asset.allocation * 100).toFixed(1)}%</div>
        `;
        
        assetsList.appendChild(assetElement);
      });
      
      contentElement.appendChild(assetsList);
    } else {
      contentElement.innerHTML = '<p class="portfolio-empty">No portfolio data available</p>';
    }
    
    container.appendChild(contentElement);
  }

  updateAtomicSwapsDisplay(data) {
    console.log('🔄 Atomic Swaps:', data.opportunities?.length || 0, 'opportunities');
    
    // Find atomic swaps container or create one
    let container = document.getElementById('atomic-swaps-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'atomic-swaps-container';
      container.className = 'card';
      container.innerHTML = `
        <div class="card-header">
          <h3>🔄 Atomic Swap Opportunities</h3>
          <span class="chip" id="atomic-swaps-chip">ANALYZING...</span>
        </div>
      `;
      
      // Find a good place to insert it (after trading grid)
      const gridContainer = document.getElementById('grid-container');
      if (gridContainer && gridContainer.parentNode) {
        gridContainer.parentNode.insertBefore(container, gridContainer.nextSibling);
      } else {
        document.body.appendChild(container);
      }
    }
    
    // Update chip status
    const chip = container.querySelector('#atomic-swaps-chip');
    if (chip) {
      const opportunityCount = data.opportunities?.length || 0;
      if (opportunityCount > 0) {
        chip.textContent = `${opportunityCount} OPPORTUNITIES`;
        chip.className = 'chip chip--ok';
      } else {
        chip.textContent = 'NO OPPORTUNITIES';
        chip.className = 'chip chip--warn';
      }
    }
    
    // Clear existing opportunities
    const existingOpportunities = container.querySelector('.atomic-opportunities');
    if (existingOpportunities) {
      existingOpportunities.remove();
    }
    
    // Create opportunities display
    const opportunitiesElement = document.createElement('div');
    opportunitiesElement.className = 'atomic-opportunities';
    
    if (data.opportunities && data.opportunities.length > 0) {
      // Add summary stats
      const summaryElement = document.createElement('div');
      summaryElement.className = 'atomic-summary';
      
      const totalGain = data.opportunities.reduce((sum, opp) => sum + (opp.expected_gain || 0), 0);
      const avgConfidence = data.opportunities.reduce((sum, opp) => sum + (opp.confidence || 0), 0) / data.opportunities.length;
      const highConfOpps = data.opportunities.filter(opp => opp.confidence > 0.8).length;
      
      summaryElement.innerHTML = `
        <div class="atomic-stats">
          <div class="atomic-stat">
            <span class="stat-label">Total Potential Gain:</span>
            <span class="stat-value positive">+${totalGain.toFixed(2)}%</span>
          </div>
          <div class="atomic-stat">
            <span class="stat-label">Avg Confidence:</span>
            <span class="stat-value">${(avgConfidence * 100).toFixed(1)}%</span>
          </div>
          <div class="atomic-stat">
            <span class="stat-label">High Confidence:</span>
            <span class="stat-value">${highConfOpps}/${data.opportunities.length}</span>
          </div>
        </div>
      `;
      
      opportunitiesElement.appendChild(summaryElement);
      
      // Add opportunities list
      const opportunitiesList = document.createElement('div');
      opportunitiesList.className = 'opportunities-list';
      
      // Sort by confidence and expected gain
      const sortedOpportunities = data.opportunities
        .sort((a, b) => (b.confidence * b.expected_gain) - (a.confidence * a.expected_gain))
        .slice(0, 10); // Show top 10
      
      sortedOpportunities.forEach((opportunity, index) => {
        const oppElement = document.createElement('div');
        oppElement.className = `atomic-swap-item ${opportunity.confidence > 0.8 ? 'high-confidence' : opportunity.confidence > 0.6 ? 'medium-confidence' : 'low-confidence'}`;
        
        const riskLevel = this.calculateRiskLevel(opportunity);
        const mlScore = this.getMlConfidenceScore(opportunity);
        
        oppElement.innerHTML = `
          <div class="swap-header">
            <div class="swap-route">${opportunity.swap_route || `${opportunity.from_symbol} → ${opportunity.to_symbol}`}</div>
            <div class="swap-rank">#${index + 1}</div>
          </div>
          <div class="swap-metrics">
            <div class="swap-metric">
              <span class="metric-label">Expected Gain:</span>
              <span class="metric-value positive">+${(opportunity.expected_gain || 0).toFixed(2)}%</span>
            </div>
            <div class="swap-metric">
              <span class="metric-label">Confidence:</span>
              <span class="metric-value">${(opportunity.confidence * 100).toFixed(1)}%</span>
            </div>
            <div class="swap-metric">
              <span class="metric-label">ML Score:</span>
              <span class="metric-value ml-score">${mlScore.toFixed(1)}%</span>
            </div>
            <div class="swap-metric">
              <span class="metric-label">Risk Level:</span>
              <span class="metric-value risk-${riskLevel.toLowerCase()}">${riskLevel}</span>
            </div>
          </div>
          <div class="swap-details">
            <div class="swap-detail">
              <span class="detail-label">Gas Cost:</span>
              <span class="detail-value">~$${opportunity.gas_cost || 'N/A'}</span>
            </div>
            <div class="swap-detail">
              <span class="detail-label">Execution Time:</span>
              <span class="detail-value">${opportunity.execution_time || 'N/A'}</span>
            </div>
            <div class="swap-detail">
              <span class="detail-label">Liquidity:</span>
              <span class="detail-value">${opportunity.liquidity_score ? (opportunity.liquidity_score * 100).toFixed(0) + '%' : 'N/A'}</span>
            </div>
          </div>
          <div class="swap-actions">
            <button class="btn-analyze" onclick="window.bottieApp.analyzeSwapOpportunity(${index})">📊 Analyze</button>
            ${opportunity.confidence > 0.7 ? `<button class="btn-execute" onclick="window.bottieApp.executeSwapOpportunity(${index})">🚀 Execute</button>` : ''}
          </div>
        `;
        
        opportunitiesList.appendChild(oppElement);
      });
      
      opportunitiesElement.appendChild(opportunitiesList);
    } else {
      opportunitiesElement.innerHTML = `
        <div class="no-opportunities">
          <p>🔍 No atomic swap opportunities detected at this time.</p>
          <p>The system is continuously analyzing market conditions for profitable swaps.</p>
        </div>
      `;
    }
    
    container.appendChild(opportunitiesElement);
    
    // Store opportunities for later use
    this.currentOpportunities = data.opportunities || [];
  }

  calculateRiskLevel(opportunity) {
    const confidence = opportunity.confidence || 0;
    const expectedGain = opportunity.expected_gain || 0;
    const liquidityScore = opportunity.liquidity_score || 0.5;
    
    // Simple risk calculation based on multiple factors
    const riskScore = (confidence * 0.4) + (expectedGain / 10 * 0.3) + (liquidityScore * 0.3);
    
    if (riskScore > 0.8) return 'LOW';
    if (riskScore > 0.6) return 'MEDIUM';
    if (riskScore > 0.4) return 'HIGH';
    return 'VERY HIGH';
  }

  getMlConfidenceScore(opportunity) {
    // Integrate with ML data if available
    if (this.mlData && this.mlData.metrics) {
      const baseAccuracy = this.mlData.metrics.accuracy || 0.5;
      const opportunityConfidence = opportunity.confidence || 0.5;
      
      // Combine ML model accuracy with opportunity-specific confidence
      return (baseAccuracy * 0.6 + opportunityConfidence * 0.4) * 100;
    }
    
    return (opportunity.confidence || 0.5) * 100;
  }

  analyzeSwapOpportunity(index) {
    const opportunity = this.currentOpportunities[index];
    if (!opportunity) return;
    
    console.log('📊 Analyzing swap opportunity:', opportunity);
    
    // Create detailed analysis modal
    const modal = document.createElement('div');
    modal.className = 'analysis-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h3>🔍 Swap Opportunity Analysis</h3>
          <button class="modal-close" onclick="this.closest('.analysis-modal').remove()">×</button>
        </div>
        <div class="analysis-content">
          <div class="analysis-section">
            <h4>Opportunity Details</h4>
            <div class="analysis-grid">
              <div class="analysis-item">
                <span class="analysis-label">Route:</span>
                <span class="analysis-value">${opportunity.swap_route || `${opportunity.from_symbol} → ${opportunity.to_symbol}`}</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">Expected Gain:</span>
                <span class="analysis-value positive">+${(opportunity.expected_gain || 0).toFixed(3)}%</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">Confidence Score:</span>
                <span class="analysis-value">${(opportunity.confidence * 100).toFixed(2)}%</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">ML Confidence:</span>
                <span class="analysis-value">${this.getMlConfidenceScore(opportunity).toFixed(2)}%</span>
              </div>
            </div>
          </div>
          
          <div class="analysis-section">
            <h4>Risk Assessment</h4>
            <div class="risk-analysis">
              <div class="risk-factor">
                <span class="risk-label">Overall Risk:</span>
                <span class="risk-value risk-${this.calculateRiskLevel(opportunity).toLowerCase()}">${this.calculateRiskLevel(opportunity)}</span>
              </div>
              <div class="risk-factor">
                <span class="risk-label">Liquidity Risk:</span>
                <span class="risk-value">${opportunity.liquidity_score ? ((1 - opportunity.liquidity_score) * 100).toFixed(0) + '% risk' : 'Unknown'}</span>
              </div>
              <div class="risk-factor">
                <span class="risk-label">Gas Cost Impact:</span>
                <span class="risk-value">${opportunity.gas_cost ? '$' + opportunity.gas_cost : 'Unknown'}</span>
              </div>
            </div>
          </div>
          
          <div class="analysis-section">
            <h4>ML Model Insights</h4>
            <div class="ml-insights">
              ${this.mlData && this.mlData.feature_importance ? 
                Object.entries(this.mlData.feature_importance)
                  .slice(0, 3)
                  .map(([feature, importance]) => `
                    <div class="insight-item">
                      <span class="insight-feature">${feature.replace('_', ' ')}:</span>
                      <span class="insight-importance">${(importance * 100).toFixed(1)}% importance</span>
                    </div>
                  `).join('') 
                : '<p>ML insights not available</p>'
              }
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-execute" onclick="window.bottieApp.executeSwapOpportunity(${index}); this.closest('.analysis-modal').remove();">
            🚀 Execute Swap
          </button>
          <button class="btn-cancel" onclick="this.closest('.analysis-modal').remove()">
            Cancel
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  }

  executeSwapOpportunity(index) {
    const opportunity = this.currentOpportunities[index];
    if (!opportunity) return;
    
    console.log('🚀 Executing swap opportunity:', opportunity);
    
    // Here you would implement the actual trading logic
    // For now, just show confirmation
    const confirmation = confirm(
      `Execute atomic swap?\n\n` +
      `Route: ${opportunity.swap_route || `${opportunity.from_symbol} → ${opportunity.to_symbol}`}\n` +
      `Expected Gain: +${(opportunity.expected_gain || 0).toFixed(2)}%\n` +
      `Confidence: ${(opportunity.confidence * 100).toFixed(1)}%\n` +
      `Risk Level: ${this.calculateRiskLevel(opportunity)}`
    );
    
    if (confirmation) {
      // Simulate execution
      alert(`✅ Swap executed successfully!\n\nRoute: ${opportunity.swap_route || `${opportunity.from_symbol} → ${opportunity.to_symbol}`}`);
      
      // Remove the opportunity from the list (it's been executed)
      this.currentOpportunities.splice(index, 1);
      this.updateAtomicSwapsDisplay({ opportunities: this.currentOpportunities });
    }
  }

  updateEndpointStatus(endpoint, status) {
    const box = document.querySelector(`[data-endpoint="${endpoint}"]`);
    if (box) {
      box.className = `endpoint-box ${status}`;
      const statusElement = box.querySelector('.endpoint-status');
      if (statusElement) {
        const statusText = {
          'success': 'Ready',
          'error': 'Error',
          'loading': 'Loading'
        };
        statusElement.textContent = statusText[status] || 'Unknown';
      }
    }
  }

  async testEndpoint(endpoint, boxElement) {
    try {
      boxElement.className = 'endpoint-box loading';
      
      const data = await this.fetchJSON(endpoint);
      
      boxElement.className = 'endpoint-box success';
      
      // Show response in modal
      this.showResponseModal(`${endpoint} Response`, data);
      
    } catch (error) {
      boxElement.className = 'endpoint-box error';
      console.error(`Endpoint ${endpoint} failed:`, error);
      
      this.showResponseModal(`${endpoint} Error`, {
        error: error.message,
        endpoint: endpoint,
        timestamp: new Date().toISOString()
      });
    }
  }

  showResponseModal(title, data) {
    const modal = document.getElementById('response-modal');
    const titleElement = document.getElementById('response-title');
    const dataElement = document.getElementById('response-data');
    
    if (modal && titleElement && dataElement) {
      titleElement.textContent = title;
      dataElement.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
      modal.style.display = 'flex';
    }
  }

  applyIntervals() {
    const healthInterval = parseInt(document.getElementById('health-interval')?.value) || 5000;
    const signalsInterval = parseInt(document.getElementById('signals-interval')?.value) || 3000;
    const gridInterval = parseInt(document.getElementById('grid-interval')?.value) || 15000;
    
    this.refreshIntervals = {
      health: healthInterval,
      signals: signalsInterval,
      grid: gridInterval,
      ml: 10000
    };
    
    console.log('✅ Applied new intervals:', this.refreshIntervals);
    
    // Restart intervals with new values
    if (this.isAuthenticated) {
      this.startDataRefresh();
    }
  }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.bottieApp = new SntaxApp();
});

// Add CSS styles for the new elements
const styles = `
<style>
.signals-list { margin-top: 10px; }
.signal-item { 
  background: #1a2332; 
  border: 1px solid #2a3441; 
  border-radius: 4px; 
  padding: 8px; 
  margin-bottom: 5px; 
}
.signal-item.signal-buy { border-left: 3px solid #4caf50; }
.signal-item.signal-sell { border-left: 3px solid #f44336; }
.signal-item.signal-hold { border-left: 3px solid #ff9800; }

.signal-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
}
.signal-symbol { font-weight: bold; color: #64ffda; }
.signal-type { 
  padding: 2px 6px; 
  border-radius: 3px; 
  font-size: 10px; 
  font-weight: bold; 
}
.signal-type.buy { background: #4caf50; color: white; }
.signal-type.sell { background: #f44336; color: white; }
.signal-type.hold { background: #ff9800; color: white; }

.grid-stats { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
  gap: 10px; 
  margin-bottom: 15px; 
}
.grid-stat { 
  background: #1a2332; 
  padding: 8px; 
  border-radius: 4px; 
  text-align: center; 
}
.stat-label { color: #8892b0; font-size: 11px; }
.stat-value { color: #64ffda; font-weight: bold; }

.trading-matrix { 
  overflow-x: auto; 
  border: 1px solid #2a3441; 
  border-radius: 4px; 
}
.matrix-row { display: flex; min-width: fit-content; }
.matrix-cell { 
  min-width: 80px; 
  padding: 4px; 
  border: 1px solid #2a3441; 
  text-align: center; 
  font-size: 10px; 
}
.header-cell { background: #1a2332; font-weight: bold; color: #64ffda; }
.row-header { background: #0f1419; font-weight: bold; color: #ffffff; }
.data-cell.buy { background: rgba(76, 175, 80, 0.2); }
.data-cell.sell { background: rgba(244, 67, 54, 0.2); }
.data-cell.hold { background: rgba(255, 152, 0, 0.2); }

.ml-health { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  margin-bottom: 10px; 
}
.ml-emoji { font-size: 20px; }
.ml-status-text { font-weight: bold; text-transform: capitalize; }
.ml-excellent .ml-status-text { color: #4caf50; }
.ml-good .ml-status-text { color: #8bc34a; }
.ml-moderate .ml-status-text { color: #ff9800; }
.ml-poor .ml-status-text { color: #f44336; }

.metric-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
  gap: 8px; 
  margin: 10px 0; 
}
.metric-item { 
  background: #1a2332; 
  padding: 6px; 
  border-radius: 4px; 
  display: flex; 
  justify-content: space-between; 
}
.metric-label { color: #8892b0; font-size: 11px; }
.metric-value { color: #ffffff; font-weight: bold; }
.brier-score { color: #64ffda !important; }
.quantum-rank { color: #ff6b6b !important; }

.importance-bars { margin-top: 10px; }
.importance-bar { 
  display: flex; 
  align-items: center; 
  margin-bottom: 8px; 
  gap: 10px; 
}
.importance-bar.quantum { 
  background: rgba(100, 255, 218, 0.1); 
  padding: 4px; 
  border-radius: 4px; 
}
.bar-label { min-width: 120px; display: flex; justify-content: space-between; }
.feature-name { color: #ffffff; font-size: 11px; }
.feature-rank { color: #64ffda; font-size: 10px; }
.bar-container { 
  flex: 1; 
  height: 12px; 
  background: #2a3441; 
  border-radius: 6px; 
  overflow: hidden; 
}
.bar-fill { 
  height: 100%; 
  background: linear-gradient(90deg, #64ffda, #4caf50); 
  transition: width 0.3s ease; 
}
.bar-value { color: #ffffff; font-size: 10px; min-width: 40px; text-align: right; }

.sentiment-summary { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
  gap: 10px; 
  margin-bottom: 15px; 
}
.sentiment-metric { 
  background: #1a2332; 
  padding: 8px; 
  border-radius: 4px; 
  display: flex; 
  justify-content: space-between; 
}
.sentiment-positive { color: #4caf50; }
.sentiment-negative { color: #f44336; }
.sentiment-neutral { color: #ff9800; }

.articles-list { margin-top: 10px; }
.article-item { 
  background: #1a2332; 
  border: 1px solid #2a3441; 
  border-radius: 4px; 
  padding: 8px; 
  margin-bottom: 8px; 
}
.article-title { font-weight: bold; margin-bottom: 5px; color: #ffffff; }
.article-meta { 
  display: flex; 
  gap: 10px; 
  font-size: 10px; 
  color: #8892b0; 
}

.portfolio-summary { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
  gap: 10px; 
  margin-bottom: 15px; 
}
.portfolio-metric { 
  background: #1a2332; 
  padding: 8px; 
  border-radius: 4px; 
  display: flex; 
  justify-content: space-between; 
}

.assets-list { margin-top: 10px; }
.asset-item { 
  background: #1a2332; 
  border: 1px solid #2a3441; 
  border-radius: 4px; 
  padding: 8px; 
  margin-bottom: 5px; 
  display: grid; 
  grid-template-columns: 1fr 1fr 1fr 1fr; 
  gap: 10px; 
  align-items: center; 
}
.asset-symbol { font-weight: bold; color: #64ffda; }
.asset-balance { color: #ffffff; }
.asset-value { color: #4caf50; }
.asset-allocation { color: #8892b0; }

.chart-summary { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
  gap: 8px; 
}
.chart-item { 
  background: #1a2332; 
  padding: 6px; 
  border-radius: 4px; 
  display: flex; 
  justify-content: space-between; 
}
.chart-label { color: #8892b0; font-size: 11px; }
.chart-value { color: #ffffff; font-weight: bold; }

/* Enhanced Atomic Swap Styles */
#atomic-swaps-container {
  background: #0f1419;
  border: 1px solid #2a3441;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 15px;
}

.atomic-summary {
  background: linear-gradient(135deg, #1a2332 0%, #0f1419 100%);
  border: 1px solid #64ffda;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 15px;
}

.atomic-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.atomic-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: rgba(100, 255, 218, 0.05);
  border-radius: 4px;
}

.opportunities-list {
  display: grid;
  gap: 12px;
}

.atomic-swap-item {
  background: #1a2332;
  border: 1px solid #2a3441;
  border-radius: 6px;
  padding: 12px;
  transition: all 0.3s ease;
  position: relative;
}

.atomic-swap-item:hover {
  border-color: #64ffda;
  background: rgba(100, 255, 218, 0.05);
  transform: translateY(-2px);
}

.atomic-swap-item.high-confidence {
  border-left: 4px solid #4caf50;
  background: rgba(76, 175, 80, 0.05);
}

.atomic-swap-item.medium-confidence {
  border-left: 4px solid #ff9800;
  background: rgba(255, 152, 0, 0.05);
}

.atomic-swap-item.low-confidence {
  border-left: 4px solid #f44336;
  background: rgba(244, 67, 54, 0.05);
}

.swap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.swap-route {
  font-weight: 600;
  color: #64ffda;
  font-size: 14px;
}

.swap-rank {
  background: #64ffda;
  color: #0c1426;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
}

.swap-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}

.swap-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: #0f1419;
  border-radius: 4px;
}

.swap-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
  padding-top: 8px;
  border-top: 1px solid #2a3441;
}

.swap-detail {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

.detail-label {
  color: #8892b0;
}

.detail-value {
  color: #ffffff;
  font-weight: 500;
}

.swap-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-analyze, .btn-execute {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-analyze {
  background: #2a3441;
  color: #64ffda;
  border: 1px solid #64ffda;
}

.btn-analyze:hover {
  background: #64ffda;
  color: #0c1426;
}

.btn-execute {
  background: #4caf50;
  color: #ffffff;
}

.btn-execute:hover {
  background: #45a049;
  transform: scale(1.05);
}

.ml-score {
  color: #64ffda !important;
}

.risk-low { color: #4caf50; }
.risk-medium { color: #ff9800; }
.risk-high { color: #f44336; }
.risk-very.high { color: #d32f2f; }

.no-opportunities {
  text-align: center;
  padding: 40px 20px;
  color: #8892b0;
}

.no-opportunities p {
  margin-bottom: 10px;
}

/* Analysis Modal Styles */
.analysis-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.analysis-modal .modal-content {
  background: #0f1419;
  border: 1px solid #2a3441;
  border-radius: 8px;
  padding: 20px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #2a3441;
}

.modal-close {
  background: #f44336;
  color: #ffffff;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.analysis-section {
  margin-bottom: 20px;
}

.analysis-section h4 {
  color: #64ffda;
  margin-bottom: 10px;
  font-size: 14px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.analysis-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 8px;
  background: #1a2332;
  border-radius: 4px;
}

.analysis-label {
  color: #8892b0;
  font-size: 11px;
}

.analysis-value {
  color: #ffffff;
  font-weight: 600;
  font-size: 11px;
}

.risk-analysis, .ml-insights {
  display: grid;
  gap: 8px;
}

.risk-factor, .insight-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 8px;
  background: #1a2332;
  border-radius: 4px;
}

.risk-label, .insight-feature {
  color: #8892b0;
  font-size: 11px;
}

.risk-value, .insight-importance {
  color: #ffffff;
  font-weight: 600;
  font-size: 11px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #2a3441;
}

.btn-cancel {
  background: #2a3441;
  color: #ffffff;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', styles);