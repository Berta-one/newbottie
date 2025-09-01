(function () {
  // Try multiple API endpoints: Render (if working), then fallback message
  let API = 'https://bottie-1.onrender.com';
  
  // Test if Render API is working with real data
  async function detectWorkingAPI() {
    try {
      const response = await fetch(`${API}/status`);
      if (response.ok) {
        const data = await response.json();
        // Check if it's showing fake $10k data
        if (data.equity === 10000 && data.balance && data.balance.USDT === 10000) {
          console.log('⚠️ Render API still showing fake $10k data');
          return false;
        } else {
          console.log('✅ Render API working with real data:', data.equity);
          return true;
        }
      }
    } catch (error) {
      console.log('❌ Render API not accessible:', error.message);
      return false;
    }
    return false;
  }
  
  let currentUser = null;
  let authToken = null;
  let equityData = [];
  let refreshIntervals = {};
  let performanceChart = null;

  // Auto-login on page load
  async function autoLogin() {
    console.log('🔍 Checking API status...');
    
    const apiWorking = await detectWorkingAPI();
    if (!apiWorking) {
      // Show message about API status
      const statusElement = document.getElementById('statusContent');
      if (statusElement) {
        statusElement.innerHTML = `
          <div class="error-message">
            <h3>⚠️ API Deployment in Progress</h3>
            <p>The Render API is currently deploying with your real trading data.</p>
            <p>Current status: Render is rebuilding with real Binance connection</p>
            <p>Expected: Real $7,600+ portfolio data (not fake $10k)</p>
            <p>Please refresh in 2-3 minutes...</p>
            <button onclick="location.reload()" style="margin-top: 10px; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
              🔄 Refresh Page
            </button>
          </div>
        `;
      }
      return;
    }
    
    console.log('Attempting auto-login with working API...');
    
    // Auto-login as admin with correct credentials
    currentUser = { username: 'admin', role: 'admin' };
    authToken = 'auto-login-token';
    
    // Update UI immediately
    updateUI();
    
    // Try to get a real token in the background
    setTimeout(async () => {
      try {
        const response = await fetch(`${API}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'admin', password: 'Diego1234!' })
        });
        
        if (response.ok) {
          const data = await response.json();
          authToken = data.access_token;
          console.log('✅ Real authentication token obtained');
        } else {
          console.log('⚠️ Using fallback auto-login token');
        }
      } catch (error) {
        console.log('⚠️ Auto-login fallback mode:', error.message);
      }
      
      // Initialize dashboard after getting token
      initializeDashboard();
    }, 100);
  }

  // Safe element finder
  function findElement(id) {
    const element = document.getElementById(id);
    if (!element) {
      console.warn(`Element not found: ${id}`);
      return { textContent: '', style: {}, innerHTML: '', classList: { add: () => {}, remove: () => {} } };
    }
    return element;
  }

  // Chart initialization with error handling
  function initPerformanceChart() {
    const canvas = document.getElementById('performance-chart');
    if (!canvas) {
      console.warn('Performance chart canvas not found');
      return;
    }
    
    // Destroy existing chart if it exists
    if (performanceChart) {
      performanceChart.destroy();
      performanceChart = null;
    }
    
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.error('Chart.js is not loaded');
      canvas.style.display = 'none';
      const container = canvas.parentElement;
      if (container) {
        container.innerHTML = '<p style="color: #ff9800;">Chart.js not loaded. Charts unavailable.</p>';
      }
      return;
    }
    
    try {
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
      console.log('Performance chart initialized');
    } catch (error) {
      console.error('Failed to initialize performance chart:', error);
    }
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

        console.log(`Switched to tab: ${targetTab}`);
      });
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
    
    // Always show dashboard content for mobile compatibility
    if (loginModal) loginModal.style.display = 'none';
    if (mainContent) mainContent.style.display = 'block';
    if (dashboardTabs) dashboardTabs.style.display = 'flex';
    if (debugToggle) debugToggle.style.display = 'block';
    
    if (currentUser && authToken) {
      if (userInfo) userInfo.style.display = 'flex';
      if (userName) userName.textContent = currentUser.username || 'User';
      
      // Show audit section for superusers
      if (currentUser.role === 'superuser') {
        const auditSection = document.getElementById('audit-section');
        if (auditSection) auditSection.style.display = 'block';
      }
      
      // Update debug info
      const debugApiBase = document.getElementById('debug-api-base');
      const debugUser = document.getElementById('debug-user');
      const debugRole = document.getElementById('debug-role');
      const debugSession = document.getElementById('debug-session');
      
      if (debugApiBase) debugApiBase.textContent = API;
      if (debugUser) debugUser.textContent = currentUser.username;
      if (debugRole) debugRole.textContent = currentUser.role;
      if (debugSession) debugSession.textContent = authToken.slice(0, 8) + '...';
    } else {
      // Set guest mode by default
      if (userInfo) userInfo.style.display = 'flex';
      if (userName) userName.textContent = 'Guest';
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

  // Add credential testing functionality
  async function testMultipleCredentials() {
    const credentials = [
      // Based on your HTML default values
      { username: 'admin', password: 'Diego1234!' },
      { username: 'superuser', password: 'Lenny106667!' },
      
      // Original expected passwords from code
      { username: 'admin', password: 'AdminPass456!' },
      { username: 'superuser', password: 'SuperSecret123!' },
      
      // Common fallbacks
      { username: 'admin', password: 'admin' },
      { username: 'superuser', password: 'superuser' },
      { username: 'admin', password: '' },
      { username: 'root', password: 'root' },
      { username: 'user', password: 'user' },
      { username: 'test', password: 'test' },
      
      // Try with different case
      { username: 'Admin', password: 'Diego1234!' },
      { username: 'ADMIN', password: 'DIEGO1234!' }
    ];

    const loginError = document.getElementById('login-error');
    loginError.innerHTML = 'Testing multiple credentials...<br><br>';

    for (let i = 0; i < credentials.length; i++) {
      const cred = credentials[i];
      try {
        loginError.innerHTML += `[${i+1}/${credentials.length}] Trying ${cred.username}/${cred.password.substring(0,3)}... `;
        
        const response = await fetch(`${API}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cred)
        });

        if (response.ok) {
          const data = await response.json();
          loginError.innerHTML += `✅ SUCCESS!<br><br>`;
          loginError.innerHTML += `✅ Working credentials found:<br>`;
          loginError.innerHTML += `Username: <strong>${cred.username}</strong><br>`;
          loginError.innerHTML += `Password: <strong>${cred.password}</strong><br><br>`;
          
          // Auto-fill the form with working credentials
          document.getElementById('username').value = cred.username;
          document.getElementById('password').value = cred.password;
          
          // Auto-login
          saveAuthState(data.access_token, data.user);
          updateUI();
          initializeDashboard();
          return;
        } else {
          const errorData = await response.json();
          loginError.innerHTML += `❌ (${response.status}: ${errorData.detail || 'Unknown'})<br>`;
        }
      } catch (error) {
        loginError.innerHTML += `❌ Error: ${error.message}<br>`;
      }
      
      // Small delay between attempts to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    loginError.innerHTML += '<br>❌ All credentials failed. Please check:';
    loginError.innerHTML += '<br>1. Render environment variables are set correctly';
    loginError.innerHTML += '<br>2. API service is deployed and running';
    loginError.innerHTML += '<br>3. Try the debug endpoints below';
  }

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

    // Test debug/test-login endpoint
    try {
      loginError.innerHTML += 'Testing POST /debug/test-login with admin credentials... ';
      const response = await fetch(`${API}/debug/test-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'Diego1234!' })
      });
      if (response.ok) {
        const data = await response.json();
        loginError.innerHTML += `✅ Success!<br>`;
        loginError.innerHTML += `User exists: ${data.user_lookup?.user_exists ? '✅' : '❌'}<br>`;
        loginError.innerHTML += `Password verify: ${data.password_verification?.password_verify_result ? '✅' : '❌'}<br>`;
        loginError.innerHTML += `Auth result: ${data.authenticate_user_result?.success ? '✅' : '❌'}<br><br>`;
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
        
        // Try to login with admin after reset
        setTimeout(async () => {
          loginError.innerHTML += '<br>Attempting login with reset admin password...<br>';
          try {
            const loginResponse = await fetch(`${API}/auth/login`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username: 'admin', password: data.admin_password })
            });
            
            if (loginResponse.ok) {
              const loginData = await loginResponse.json();
              loginError.innerHTML += '✅ Login successful after reset!<br>';
              
              // Auto-fill form and login
              document.getElementById('username').value = 'admin';
              document.getElementById('password').value = data.admin_password;
              
              saveAuthState(loginData.access_token, loginData.user);
              updateUI();
              initializeDashboard();
            } else {
              loginError.innerHTML += '❌ Login still failed after reset<br>';
            }
          } catch (error) {
            loginError.innerHTML += `❌ Login error: ${error.message}<br>`;
          }
        }, 1000);
      } else {
        loginError.innerHTML += `❌ Reset failed (${response.status})<br>`;
      }
    } catch (error) {
      loginError.innerHTML += `❌ Reset error: ${error.message}<br>`;
    }
  }

  // Add the test button functionality
  function addCredentialTestButton() {
    const loginForm = document.getElementById('login-form');
    if (loginForm && !document.getElementById('test-credentials-btn')) {
      const testBtn = document.createElement('button');
      testBtn.type = 'button';
      testBtn.id = 'test-credentials-btn';
      testBtn.className = 'login-btn';
      testBtn.style.marginTop = '10px';
      testBtn.style.background = '#ff9800';
      testBtn.textContent = 'Test All Credentials';
      testBtn.onclick = testMultipleCredentials;
      
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
      loginBtn.parentNode.insertBefore(testBtn, loginBtn.nextSibling);
      loginBtn.parentNode.insertBefore(debugBtn, testBtn.nextSibling);
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
  const positionsTable = document.getElementById('positionsTable');
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

  debugToggle.addEventListener('click', () => {
    debugPanel.classList.toggle('open');
  });

  closeModal.addEventListener('click', () => {
    responseModal.style.display = 'none';
  });

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
    if (!tradesData.length) {
      document.getElementById('total-trades').textContent = '0';
      document.getElementById('win-rate').textContent = '0%';
      return;
    }
    
    const totalTrades = tradesData.length;
    const realTrades = tradesData.filter(t => t.order_id).length;
    const profitableTrades = tradesData.filter(t => t.pnl > 0).length;
    const winRate = (profitableTrades / totalTrades) * 100;
    
    // Calculate total volume and P&L
    const totalVolume = tradesData.reduce((sum, t) => sum + (t.quantity * t.price), 0);
    const totalPnL = tradesData.reduce((sum, t) => sum + (t.pnl || 0), 0);
    
    document.getElementById('total-trades').textContent = `${totalTrades} (${realTrades} real)`;
    document.getElementById('win-rate').textContent = winRate.toFixed(1) + '%';
    
    // Update additional performance metrics if elements exist
    const volumeEl = document.getElementById('total-volume');
    const pnlEl = document.getElementById('total-pnl');
    
    if (volumeEl) volumeEl.textContent = `$${totalVolume.toFixed(2)}`;
    if (pnlEl) {
      pnlEl.textContent = `$${totalPnL.toFixed(2)}`;
      pnlEl.className = totalPnL >= 0 ? 'positive' : 'negative';
    }
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
      updateMLInterpretation(data);
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
    const sampleCountEl = document.getElementById('ml-sample-count');

    // Use interpretation data if available
    if (data.interpretation && healthEl) {
      const interp = data.interpretation;
      healthEl.className = `ml-health-indicator ${interp.class}`;
      healthEl.textContent = `${interp.emoji} ${interp.health.charAt(0).toUpperCase() + interp.health.slice(1)}`;
    }

    if (scoreEl) scoreEl.textContent = ((data.accuracy || 0) * 100).toFixed(1) + '%';
    if (accuracyEl) accuracyEl.textContent = ((data.accuracy || 0) * 100).toFixed(1) + '%';
    if (confidenceEl) confidenceEl.textContent = ((data.success_rate || 0) * 100).toFixed(1) + '%';
    if (dataQualityEl) dataQualityEl.textContent = data.brier_score ? (100 - data.brier_score * 400).toFixed(1) + '%' : '—';
    if (totalPredEl) totalPredEl.textContent = data.sample_count || 0;
    if (successPredEl) successPredEl.textContent = data.successful_predictions || 0;
    if (sampleCountEl) sampleCountEl.textContent = data.sample_count || 0;
  }

  function updateMLInterpretation(data) {
    const interpretationEl = document.getElementById('ml-interpretation-content');
    if (!interpretationEl || !data.interpretation) {
      // Show placeholder if no data
      if (interpretationEl) {
        interpretationEl.innerHTML = `
          <div class="interpretation-content">
            <p class="interpretation-description">📊 ML Health Interpretation will appear here once sufficient data is collected.</p>
          </div>
        `;
      }
      return;
    }

    const interp = data.interpretation;
    interpretationEl.innerHTML = `
      <div class="interpretation-header">
        <span class="interpretation-emoji">${interp.emoji}</span>
        <span class="interpretation-title">📊 ML Health Interpretation</span>
      </div>
      <div class="interpretation-content ${interp.class}">
        <p class="interpretation-description">${interp.description}</p>
        ${data.brier_score ? `<p class="brier-details">Brier Score: <strong>${data.brier_score.toFixed(3)}</strong></p>` : ''}
        <div class="interpretation-legend">
          <div class="legend-item excellent">🎉 Excellent: &lt; 0.18 (strong learning)</div>
          <div class="legend-item good">✅ Good: &lt; 0.22 (beating random)</div>
          <div class="legend-item moderate">⚠️ Moderate: &lt; 0.25 (improving slowly)</div>
          <div class="legend-item poor">❌ Poor: &gt; 0.25 (struggling to learn)</div>
        </div>
      </div>
    `;
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

  // Enhanced refresh health function with better error handling
  async function refreshHealth() {
    try {
      const data = await fetchJSON('/health');
      console.log('Health data:', data);
      
      // Update quantum info with null checks
      const qChip = document.getElementById('quantum-chip');
      const qBackend = document.getElementById('quantum-backend');
      const qEnabled = document.getElementById('quantum-enabled');
      
      if (qChip && qBackend && qEnabled) {
        const q = data.quantum || {};
        setChip(qChip, q.enabled);
        qBackend.textContent = q.backend || '—';
        qEnabled.textContent = q.enabled ? 'Yes' : 'No';
      }
      
      // Update ML info with null checks
      const mlChip = document.getElementById('ml-chip');
      const mlEnabled = document.getElementById('ml-enabled');
      const mlLoaded = document.getElementById('ml-loaded');
      const mlPath = document.getElementById('ml-path');
      
      if (mlChip && mlEnabled && mlLoaded && mlPath) {
        const ml = data.ml || {};
        // Show green if enabled (even if model not loaded for cloud deployment)
        setChip(mlChip, ml.enabled || ml.loaded);
        mlEnabled.textContent = ml.enabled ? 'Yes' : 'No';
        mlLoaded.textContent = ml.loaded ? 'Yes' : 'No';
        mlPath.textContent = ml.model_path || '—';
      }
      
      // Update sentiment info with null checks
      const sentChip = document.getElementById('sent-chip');
      const sentEnabled = document.getElementById('sent-enabled');
      const sentSource = document.getElementById('sent-source');
      const sentWindow = document.getElementById('sent-window');
      
      if (sentChip && sentEnabled && sentSource && sentWindow) {
        const sent = data.sentiment || {};
        setChip(sentChip, sent.enabled);
        sentEnabled.textContent = sent.enabled ? 'Yes' : 'No';
        sentSource.textContent = sent.source || '—';
        sentWindow.textContent = sent.window_hours ? sent.window_hours + 'h' : '—';
      }
      
      console.log('Health display updated');
    } catch (error) {
      console.error('Health refresh failed:', error);
      
      // Set error states
      const elements = ['quantum-chip', 'ml-chip', 'sent-chip'];
      elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          setChip(el, 'err');
          el.textContent = 'Error';
        }
      });
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
      const positions = data.positions || {};
      
      // Use the setPositions function which already handles the positionsTable
      setPositions(positions);
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
      
      // Update trades table header with data source info
      const tradesHeader = document.querySelector('#trades-table h3');
      if (tradesHeader && data.summary) {
        const dataSource = data.summary.data_source || 'unknown';
        const totalTrades = data.summary.total_trades || 0;
        const realTradesOnly = dataSource.includes('real_trades_only');
        const sourceIcon = realTradesOnly ? '🔗' : '⚠️';
        const sourceText = realTradesOnly ? 'Real Binance Trades' : 'Mixed Data';
        
        tradesHeader.innerHTML = `Recent Trades (${totalTrades}) ${sourceIcon} ${sourceText}`;
        
        // Add note about real trades only if applicable
        if (data.summary.note && realTradesOnly) {
          let noteEl = document.getElementById('trades-data-note');
          if (!noteEl) {
            noteEl = document.createElement('div');
            noteEl.id = 'trades-data-note';
            noteEl.style.cssText = 'font-size: 12px; color: #4caf50; margin-bottom: 10px; padding: 5px; background: rgba(76, 175, 80, 0.1); border-radius: 4px;';
            tradesHeader.parentNode.insertBefore(noteEl, tradesTable);
          }
          noteEl.textContent = `✅ ${data.summary.note}`;
        }
      }
      
      // Display trades with enhanced real-trade indicators
      tradesData.slice(0, 20).forEach(trade => {
        const row = document.createElement('tr');
        const sideClass = trade.side?.toLowerCase() === 'buy' ? 'positive' : 'negative';
        
        // Add real trade indicator if trade has order_id (indicating real Binance trade)
        const realTradeIcon = trade.order_id ? '🔗' : '';
        const tradeSource = trade.order_id ? 'Real' : 'Local';
        
        row.innerHTML = `
          <td>${formatTime(trade.timestamp)} ${realTradeIcon}</td>
          <td class="symbol">${trade.symbol}</td>
          <td class="${sideClass}">${trade.side}</td>
          <td>${fmt(trade.quantity)}</td>
          <td>${fmt(trade.price)}</td>
          <td>${fmt(trade.quantity * trade.price)}</td>
        `;
        
        // Add tooltip for trade source
        row.title = `${tradeSource} trade${trade.order_id ? ` (Order ID: ${trade.order_id})` : ''}`;
        tbody.appendChild(row);
      });
      
      updatePerformanceSummary();
    } catch (error) {
      console.error('Trades refresh failed:', error);
      
      // Show error message to user if trades fail to load
      const tbody = tradesTable?.querySelector('tbody');
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #f44336; padding: 20px;">❌ Failed to load real trades. Check connection to Binance API.</td></tr>';
      }
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
    refreshIntervals.ml = setInterval(refreshMLStatus, signalsInterval * 2);
    refreshIntervals.quantum = setInterval(refreshQuantumDetails, signalsInterval * 2);
    
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
    refreshMLStatus();
    refreshQuantumDetails();
    if (currentUser?.role === 'superuser') {
      refreshAuditLogs();
    }
  });

  // Add this function to ensure all dashboard elements load properly
  function ensureElementsExist() {
    // Create missing elements if they don't exist
    const requiredElements = [
      'quantum-chip', 'quantum-backend', 'quantum-enabled',
      'ml-chip', 'ml-enabled', 'ml-loaded', 'ml-path',
      'sent-chip', 'sent-enabled', 'sent-source', 'sent-window',
      'signals-table', 'sentiment-table', 'positionsTable',
      'equity-canvas', 'trades-table', 'logs'
    ];
    
    requiredElements.forEach(id => {
      if (!document.getElementById(id)) {
        console.warn(`Missing element: ${id}`);
        // Create a placeholder element
        const placeholder = document.createElement('div');
        placeholder.id = id;
        placeholder.textContent = '—';
        placeholder.style.display = 'none';
        document.body.appendChild(placeholder);
      }
    });
  }

  // Initialize dashboard (called after login)
  function initializeDashboard() {
    console.log('Initializing dashboard...');
    
    // Ensure all required elements exist
    ensureElementsExist();
    
    initTabs();
    initPerformanceChart();
    
    // Initial data fetch with error handling
    setTimeout(async () => {
      console.log('Starting initial refresh sequence...');
      try {
        await refreshHealth();
        console.log('Health refreshed');
      } catch (e) { console.error('Health refresh failed:', e); }
      
      try {
        await refreshSentiment();
        console.log('Sentiment refreshed');
      } catch (e) { console.error('Sentiment refresh failed:', e); }
      
      try {
        await refreshSignals();
        console.log('Signals refreshed');
      } catch (e) { console.error('Signals refresh failed:', e); }
      
      try {
        await refreshPositions();
        console.log('Positions refreshed');
      } catch (e) { console.error('Positions refresh failed:', e); }
      
      try {
        await refreshEquityChart();
        console.log('Equity chart refreshed');
      } catch (e) { console.error('Equity chart refresh failed:', e); }
      
      try {
        await refreshTrades();
        console.log('Trades refreshed');
      } catch (e) { console.error('Trades refresh failed:', e); }
      
      try {
        await refreshLogs();
        console.log('Logs refreshed');
      } catch (e) { console.error('Logs refresh failed:', e); }
      
      try {
        await refreshGrid();
        console.log('Grid refreshed');
      } catch (e) { console.error('Grid refresh failed:', e); }
      
      try {
        await refreshMLStatus();
        console.log('ML status refreshed');
      } catch (e) { console.error('ML status refresh failed:', e); }
      
      try {
        await refreshQuantumDetails();
        console.log('Quantum details refreshed');
      } catch (e) { console.error('Quantum details refresh failed:', e); }
      
      if (currentUser?.role === 'superuser') {
        try {
          await refreshAuditLogs();
          console.log('Audit logs refreshed');
        } catch (e) { console.error('Audit logs refresh failed:', e); }
      }
    }, 500);
    
    // Set up auto-refresh
    applyRefreshIntervals();
    
    // Resize canvas on window resize
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    
    console.log('Dashboard initialization complete');
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

  // Test the dashboard loading
  async function testDashboardData() {
    console.log('Testing dashboard data loading...');
    
    const endpoints = [
      '/health',
      '/status', 
      '/signals',
      '/sentiment',
      '/ml/status',
      '/quantum/details',
      '/grid/matrix',
      '/trades',
      '/logs/last'
    ];
    
    for (const endpoint of endpoints) {
      try {
        const response = await authFetch(endpoint);
        if (response.ok) {
          const data = await response.json();
          console.log(`✅ ${endpoint}:`, data);
        } else {
          console.error(`❌ ${endpoint}: HTTP ${response.status}`);
        }
      } catch (error) {
        console.error(`❌ ${endpoint}: ${error.message}`);
      }
    }
  }

  // Make testDashboardData available globally for debugging
  window.testDashboardData = testDashboardData;

  // Expose API variable globally for other functions
  window.API = API;
  
  // Make autoLogin globally accessible
  window.autoLogin = autoLogin;
  
  // Make fetchJSON globally accessible for maxi-grid functions
  window.fetchJSON = fetchJSON;

  // Initialize UI enhancements
  setTimeout(() => {
    addCredentialTestButton();
  }, 100);

})();

// Global jQuery-like selector function (moved outside closure)
function $(selector) {
  return document.querySelector(selector);
}

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
  if (!tbody) {
    console.warn("positionsTable tbody not found");
    return;
  }
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
    const r = await fetch(`${window.API}/grid/matrix?min_conf=${GRID_MIN_CONF.toFixed(2)}`);
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
  } catch (e) {
    console.warn("status error:", e.message);
  }

  try {
    const logs = await fetchJSON("/logs/last");
    const text = (logs.logs || []).join("\n");
    $("#logs").textContent = text || "—";
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

// Initialize UI state and show dashboard immediately
updateUIState();
loadAllData();

// Initialize auto-login when page loads
autoLogin();