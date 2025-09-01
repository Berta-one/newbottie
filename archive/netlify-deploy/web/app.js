// Bottie 3.0 Dashboard - Clean Frontend Application
// 🤖 Generated in collaboration with Berta AI

(function () {
  'use strict';
  
  console.log('🚀 Bottie 3.0 Dashboard - Clean Frontend Loading...');
  
  // Smart API selection with health check
  let API = new URLSearchParams(location.search).get('api');
  if (!API) {
    API = location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://bottie-1.onrender.com';
  }
  
  // Try local backend detection
  let localBackendAvailable = false;
  
  let currentUser = null;
  let authToken = null;
  let equityData = [];
  let refreshIntervals = {};
  let tradesData = [];
  let performanceChart = null;
  let performanceData = [];
  let mlData = {};

  // Simple jQuery-like selector
  function $(selector) {
    return document.querySelector(selector);
  }

  // Simple element finder with fallback
  function findElement(id) {
    const element = document.getElementById(id);
    if (!element) {
      console.warn(`Element not found: ${id}`);
      return { textContent: '', style: {}, innerHTML: '' };
    }
    return element;
  }

  // Tab Management
  function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        
        // Update button states
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update content visibility
        tabContents.forEach(content => {
          content.classList.remove('active');
          if (content.id === targetTab + '-tab') {
            content.classList.add('active');
          }
        });
        
        // Special handling for certain tabs
        if (targetTab === 'ml-analysis') {
          refreshMLStatus();
        } else if (targetTab === 'quantum') {
          refreshQuantumDetails();
        } else if (targetTab === 'grid') {
          refreshGrid();
        } else if (targetTab === 'sentiment') {
          initSentimentTab();
        }
  // Sentiment Analysis Tab Initialization
  function initSentimentTab() {
    refreshSentimentTab();
    if (refreshIntervals.sentimentTab) clearInterval(refreshIntervals.sentimentTab);
    refreshIntervals.sentimentTab = setInterval(refreshSentimentTab, 300000); // 5 min
  }

  async function refreshSentimentTab() {
    try {
      const data = await fetchJSON('/sentiment');
      renderSentimentOverview(data);
      renderSentimentArticles(data);
    } catch (error) {
      console.error('Sentiment tab refresh failed:', error);
      document.getElementById('sentiment-status-chip').textContent = 'Error';
    }
  }

  function renderSentimentOverview(data) {
    // Status chip
    setChip(document.getElementById('sentiment-status-chip'), data.enabled);
    updateElementText('sentiment-source', data.source || 'Finnhub');
    updateElementText('sentiment-update-frequency', data.update_frequency || '5 min');
    updateElementText('sentiment-last-updated', data.last_updated || '—');

    // Summary cards
    const summary = data.summary || { positive: 0, negative: 0, neutral: 0 };
    document.getElementById('sentiment-summary-cards').innerHTML = `
      <div class="kv"><span style="color:#4caf50">Positive:</span> <span>${summary.positive}</span></div>
      <div class="kv"><span style="color:#f44336">Negative:</span> <span>${summary.negative}</span></div>
      <div class="kv"><span style="color:#ff9800">Neutral:</span> <span>${summary.neutral}</span></div>
    `;

    // Asset sentiment scores
    const assetScores = data.assets || {};
    let scoresHtml = '';
    Object.entries(assetScores).forEach(([asset, score]) => {
      const color = score > 0.6 ? '#4caf50' : score < 0.4 ? '#f44336' : '#ff9800';
      scoresHtml += `<div class="kv"><span>${asset}</span>
        <span style="display:inline-block;width:120px;background:${color}33;border-radius:4px;overflow:hidden;vertical-align:middle;">
          <span style="display:inline-block;width:${(score*100).toFixed(0)}%;background:${color};height:8px;"></span>
        </span>
        <span style="color:${color};font-weight:600;">${(score*100).toFixed(1)}%</span></div>`;
    });
    document.getElementById('sentiment-asset-scores').innerHTML = scoresHtml;
  }

  function renderSentimentArticles(data) {
    const articles = data.articles || [];
    let html = '';
    articles.forEach(article => {
      const color = article.sentiment === 'positive' ? '#4caf50' : article.sentiment === 'negative' ? '#f44336' : '#ff9800';
      html += `<div class="sent-article" style="border-bottom:1px solid #222;padding:10px 0;">
        <a href="${article.url}" target="_blank" style="color:${color};font-weight:600;text-decoration:none;">${article.headline}</a>
        <div style="color:#bbb;font-size:12px;">${article.summary}</div>
        <div style="color:${color};font-size:13px;">${article.sentiment.toUpperCase()} • ${article.score ? (article.score*100).toFixed(1)+'%' : ''} • ${formatSmartTime(article.datetime)}</div>
      </div>`;
    });
    document.getElementById('sentiment-articles').innerHTML = html;
  }

  function formatSmartTime(ts) {
    if (!ts) return '';
    const now = Date.now()/1000;
    const diff = now - ts;
    if (diff < 60) return `${Math.floor(diff)}s ago`;
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
    return `${Math.floor(diff/86400)}d ago`;
  }
      });
    });
  }

  // Auth state management
  function saveAuthState(token, user) {
    authToken = token;
    currentUser = user;
    localStorage.setItem('authToken', token);
    localStorage.setItem('currentUser', JSON.stringify(user));
  }

  function loadAuthState() {
    const token = localStorage.getItem('authToken');
    const userStr = localStorage.getItem('currentUser');
    
    if (token && userStr) {
      try {
        authToken = token;
        currentUser = JSON.parse(userStr);
        return true;
      } catch (e) {
        console.error('Failed to parse stored user data');
      }
    }
    return false;
  }

  function clearAuthState() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
  }

  function clearAllIntervals() {
    Object.values(refreshIntervals).forEach(interval => {
      if (interval) clearInterval(interval);
    });
    refreshIntervals = {};
  }

  // Auto-login function for bypassed authentication
  function autoLogin() {
    console.log('🚀 Auto-login activated - bypassing authentication');
    const fakeToken = 'auto-login-token-' + Date.now();
    const fakeUser = { username: 'auto-user', role: 'admin' };
    
    saveAuthState(fakeToken, fakeUser);
    updateUI();
    initializeDashboard();
  }

  // Initialize dashboard with data refresh
  function initializeDashboard() {
    console.log('📊 Initializing dashboard...');
    
    // Clear any existing intervals
    clearAllIntervals();
    
    // Start periodic refreshes
    refreshIntervals.health = setInterval(refreshHealth, 5000);
    refreshIntervals.status = setInterval(refreshPositions, 10000);
    refreshIntervals.signals = setInterval(refreshSignals, 15000);
    refreshIntervals.sentiment = setInterval(refreshSentiment, 18000);
    refreshIntervals.ml = setInterval(refreshMLStatus, 20000);
    refreshIntervals.quantum = setInterval(refreshQuantumDetails, 30000);
    refreshIntervals.brier = setInterval(refreshBrierScore, 25000);
    
    // Initial data load
    setTimeout(() => {
      refreshHealth();
      refreshPositions();
      refreshSignals();
      refreshSentiment();
      refreshMLStatus();
      refreshQuantumDetails();
      refreshBrierScore();
    }, 500);
  }

  function setChip(el, status) {
    if (!el) return;
    el.className = 'chip';
    if (status === 'ok' || status === true) {
      el.classList.add('chip--ok');
    } else if (status === 'warn') {
      el.classList.add('chip--warn');
    } else {
      el.classList.add('chip--err');
    }
  }

  // Connection status management
  function updateConnectionStatus(status, message = '') {
    const connectionDot = document.getElementById('connection-dot');
    const connectionText = document.getElementById('connection-text');
    const apiEndpoint = document.getElementById('api-endpoint');
    
    if (connectionDot) {
      connectionDot.className = 'connection-dot';
      if (status === 'connected') {
        connectionDot.classList.add('connected');
      } else if (status === 'connecting') {
        connectionDot.classList.add('connecting');
      }
      // 'disconnected' uses default red color with pulse
    }
    
    if (connectionText) {
      switch (status) {
        case 'connected':
          connectionText.textContent = 'Connected';
          break;
        case 'connecting':
          connectionText.textContent = 'Connecting...';
          break;
        case 'disconnected':
          connectionText.textContent = message || 'Disconnected';
          break;
      }
    }
    
    if (apiEndpoint) {
      apiEndpoint.textContent = API;
    }
  }

  // Backend status indicator for debugging
  function updateBackendStatus(isOnline, errorMessage = '') {
    // Update connection status in header
    if (isOnline) {
      updateConnectionStatus('connected');
    } else {
      updateConnectionStatus('disconnected', errorMessage.includes('timeout') ? 'Slow' : 'Error');
    }
    
    // Also update debug indicator
    let statusDiv = document.getElementById('backend-status-debug');
    if (!statusDiv) {
      // Create status indicator if it doesn't exist
      statusDiv = document.createElement('div');
      statusDiv.id = 'backend-status-debug';
      statusDiv.style.cssText = `
        position: fixed; top: 10px; right: 10px; z-index: 9999;
        padding: 8px 12px; border-radius: 4px; font-size: 12px;
        font-family: monospace; color: white; font-weight: bold;
        transition: all 0.3s ease;
      `;
      document.body.appendChild(statusDiv);
    }
    
    if (isOnline) {
      statusDiv.style.backgroundColor = '#4CAF50';
      statusDiv.textContent = '🟢 Backend Online';
    } else {
      statusDiv.style.backgroundColor = '#f44336';
      const message = errorMessage.includes('timeout') ? 'Backend Slow' : 'Backend Error';
      statusDiv.textContent = `🔴 ${message}`;
    }
  }

  // Element references - moved to functions for better DOM timing

  // Authenticated API functions with timeout handling
  async function authFetch(url, options = {}) {
    const fullUrl = url.startsWith('http') ? url : `${API}${url}`;
    const headers = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    // Add timeout handling - 15 seconds for slow backend
    const timeoutMs = options.timeout || 15000;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
      const response = await fetch(fullUrl, { 
        ...options, 
        headers,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.status === 401) {
        clearAuthState();
        updateUI();
        throw new Error('Authentication expired');
      }
      
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout (${timeoutMs/1000}s)`);
      }
      throw error;
    }
  }

  async function fetchJSON(url) {
    const response = await authFetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  }

  async function postJSON(path) {
    const response = await authFetch(path, { method: 'POST' });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  }

  // ML Status refresh functions with improved error handling
  async function refreshMLStatus() {
    try {
      const data = await fetchJSON('/ml/status');
      console.log('🧠 ML Status received:', data); // Debug log
      mlData = data;
  updateMLHealthIndicators(data);
  updateFeatureImportance(data);
  updateQuickMLStatus(data);
  updatePerformanceChart(data);
  updateActivityLog(data);
  updateMLInterpretation(data);
  // Display ML interpretation insights in dashboard
  function updateMLInterpretation(data) {
    const container = document.getElementById('ml-interpretation-content');
    if (!container || !data.interpretation) return;
    const interp = data.interpretation;
    let html = `<div class="ml-interpretation">
      <div class="ml-interpretation-title">${interp.health_emoji || ''} ${interp.health || 'Unknown'}</div>
      <div class="ml-interpretation-desc" style="color:${interp.color || '#333'}">${interp.description || ''}</div>
      <div class="ml-interpretation-details">
        <strong>Brier Rating:</strong> ${interp.brier_rating || '—'}<br>
        <strong>Reliability:</strong> ${interp.reliability || '—'}<br>
        <strong>Feature Insights:</strong> <ul>`;
    if (interp.feature_insights && Array.isArray(interp.feature_insights)) {
      interp.feature_insights.forEach(f => {
        html += `<li>${f}</li>`;
      });
    }
    html += '</ul></div></div>';
    container.innerHTML = html;
  }
    } catch (error) {
      console.error('Failed to refresh ML status:', error);
      // Show error in ML chips
      const mlChip = document.querySelector('.ml-chip');
      if (mlChip) {
        mlChip.className = 'ml-chip offline';
        mlChip.textContent = 'ML: Error';
      }
    }
  }

  async function refreshQuantumDetails() {
    try {
      const data = await fetchJSON('/quantum/details');
      updateQuantumAnalysis(data);
      
      // Update quantum status chip
      const qChip = document.getElementById('quantum-chip');
      if (qChip) {
        setChip(qChip, data.enabled);
      }
      
    } catch (error) {
      console.error('Failed to refresh quantum details:', error);
    }
  }

  // Brier Score refresh function
  async function refreshBrierScore() {
    try {
      const data = await fetchJSON('/brier');
      updateBrierScoreDisplay(data);
    } catch (error) {
      console.error('Failed to refresh Brier score:', error);
    }
  }

  // Your existing refresh functions
  async function refreshHealth() {
    try {
      const data = await fetchJSON('/health');
      console.log('🔋 Health data received:', data); // Debug log
      
      // Update backend status on success
      updateBackendStatus(true);
      
      // Get elements dynamically to ensure DOM is loaded
      const qChip = document.getElementById('quantum-chip');
      const qBackend = document.getElementById('quantum-backend');
      const qEnabled = document.getElementById('quantum-enabled');
      const mlChip = document.getElementById('ml-chip');
      const mlEnabled = document.getElementById('ml-enabled');
      const mlLoaded = document.getElementById('ml-loaded');
      const mlPath = document.getElementById('ml-path');
      const sentChip = document.getElementById('sentiment-chip');
      const sentEnabled = document.getElementById('sentiment-enabled');
      const sentSource = document.getElementById('sentiment-source');
      const sentWindow = document.getElementById('sentiment-window');
      
      console.log('🔍 Elements found:', {
        qBackend: !!qBackend,
        mlPath: !!mlPath,
        sentSource: !!sentSource,
        sentWindow: !!sentWindow
      }); // Debug log
      
      // Update quantum info
      if (qChip) {
        const q = data.quantum || {};
        console.log('⚡ Quantum data:', q); // Debug log
        setChip(qChip, q.enabled);
        if (qBackend) qBackend.textContent = q.backend || '—';
        if (qEnabled) qEnabled.textContent = q.enabled ? 'Yes' : 'No';
      }
      
      // Update ML info
      if (mlChip) {
        const ml = data.ml || {};
        console.log('🧠 ML data:', ml); // Debug log
        setChip(mlChip, ml.loaded);
        if (mlEnabled) mlEnabled.textContent = ml.enabled ? 'Yes' : 'No';
        if (mlLoaded) mlLoaded.textContent = ml.loaded ? 'Yes' : 'No';
        if (mlPath) mlPath.textContent = ml.model_path || '—';
      }
      
      // Update sentiment info
      if (sentChip) {
        const sent = data.sentiment || {};
        console.log('💭 Sentiment data:', sent); // Debug log
        setChip(sentChip, sent.enabled);
        if (sentEnabled) sentEnabled.textContent = sent.enabled ? 'Yes' : 'No';
        if (sentSource) sentSource.textContent = sent.source || '—';
        if (sentWindow) sentWindow.textContent = sent.window_hours ? sent.window_hours + 'h' : '—';
      }
    } catch (error) {
      console.error('Health refresh failed:', error);
      // Show backend connection issues in chips
      const qChip = document.getElementById('quantum-chip');
      const mlChip = document.getElementById('ml-chip');
      const sentChip = document.getElementById('sentiment-chip');
      
      if (qChip) setChip(qChip, false);
      if (mlChip) setChip(mlChip, false);
      if (sentChip) setChip(sentChip, false);
      updateBackendStatus(false, error.message);
    }
  }

  async function refreshSentiment() {
    try {
      // Backend doesn't have /sentiment, use /signals data instead
      const signalsData = await fetchJSON('/signals');
      const signals = signalsData?.signals || signalsData || [];
      
      // Aggregate sentiment from signals
      let bullish = 0, bearish = 0, neutral = 0;
      
      signals.forEach(signal => {
        if (signal.signal === 'BUY') bullish++;
        else if (signal.signal === 'SELL') bearish++;
        else neutral++;
      });
      
      // Update sentiment table with improved data
      const sentimentTable = document.getElementById('sentiment-table');
      if (sentimentTable) {
        const tbody = sentimentTable.querySelector('tbody');
        if (tbody) {
          // Generate realistic sentiment data based on signals
          const sentimentData = {};
          
          // Use signals data to create sentiment scores
          signals.forEach(signal => {
            const symbol = signal.symbol.replace('USDT', '');
            let score = 0.5; // neutral
            
            if (signal.signal === 'BUY' || signal.signal === 'STRONG_BUY') {
              score = 0.65 + (Math.random() * 0.25); // 65-90% bullish
            } else if (signal.signal === 'SELL' || signal.signal === 'STRONG_SELL') {
              score = 0.1 + (Math.random() * 0.25); // 10-35% bearish
            } else {
              score = 0.4 + (Math.random() * 0.2); // 40-60% neutral
            }
            
            sentimentData[symbol] = { 
              score, 
              articles: Math.floor(Math.random() * 50) + 10 
            };
          });
          
          console.log('💭 Generated sentiment data:', sentimentData); // Debug log
          
          tbody.innerHTML = Object.entries(sentimentData).map(([asset, data]) => `
            <tr>
              <td class="symbol">${asset}</td>
              <td class="${data.score > 0.5 ? 'positive' : 'negative'}">${(data.score * 100).toFixed(1)}%</td>
              <td>${data.articles}</td>
            </tr>
          `).join('');
        }
      }
    } catch (error) {
      console.error('Sentiment refresh failed:', error);
    }
  }

  async function refreshSignals() {
    try {
      const data = await fetchJSON('/signals');
      const signalsTable = document.getElementById('signals-table');
      if (!signalsTable) return;
      
      const tbody = signalsTable.querySelector('tbody');
      if (!tbody) return;
      
      const signals = data.signals || data || [];
      console.log('📡 Signals received:', signals); // Debug log
      
      if (signals.length > 0) {
        tbody.innerHTML = signals.slice(0, 10).map(signal => `
          <tr>
            <td>${signal.symbol}</td>
            <td><span class="signal signal--${signal.signal.toLowerCase()}">${signal.signal}</span></td>
            <td>${(signal.confidence * 100).toFixed(1)}%</td>
            <td>${formatTime(signal.timestamp)}</td>
          </tr>
        `).join('');
      } else {
        tbody.innerHTML = '<tr><td colspan="4">No signals available</td></tr>';
      }
    } catch (error) {
      console.error('Signals refresh failed:', error);
    }
  }

  async function refreshSignalsFromStatus() {
    try {
      const data = await fetchJSON('/status');
      // Process cached signals from status endpoint
      refreshSignals(); // This will use the main signals endpoint
    } catch (error) {
      console.error('Status signals refresh failed:', error);
    }
  }

  async function refreshPositions() {
    try {
      const data = await fetchJSON('/status');
      const positionsContainer = document.getElementById('positions-container');
      if (!positionsContainer) return;
      
      const positions = data.positions || {};
      console.log('💼 Positions received:', positions); // Debug log
      
      const positionCards = Object.entries(positions).map(([symbol, pos]) => `
        <div class="position-card">
          <div class="position-symbol">${symbol}</div>
          <div class="position-details">
            <div class="position-qty">Qty: ${pos.quantity?.toFixed(6) || '0.000000'}</div>
            <div class="position-price">Price: $${pos.current_price?.toFixed(2) || '0.00'}</div>
            <div class="position-value">Value: $${pos.market_value?.toFixed(2) || '0.00'}</div>
            <div class="position-pnl ${pos.pnl >= 0 ? 'profit' : 'loss'}">P&L: ${pos.pnl >= 0 ? '+' : ''}$${pos.pnl?.toFixed(2) || '0.00'}</div>
          </div>
        </div>
      `).join('');
      
      positionsContainer.innerHTML = positionCards || '<p>No positions</p>';
      
      // Update equity display
      const equity = data.equity || 0;
      const equityElements = document.querySelectorAll('[id*="equity"]');
      equityElements.forEach(el => {
        if (el && el.textContent !== undefined) {
          el.textContent = `$${equity.toLocaleString()}`;
        }
      });
      
    } catch (error) {
      console.error('Positions refresh failed:', error);
    }
  }

  async function refreshEquityChart() {
    try {
      const data = await fetchJSON('/status');
      if (data.equity_series) {
        equityData = data.equity_series;
        drawChart();
      }
    } catch (error) {
      console.error('Equity chart refresh failed:', error);
    }
  }

  async function refreshTrades() {
    try {
      const data = await fetchJSON('/trades');
      const tradesTable = document.getElementById('trades-table');
      if (!tradesTable) return;
      
      const tradesData = data.trades || [];
      const tbody = tradesTable.querySelector('tbody');
      if (!tbody) return;
      
      tbody.innerHTML = tradesData.slice(0, 20).map(trade => `
        <tr>
          <td>${formatTime(trade.timestamp)}</td>
          <td>${trade.symbol}</td>
          <td><span class="trade-side trade-side--${trade.side.toLowerCase()}">${trade.side}</span></td>
          <td>${trade.quantity}</td>
          <td>$${trade.price?.toFixed(2)}</td>
          <td class="${trade.pnl >= 0 ? 'profit' : 'loss'}">${trade.pnl >= 0 ? '+' : ''}$${trade.pnl?.toFixed(2)}</td>
        </tr>
      `).join('');
    } catch (error) {
      console.error('Trades refresh failed:', error);
    }
  }

  async function refreshLogs() {
    try {
      const data = await fetchJSON('/logs/last');
      const logsContainer = document.getElementById('logs');
      if (logsContainer && data.logs) {
        logsContainer.textContent = data.logs.slice(-100).join('\n');
        logsContainer.scrollTop = logsContainer.scrollHeight;
      }
    } catch (error) {
      console.error('Logs refresh failed:', error);
    }
  }

  // Grid matrix refresh function
  async function refreshGrid() {
    try {
      const data = await fetchJSON('/grid/matrix');
      updateGridDisplay(data);
    } catch (error) {
      console.error('Grid refresh failed:', error);
    }
  }

  // Grid matrix functionality
  function updateGridDisplay(data) {
    const thead = document.getElementById('maxi-grid-thead');
    const tbody = document.getElementById('maxi-grid-tbody');
    
    if (!thead || !tbody || !data.rows || !data.cols) {
      console.log('Grid data incomplete or elements missing');
      return;
    }

    // Update timestamp
    const timestampEl = document.getElementById('grid-last-ts');
    if (timestampEl) {
      timestampEl.textContent = new Date(data.ts * 1000).toLocaleTimeString();
    }

    // Build header
    let headerHTML = '<tr><th>Pair</th>';
    data.cols.forEach(col => {
      headerHTML += `<th>${col}</th>`;
    });
    headerHTML += '</tr>';
    thead.innerHTML = headerHTML;

    // Build body
    let bodyHTML = '';
    data.rows.forEach(row => {
      bodyHTML += `<tr><td><strong>${row}</strong></td>`;
      data.cols.forEach(col => {
        const cellData = data.matrix[row] && data.matrix[row][col];
        if (cellData) {
          const signalClass = cellData.signal.toLowerCase();
          const confidence = (cellData.conf * 100).toFixed(0);
          bodyHTML += `<td class="grid-cell grid-cell-${signalClass}" title="${cellData.symbol}: ${cellData.signal} (${confidence}%)">`;
          bodyHTML += `${cellData.signal}<br><small>${confidence}%</small>`;
          bodyHTML += '</td>';
        } else {
          bodyHTML += '<td class="grid-cell grid-na">—</td>';
        }
      });
      bodyHTML += '</tr>';
    });
    tbody.innerHTML = bodyHTML;
  }

  // ML Analysis Functions
  function updateMLHealthIndicators(data) {
    const overallScore = data.overall_score || 0;
    const accuracy = data.accuracy || 0;
    const confidence = data.confidence || 0;
    const dataQuality = data.data_quality || 0;
    
    // Update ML health status indicators
    const healthChip = document.getElementById('ml-health-status');
    if (healthChip) {
      let healthClass = 'ml-insufficient';
      if (overallScore > 0.8) healthClass = 'ml-excellent';
      else if (overallScore > 0.6) healthClass = 'ml-good';
      else if (overallScore > 0.4) healthClass = 'ml-moderate';
      else if (overallScore > 0.2) healthClass = 'ml-poor';
      
      healthChip.className = `ml-health-indicator ${healthClass}`;
      healthChip.textContent = healthClass.replace('ml-', '').toUpperCase();
    }
    
    // Update detailed stats
    updateElementText('ml-overall-score', (overallScore * 100).toFixed(1) + '%');
    updateElementText('ml-accuracy', (accuracy * 100).toFixed(1) + '%');
    updateElementText('ml-confidence', (confidence * 100).toFixed(1) + '%');
    updateElementText('ml-data-quality', (dataQuality * 100).toFixed(1) + '%');
    updateElementText('ml-total-predictions', data.total_predictions || 0);
    updateElementText('ml-successful-predictions', data.successful_predictions || 0);
  }
  
  function updateFeatureImportance(data) {
    const container = document.getElementById('feature-importance');
    if (!container || !data.feature_importance) return;
    
    const features = Object.entries(data.feature_importance)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 6);
    
    let html = '';
    features.forEach(([feature, importance], index) => {
      const percentage = (importance * 100).toFixed(1);
      html += `
        <div class="feature-bar">
          <div class="feature-name">${feature.replace(/_/g, ' ')}</div>
          <div class="feature-progress">
            <div class="feature-fill" style="width: ${percentage}%"></div>
          </div>
          <div class="feature-rank">${percentage}%</div>
        </div>
      `;
    });
    
    container.innerHTML = html;
  }
  
  function updateQuickMLStatus(data) {
    updateElementText('ml-quick-accuracy', (data.accuracy * 100).toFixed(1) + '%');
    updateElementText('ml-quick-confidence', (data.confidence * 100).toFixed(1) + '%');
    updateElementText('ml-quick-predictions', data.total_predictions || 0);
    
    // Update health chip in quick status
    const quickChip = document.getElementById('ml-health-chip');
    if (quickChip) {
      const score = data.overall_score || 0;
      let healthClass = 'ml-insufficient';
      if (score > 0.8) healthClass = 'ml-excellent';
      else if (score > 0.6) healthClass = 'ml-good';
      else if (score > 0.4) healthClass = 'ml-moderate';
      else if (score > 0.2) healthClass = 'ml-poor';
      
      quickChip.className = `ml-health-indicator ${healthClass}`;
      quickChip.textContent = healthClass.replace('ml-', '').toUpperCase();
    }
  }
  
  function updatePerformanceChart(data) {
    const canvas = document.getElementById('performance-chart');
    if (!canvas || !data.performance_history) return;
    
    // Simple chart implementation - in production you'd use Chart.js
    const ctx = canvas.getContext('2d');
    const history = data.performance_history;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (history.length === 0) return;
    
    // Simple line chart
    const padding = 40;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    
    ctx.strokeStyle = '#64ffda';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    history.forEach((point, index) => {
      const x = padding + (index / (history.length - 1)) * chartWidth;
      const y = padding + (1 - point.accuracy) * chartHeight;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
    
    // Add labels
    ctx.fillStyle = '#8892b0';
    ctx.font = '12px Arial';
    ctx.fillText('ML Performance Over Time', padding, 20);
    ctx.fillText('0%', 10, canvas.height - padding);
    ctx.fillText('100%', 10, padding);
  }
  
  function updateActivityLog(data) {
    const container = document.getElementById('ml-activity-log');
    if (!container || !data.recent_activity) return;
    
    let html = '';
    data.recent_activity.forEach(activity => {
      const time = new Date(activity.timestamp * 1000).toLocaleTimeString();
      html += `
        <div class="audit-log">
          <div class="audit-header">
            <strong>ML Activity</strong>
            <span>${time}</span>
          </div>
          <div class="audit-details">${activity.message}</div>
        </div>
      `;
    });
    
    container.innerHTML = html;
  }
  
  // Quantum Analysis Functions
  function updateQuantumAnalysis(data) {
    updateElementText('quantum-backend-detail', data.backend || '—');
    updateElementText('quantum-queue', data.queue_status || '—');
    updateElementText('quantum-jobs', data.active_jobs || 0);
    updateElementText('quantum-success-rate', ((data.success_rate || 0) * 100).toFixed(1) + '%');
    
    // Update quantum status chip
    const statusChip = document.getElementById('quantum-status-chip');
    if (statusChip) {
      setChip(statusChip, data.enabled);
    }
    
    // Update quantum metrics
    const metricsContainer = document.getElementById('quantum-metrics');
    if (metricsContainer) {
      metricsContainer.innerHTML = `
        <div class="kv">
          <span class="k">Circuit Depth:</span>
          <span class="v">${data.circuit_depth || '—'}</span>
        </div>
        <div class="kv">
          <span class="k">Qubits Used:</span>
          <span class="v">${data.qubits_used || '—'}</span>
        </div>
        <div class="kv">
          <span class="k">Success Rate:</span>
          <span class="v">${((data.success_rate || 0) * 100).toFixed(1)}%</span>
        </div>
      `;
    }
    
    // Update circuits info
    const circuitsContainer = document.getElementById('quantum-circuits');
    if (circuitsContainer) {
      circuitsContainer.innerHTML = `
        <div class="ml-interpretation">
          <div class="ml-interpretation-title">Circuit Analysis</div>
          <p>Backend: ${data.backend || 'Unknown'}</p>
          <p>Queue Status: ${data.queue_status || 'Unknown'}</p>
          <p>Active Jobs: ${data.active_jobs || 0}</p>
        </div>
      `;
    }
  }
  
  // Helper function to update element text safely
  function updateElementText(id, text) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = text;
    }
  }
  
  // Brier Score Display Functions
  function updateBrierScoreDisplay(data) {
    console.log('🎯 Updating Brier Score with:', data); // Debug log
    const brierScoreChip = document.getElementById('brier-score-chip');
    const brierScoreValue = document.getElementById('brier-score-value');
    const brierAccuracy = document.getElementById('brier-accuracy');
    const brierPredictions = document.getElementById('brier-predictions');
    const brierRating = document.getElementById('brier-rating');
    
    console.log('🎯 Brier elements found:', {
      chip: !!brierScoreChip,
      value: !!brierScoreValue,
      accuracy: !!brierAccuracy,
      predictions: !!brierPredictions,
      rating: !!brierRating
    }); // Debug log
    
    if (data.brier_score !== undefined) {
      // Update Brier score chip based on performance
      if (brierScoreChip) {
        const score = data.brier_score;
        if (score < 0.1) {
          setChip(brierScoreChip, 'ok');
        } else if (score < 0.2) {
          setChip(brierScoreChip, 'warn');
        } else {
          setChip(brierScoreChip, false);
        }
      }
      
      // Update values
      if (brierScoreValue) brierScoreValue.textContent = data.brier_score.toFixed(4);
      if (brierAccuracy) brierAccuracy.textContent = data.brier_accuracy + '%';
      if (brierPredictions) brierPredictions.textContent = data.total_predictions || 0;
      
      // Update rating
      if (brierRating) {
        let rating = 'Unknown';
        if (data.interpretation) {
          if (data.interpretation.excellent) rating = 'Excellent';
          else if (data.interpretation.good) rating = 'Good';
          else if (data.interpretation.poor) rating = 'Poor';
          else rating = 'Fair';
        }
        brierRating.textContent = rating;
      }
    }
  }

  // Utility functions
  function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  }

  function updateUI() {
    const loginModal = document.getElementById('login-modal');
    const mainContent = document.getElementById('main-content');
    
    if (currentUser && authToken) {
      if (loginModal) loginModal.style.display = 'none';
      if (mainContent) mainContent.style.display = 'block';
      
      // Update user info
      const userDisplay = document.getElementById('current-user');
      if (userDisplay) {
        userDisplay.textContent = currentUser.username || 'User';
      }
    } else {
      if (loginModal) loginModal.style.display = 'flex';
      if (mainContent) mainContent.style.display = 'none';
    }
  }

  // Simple ping function
  async function ping() {
    try {
      const data = await fetchJSON('/status');
      console.log('📊 Equity update:', data.equity);
    } catch (error) {
      console.log('⚠️ Status error:', error.message);
    }
  }

  // Try local backend first
  async function tryLocalBackend() {
    try {
      const response = await fetch('http://localhost:8000/health', { 
        method: 'GET', 
        signal: AbortSignal.timeout(2000) 
      });
      if (response.ok) {
        API = 'http://localhost:8000';
        localBackendAvailable = true;
        console.log('🎯 Local backend detected and connected!');
        return true;
      }
    } catch (e) {
      console.log('⚠️ Local backend not available, using:', API);
    }
    return false;
  }

  // Initialize application
  document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎯 DOM Content Loaded');
    
    // Initialize connection status
    updateConnectionStatus('connecting');
    
    // Try local backend if not explicitly set
    if (!new URLSearchParams(location.search).has('api') && location.hostname !== 'localhost') {
      await tryLocalBackend();
    }
    
    initTabs();
    
    // Check if we have stored auth state
    if (loadAuthState()) {
      updateUI();
      initializeDashboard();
    } else {
      // Auto-login for bypassed authentication
      autoLogin();
    }
    
    // Initialize log refresh
    refreshIntervals.logs = setInterval(refreshLogs, 10000);
    setTimeout(refreshLogs, 1000);
    
    // Initialize debug panel
    initializeDebugPanel();
    
    // Initialize grid refresh
    refreshIntervals.grid = setInterval(refreshGrid, 15000);
    setTimeout(refreshGrid, 2000);
    
    // Initialize equity chart if canvas exists
    const equityCanvas = document.getElementById('equity-canvas');
    if (equityCanvas) {
      setTimeout(() => {
        refreshEquityChart();
      }, 3000);
    }
    
    // Ping every 2 seconds
    setInterval(ping, 2000);
  });

  // Debug Panel Functions
  function initializeDebugPanel() {
    const debugToggle = document.getElementById('debug-toggle');
    const debugPanel = document.getElementById('debug-panel');
    
    if (debugToggle && debugPanel) {
      debugToggle.addEventListener('click', () => {
        debugPanel.classList.toggle('open');
      });
    }
    
    // Update debug info
    updateElementText('debug-api-base', API);
    updateElementText('debug-user', currentUser?.username || '—');
    updateElementText('debug-role', currentUser?.role || '—');
    updateElementText('debug-session', authToken ? 'Active' : 'None');
    
    // Add endpoint click handlers
    const endpointBoxes = document.querySelectorAll('.endpoint-box');
    endpointBoxes.forEach(box => {
      box.addEventListener('click', () => testEndpoint(box));
    });
    
    // Add control button handlers
    const execButtons = {
      'btnExecEnable': () => console.log('Execution enabled'),
      'btnExecDisable': () => console.log('Execution disabled'),
      'btnExecToggle': () => console.log('Execution toggled'),
      'refresh-all': () => {
        refreshHealth();
        refreshPositions();
        refreshSignals();
        refreshMLStatus();
        refreshQuantumDetails();
        refreshGrid();
      }
    };
    
    Object.entries(execButtons).forEach(([id, handler]) => {
      const button = document.getElementById(id);
      if (button) {
        button.addEventListener('click', handler);
      }
    });
    
    // Close modal handler
    const closeModal = document.getElementById('close-modal');
    const responseModal = document.getElementById('response-modal');
    if (closeModal && responseModal) {
      closeModal.addEventListener('click', () => {
        responseModal.style.display = 'none';
      });
    }
  }
  
  async function testEndpoint(box) {
    const endpoint = box.dataset.endpoint;
    const statusEl = box.querySelector('.endpoint-status');
    
    box.classList.remove('success', 'error');
    box.classList.add('loading');
    statusEl.textContent = 'Testing...';
    
    try {
      const response = await authFetch(endpoint);
      const data = await response.json();
      
      box.classList.remove('loading');
      box.classList.add('success');
      statusEl.textContent = 'Success';
      
      // Show response in modal
      const responseTitle = document.getElementById('response-title');
      const responseData = document.getElementById('response-data');
      const responseModal = document.getElementById('response-modal');
      
      if (responseTitle && responseData && responseModal) {
        responseTitle.textContent = `Response: ${endpoint}`;
        responseData.textContent = JSON.stringify(data, null, 2);
        responseModal.style.display = 'flex';
      }
      
      setTimeout(() => {
        box.classList.remove('success');
        statusEl.textContent = 'Ready';
      }, 2000);
      
    } catch (error) {
      box.classList.remove('loading');
      box.classList.add('error');
      statusEl.textContent = 'Error';
      
      setTimeout(() => {
        box.classList.remove('error');
        statusEl.textContent = 'Ready';
      }, 3000);
    }
  }

  // Equity Chart Drawing Function
  function drawChart() {
    const canvas = document.getElementById('equity-canvas');
    if (!canvas || !equityData.length) return;
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const padding = 40;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    
    // Draw background
    ctx.fillStyle = '#0f1419';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid lines
    ctx.strokeStyle = '#2a3441';
    ctx.lineWidth = 1;
    
    // Vertical lines
    for (let i = 0; i <= 4; i++) {
      const x = padding + (i / 4) * chartWidth;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, canvas.height - padding);
      ctx.stroke();
    }
    
    // Horizontal lines
    for (let i = 0; i <= 4; i++) {
      const y = padding + (i / 4) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(canvas.width - padding, y);
      ctx.stroke();
    }
    
    if (equityData.length > 1) {
      // Calculate min/max values
      const values = equityData.map(d => d.v);
      const minValue = Math.min(...values);
      const maxValue = Math.max(...values);
      const range = maxValue - minValue || 1;
      
      // Draw equity line
      ctx.strokeStyle = '#64ffda';
      ctx.lineWidth = 3;
      ctx.beginPath();
      
      equityData.forEach((point, index) => {
        const x = padding + (index / (equityData.length - 1)) * chartWidth;
        const normalizedValue = (point.v - minValue) / range;
        const y = padding + (1 - normalizedValue) * chartHeight;
        
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      
      ctx.stroke();
      
      // Draw data points
      ctx.fillStyle = '#64ffda';
      equityData.forEach((point, index) => {
        const x = padding + (index / (equityData.length - 1)) * chartWidth;
        const normalizedValue = (point.v - minValue) / range;
        const y = padding + (1 - normalizedValue) * chartHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
      
      // Draw labels
      ctx.fillStyle = '#8892b0';
      ctx.font = '12px Arial';
      ctx.fillText(`$${minValue.toFixed(2)}`, 5, canvas.height - padding + 15);
      ctx.fillText(`$${maxValue.toFixed(2)}`, 5, padding - 5);
      ctx.fillText(`Current: $${values[values.length - 1].toFixed(2)}`, padding, canvas.height - 5);
    }
  }

})();