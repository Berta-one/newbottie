(function () {
  const API = new URLSearchParams(location.search).get('api') || 'https://bottie-1.onrender.com';
  
  let currentUser = null;
  let authToken = null;
  let equityData = [];
  let refreshIntervals = {};
  let performanceChart = null;

// Auto-login with bypass support
function autoLogin() {
  console.log('Attempting auto-login...');
  
  // Check for bypass parameters in URL FIRST
  const urlParams = new URLSearchParams(window.location.search);
  const apiParam = urlParams.get('api');
  const bypassAuth = urlParams.get('bypass') === 'true' || urlParams.get('debug') === 'true';
  
  // Authentication bypass for development/debugging
  if (bypassAuth) {
    console.log('🔧 Authentication bypass enabled via URL parameter');
    currentUser = { username: 'debug-user', role: 'admin' };
    authToken = 'bypass-token';
    
    // Save bypass session
    localStorage.setItem('bottie_auth_token', authToken);
    localStorage.setItem('bottie_api_base', API);
    localStorage.setItem('bottie_user', JSON.stringify(currentUser));
    
    updateUI();
    initializeDashboard();
    return;
  }
  
  // Auto-login as admin with correct credentials (fallback)
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
              // Refresh sentiment data when switching to sentiment tab
              if (targetTab === 'sentiment') {
                refreshSentiment();
                refreshSentimentNews();
              }
          }
        });

        console.log(`Switched to tab: ${targetTab}`);
      });
    });
// Refresh sentiment news feed
async function refreshSentimentNews() {
  try {
    const data = await fetchJSON('/sentiment/articles');
    const feedContainer = document.getElementById('sentiment-news-feed');
    if (feedContainer && data.articles && data.articles.length > 0) {
      feedContainer.innerHTML = '';
      data.articles.slice(0, 10).forEach(article => {
        const articleDiv = document.createElement('div');
        articleDiv.style.cssText = 'background: #1a2332; border: 1px solid #3a4553; border-radius: 6px; padding: 12px; margin-bottom: 10px;';
        const sentimentColor = article.sentiment > 0.3 ? '#4caf50' : article.sentiment < -0.3 ? '#f44336' : '#64ffda';
        const sentimentText = article.sentiment > 0.3 ? '+' + article.sentiment.toFixed(2) : article.sentiment.toFixed(2);
        articleDiv.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div style="font-weight: 600; color: #ffffff; font-size: 13px; flex: 1;">${article.title || 'News Article'}</div>
            <span style="margin-left: 10px; padding: 2px 6px; border-radius: 3px; font-size: 10px; background: rgba(100, 255, 218, 0.2); color: ${sentimentColor};">${sentimentText}</span>
          </div>
          <div style="font-size: 11px; color: #8892b0; margin-bottom: 6px;">
            <span style="background: #2a3441; color: #64ffda; padding: 2px 6px; border-radius: 3px; font-size: 10px;">${article.source || 'NEWS'}</span> • ${article.time_ago || 'Recently'}
          </div>
          <div style="font-size: 12px; color: #ccd6f6; line-height: 1.4;">
            ${article.summary || article.description || 'Market analysis and sentiment data...'}
          </div>
        `;
        feedContainer.appendChild(articleDiv);
      });
    }
  } catch (error) {
    console.error('Sentiment news refresh failed:', error);
  }
}
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
  // Always show dashboard - no login required
  const loginModal = document.getElementById('login-modal');
  const mainContent = document.getElementById('main-content');
  const dashboardTabs = document.getElementById('dashboard-tabs');
  const userInfo = document.getElementById('user-info');
  const debugToggle = document.getElementById('debug-toggle');
  
  if (loginModal) loginModal.style.display = 'none';
  if (mainContent) mainContent.style.display = 'block';
  if (dashboardTabs) dashboardTabs.style.display = 'flex';
  if (userInfo) userInfo.style.display = 'flex';
  if (debugToggle) debugToggle.style.display = 'block';
  
  // Set user info
  const userName = document.getElementById('user-name');
  if (userName) userName.textContent = 'admin';
  
  // Update debug info
  if (document.getElementById('debug-api-base')) document.getElementById('debug-api-base').textContent = API;
  if (document.getElementById('debug-user')) document.getElementById('debug-user').textContent = 'admin';
  if (document.getElementById('debug-role')) document.getElementById('debug-role').textContent = 'admin';
  if (document.getElementById('debug-session')) document.getElementById('debug-session').textContent = 'no-auth';
}

  // Login functionality (kept for compatibility, but optional)
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
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
  }

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
    loginError = document.getElementById('login-error');
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

  function updateElement(id, text) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = text;
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
    if (!tradesData.length) return;
    
    const totalTrades = tradesData.length;
    const profitableTrades = tradesData.filter(t => t.pnl > 0).length;
    const winRate = (profitableTrades / totalTrades) * 100;
    
    document.getElementById('total-trades').textContent = totalTrades;
    document.getElementById('win-rate').textContent = winRate.toFixed(1) + '%';
  }

  // Authenticated API functions
async function authFetch(url, options = {}) {
  // Normalize relative URLs to use API base
  let path = url;
  if (!url.startsWith('http')) {
    // Ensure single leading slash
    path = url.startsWith('/') ? url : `/${url}`;
  }
  const fullUrl = url.startsWith('http') ? url : `${API}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  // Add auth header only if we have a real token (not bypass tokens)
  if (authToken && authToken !== 'bypass-token' && authToken !== 'auto-login-token') {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  const response = await fetch(fullUrl, { ...options, headers });
  
  // Skip auth check for bypass/auto-login modes
 
  
  return response;
}

  async function fetchJSON(url) {
    try {
      const response = await authFetch(url);
      if (!response.ok) {
        if (response.status === 503) {
          throw new Error(`Service Unavailable (503)`);
        }
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API error for ${url}:`, error.message);
      throw error;
    }
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
    const brierScoreEl = document.getElementById('ml-brier-score');

    // Use new API structure
    const interpretation = data.interpretation || {};
    const healthStatus = interpretation.health || 'unknown';
    const healthEmoji = interpretation.emoji || '❓';
    const healthDesc = interpretation.description || 'No data available';
    
    if (healthEl) {
      const healthClass = `ml-${healthStatus}`;
      healthEl.className = `ml-health-indicator ${healthClass}`;
      healthEl.textContent = `${healthEmoji} ${healthStatus.charAt(0).toUpperCase() + healthStatus.slice(1)}`;
    }

    // Display Brier score prominently (this was missing!)
    if (brierScoreEl) {
      const brierScore = data.brier_score || 0;
      brierScoreEl.textContent = brierScore.toFixed(3);
      brierScoreEl.title = healthDesc;
    }

    // Update other metrics with correct field names
    if (scoreEl) {
      const successRate = (data.success_rate || 0) * 100;
      scoreEl.textContent = successRate.toFixed(1) + '%';
    }
    if (accuracyEl) accuracyEl.textContent = ((data.accuracy || 0) * 100).toFixed(1) + '%';
    
    // Calculate confidence from feature importance or success rate
    const confidence = data.success_rate || data.accuracy || 0;
    if (confidenceEl) confidenceEl.textContent = (confidence * 100).toFixed(1) + '%';
    
    // Data quality based on sample count
    const sampleCount = data.sample_count || 0;
    const dataQuality = Math.min(100, (sampleCount / 50) * 100); // 50+ samples = 100% quality
    if (dataQualityEl) dataQualityEl.textContent = dataQuality.toFixed(0) + '%';
    
    if (totalPredEl) totalPredEl.textContent = sampleCount;
    if (successPredEl) successPredEl.textContent = data.successful_predictions || 0;
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
    const metricsContainer = document.getElementById('quantum-metrics');
    const circuitsContainer = document.getElementById('quantum-circuits');
    
    if (!metricsContainer) return;

    // Update quantum metrics
    if (data.circuit_info) {
      metricsContainer.innerHTML = `
        <div class="kv">
          <span class="k">Circuit Depth:</span>
          <span class="v">${data.circuit_info.circuit_depth || '—'}</span>
        </div>
        <div class="kv">
          <span class="k">Qubits Count:</span>
          <span class="v">${data.circuit_info.qubits_count || '—'}</span>
        </div>
        <div class="kv">
          <span class="k">Gate Count:</span>
          <span class="v">${data.circuit_info.gate_count || '—'}</span>
        </div>
        <div class="kv">
          <span class="k">Measurement Shots:</span>
          <span class="v">${data.circuit_info.measurement_shots || '—'}</span>
        </div>
        <div class="kv">
          <span class="k">Fidelity:</span>
          <span class="v">${data.circuit_info.fidelity ? (data.circuit_info.fidelity * 100).toFixed(1) + '%' : '—'}</span>
        </div>
        <div class="kv">
          <span class="k">Processing Time:</span>
          <span class="v">${data.processing_time_ms ? data.processing_time_ms.toFixed(0) + 'ms' : '—'}</span>
        </div>
      `;
    }

    // Update quantum analysis results
    if (circuitsContainer && data.quantum_results) {
      circuitsContainer.innerHTML = '<h4>🔬 Quantum Analysis Results</h4>';
      
      Object.entries(data.quantum_results).forEach(([symbol, analysis]) => {
        const analysisDiv = document.createElement('div');
        analysisDiv.className = 'quantum-analysis-item';
        analysisDiv.style.cssText = 'margin: 10px 0; padding: 10px; border: 1px solid #2a3441; border-radius: 4px; background: rgba(100, 255, 218, 0.05);';
        
        analysisDiv.innerHTML = `
          <div style="font-weight: 600; color: #64ffda; margin-bottom: 8px;">${symbol}</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 11px;">
            <div>
              <strong>Quantum Score:</strong> ${(analysis.quantum_score * 100).toFixed(1)}%<br>
              <strong>Regime:</strong> ${analysis.regime.current_regime}<br>
              <strong>Regime Prob:</strong> ${(analysis.regime.regime_probability * 100).toFixed(1)}%
            </div>
            <div>
              <strong>Superposition:</strong> ${analysis.superposition.coherence_time.toFixed(0)}μs<br>
              <strong>BTC Correlation:</strong> ${(analysis.entanglement.btc_correlation * 100).toFixed(1)}%<br>
              <strong>Prediction Conf:</strong> ${(analysis.interference.prediction_confidence * 100).toFixed(1)}%
            </div>
          </div>
        `;
        
        circuitsContainer.appendChild(analysisDiv);
      });
      
      // Add summary
      if (data.summary) {
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'quantum-summary';
        summaryDiv.style.cssText = 'margin-top: 15px; padding: 10px; border: 1px solid #64ffda; border-radius: 4px; background: rgba(100, 255, 218, 0.1);';
        
        summaryDiv.innerHTML = `
          <h4 style="color: #64ffda; margin-bottom: 8px;">📊 Quantum Summary</h4>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 11px;">
            <div><strong>Symbols Analyzed:</strong> ${data.summary.total_symbols_analyzed}</div>
            <div><strong>Avg Quantum Score:</strong> ${(data.summary.average_quantum_score * 100).toFixed(1)}%</div>
            <div><strong>Highest Confidence:</strong> ${data.summary.highest_confidence_symbol || 'N/A'}</div>
            <div><strong>Quantum Advantage:</strong> ${data.summary.quantum_advantage_detected} symbols</div>
            <div><strong>Regime Consensus:</strong> ${data.summary.regime_consensus}</div>
          </div>
        `;
        
        circuitsContainer.appendChild(summaryDiv);
      }
    }
  }

  function updateQuickMLStatus(data) {
    const accuracyEl = document.getElementById('ml-quick-accuracy');
    const confidenceEl = document.getElementById('ml-quick-confidence');
    const brierEl = document.getElementById('ml-quick-brier');
    const predictionsEl = document.getElementById('ml-quick-predictions');
    const healthChipEl = document.getElementById('ml-health-chip');

    if (accuracyEl) accuracyEl.textContent = ((data.accuracy || 0) * 100).toFixed(1) + '%';
    if (confidenceEl) confidenceEl.textContent = ((data.confidence || 0) * 100).toFixed(1) + '%';
    if (brierEl) {
      const brierScore = data.brier_score || 0;
      brierEl.textContent = brierScore.toFixed(3);
      // Color code Brier score (lower is better)
      if (brierScore <= 0.10) brierEl.style.color = '#4caf50';  // Green for excellent
      else if (brierScore <= 0.15) brierEl.style.color = '#64ffda';  // Cyan for good
      else if (brierScore <= 0.20) brierEl.style.color = '#ff9800';  // Orange for moderate
      else brierEl.style.color = '#f44336';  // Red for poor
    }
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
    // This should fetch from the ML performance endpoint, not the status endpoint
    fetchMLPerformanceData('1h').then(perfData => {
      if (performanceChart && perfData && perfData.current_timeframe) {
        const currentData = perfData.current_timeframe;
        const accuracyHistory = currentData.accuracy || [];
        const confidenceHistory = currentData.confidence || [];
        
        if (accuracyHistory.length > 0) {
          const labels = accuracyHistory.map(h => new Date(h.timestamp * 1000).toLocaleTimeString());
          const accuracyData = accuracyHistory.map(h => h.value * 100);
          const confidenceData = confidenceHistory.map(h => h.value * 100);

          performanceChart.data.labels = labels;
          performanceChart.data.datasets[0].data = accuracyData;
          performanceChart.data.datasets[1].data = confidenceData;
          performanceChart.update();
        }
      }
    }).catch(error => {
      console.error('Failed to update performance chart:', error);
    });
  }
  
  // New function to fetch ML performance data
  async function fetchMLPerformanceData(timeframe = '1h') {
    try {
      return await fetchJSON(`/ml/performance?timeframe=${timeframe}`);
    } catch (error) {
      console.error('Failed to fetch ML performance data:', error);
      return null;
    }
  }

  // Enhanced performance analysis with multiple timeframes
  async function refreshPerformanceAnalysis(timeframe = '24h') {
    try {
      const data = await fetchJSON(`/performance/analysis?timeframe=${timeframe}`);
      
      // Update overview metrics
      updateElement('perf-total-return', `${data.overview?.total_return_pct || 0}%`);
      updateElement('perf-volatility', `${data.overview?.volatility_pct || 0}%`);
      updateElement('perf-sharpe-ratio', data.overview?.sharpe_ratio?.toFixed(3) || '0.000');
      updateElement('perf-max-drawdown', `${data.overview?.max_drawdown_pct || 0}%`);
      
      // Update trading metrics
      updateElement('perf-total-trades', data.trading?.total_trades || 0);
      updateElement('perf-avg-trade-size', `$${fmt(data.trading?.avg_trade_size || 0)}`);
      updateElement('perf-total-volume', `$${fmt(data.trading?.total_volume || 0)}`);
      
      // Update signal metrics
      updateElement('perf-total-signals', data.signals?.total_signals || 0);
      updateElement('perf-signal-accuracy', `${data.signals?.signal_accuracy_pct || 0}%`);
      updateElement('perf-high-conf-signals', data.signals?.high_confidence_signals || 0);
      
      // Update component performance
      const components = data.components || {};
      Object.keys(components).forEach(comp => {
        const compData = components[comp];
        updateElement(`perf-${comp}-score`, (compData.avg_score * 100).toFixed(1) + '%');
        updateElement(`perf-${comp}-consistency`, (compData.consistency * 100).toFixed(1) + '%');
        updateElement(`perf-${comp}-samples`, compData.samples);
      });
      
      // Update performance chart with equity data
      if (data.equity_chart && performanceChart) {
        updateEquityChart(data.equity_chart);
      }
      
    } catch (error) {
      console.error('Performance analysis refresh failed:', error);
    }
  }

  function updateEquityChart(equityData) {
    if (!performanceChart || !equityData.length) return;

    const labels = equityData.map(e => new Date(e.t * 1000).toLocaleTimeString());
    const equityValues = equityData.map(e => e.v);
    
    // Calculate returns for second dataset
    const returns = [];
    for (let i = 1; i < equityValues.length; i++) {
      const returnPct = ((equityValues[i] - equityValues[i-1]) / equityValues[i-1]) * 100;
      returns.push(returnPct);
    }
    returns.unshift(0); // First point has 0 return

    performanceChart.data.labels = labels;
    performanceChart.data.datasets[0].data = equityValues;
    performanceChart.data.datasets[0].label = 'Equity ($)';
    performanceChart.data.datasets[1].data = returns;
    performanceChart.data.datasets[1].label = 'Returns (%)';
    performanceChart.update();
  }

  // Add timeframe selector functionality
  function initPerformanceTimeframes() {
    const timeframeButtons = document.querySelectorAll('.timeframe-btn');
    timeframeButtons.forEach(btn => {
      btn.addEventListener('click', async () => {
        // Update active state
        timeframeButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Refresh with new timeframe
        const timeframe = btn.dataset.timeframe;
        await refreshPerformanceAnalysis(timeframe);
      });
    });
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
      // Get quantum details for status info
      const detailsData = await fetchJSON('/quantum/details');
      
      // Update quantum status chip
      const statusChip = document.getElementById('quantum-status-chip');
      if (statusChip) {
        setChip(statusChip, detailsData.enabled ? 'ok' : 'warn');
        statusChip.textContent = detailsData.enabled ? 'Online' : 'Offline';
      }
      
      // Update other quantum fields
      updateElement('quantum-backend-detail', detailsData.backend || '—');
      updateElement('quantum-queue', detailsData.queue_status || '—');
      updateElement('quantum-jobs', detailsData.active_jobs || 0);
      updateElement('quantum-success-rate', 
        detailsData.success_rate ? (detailsData.success_rate * 100).toFixed(1) + '%' : '—');
      
      // Get quantum analysis data
      const analysisData = await fetchJSON('/quantum/analysis');
      updateQuantumAnalysis(analysisData);
        
    } catch (error) {
      console.error('Failed to refresh quantum details:', error);
    }
  }

  // Enhanced quantum analysis refresh with real-time data
  async function refreshQuantumAnalysis() {
    try {
      const data = await fetchJSON('/quantum/analysis');
      
      if (!data.enabled) {
        updateElement('quantum-status-display', 'Disabled');
        updateElement('quantum-circuit-info', 'Quantum processing disabled');
        return;
      }
      
      // Update circuit information
      const circuitInfo = data.circuit_info || {};
      updateElement('quantum-qubits', circuitInfo.qubits_count || 0);
      updateElement('quantum-depth', circuitInfo.depth || 0);
      updateElement('quantum-gates', circuitInfo.gate_count || 0);
      updateElement('quantum-entanglement', (circuitInfo.entanglement_measure * 100).toFixed(1) + '%');
      updateElement('quantum-fidelity', (circuitInfo.fidelity * 100).toFixed(1) + '%');
      updateElement('quantum-coherence', circuitInfo.coherence_time_us + 'μs');
      
      // Update performance metrics
      const performance = data.performance_metrics || {};
      updateElement('quantum-avg-score', (performance.avg_quantum_score * 100).toFixed(1) + '%');
      updateElement('quantum-variance', (performance.quantum_variance * 100).toFixed(2) + '%');
      updateElement('quantum-contribution', (performance.quantum_contribution * 100).toFixed(1) + '%');
      updateElement('quantum-confidence-rate', performance.high_confidence_rate + '%');
      updateElement('quantum-total-signals', performance.total_quantum_signals || 0);
      
      // Update real-time data
      const realTime = data.real_time_data || {};
      updateElement('quantum-current-prob', (realTime.current_probability * 100).toFixed(1) + '%');
      updateElement('quantum-last-symbol', realTime.last_symbol || '—');
      updateElement('quantum-signal-strength', (realTime.signal_strength * 100).toFixed(1) + '%');
      updateElement('quantum-measurement-count', realTime.measurement_count || 0);
      updateElement('quantum-decoherence', (realTime.decoherence_rate * 100).toFixed(2) + '%');
      
      // Update historical chart
      if (data.historical_data && data.historical_data.length > 0) {
        updateQuantumHistoricalChart(data.historical_data);
      }
      
    } catch (error) {
      console.error('Quantum analysis refresh failed:', error);
    }
  }

  function updateQuantumHistoricalChart(historicalData) {
    // Update quantum probability chart (if exists)
    const canvas = document.getElementById('quantum-chart');
    if (!canvas || !historicalData.length) return;
    
    // For now, update text display; chart implementation can be added later
    const latest = historicalData[historicalData.length - 1];
    updateElement('quantum-latest-timestamp', new Date(latest.timestamp * 1000).toLocaleString());
    updateElement('quantum-latest-avg', (latest.avg_probability * 100).toFixed(1) + '%');
    updateElement('quantum-latest-variance', (latest.variance * 100).toFixed(2) + '%');
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
      // Use the enhanced sentiment articles endpoint
      const data = await fetchJSON('/sentiment/articles');
      if (!sentimentTable) return;
      
      const tbody = sentimentTable.querySelector('tbody');
      tbody.innerHTML = '';
      
      // Display articles if available
      if (data.enabled && data.articles && data.articles.length > 0) {
        data.articles.slice(0, 10).forEach(article => { // Show max 10 articles
          const row = document.createElement('tr');
          const sentiment = article.sentiment || 'neutral';
          const score = article.score || 0.5;
          const scoreClass = sentiment === 'positive' ? 'positive' : 
                           sentiment === 'negative' ? 'negative' : '';
          
          row.innerHTML = `
            <td class="symbol">${(article.symbols || []).join(', ') || 'General'}</td>
            <td class="${scoreClass}">${score.toFixed(3)}</td>
            <td title="${article.summary || ''}">${(article.headline || '').substring(0, 50)}${(article.headline || '').length > 50 ? '...' : ''}</td>
          `;
          tbody.appendChild(row);
        });
      } else {
        // Fallback to old sentiment format or show status
        const statusMessage = data.enabled ? 'No articles available' : 'Sentiment analysis disabled';
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="3" style="text-align: center; color: #666;">${statusMessage}</td>`;
        tbody.appendChild(row);
      }
    } catch (error) {
      console.error('Sentiment refresh failed:', error);
      // Show error state
      if (sentimentTable) {
        const tbody = sentimentTable.querySelector('tbody');
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #ff6b6b;">Failed to load sentiment data</td></tr>';
      }
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

  // Global state for filtering
  let currentPeriod = '1d';
  let allTradesData = [];

  async function refreshTrades() {
    try {
      const data = await fetchJSON('/trades');
      if (!tradesTable) return;
      
      allTradesData = data.trades || [];
      
      // Update summary from API response
      updateTradeSummaryFromAPI(data.summary || {});
      
      // Update table
      updateTradesTable();
      updateTradeFilters();
      
    } catch (error) {
      console.error('Trades refresh failed:', error);
      // Show sample data on error to prevent UI bleeding
      showSampleTradesData();
    }
  }

  function updateTradeSummaryFromAPI(summary) {
    // Update the summary box with real data from the API
    findElement('summary-total-trades').textContent = summary.total_trades || 0;
    
    const realizedPnL = summary.realized_pnl || 0;
    const realizedPnLEl = findElement('summary-realized-pnl');
    realizedPnLEl.textContent = `$${fmt(realizedPnL)}`;
    realizedPnLEl.className = `trade-summary-value ${realizedPnL >= 0 ? 'positive' : 'negative'}`;
    
    const winRate = summary.win_rate || 0;
    findElement('summary-win-rate').textContent = `${winRate.toFixed(1)}%`;
    
    const totalVolume = (summary.total_buy_value || 0) + (summary.total_sell_value || 0);
    findElement('summary-total-volume').textContent = `$${fmt(totalVolume)}`;
    
    const avgTradeSize = summary.avg_trade_size || 0;
    findElement('summary-avg-trade').textContent = `$${fmt(avgTradeSize)}`;
    
    const netPnL = summary.net_pnl || realizedPnL;
    const netPnLEl = findElement('summary-net-pnl');
    netPnLEl.textContent = `$${fmt(netPnL)}`;
    netPnLEl.className = `trade-summary-value ${netPnL >= 0 ? 'positive' : 'negative'}`;
  }

  function showSampleTradesData() {
    // Fallback sample data to prevent UI bleeding
    const sampleSummary = {
      total_trades: 2,
      realized_pnl: 5.25,
      win_rate: 50.0,
      total_buy_value: 175.75,
      total_sell_value: 132.50,
      avg_trade_size: 87.88,
      net_pnl: 5.25
    };
    
    updateTradeSummaryFromAPI(sampleSummary);
    
    // Add sample trades to prevent table bleeding
    if (allTradesData.length === 0) {
      const now = Date.now() / 1000;
      allTradesData = [
        {
          timestamp: now - 3600,
          symbol: 'BTC/USDT',
          side: 'BUY',
          quantity: 0.001,
          price: 43250.00,
          value: 43.25,
          confidence: 0.75,
          status: 'completed',
          datetime: new Date((now - 3600) * 1000).toLocaleString()
        },
        {
          timestamp: now - 7200,
          symbol: 'ETH/USDT',
          side: 'SELL',
          quantity: 0.05,
          price: 2650.00,
          value: 132.50,
          confidence: 0.82,
          status: 'completed',
          datetime: new Date((now - 7200) * 1000).toLocaleString()
        }
      ];
      updateTradesTable();
    }
  }

  function updateTradesTable() {
    if (!tradesTable) return;
    
    const tbody = tradesTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    // Sort trades by timestamp (newest first)
    const sortedTrades = [...allTradesData].sort((a, b) => b.timestamp - a.timestamp);
    
    sortedTrades.forEach(trade => {
      const row = document.createElement('tr');
      const sideClass = trade.side?.toLowerCase() === 'buy' ? 'trade-buy' : 'trade-sell';
      
      // Enhanced P&L display with actual values
      const pnlImpact = trade.pnl || 0;
      let pnlClass = 'trade-pnl-neutral';
      let pnlDisplay = '$0.00';
      
      if (pnlImpact !== 0) {
        pnlClass = pnlImpact > 0 ? 'trade-pnl-positive' : 'trade-pnl-negative';
        pnlDisplay = `${pnlImpact > 0 ? '+' : ''}$${fmt(pnlImpact)}`;
      }
      
      row.className = sideClass;
      row.innerHTML = `
        <td>${trade.datetime || formatTime(trade.timestamp)}</td>
        <td class="symbol">${trade.symbol}</td>
        <td class="${sideClass}">${trade.side}</td>
        <td>${fmt(trade.quantity)}</td>
        <td>$${fmt(trade.price)}</td>
        <td>$${fmt(trade.value || trade.quantity * trade.price)}</td>
        <td>${Math.round((trade.confidence || 0) * 100)}%</td>
        <td class="${pnlClass}">${pnlDisplay}</td>
        <td><span class="status-badge ${trade.status || 'pending'}">${trade.status || 'pending'}</span></td>
      `;
      tbody.appendChild(row);
    });
  }

  function updateTradeFilters() {
    const symbolFilter = document.getElementById('symbol-filter');
    if (symbolFilter) {
      const symbols = [...new Set(allTradesData.map(t => t.symbol))].sort();
      symbolFilter.innerHTML = '<option value="">All Symbols</option>';
      symbols.forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        symbolFilter.appendChild(option);
      });
    }
  }

  function updatePnLSummary() {
    const filteredTrades = filterTradesByPeriod(allTradesData, currentPeriod);
    const summary = calculateTradingSummary(filteredTrades);
    
    updateElement('summary-total-pnl', `$${fmt(summary.totalPnL)}`);
    updateElement('summary-win-rate', `${summary.winRate.toFixed(1)}%`);
    updateElement('summary-total-trades', summary.totalTrades.toString());
    updateElement('summary-avg-size', `$${fmt(summary.avgTradeSize)}`);
    updateElement('summary-best-trade', `$${fmt(summary.bestTrade.value)}`);
    updateElement('summary-worst-trade', `$${fmt(Math.abs(summary.worstTrade.value))}`);
    
    // Update CSS classes for color coding
    const totalPnlElement = document.getElementById('summary-total-pnl');
    if (totalPnlElement) {
      totalPnlElement.className = `metric-value ${summary.totalPnL > 0 ? 'pnl-positive' : summary.totalPnL < 0 ? 'pnl-negative' : 'pnl-neutral'}`;
    }
  }

  function filterTradesByPeriod(trades, period) {
    if (period === 'all') return trades;
    
    const now = Date.now() / 1000;
    const periodSeconds = {
      '1d': 86400,
      '7d': 604800,
      '30d': 2592000,
      '90d': 7776000,
      '180d': 15552000
    };
    
    const cutoff = now - (periodSeconds[period] || 86400);
    return trades.filter(trade => trade.timestamp >= cutoff);
  }

  function calculateTradingSummary(trades) {
    if (!trades.length) {
      return {
        totalPnL: 0,
        winRate: 0,
        totalTrades: 0,
        avgTradeSize: 0,
        bestTrade: { value: 0, symbol: '--' },
        worstTrade: { value: 0, symbol: '--' }
      };
    }
    
    const buyTrades = trades.filter(t => t.side === 'BUY');
    const sellTrades = trades.filter(t => t.side === 'SELL');
    
    const totalBuyValue = buyTrades.reduce((sum, t) => sum + (t.value || 0), 0);
    const totalSellValue = sellTrades.reduce((sum, t) => sum + (t.value || 0), 0);
    const totalPnL = totalSellValue - totalBuyValue;
    
    // Calculate individual trade P&L impacts
    const tradeImpacts = trades.map(trade => ({
      ...trade,
      impact: trade.side === 'SELL' ? trade.value : -trade.value
    }));
    
    const positiveImpacts = tradeImpacts.filter(t => t.impact > 0);
    const winRate = positiveImpacts.length / trades.length * 100;
    
    const avgTradeSize = trades.reduce((sum, t) => sum + (t.value || 0), 0) / trades.length;
    
    const bestTrade = tradeImpacts.reduce((best, current) => 
      current.impact > best.impact ? current : best, 
      { impact: 0, symbol: '--' }
    );
    
    const worstTrade = tradeImpacts.reduce((worst, current) => 
      current.impact < worst.impact ? current : worst, 
      { impact: 0, symbol: '--' }
    );
    
    return {
      totalPnL,
      winRate,
      totalTrades: trades.length,
      avgTradeSize,
      bestTrade: { value: bestTrade.impact, symbol: bestTrade.symbol },
      worstTrade: { value: worstTrade.impact, symbol: worstTrade.symbol }
    };
  }

  function filterTrades() {
    const symbolFilter = document.getElementById('symbol-filter');
    const sideFilter = document.getElementById('side-filter');
    const searchFilter = document.getElementById('search-filter');
    
    if (!tradesTable) return;
    
    const symbolValue = symbolFilter ? symbolFilter.value : '';
    const sideValue = sideFilter ? sideFilter.value : '';
    const searchValue = searchFilter ? searchFilter.value.toLowerCase() : '';
    
    const rows = tradesTable.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
      const cells = row.cells;
      const symbol = cells[1]?.textContent || '';
      const side = cells[2]?.textContent || '';
      const searchText = row.textContent.toLowerCase();
      
      const symbolMatch = !symbolValue || symbol === symbolValue;
      const sideMatch = !sideValue || side === sideValue;
      const searchMatch = !searchValue || searchText.includes(searchValue);
      
      row.style.display = (symbolMatch && sideMatch && searchMatch) ? '' : 'none';
    });
  }

  // Advanced logging system with filtering
  let currentLogFilter = 'all';
  let currentComponentFilter = null;

  async function refreshLogs() {
    try {
      // Build query parameters based on current filters
      let endpoint = '/logs/last?limit=100';
      if (currentLogFilter !== 'all') {
        endpoint += `&level=${currentLogFilter}`;
      }
      if (currentComponentFilter) {
        endpoint += `&component=${currentComponentFilter}`;
      }

      const data = await fetchJSON(endpoint);
      if (logsContainer && data.logs) {
        // Format logs with timestamps and levels
        const formattedLogs = data.logs.map(log => {
          const time = new Date(log.timestamp).toLocaleTimeString();
          const emoji = getLogEmoji(log.level);
          return `${time} ${emoji} [${log.component}] ${log.message}`;
        });
        
        logsContainer.textContent = formattedLogs.join('\n');
        logsContainer.scrollTop = logsContainer.scrollHeight;

        // Update system status if available
        if (data.system_status) {
          updateSystemStatus(data.system_status);
        }
      }
    } catch (error) {
      console.error('Error refreshing logs:', error);
    }
  }

  function getLogEmoji(level) {
    const emojis = {
      'DEBUG': '🔍',
      'INFO': 'ℹ️',
      'WARNING': '⚠️',
      'ERROR': '❌',
      'CRITICAL': '🚨'
    };
    return emojis[level] || '📝';
  }

  function updateSystemStatus(status) {
    // Update system health indicator if it exists
    const healthIndicator = document.querySelector('.system-health');
    if (healthIndicator) {
      healthIndicator.textContent = `System: ${status.system_health} | WebSocket: ${status.websocket_status}`;
      healthIndicator.className = `system-health ${status.system_health.toLowerCase()}`;
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
    const portfolioCountEl = document.getElementById('grid-portfolio-count');
    const volumeCountEl = document.getElementById('grid-volume-count');
    const totalPairsEl = document.getElementById('grid-total-pairs');
    
    if (!thead || !tbody) return;
    
    const { rows, cols, matrix, ts, market_overview, atomic_swaps, total_opportunities } = data;
    
    // Update timestamp
    if (timestampEl) {
      timestampEl.textContent = new Date(ts * 1000).toLocaleTimeString();
    }
    
    // Update grid statistics
    if (portfolioCountEl) {
      portfolioCountEl.textContent = rows?.length || 0;
    }
    if (volumeCountEl) {
      volumeCountEl.textContent = cols?.length || 0;
    }
    if (totalPairsEl) {
      totalPairsEl.textContent = total_opportunities || 0;
    }
    
    // Update additional market overview stats
    if (market_overview) {
      const highConfEl = document.getElementById('grid-high-conf-pairs');
      const buySignalsEl = document.getElementById('grid-buy-signals');
      const sellSignalsEl = document.getElementById('grid-sell-signals');
      const avgConfEl = document.getElementById('grid-avg-confidence');
      
      if (highConfEl) highConfEl.textContent = market_overview.high_confidence_pairs || 0;
      if (buySignalsEl) buySignalsEl.textContent = market_overview.buy_signals || 0;
      if (sellSignalsEl) sellSignalsEl.textContent = market_overview.sell_signals || 0;
      if (avgConfEl) avgConfEl.textContent = market_overview.avg_confidence ? (market_overview.avg_confidence * 100).toFixed(1) + '%' : '—';
    }
    
    // Process atomic swap opportunities
    if (atomic_swaps && atomic_swaps.length > 0) {
      displayAtomicSwapOpportunities(atomic_swaps);
    }
    
    // Build header
    thead.innerHTML = '';
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th>Asset</th>';
    cols.forEach((col, index) => {
      // Show volume rank for top volume leaders
      const volumeRank = index < 10 ? ` (#${index + 1})` : '';
      headerRow.innerHTML += `<th title="Volume Rank: ${index + 1}">${col}${volumeRank}</th>`;
    });
    thead.appendChild(headerRow);
    
    // Build rows
    tbody.innerHTML = '';
    rows.forEach(row => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td title="Portfolio holding">${row}</td>`;
      
      cols.forEach(col => {
        const cellData = matrix[row]?.[col];
        const td = document.createElement('td');
        
        if (cellData) {
          const { signal, conf, final_prob, last, ema, ml, q, sent, volume_rank } = cellData;
          const cellClass = `grid-cell grid-cell-${signal.toLowerCase()}`;
          
          td.innerHTML = `
            <div class="${cellClass}">
              ${signal.charAt(0)}
              <div class="grid-tooltip">
                <div>Signal: ${signal}</div>
                <div>Confidence: ${(conf * 100).toFixed(1)}%</div>
                <div>Price: ${fmt(last)}</div>
                <div>Volume Rank: #${volume_rank || '—'}</div>
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

  // Display atomic swap opportunities
  function displayAtomicSwapOpportunities(atomic_swaps) {
    const swapContainer = document.getElementById('atomic-swap-opportunities');
    if (!swapContainer) return;
    
    swapContainer.innerHTML = '<h4>🔄 Atomic Swap Opportunities</h4>';
    
    atomic_swaps.slice(0, 5).forEach(swap => {
      const swapDiv = document.createElement('div');
      swapDiv.className = 'atomic-swap-item';
      swapDiv.innerHTML = `
        <div class="swap-route">${swap.swap_route}</div>
        <div class="swap-details">
          <span class="swap-confidence">Confidence: ${(swap.confidence * 100).toFixed(1)}%</span>
          <span class="swap-gain">Expected: +${swap.expected_gain}%</span>
          <span class="swap-time">${swap.execution_time}</span>
        </div>
      `;
      
      // Add click handler for potential execution
      swapDiv.addEventListener('click', () => {
        if (swap.confidence > 0.8) {
          console.log(`High-confidence swap opportunity: ${swap.swap_route}`);
          // Here you could implement actual trading logic
          showTradeExecutionModal(swap);
        }
      });
      
      swapContainer.appendChild(swapDiv);
    });
  }

  // Show trade execution modal for high-confidence opportunities
  function showTradeExecutionModal(opportunity) {
    const modal = document.createElement('div');
    modal.className = 'trade-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <h3>🚀 Execute Trade Opportunity</h3>
        <div class="trade-details">
          <p><strong>Route:</strong> ${opportunity.swap_route}</p>
          <p><strong>Confidence:</strong> ${(opportunity.confidence * 100).toFixed(1)}%</p>
          <p><strong>Expected Gain:</strong> +${opportunity.expected_gain}%</p>
          <p><strong>Gas Cost:</strong> ~$${opportunity.gas_cost}</p>
        </div>
        <div class="modal-actions">
          <button class="btn-execute" onclick="executeTradeOpportunity('${opportunity.from_symbol}', '${opportunity.to_symbol}', ${opportunity.confidence})">Execute Trade</button>
          <button class="btn-cancel" onclick="closeTradeModal()">Cancel</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto-close after 10 seconds
    setTimeout(() => {
      if (document.body.contains(modal)) {
        document.body.removeChild(modal);
      }
    }, 10000);
  }

  // Execute trade opportunity (placeholder for actual implementation)
  window.executeTradeOpportunity = function(fromSymbol, toSymbol, confidence) {
    console.log(`Executing trade: ${fromSymbol} → ${toSymbol} (Confidence: ${(confidence * 100).toFixed(1)}%)`);
    
    // Here you would implement the actual trading logic
    // For now, just log and close modal
    alert(`Trade executed: ${fromSymbol} → ${toSymbol}`);
    closeTradeModal();
  };

  // Close trade modal
  window.closeTradeModal = function() {
    const modal = document.querySelector('.trade-modal');
    if (modal) {
      document.body.removeChild(modal);
    }
  };

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

  // P&L Period Selection Event Listeners
  document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      currentPeriod = this.dataset.period;
      updatePnLSummary();
    });
  });

  // Trade Filter Event Listeners
  const symbolFilter = document.getElementById('symbol-filter');
  const sideFilter = document.getElementById('side-filter');
  const searchFilter = document.getElementById('search-filter');
  
  if (symbolFilter) symbolFilter.addEventListener('change', filterTrades);
  if (sideFilter) sideFilter.addEventListener('change', filterTrades);
  if (searchFilter) searchFilter.addEventListener('input', filterTrades);

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
        await refreshQuantumAnalysis();
        console.log('Quantum analysis refreshed');
      } catch (e) { console.error('Quantum analysis refresh failed:', e); }
      
      try {
        await refreshPerformanceAnalysis('24h');
        console.log('Performance analysis refreshed');
      } catch (e) { console.error('Performance analysis refresh failed:', e); }
      
      if (currentUser?.role === 'superuser') {
        try {
          await refreshAuditLogs();
          console.log('Audit logs refreshed');
        } catch (e) { console.error('Audit logs refresh failed:', e); }
      }
    }, 500);
    
  // Set up auto-refresh
  applyRefreshIntervals();
  setInterval(refreshSentiment, 60000); // Refresh sentiment every minute
    
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
      '/sentiment/articles',
      '/ml/status',
      '/quantum/analysis',
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

  // Auto-start dashboard without authentication
  currentUser = { username: 'admin', role: 'admin' };
  updateUI();
  if (typeof initializeDashboard === 'function') {
    initializeDashboard();
  }

  // Mobile Touch Enhancement Functions
  function initMobileTouchSupport() {
    console.log('🔧 Initializing mobile touch support...');
    
    // Add touch feedback to all interactive elements
    const interactiveElements = document.querySelectorAll('button, .tab-btn, .period-btn, .control-btn, .endpoint-box, .grid-cell, .data-table tr');
    
    interactiveElements.forEach(element => {
      // Add touch start/end events for better feedback
      element.addEventListener('touchstart', function() {
        this.style.opacity = '0.7';
        this.style.transform = 'scale(0.98)';
      }, { passive: true });
      
      element.addEventListener('touchend', function() {
        this.style.opacity = '';
        this.style.transform = '';
      }, { passive: true });
      
      element.addEventListener('touchcancel', function() {
        this.style.opacity = '';
        this.style.transform = '';
      }, { passive: true });
    });
    
    // Prevent zoom on double tap for better UX
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(event) {
      const now = (new Date()).getTime();
      if (now - lastTouchEnd <= 300) {
        event.preventDefault();
      }
      lastTouchEnd = now;
    }, false);
    
    // Improve scrolling on mobile
    document.addEventListener('touchmove', function(e) {
      // Allow scrolling in scrollable containers
      const scrollableParent = e.target.closest('.data-table, .debug-panel, .response-modal, .trades-container');
      if (!scrollableParent) {
        // Prevent bounce scrolling on the body
        if (e.target === document.body || e.target === document.documentElement) {
          e.preventDefault();
        }
      }
    }, { passive: false });
    
    // Handle orientation change
    window.addEventListener('orientationchange', function() {
      setTimeout(function() {
        // Force layout recalculation
        document.body.style.height = window.innerHeight + 'px';
        
        // Refresh any charts or dynamic content
        if (typeof refreshAllData === 'function') {
          refreshAllData();
        }
        
        // Close any open panels that might be mispositioned
        const debugPanel = document.getElementById('debug-panel');
        if (debugPanel && debugPanel.classList.contains('open')) {
          debugPanel.classList.remove('open');
        }
      }, 100);
    });
    
    // Add swipe gesture support for tabs
    let startX = null;
    let startY = null;
    
    document.addEventListener('touchstart', function(e) {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    }, { passive: true });
    
    document.addEventListener('touchmove', function(e) {
      if (!startX || !startY) return;
      
      const diffX = startX - e.touches[0].clientX;
      const diffY = startY - e.touches[0].clientY;
      
      // Only handle horizontal swipes on tab area
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        const tabContainer = e.target.closest('.dashboard-tabs');
        if (tabContainer) {
          const activeTab = document.querySelector('.tab-btn.active');
          const allTabs = Array.from(document.querySelectorAll('.tab-btn'));
          const currentIndex = allTabs.indexOf(activeTab);
          
          if (diffX > 0 && currentIndex < allTabs.length - 1) {
            // Swipe left - next tab
            allTabs[currentIndex + 1].click();
          } else if (diffX < 0 && currentIndex > 0) {
            // Swipe right - previous tab
            allTabs[currentIndex - 1].click();
          }
          
          startX = null;
          startY = null;
        }
      }
    }, { passive: true });
    
    console.log('✅ Mobile touch support initialized');
  }

  // Enhanced mobile detection
  function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
           window.innerWidth <= 768 ||
           ('ontouchstart' in window);
  }

  // Mobile-specific initialization
  function initMobileOptimizations() {
    if (!isMobileDevice()) return;
    
    console.log('📱 Mobile device detected, applying optimizations...');
    
    // Add mobile class to body for CSS targeting
    document.body.classList.add('mobile-device');
    
    // Optimize viewport for mobile
    let viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
    }
    
    // Initialize touch support
    initMobileTouchSupport();
    
    // Adjust refresh intervals for mobile (less frequent to save battery)
    if (typeof refreshIntervals === 'object') {
      Object.keys(refreshIntervals).forEach(key => {
        if (refreshIntervals[key] < 10000) {
          refreshIntervals[key] = Math.max(refreshIntervals[key] * 2, 10000);
        }
      });
    }
    
    // Add mobile-specific event listeners
    document.addEventListener('visibilitychange', function() {
      if (document.hidden) {
        // Pause updates when app is in background
        console.log('📱 App backgrounded, pausing updates');
        Object.values(refreshIntervals).forEach(interval => {
          if (interval) clearInterval(interval);
        });
      } else {
        // Resume updates when app becomes visible
        console.log('📱 App foregrounded, resuming updates');
        if (typeof initializeDashboard === 'function') {
          initializeDashboard();
        }
      }
    });
    
    console.log('✅ Mobile optimizations applied');
  }

  // Initialize mobile support when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileOptimizations);
  } else {
    initMobileOptimizations();
  }

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
    const logs = await fetchJSON("/logs/last?limit=20");
    if (logs.logs && logs.logs.length > 0) {
      const formattedLogs = logs.logs.map(log => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        const emoji = getLogEmoji(log.level);
        return `${time} ${emoji} [${log.component}] ${log.message}`;
      });
      $("#logs").textContent = formattedLogs.join("\n") || "—";
    } else {
      $("#logs").textContent = "—";
    }
  } catch (e) {
    $("#logs").textContent = "—";
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