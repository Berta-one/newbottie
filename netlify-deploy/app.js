(function () {
  const API = new URLSearchParams(location.search).get('api') || 'https://bottie-1.onrender.com';
  
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

        // Trigger tab-specific refresh
        if (targetTab === 'ml-monitor') {
          refreshMLStatus();
        } else if (targetTab === 'quantum') {
          refreshQuantumDetails();
        }
      });
    });
  }

  // Chart Initialization for ML Monitor
  function initPerformanceChart() {
    const canvas = document.getElementById('performance-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    performanceChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Accuracy',
            data: [],
            borderColor: '#4caf50',
            backgroundColor: 'rgba(76, 175, 80, 0.1)',
            fill: false,
            tension: 0.1
          },
          {
            label: 'Confidence',
            data: [],
            borderColor: '#2196f3',
            backgroundColor: 'rgba(33, 150, 243, 0.1)',
            fill: false,
            tension: 0.1
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            labels: { color: '#ffffff' }
          }
        },
        scales: {
          x: {
            ticks: { color: '#8892b0' },
            grid: { color: 'rgba(136, 146, 176, 0.1)' }
          },
          y: {
            ticks: { color: '#8892b0' },
            grid: { color: 'rgba(136, 146, 176, 0.1)' }
          }
        }
      }
    });
  }

  // Authentication State Management
  function saveAuthState(token, user) {
    localStorage.setItem('bottie_auth_token', token);
    localStorage.setItem('bottie_user', JSON.stringify(user));
    authToken = token;
    currentUser = user;
  }

  function loadAuthState() {
    const token = localStorage.getItem('bottie_auth_token');
    const userStr = localStorage.getItem('bottie_user');
    if (token && userStr) {
      authToken = token;
      currentUser = JSON.parse(userStr);
      return true;
    }
    return false;
  }

  function clearAuthState() {
    localStorage.removeItem('bottie_auth_token');
    localStorage.removeItem('bottie_user');
    authToken = null;
    currentUser = null;
  }

  function updateUI() {
    const loginModal = document.getElementById('login-modal');
    const mainContent = document.getElementById('main-content');
    const dashboardTabs = document.getElementById('dashboard-tabs');
    const userInfo = document.getElementById('user-info');
    const debugToggle = document.getElementById('debug-toggle');
    const userName = document.getElementById('user-name');
    
    if (currentUser && authToken) {
      loginModal.style.display = 'none';
      mainContent.style.display = 'block';
      dashboardTabs.style.display = 'flex';
      userInfo.style.display = 'flex';
      debugToggle.style.display = 'block';
      userName.textContent = currentUser.username || 'User';
      
      // Show audit section for superusers
      if (currentUser.role === 'superuser') {
        document.getElementById('audit-section').style.display = 'block';
      }
      
      // Update debug info
      document.getElementById('debug-api-base').textContent = API;
      document.getElementById('debug-user').textContent = currentUser.username;
      document.getElementById('debug-role').textContent = currentUser.role;
      document.getElementById('debug-session').textContent = authToken.slice(0, 8) + '...';
    } else {
      loginModal.style.display = 'flex';
      mainContent.style.display = 'none';
      dashboardTabs.style.display = 'none';
      userInfo.style.display = 'none';
      debugToggle.style.display = 'none';
    }
  }

  // Login functionality
  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('login-btn');
    const loginError = document.getElementById('login-error');
    
    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';
    loginError.textContent = '';
    
    try {
      const response = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        saveAuthState(data.access_token, data.user);
        updateUI();
        initializeDashboard();
      } else {
        loginError.textContent = data.detail || 'Login failed';
      }
    } catch (error) {
      loginError.textContent = 'Connection error. Please try again.';
      console.error('Login error:', error);
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Login';
    }
  });

  // Guest mode functionality (view-only without authentication)
  async function enterGuestMode() {
    const loginError = document.getElementById('login-error');
    loginError.innerHTML = 'Entering guest mode (view-only access)...';
    
    try {
      // Test if we can access basic status without auth
      const response = await fetch(`${API}/status`, { method: 'GET' });
      if (response.ok) {
        const data = await response.json();
        loginError.innerHTML = `✅ Guest mode enabled! Portfolio Equity: $${data.equity?.toFixed(2) || 'Unknown'}`;
        
        // Hide login modal and show dashboard
        document.getElementById('login-modal').style.display = 'none';
        
        // Set currentUser to guest
        currentUser = { username: 'guest', role: 'viewer' };
        updateUI();
        
        // Start basic data refresh (only non-auth endpoints)
        startBasicDataRefresh();
        
      } else {
        loginError.innerHTML = '❌ Guest mode not available - authentication required.';
      }
    } catch (error) {
      loginError.innerHTML = '❌ Connection error - cannot access guest mode.';
    }
  }

  // Basic data refresh for guest mode
  function startBasicDataRefresh() {
    // Refresh basic status every 5 seconds
    setInterval(async () => {
      try {
        await refreshPositions();
        await refreshEquity();
      } catch (error) {
        console.log('Guest refresh error:', error);
      }
    }, 5000);
    
    // Initial load
    setTimeout(() => {
      refreshPositions();
      refreshEquity();
    }, 500);
  }

  // Debug endpoint testing functions
  async function testDebugEndpoints() {
    const loginError = document.getElementById('login-error');
    loginError.innerHTML = 'Testing debug endpoints...<br><br>';

    // Test debug/auth endpoint
    try {
      loginError.innerHTML += 'Testing GET /debug/auth... ';
      const response = await fetch(`${API}/debug/auth`);
      if (response.ok) {
        const data = await response.json();
        loginError.innerHTML += `✅ Success!<br>`;
        loginError.innerHTML += `Admin Password: ${data.environment_variables?.ADMIN_PASSWORD || 'Not found'}<br>`;
        loginError.innerHTML += `Superuser Password: ${data.environment_variables?.SUPERUSER_PASSWORD || 'Not found'}<br>`;
        loginError.innerHTML += `Admin Verify: ${data.password_verification_test?.admin_password_verify ? '✅' : '❌'}<br>`;
        loginError.innerHTML += `Superuser Verify: ${data.password_verification_test?.superuser_password_verify ? '✅' : '❌'}<br><br>`;
      } else {
        loginError.innerHTML += `❌ Failed (${response.status})<br>`;
      }
    } catch (error) {
      loginError.innerHTML += `❌ Error: ${error.message}<br>`;
    }

    // Test basic API connectivity
    try {
      loginError.innerHTML += 'Testing GET /health... ';
      const response = await fetch(`${API}/health`);
      if (response.ok) {
        loginError.innerHTML += `✅ Success!<br>`;
      } else {
        loginError.innerHTML += `❌ Failed (${response.status})<br>`;
      }
    } catch (error) {
      loginError.innerHTML += `❌ Error: ${error.message}<br>`;
    }
  }

  async function resetPasswordsDebug() {
    const loginError = document.getElementById('login-error');
    loginError.innerHTML = 'Attempting to reset passwords...<br>';

    try {
      const response = await fetch(`${API}/debug/reset-passwords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        loginError.innerHTML += `✅ Reset successful!<br>`;
        loginError.innerHTML += `Admin Password: ${data.admin_password}<br>`;
        loginError.innerHTML += `Superuser Password: ${data.superuser_password}<br>`;
        loginError.innerHTML += `Admin Verify: ${data.verification?.admin_verify ? '✅' : '❌'}<br>`;
        loginError.innerHTML += `Superuser Verify: ${data.verification?.superuser_verify ? '✅' : '❌'}<br>`;
        
        // Display new credentials for manual login
        loginError.innerHTML += '<br>Please use the above passwords to log in manually.<br>';
      } else {
        loginError.innerHTML += `❌ Reset failed (${response.status})<br>`;
      }
    } catch (error) {
      loginError.innerHTML += `❌ Reset error: ${error.message}<br>`;
    }
  }

  // Add debug and utility buttons to the login form
  function addCredentialTestButton() {
    const loginForm = document.getElementById('login-form');
    if (loginForm && !document.getElementById('debug-endpoints-btn')) {
      const debugBtn = document.createElement('button');
      debugBtn.type = 'button';
      debugBtn.id = 'debug-endpoints-btn';
      debugBtn.className = 'login-btn';
      debugBtn.style.marginTop = '10px';
      debugBtn.style.background = '#9c27b0';
      debugBtn.textContent = 'Test Debug Endpoints';
      debugBtn.onclick = testDebugEndpoints;

      const resetBtn = document.createElement('button');
      resetBtn.type = 'button';
      resetBtn.id = 'reset-passwords-btn';
      resetBtn.className = 'login-btn';
      resetBtn.style.marginTop = '10px';
      resetBtn.style.background = '#f44336';
      resetBtn.textContent = 'Reset Passwords';
      resetBtn.onclick = resetPasswordsDebug;

      const guestBtn = document.createElement('button');
      guestBtn.type = 'button';
      guestBtn.id = 'guest-mode-btn';
      guestBtn.className = 'login-btn';
      guestBtn.style.marginTop = '10px';
      guestBtn.style.background = '#4caf50';
      guestBtn.textContent = 'Enter Guest Mode';
      guestBtn.onclick = enterGuestMode;

      const loginBtn = document.getElementById('login-btn');
      loginBtn.parentNode.insertBefore(debugBtn, loginBtn.nextSibling);
      loginBtn.parentNode.insertBefore(resetBtn, debugBtn.nextSibling);
      loginBtn.parentNode.insertBefore(guestBtn, resetBtn.nextSibling);
    }
  }

  // Logout functionality
  document.getElementById('logout-btn').addEventListener('click', async () => {
    try {
      await authFetch('/auth/logout', { method: 'POST' });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuthState();
      clearAllIntervals();
      updateUI();
    }
  });

  // Utility functions
  function pct01(x) {
    return Math.round(x * 100 * 100) / 100;
  }

  function fmt(n) {
    if (n == null || isNaN(n)) return '—';
    return Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 });
  }

  function formatTime(timestamp) {
    if (!timestamp) return '—';
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
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

  // Element references
  const qChip = document.getElementById('quantum-chip');
  const qBackend = document.getElementById('quantum-backend');
  const qEnabled = document.getElementById('quantum-enabled');
  const mlChip = document.getElementById('ml-chip');
  const mlEnabled = document.getElementById('ml-enabled');
  const mlLoaded = document.getElementById('ml-loaded');
  const mlPath = document.getElementById('ml-path');
  const sentChip = document.getElementById('sent-chip');
  const sentEnabled = document.getElementById('sent-enabled');
  const sentSource = document.getElementById('sent-source');
  const sentWindow = document.getElementById('sent-window');
  const logsContainer = document.getElementById('logs');
  const signalsTable = document.getElementById('signals-table');
  const sentimentTable = document.getElementById('sentiment-table');
  const positionsContainer = document.getElementById('positions-container');
  const equityCanvas = document.getElementById('equity-canvas');
  const ctx = equityCanvas?.getContext('2d');
  const tradesPanel = document.getElementById('trades-panel');
  const tradesTable = document.getElementById('trades-table');

  // Debug panel functionality
  const debugToggle = document.getElementById('debug-toggle');
  const debugPanel = document.getElementById('debug-panel');
  const responseModal = document.getElementById('response-modal');
  const responseTitle = document.getElementById('response-title');
  const responseData = document.getElementById('response-data');
  const closeModal = document.getElementById('close-modal');

  if (debugToggle) {
    debugToggle.addEventListener('click', () => {
      if (debugPanel) debugPanel.classList.toggle('open');
    });
  }

  if (closeModal) {
    closeModal.addEventListener('click', () => {
      if (responseModal) responseModal.style.display = 'none';
    });
  }

  // Canvas functions
  function resizeCanvas() {
    if (!equityCanvas || !ctx) return;
    const rect = equityCanvas.getBoundingClientRect();
    equityCanvas.width = rect.width;
    equityCanvas.height = rect.height;
    drawChart();
  }

  function drawChart() {
    if (!equityCanvas || !ctx || !equityData.length) return;
    
    ctx.clearRect(0, 0, equityCanvas.width, equityCanvas.height);
    
    const values = equityData.map(d => d.v);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;
    
    ctx.strokeStyle = '#5aa0ff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    equityData.forEach((point, i) => {
      const x = (i / (equityData.length - 1)) * equityCanvas.width;
      const y = equityCanvas.height - ((point.v - minVal) / range) * equityCanvas.height;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
  }

  function updateChartStats() {
    const statsEl = document.getElementById('chart-stats');
    if (!statsEl || !equityData.length) return;
    
    const first = equityData[0].v;
    const last = equityData[equityData.length - 1].v;
    const change = ((last - first) / first) * 100;
    const changeClass = change >= 0 ? 'positive' : 'negative';
    
    statsEl.innerHTML = `
      <span>Period: ${equityData.length} points</span>
      <span class="${changeClass}">Change: ${change.toFixed(2)}%</span>
    `;
  }

  function updatePerformanceSummary() {
    if (!tradesData.length) return;
    
    const totalTrades = tradesData.length;
    const profitableTrades = tradesData.filter(t => t.pnl > 0).length;
    const winRate = (profitableTrades / totalTrades) * 100;
    
    document.getElementById('total-trades').textContent = totalTrades;
    document.getElementById('win-rate').textContent = winRate.toFixed(1) + '%';
  }

  // Authenticated API functions
  async function authFetch(url, options = {}) {
    const fullUrl = url.startsWith('http') ? url : `${API}${url}`;
    const headers = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    const response = await fetch(fullUrl, { ...options, headers });
    
    if (response.status === 401) {
      clearAuthState();
      updateUI();
      throw new Error('Authentication expired');
    }
    
    return response;
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

  // ML Status refresh functions
  async function refreshMLStatus() {
    try {
      const data = await fetchJSON('/ml/status');
      mlData = data;
      updateMLHealthIndicators(data);
      updateFeatureImportance(data);
      updateQuickMLStatus(data);
      updatePerformanceChart(data);
      updateActivityLog(data);
    } catch (error) {
      console.error('Failed to refresh ML status:', error);
    }
  }

  function updateMLHealthIndicators(data) {
    const healthEl = document.getElementById('ml-health-status');
    const scoreEl = document.getElementById('ml-overall-score');
    const accuracyEl = document.getElementById('ml-accuracy');
    const confidenceEl = document.getElementById('ml-confidence');
    const dataQualityEl = document.getElementById('ml-data-quality');
    const totalPredEl = document.getElementById('ml-total-predictions');
    const successPredEl = document.getElementById('ml-successful-predictions');

    if (healthEl) {
      const score = data.overall_score || 0;
      let healthClass = 'ml-insufficient';
      let healthText = 'Insufficient Data';
      
      if (score >= 0.8) { healthClass = 'ml-excellent'; healthText = 'Excellent'; }
      else if (score >= 0.6) { healthClass = 'ml-good'; healthText = 'Good'; }
      else if (score >= 0.4) { healthClass = 'ml-moderate'; healthText = 'Moderate'; }
      else if (score >= 0.2) { healthClass = 'ml-poor'; healthText = 'Poor'; }
      
      healthEl.className = `ml-health-indicator ${healthClass}`;
      healthEl.textContent = healthText;
    }

    if (scoreEl) scoreEl.textContent = ((data.overall_score || 0) * 100).toFixed(1) + '%';
    if (accuracyEl) accuracyEl.textContent = ((data.accuracy || 0) * 100).toFixed(1) + '%';
    if (confidenceEl) confidenceEl.textContent = ((data.confidence || 0) * 100).toFixed(1) + '%';
    if (dataQualityEl) dataQualityEl.textContent = ((data.data_quality || 0) * 100).toFixed(1) + '%';
    if (totalPredEl) totalPredEl.textContent = data.total_predictions || 0;
    if (successPredEl) successPredEl.textContent = data.successful_predictions || 0;
  }

  function updateFeatureImportance(data) {
    const container = document.getElementById('feature-importance');
    if (!container || !data.feature_importance) return;

    container.innerHTML = '';
    const features = Object.entries(data.feature_importance)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10);

    features.forEach(([name, importance], index) => {
      const featureDiv = document.createElement('div');
      featureDiv.className = 'feature-bar';
      featureDiv.innerHTML = `
        <span class="feature-name">${name}</span>
        <div class="feature-progress">
          <div class="feature-fill" style="width: ${importance * 100}%"></div>
        </div>
        <span class="feature-rank">#${index + 1}</span>
      `;
      container.appendChild(featureDiv);
    });
  }

  function updateQuantumAnalysis(data) {
    const container = document.getElementById('quantum-metrics');
    if (!container) return;

    container.innerHTML = `
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
        <span class="v">${data.success_rate ? (data.success_rate * 100).toFixed(1) + '%' : '—'}</span>
      </div>
    `;
  }

  function updateQuickMLStatus(data) {
    const accuracyEl = document.getElementById('ml-quick-accuracy');
    const confidenceEl = document.getElementById('ml-quick-confidence');
    const predictionsEl = document.getElementById('ml-quick-predictions');
    const healthChipEl = document.getElementById('ml-health-chip');

    if (accuracyEl) accuracyEl.textContent = ((data.accuracy || 0) * 100).toFixed(1) + '%';
    if (confidenceEl) confidenceEl.textContent = ((data.confidence || 0) * 100).toFixed(1) + '%';
    if (predictionsEl) predictionsEl.textContent = data.total_predictions || 0;
    
    if (healthChipEl) {
      const score = data.overall_score || 0;
      let healthClass = 'ml-insufficient';
      let healthText = 'Unknown';
      
      if (score >= 0.8) { healthClass = 'ml-excellent'; healthText = 'Excellent'; }
      else if (score >= 0.6) { healthClass = 'ml-good'; healthText = 'Good'; }
      else if (score >= 0.4) { healthClass = 'ml-moderate'; healthText = 'Moderate'; }
      else if (score >= 0.2) { healthClass = 'ml-poor'; healthText = 'Poor'; }
      
      healthChipEl.className = `ml-health-indicator ${healthClass}`;
      healthChipEl.textContent = healthText;
    }
  }

  function updatePerformanceChart(data) {
    if (!performanceChart || !data.performance_history) return;

    const history = data.performance_history;
    const labels = history.map(h => new Date(h.timestamp * 1000).toLocaleTimeString());
    const accuracyData = history.map(h => h.accuracy * 100);
    const confidenceData = history.map(h => h.confidence * 100);

    performanceChart.data.labels = labels;
    performanceChart.data.datasets[0].data = accuracyData;
    performanceChart.data.datasets[1].data = confidenceData;
    performanceChart.update();
  }

  function updateActivityLog(data) {
    const container = document.getElementById('ml-activity-log');
    if (!container || !data.recent_activity) return;

    container.innerHTML = '';
    data.recent_activity.slice(0, 10).forEach(activity => {
      const logDiv = document.createElement('div');
      logDiv.className = 'kv';
      logDiv.innerHTML = `
        <span class="k">${formatTime(activity.timestamp)}</span>
        <span class="v">${activity.message}</span>
      `;
      container.appendChild(logDiv);
    });
  }

  async function refreshQuantumDetails() {
    try {
      const data = await fetchJSON('/quantum/details');
      updateQuantumAnalysis(data);
      
      // Update quantum status chip
      const statusChip = document.getElementById('quantum-status-chip');
      if (statusChip) {
        setChip(statusChip, data.enabled ? 'ok' : 'warn');
        statusChip.textContent = data.enabled ? 'Online' : 'Offline';
      }
      
      // Update other quantum fields
      document.getElementById('quantum-backend-detail').textContent = data.backend || '—';
      document.getElementById('quantum-queue').textContent = data.queue_status || '—';
      document.getElementById('quantum-jobs').textContent = data.active_jobs || 0;
      document.getElementById('quantum-success-rate').textContent = 
        data.success_rate ? (data.success_rate * 100).toFixed(1) + '%' : '—';
    } catch (error) {
      console.error('Failed to refresh quantum details:', error);
    }
  }

  // Your existing refresh functions
  async function refreshHealth() {
    try {
      const data = await fetchJSON('/health');
      
      // Update quantum info
      if (qChip && qBackend && qEnabled) {
        const q = data.quantum || {};
        setChip(qChip, q.enabled);
        qBackend.textContent = q.backend || '—';
        qEnabled.textContent = q.enabled ? 'Yes' : 'No';
      }
      
      // Update ML info
      if (mlChip && mlEnabled && mlLoaded && mlPath) {
        const ml = data.ml || {};
        setChip(mlChip, ml.loaded);
        mlEnabled.textContent = ml.enabled ? 'Yes' : 'No';
        mlLoaded.textContent = ml.loaded ? 'Yes' : 'No';
        mlPath.textContent = ml.model_path || '—';
      }
      
      // Update sentiment info
      if (sentChip && sentEnabled && sentSource && sentWindow) {
        const sent = data.sentiment || {};
        setChip(sentChip, sent.enabled);
        sentEnabled.textContent = sent.enabled ? 'Yes' : 'No';
        sentSource.textContent = sent.source || '—';
        sentWindow.textContent = sent.window_hours ? sent.window_hours + 'h' : '—';
      }
    } catch (error) {
      console.error('Health refresh failed:', error);
    }
  }

  async function refreshSentiment() {
    try {
      const data = await fetchJSON('/sentiment');
      if (!sentimentTable) return;
      
      const tbody = sentimentTable.querySelector('tbody');
      tbody.innerHTML = '';
      
      Object.entries(data.scores || {}).forEach(([asset, info]) => {
        const row = document.createElement('tr');
        const score = info.score || 0;
        const scoreClass = score > 0.1 ? 'positive' : score < -0.1 ? 'negative' : '';
        
        row.innerHTML = `
          <td class="symbol">${asset}</td>
          <td class="${scoreClass}">${score.toFixed(3)}</td>
          <td>${info.count || 0}</td>
        `;
        tbody.appendChild(row);
      });
    } catch (error) {
      console.error('Sentiment refresh failed:', error);
    }
  }

  async function refreshSignals() {
    try {
      const data = await fetchJSON('/signals');
      if (!signalsTable) return;
      
      const tbody = signalsTable.querySelector('tbody');
      tbody.innerHTML = '';
      
      (data.signals || []).forEach(signal => {
        const row = document.createElement('tr');
        const signalClass = signal.signal?.toLowerCase() || 'hold';
        const weights = signal.weights || {};
        const weightStr = Object.entries(weights).map(([k, v]) => `${k}:${(v*100).toFixed(0)}%`).join(' ');
        
        row.innerHTML = `
          <td class="symbol">${signal.symbol}</td>
          <td><span class="${signalClass}-badge">${signal.signal}</span></td>
          <td>${signal.final_prob?.toFixed(3) || '—'}</td>
          <td>${signal.ema?.toFixed(3) || '—'}</td>
          <td>${signal.ml?.toFixed(3) || '—'}</td>
          <td>${signal.q?.toFixed(3) || '—'}</td>
          <td>${signal.sent?.toFixed(3) || '—'}</td>
          <td style="font-size: 10px;">${weightStr}</td>
          <td>${signal.thr_buy?.toFixed(2) || '—'}/${signal.thr_sell?.toFixed(2) || '—'}</td>
          <td>${signal.t ? Math.floor((Date.now()/1000 - signal.t)/60) + 'm' : '—'}</td>
        `;
        tbody.appendChild(row);
      });
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
      console.error('Status-based signals refresh failed:', error);
    }
  }

  async function refreshPositions() {
    try {
      const data = await fetchJSON('/status');
      if (!positionsContainer) return;
      
      const positions = data.positions || {};
      positionsContainer.innerHTML = '';
      
      if (Object.keys(positions).length === 0) {
        positionsContainer.innerHTML = '<p style="color: #8892b0;">No open positions</p>';
        return;
      }
      
      const table = document.createElement('table');
      table.className = 'data-table';
      table.innerHTML = `
        <thead>
          <tr><th>Symbol</th><th>Quantity</th><th>Avg Price</th><th>Current Price</th><th>P&L</th></tr>
        </thead>
        <tbody></tbody>
      `;
      
      const tbody = table.querySelector('tbody');
      Object.entries(positions).forEach(([symbol, pos]) => {
        const pnl = (pos.last_px - pos.avg_px) * pos.qty;
        const pnlClass = pnl >= 0 ? 'positive' : 'negative';
        
        const row = document.createElement('tr');
        row.innerHTML = `
          <td class="symbol">${symbol}</td>
          <td>${fmt(pos.qty)}</td>
          <td>${fmt(pos.avg_px)}</td>
          <td>${fmt(pos.last_px)}</td>
          <td class="${pnlClass}">${fmt(pnl)}</td>
        `;
        tbody.appendChild(row);
      });
      
      positionsContainer.appendChild(table);
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
        updateChartStats();
      }
    } catch (error) {
      console.error('Equity chart refresh failed:', error);
    }
  }

  async function refreshTrades() {
    try {
      const data = await fetchJSON('/trades');
      if (!tradesTable) return;
      
      tradesData = data.trades || [];
      const tbody = tradesTable.querySelector('tbody');
      tbody.innerHTML = '';
      
      tradesData.slice(0, 20).forEach(trade => {
        const row = document.createElement('tr');
        const sideClass = trade.side?.toLowerCase() === 'buy' ? 'positive' : 'negative';
        
        row.innerHTML = `
          <td>${formatTime(trade.timestamp)}</td>
          <td class="symbol">${trade.symbol}</td>
          <td class="${sideClass}">${trade.side}</td>
          <td>${fmt(trade.quantity)}</td>
          <td>${fmt(trade.price)}</td>
          <td>${fmt(trade.quantity * trade.price)}</td>
        `;
        tbody.appendChild(row);
      });
      
      updatePerformanceSummary();
    } catch (error) {
      console.error('Trades refresh failed:', error);
    }
  }

  async function refreshLogs() {
    try {
      const data = await fetchJSON('/logs/last');
      if (logsContainer && data.logs) {
        logsContainer.textContent = data.logs.slice(-100).join('\n');
        logsContainer.scrollTop = logsContainer.scrollHeight;
      }
    } catch (error) {
      console.error('Logs refresh failed:', error);
    }
  }

  async function refreshExec() {
    try {
      const data = await fetchJSON('/status');
      // Update execution status in debug panel
    } catch (error) {
      console.error('Exec refresh failed:', error);
    }
  }

  // Grid refresh function
  async function refreshGrid() {
    try {
      const data = await fetchJSON('/grid/matrix');
      updateGridDisplay(data);
    } catch (error) {
      console.error('Grid refresh failed:', error);
    }
  }

  function updateGridDisplay(data) {
    const thead = document.getElementById('maxi-grid-thead');
    const tbody = document.getElementById('maxi-grid-tbody');
    const timestampEl = document.getElementById('grid-last-ts');
    
    if (!thead || !tbody) return;
    
    const { rows, cols, matrix, ts } = data;
    
    // Update timestamp
    if (timestampEl) {
      timestampEl.textContent = new Date(ts * 1000).toLocaleTimeString();
    }
    
    // Build header
    thead.innerHTML = '';
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th>Asset</th>';
    cols.forEach(col => {
      headerRow.innerHTML += `<th>${col}</th>`;
    });
    thead.appendChild(headerRow);
    
    // Build rows
    tbody.innerHTML = '';
    rows.forEach(row => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${row}</td>`;
      
      cols.forEach(col => {
        const cellData = matrix[row]?.[col];
        const td = document.createElement('td');
        
        if (cellData) {
          const { signal, conf, final_prob, last, ema, ml, q, sent } = cellData;
          const cellClass = `grid-cell grid-cell-${signal.toLowerCase()}`;
          
          td.innerHTML = `
            <div class="${cellClass}">
              ${signal.charAt(0)}
              <div class="grid-tooltip">
                <div>Signal: ${signal}</div>
                <div>Confidence: ${(conf * 100).toFixed(1)}%</div>
                <div>Price: ${fmt(last)}</div>
                <div>EMA: ${ema?.toFixed(3) || '—'}</div>
                <div>ML: ${ml?.toFixed(3) || '—'}</div>
                <div>Quantum: ${q?.toFixed(3) || '—'}</div>
                <div>Sentiment: ${sent?.toFixed(3) || '—'}</div>
              </div>
            </div>
          `;
        } else {
          td.innerHTML = '<div class="grid-empty">—</div>';
        }
        
        tr.appendChild(td);
      });
      
      tbody.appendChild(tr);
    });
  }

  // Audit trail functions (superuser only)
  async function refreshAuditLogs() {
    if (currentUser?.role !== 'superuser') return;
    
    try {
      const data = await fetchJSON('/admin/audit');
      const container = document.getElementById('audit-logs');
      if (!container) return;
      
      container.innerHTML = '';
      (data.logs || []).slice(0, 10).forEach(log => {
        const logDiv = document.createElement('div');
        logDiv.className = 'audit-log';
        logDiv.innerHTML = `
          <div class="audit-header">
            <span>${log.action}</span>
            <span>${formatTime(log.timestamp)}</span>
          </div>
          <div class="audit-details">${log.details}</div>
        `;
        container.appendChild(logDiv);
      });
    } catch (error) {
      console.error('Audit logs refresh failed:', error);
    }
  }

  // Endpoint testing
  document.querySelectorAll('.endpoint-box').forEach(box => {
    box.addEventListener('click', async () => {
      const endpoint = box.dataset.endpoint;
      const statusEl = box.querySelector('.endpoint-status');
      
      box.classList.add('loading');
      statusEl.textContent = 'Testing...';
      
      try {
        const response = await authFetch(endpoint);
        const data = await response.json();
        
        box.classList.remove('loading');
        box.classList.add('success');
        statusEl.textContent = 'Success';
        
        // Show response in modal
        document.getElementById('response-title').textContent = `Response: ${endpoint}`;
        document.getElementById('response-data').textContent = JSON.stringify(data, null, 2);
        document.getElementById('response-modal').style.display = 'flex';
        
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
    });
  });

  function showNotImplementedModal(endpoint) {
    document.getElementById('response-title').textContent = `Endpoint: ${endpoint}`;
    document.getElementById('response-data').textContent = 'This endpoint is not yet implemented.';
    document.getElementById('response-modal').style.display = 'flex';
  }

  // Execution control buttons
  document.getElementById('btnExecEnable').addEventListener('click', async () => {
    try {
      await postJSON('/execution/enable');
      console.log('Execution enabled');
    } catch (error) {
      console.error('Failed to enable execution:', error);
    }
  });

  document.getElementById('btnExecDisable').addEventListener('click', async () => {
    try {
      await postJSON('/execution/disable');
      console.log('Execution disabled');
    } catch (error) {
      console.error('Failed to disable execution:', error);
    }
  });

  document.getElementById('btnExecToggle').addEventListener('click', async () => {
    try {
      await postJSON('/execution/toggle');
      console.log('Execution toggled');
    } catch (error) {
      console.error('Failed to toggle execution:', error);
    }
  });

  // Audit log refresh button
  document.getElementById('refresh-audit').addEventListener('click', refreshAuditLogs);

  // Interval management
  function clearAllIntervals() {
    Object.values(refreshIntervals).forEach(id => clearInterval(id));
    refreshIntervals = {};
  }

  function applyRefreshIntervals() {
    clearAllIntervals();
    
    const healthInterval = parseInt(document.getElementById('health-interval').value) || 5000;
    const signalsInterval = parseInt(document.getElementById('signals-interval').value) || 3000;
    const gridInterval = parseInt(document.getElementById('grid-interval').value) || 15000;
    
    refreshIntervals.health = setInterval(refreshHealth, healthInterval);
    refreshIntervals.sentiment = setInterval(refreshSentiment, signalsInterval);
    refreshIntervals.signals = setInterval(refreshSignals, signalsInterval);
    refreshIntervals.positions = setInterval(refreshPositions, signalsInterval);
    refreshIntervals.equity = setInterval(refreshEquityChart, signalsInterval);
    refreshIntervals.trades = setInterval(refreshTrades, signalsInterval * 2);
    refreshIntervals.logs = setInterval(refreshLogs, signalsInterval * 3);
    refreshIntervals.grid = setInterval(refreshGrid, gridInterval);
    
    console.log('Refresh intervals applied');
  }

  document.getElementById('apply-intervals').addEventListener('click', applyRefreshIntervals);

  document.getElementById('refresh-all').addEventListener('click', () => {
    refreshHealth();
    refreshSentiment();
    refreshSignals();
    refreshPositions();
    refreshEquityChart();
    refreshTrades();
    refreshLogs();
    refreshGrid();
    if (currentUser?.role === 'superuser') {
      refreshAuditLogs();
    }
  });

  // Initialize dashboard (called after login)
  function initializeDashboard() {
    initTabs();
    initPerformanceChart();
    
    // Initial data fetch
    refreshHealth();
    refreshSentiment();
    refreshSignals();
    refreshPositions();
    refreshEquityChart();
    refreshTrades();
    refreshLogs();
    refreshGrid();
    
    if (currentUser?.role === 'superuser') {
      refreshAuditLogs();
    }
    
    // Set up auto-refresh
    applyRefreshIntervals();
    
    // Resize canvas on window resize
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
  }

  // Auto-login check on page load
  if (loadAuthState()) {
    updateUI();
    initializeDashboard();
  } else {
    updateUI();
  }

  // UI helpers (moved inside closure)
  window.setHealth = function(ok, ts, quantum) {
    const statusEl = findElement("health-status");
    const timeEl = findElement("health-time");
    const quantumEl = findElement("health-quantum");
    
    statusEl.textContent = ok ? "OK" : "DOWN";
    statusEl.style.color = ok ? "#66e0a3" : "#ef6f6c";
    timeEl.textContent = ts ? new Date(ts * 1000).toLocaleTimeString() : "—";
    quantumEl.textContent = quantum || "—";
  };

  window.setEquity = function(eq) {
    const equityEl = findElement("equity");
    equityEl.textContent = typeof eq === "number" ? eq.toFixed(2) : "—";
  };

  // Expose API variable globally for other functions
  window.API = API;

  // Initialize UI enhancements
  setTimeout(() => {
    addCredentialTestButton();
  }, 100);

})();

/* UI helpers */
function setHealth(ok, ts, quantum) {
  $("#health-status").textContent = ok ? "OK" : "DOWN";
  $("#health-status").style.color = ok ? "#66e0a3" : "#ef6f6c";
  $("#health-time").textContent = ts ? new Date(ts * 1000).toLocaleTimeString() : "—";
  $("#health-quantum").textContent = quantum || "—";
}

function setEquity(eq) {
  $("#equity").textContent = typeof eq === "number" ? eq.toFixed(2) : "—";
  const ds = equityChart.data.datasets[0];
  const labels = equityChart.data.labels;
  const now = new Date().toLocaleTimeString();
  if (typeof eq === "number") {
    labels.push(now);
    ds.data.push(eq);
    if (labels.length > 120) { labels.shift(); ds.data.shift(); }
    equityChart.update();
  }
}

function setPositions(positions) {
  const tbody = $("#positionsTable tbody");
  tbody.innerHTML = "";
  if (!positions || !Object.keys(positions).length) {
    tbody.innerHTML = `<tr><td colspan="3" style="color:#9bb0bf">No positions</td></tr>`;
    return;
  }
  for (const [sym, p] of Object.entries(positions)) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${sym}</td><td>${(+p.qty).toFixed(6)}</td><td>${(+p.avg_px).toFixed(4)}</td>`;
    tbody.appendChild(tr);
  }
}

function setSignals(signals) {
  const tbody = $("#signalsTable tbody");
  tbody.innerHTML = "";
  if (!signals || !signals.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:#9bb0bf">No signals yet</td></tr>`;
    return;
  }
  const last = signals.slice(-50).reverse();
  for (const s of last) {
    const t = s.t ? new Date(s.t * 1000).toLocaleTimeString() : "–";
    const conf = (s.conf != null) ? (+s.conf).toFixed(3) : "–";
    const tr = document.createElement("tr");
    let color = "#9bb0bf";
    if (s.signal === "BUY") color = "#66e0a3";
    if (s.signal === "SELL") color = "#ef6f6c";
    tr.innerHTML = `<td>${t}</td><td>${s.symbol || "–"}</td><td style="color:${color};font-weight:700">${s.signal || "–"}</td><td>${conf}</td>`;
    tbody.appendChild(tr);
  }
}

async function fetchJSON(path) {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

// ============ MAXI GRID (improved) ============
let GRID_ROWS = [];
let GRID_COLS = [];
let GRID_DATA = {}; // matrix[base][quote] = {symbol, signal, conf, ema, ml, q, sent, final_prob, thr_buy, thr_sell, last, t}
let GRID_MIN_CONF = 0.0;
let GRID_ONLY_TRADABLE = false;

const elMinConf = document.getElementById('grid-min-conf');
const elMinConfVal = document.getElementById('grid-min-conf-val');
const elOnlyTradable = document.getElementById('grid-only-tradable');

function gridSigToClass(sig) {
  if (sig === 'BUY') return 'grid-buy';
  if (sig === 'SELL') return 'grid-sell';
  if (sig === 'HOLD') return 'grid-hold';
  return 'grid-na';
}
function pct01(x){ return (typeof x==='number' && !isNaN(x)) ? (x*100).toFixed(1)+'%' : '—'; }

function gridTooltip(d) {
  if (!d) return 'No data';
  return [
    `${d.symbol || '—'}`,
    `Signal: ${d.signal || '—'} • Confidence: ${pct01(d.conf)}`,
    `EMA: ${pct01(d.ema)} ML: ${pct01(d.ml)} Q: ${pct01(d.q)} Sent: ${pct01(d.sent)}`,
    `Final Prob: ${pct01(d.final_prob)} • Thr: ${pct01(d.thr_buy)} / ${pct01(d.thr_sell)}`,
    `Price: ${d.last != null ? d.last : '—'} • ${d.t ? new Date(d.t*1000).toLocaleTimeString() : '—'}`
  ].join('\n');
}

function symbolIsTradable(base, quote){
  if (!GRID_DATA[base] || !GRID_DATA[base][quote]) return false;
  const s = GRID_DATA[base][quote];
  return !!(s.symbol && s.last > 0);
}

function renderMaxiGrid() {
  const thead = document.getElementById('maxi-grid-thead');
  const tbody = document.getElementById('maxi-grid-tbody');

  // Header
  const hr = document.createElement('tr');
  const corner = document.createElement('th');
  corner.textContent = ''; corner.className = 'rowhdr';
  hr.appendChild(corner);

  GRID_COLS.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    th.style.minWidth = '90px';
    th.style.maxWidth = '140px';
    hr.appendChild(th);
  });
  thead.innerHTML = ''; thead.appendChild(hr);

  // Body
  const frag = document.createDocumentFragment();
  GRID_ROWS.forEach(base => {
    const tr = document.createElement('tr');
    const th = document.createElement('th');
    th.textContent = base; th.className = 'rowhdr';
    tr.appendChild(th);

    GRID_COLS.forEach(quote => {
      const td = document.createElement('td');
      td.className = 'grid-cell';

      const d = (GRID_DATA[base] && GRID_DATA[base][quote]) ? GRID_DATA[base][quote] : null;

      // client-side filters
      if (GRID_ONLY_TRADABLE && !symbolIsTradable(base, quote)) {
        td.textContent = '—'; td.classList.add('grid-na'); td.title = 'Not tradable'; tr.appendChild(td); return;
      }
      if (d && typeof d.conf === 'number' && d.conf < GRID_MIN_CONF) {
        td.textContent = '—'; td.classList.add('grid-na'); td.title = gridTooltip(d); tr.appendChild(td); return;
      }

      const sig = d ? d.signal : 'NA';
      td.textContent = sig || 'NA';
      td.classList.add(gridSigToClass(sig));
      td.title = gridTooltip(d);
      tr.appendChild(td);
    });

    frag.appendChild(tr);
  });
  tbody.innerHTML = ''; tbody.appendChild(frag);
}

async function refreshMaxiGrid() {
  try {
    // NOTE: we keep server param for the future, but filter is client-side now
    const r = await fetch(`${API}/grid/matrix?min_conf=${GRID_MIN_CONF.toFixed(2)}`);
    const g = await r.json();
    GRID_ROWS = g.rows || [];
    GRID_COLS = g.cols || [];
    GRID_DATA = g.matrix || {};
    document.getElementById('grid-last-ts').textContent =
      g.ts ? `Updated: ${new Date(g.ts*1000).toLocaleTimeString()}` : '';
    renderMaxiGrid();
  } catch (e) {
    console.error('grid fetch failed', e);
  }
}

// controls wiring
if (elMinConf && elMinConfVal) {
  elMinConf.addEventListener('input', () => {
    GRID_MIN_CONF = parseFloat(elMinConf.value) || 0;
    elMinConfVal.textContent = `${Math.round(GRID_MIN_CONF*100)}%`;
    renderMaxiGrid(); // instant local response
  });
}
if (elOnlyTradable) {
  elOnlyTradable.addEventListener('change', () => {
    GRID_ONLY_TRADABLE = !!elOnlyTradable.checked;
    renderMaxiGrid();
  });
}

/* Polling */
async function ping() {
  try {
    const health = await fetchJSON("/health");
    const q = health.quantum ? `${health.quantum.kind}:${health.quantum.backend}` : "—";
    setHealth(!!health.ok, health.time, q);
  } catch (e) {
    setHealth(false, null, null);
  }

  try {
    const status = await fetchJSON("/status");
    setEquity(status.equity);
    setPositions(status.positions);
    setSignals(status.last_signals || status.signals);
  } catch (e) {
    console.warn("status error:", e.message);
  }

  try {
    const logs = await fetchJSON("/logs/last");
    const text = (logs.logs || []).join("\n");
    $("#logsView").textContent = text || "—";
  } catch (e) {
    // ignore
  }
}

// Grid refresh with separate interval (every 15 seconds)
let gridInterval;
function startGridPolling() {
  if (gridInterval) clearInterval(gridInterval);
  gridInterval = setInterval(refreshMaxiGrid, 15000);
  // Initial load after a short delay
  setTimeout(refreshMaxiGrid, 1200);
}

setInterval(ping, 2000);
ping();
startGridPolling();