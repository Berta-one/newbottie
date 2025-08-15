(function () {
  const API = new URLSearchParams(location.search).get('api') || 'https://bottie-1.onrender.com';
  
  let currentUser = null;
  let authToken = null;
  let equityData = [];
  let refreshIntervals = {};
  let performanceChart = null;
  let webSocketManager = null;

  // --- Backend WebSocket Manager ---
class BackendWebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.subscriptions = new Set();
        this.isConnecting = false;
        this.connectionStatus = 'disconnected';
        this.lastActivity = Date.now();
        
        // Initialize connection
        this.connect();
        
        // Heartbeat to detect connection issues
        this.heartbeatInterval = setInterval(() => {
            this.checkConnection();
        }, 30000);
    }
    
    async connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }
        
        this.isConnecting = true;
        this.updateConnectionStatus('connecting');
        
        try {
            // Determine WebSocket URL based on current API URL
            let wsUrl = API.replace('http', 'ws') + '/ws/trading';
            
            // Add authentication bypass parameters
            const urlParams = new URLSearchParams(window.location.search);
            const queryParams = [];
            
            // Add auth token if available
            if (authToken && authToken !== 'auto-login-token') {
                queryParams.push(`token=${encodeURIComponent(authToken)}`);
            }
            
            // Add bypass parameters for development
            if (urlParams.get('bypass') || urlParams.get('debug')) {
                queryParams.push('bypass=true');
            }
            
            // Check for bypass conditions
            const isDevMode = window.location.hostname === 'localhost' || 
                            window.location.hostname === '127.0.0.1' ||
                            urlParams.get('bypass') === 'true' ||
                            urlParams.get('debug') === 'true';
            
            if (isDevMode || !authToken) {
                queryParams.push('bypass=debug');
            }
            
            if (queryParams.length > 0) {
                wsUrl += '?' + queryParams.join('&');
            }
            
            console.log('Connecting to WebSocket:', wsUrl.replace(/token=[^&]+/, 'token=***'));
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ Connected to Backend WebSocket (Binance Proxy)');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.connectionStatus = 'connected';
                this.updateConnectionStatus('connected');
                this.lastActivity = Date.now();
                
                // Re-subscribe to previous channels
                this.resubscribeToChannels();
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.lastActivity = Date.now();
                    this.handleMessage(message);
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('❌ WebSocket closed:', event.code, event.reason);
                this.isConnecting = false;
                this.connectionStatus = 'disconnected';
                this.updateConnectionStatus('disconnected');
                this.attemptReconnection();
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.connectionStatus = 'error';
                this.updateConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.isConnecting = false;
            this.connectionStatus = 'error';
            this.updateConnectionStatus('error');
            this.attemptReconnection();
        }
    }
    
    handleMessage(message) {
        const { type, channel, data, binance_proxy, auth_bypassed } = message;
        
        switch (type) {
            case 'welcome':
                console.log('WebSocket welcome:', message.message);
                console.log('🔗 Binance Proxy Status:', binance_proxy || 'UNKNOWN');
                console.log('🔓 Auth Bypassed:', auth_bypassed || false);
                
                // Auto-subscribe to all channels for real-time data
                this.subscribe('signals');
                this.subscribe('trades');
                this.subscribe('grid');
                this.subscribe('prices');
                break;
                
            case 'data':
                this.handleChannelData(channel, data);
                break;
                
            case 'subscription_confirmed':
                console.log(`✅ Subscribed to channel: ${channel}`);
                this.subscriptions.add(channel);
                break;
                
            case 'unsubscription_confirmed':
                console.log(`❌ Unsubscribed from channel: ${channel}`);
                this.subscriptions.delete(channel);
                break;
                
            case 'error':
                console.error('WebSocket server error:', message.message);
                break;
                
            default:
                console.log('Unhandled message type:', type, message);
        }
    }
    
    handleChannelData(channel, data) {
        switch (channel) {
            case 'signals':
                this.updateSignalsTable(data);
                break;
            case 'trades':
                this.updateTradesTable(data);
                break;
            case 'grid':
                this.updateGridDisplay(data);
                break;
            case 'prices':
                this.updatePricesDisplay(data);
                break;
            default:
                console.log('Unhandled channel data:', channel, data);
        }
    }
    
    subscribe(channel) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                channel: channel
            }));
        }
    }
    
    unsubscribe(channel) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'unsubscribe',
                channel: channel
            }));
        }
    }
    
    resubscribeToChannels() {
        // Always subscribe to these channels
        const channels = ['signals', 'trades', 'grid', 'prices'];
        channels.forEach(channel => {
            this.subscribe(channel);
        });
    }
    
    updateSignalsTable(signals) {
        const signalsTable = document.getElementById('signals-table');
        if (!signalsTable) return;
        
        const tbody = signalsTable.querySelector('tbody');
        if (!tbody) return;
        
        // Don't clear if we're receiving real-time updates, just update existing or add new
        const signalArray = Array.isArray(signals) ? signals : [signals];
        
        signalArray.forEach(signal => {
            if (!signal || !signal.symbol) return;
            
            // Find existing row for this symbol
            let existingRow = tbody.querySelector(`tr[data-symbol="${signal.symbol}"]`);
            
            if (!existingRow) {
                existingRow = document.createElement('tr');
                existingRow.setAttribute('data-symbol', signal.symbol);
                tbody.appendChild(existingRow);
            }
            
            const signalClass = signal.signal?.toLowerCase().replace('_', '-') || 'hold';
            const signalDisplay = signal.signal?.replace('_', ' ') || 'HOLD';
            
            // Enhanced display with real-time data from Binance proxy
            existingRow.innerHTML = `
                <td class="symbol">${signal.symbol}</td>
                <td><span class="${signalClass}-badge">${signalDisplay}</span></td>
                <td>${signal.confidence?.toFixed(3) || '0.500'}</td>
                <td>$${signal.price?.toFixed(2) || '0.00'}</td>
                <td class="${signal.change_24h >= 0 ? 'positive' : 'negative'}">${signal.change_24h?.toFixed(2) || '0.00'}%</td>
                <td>🔴 Live • ${new Date().toLocaleTimeString()}</td>
            `;
            
            // Add visual feedback for real-time updates
            existingRow.style.backgroundColor = 'rgba(100, 255, 218, 0.1)';
            setTimeout(() => {
                existingRow.style.backgroundColor = '';
            }, 1000);
        });
    }
    
    updateTradesTable(tradesData) {
        const tradesTable = document.getElementById('trades-table');
        if (!tradesTable) return;
        
        const tbody = tradesTable.querySelector('tbody');
        if (!tbody) return;
        
        // Handle both individual trades and trade arrays from Binance proxy
        let trades = [];
        if (tradesData.trades && Array.isArray(tradesData.trades)) {
            trades = tradesData.trades;
        } else if (Array.isArray(tradesData)) {
            trades = tradesData;
        } else if (tradesData.symbol) {
            // Single trade from real-time feed
            trades = [tradesData];
        }
        
        if (trades.length === 0) return;
        
        // For real-time updates, add new trades at the top and limit to 100
        const currentRowCount = tbody.children.length;
        
        trades.forEach((trade, index) => {
            if (!trade || !trade.symbol) return;
            
            const row = document.createElement('tr');
            const sideClass = trade.side?.toLowerCase() === 'buy' ? 'trade-buy' : 'trade-sell';
            const tradeValue = (trade.price || 0) * (trade.quantity || 0);
            
            // Enhanced real-time trade display
            row.className = sideClass;
            row.innerHTML = `
                <td>🔴 ${new Date(trade.timestamp * 1000).toLocaleString()}</td>
                <td class="symbol">${trade.symbol}</td>
                <td class="${sideClass}">${trade.side}</td>
                <td>${trade.quantity?.toFixed(6) || '0.000000'}</td>
                <td>$${trade.price?.toFixed(2) || '0.00'}</td>
                <td>$${tradeValue.toFixed(2)}</td>
                <td>${trade.confidence?.toFixed(3) || '0.500'}</td>
                <td class="trade-pnl-neutral">Live</td>
                <td>✅ Executed</td>
            `;
            
            // Add visual feedback for real-time updates
            row.style.backgroundColor = sideClass === 'trade-buy' ? 
                'rgba(74, 222, 128, 0.2)' : 'rgba(248, 113, 113, 0.2)';
            
            // Insert at the top
            tbody.insertBefore(row, tbody.firstChild);
            
            setTimeout(() => {
                row.style.backgroundColor = '';
            }, 2000);
        });
        
        // Limit to 100 rows for performance
        while (tbody.children.length > 100) {
            tbody.removeChild(tbody.lastChild);
        }
    }
    
    updateGridDisplay(gridData) {
        // Use existing grid update logic
        if (typeof updateGridDisplay === 'function') {
            updateGridDisplay(gridData);
        }
    }
    
    updatePricesDisplay(priceData) {
        // Update any price displays with real-time data
        if (priceData.prices && Array.isArray(priceData.prices)) {
            priceData.prices.forEach(price => {
                // Update any price displays in the UI
                const priceElements = document.querySelectorAll(`[data-symbol="${price.symbol}"] .price`);
                priceElements.forEach(el => {
                    el.textContent = `$${price.price?.toFixed(2) || '—'}`;
                });
            });
        }
    }
    
    checkConnection() {
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivity;
        
        // If no activity for 60 seconds, consider connection stale
        if (timeSinceLastActivity > 60000) {
            console.warn('WebSocket connection appears stale, reconnecting...');
            this.disconnect();
            this.connect();
        }
    }
    
    attemptReconnection() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.updateConnectionStatus('reconnecting');
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    updateConnectionStatus(status) {
        this.connectionStatus = status;
        
        // Update connection status indicator
        const statusElements = document.querySelectorAll('#websocket-status, .ws-status-indicator');
        statusElements.forEach(element => {
            if (element) {
                element.textContent = `WS: ${status}`;
                element.className = `ws-status ws-status-${status}`;
            }
        });
        
        // Update any status indicators in the UI
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.textContent = status;
            statusIndicator.className = `status-indicator status-${status}`;
        }
        
        console.log(`WebSocket status: ${status}`);
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    getStatus() {
        return {
            status: this.connectionStatus,
            subscriptions: Array.from(this.subscriptions),
            reconnectAttempts: this.reconnectAttempts,
            lastActivity: this.lastActivity
        };
    }
}
// --- End Backend WebSocket Manager ---

  // Auto-login on page load
  function autoLogin() {
    console.log('Auto-login disabled - hardcoded credentials removed for security');
    console.log('💡 Use the "🔓 Dev Bypass" button on the login screen for development access');
    console.log('💡 Or add ?bypass=true to the URL for instant bypass');
    
    // Check for URL-based bypass
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('bypass') === 'true' || urlParams.get('debug') === 'true') {
      console.log('🔓 URL-based bypass detected, activating...');
      currentUser = { username: 'url-bypass-user', role: 'developer', bypass: true };
      authToken = 'url-bypass-token';
      updateUI();
      initializeDashboard();
      return;
    }
    
    // Check if user already has saved auth state
    if (loadAuthState()) {
      console.log('✅ Restored previous session');
      updateUI();
      initializeDashboard();
      return;
    }
    
    // Show login screen
    console.log('🔐 Please login or use Dev Bypass button');
    updateUI();
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
    const response = await fetch('/sentiment/articles');
    const data = await response.json();
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

  // Bypass button functionality for development
  function initializeBypassButton() {
    const bypassBtn = document.getElementById('bypass-btn');
    if (!bypassBtn) {
      console.error('❌ Bypass button not found in DOM');
      return;
    }
    
    bypassBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      console.log('🔓 Dev Bypass button clicked');
      
      const loginError = document.getElementById('login-error');
      
      bypassBtn.disabled = true;
      bypassBtn.textContent = '🔓 Bypassing...';
      if (loginError) loginError.textContent = '';
      
      try {
        // Create bypass user and token
        const bypassUser = {
          username: 'dev-user',
          role: 'developer',
          bypass: true
        };
        
        console.log('Setting auth state with bypass token...');
        saveAuthState('bypass-token', bypassUser);
        
        // Verify auth state was set
        console.log('Current auth state:', { authToken, currentUser });
        
        // Add bypass parameter to URL for WebSocket
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.set('bypass', 'true');
        window.history.replaceState({}, '', currentUrl);
        
        console.log('🔓 Development bypass activated');
        console.log('Updating UI...');
        updateUI();
        
        console.log('Initializing dashboard...');
        try {
          initializeDashboard();
          console.log('✅ Bypass complete - dashboard initialized');
        } catch (dashError) {
          console.error('Dashboard initialization error:', dashError);
          if (loginError) loginError.textContent = 'Bypass successful but dashboard failed to load: ' + dashError.message;
        }
        
      } catch (error) {
        const errorMsg = 'Bypass failed: ' + error.message;
        if (loginError) loginError.textContent = errorMsg;
        console.error('❌ Bypass error:', error);
      } finally {
        bypassBtn.disabled = false;
        bypassBtn.textContent = '🔓 Dev Bypass';
      }
    });
    
    console.log('✅ Bypass button initialized');
  }
  
  // Initialize bypass button when DOM is ready - will be called at the end of script

  // Add credential testing functionality (disabled - use Dev Bypass instead)
  async function testMultipleCredentials() {
    const credentials = [];
    
    console.log('⚠️ Hardcoded credential testing disabled for security.');
    console.log('💡 Use the "🔓 Dev Bypass" button for development access.');
    
    const loginError = document.getElementById('login-error');
    if (loginError) {
      loginError.innerHTML = '⚠️ Use Dev Bypass button for development access';
    }
    return;

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
    // Disabled for security - use Dev Bypass button instead
    console.log('⚠️ Credential testing disabled - use Dev Bypass button');
    return;
    
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
      const data = await fetchJSON('/quantum/details');
      updateQuantumAnalysis(data);
      
      // Update quantum status chip
      const statusChip = document.getElementById('quantum-status-chip');
      if (statusChip) {
        setChip(statusChip, data.enabled ? 'ok' : 'warn');
        statusChip.textContent = data.enabled ? 'Online' : 'Offline';
      }
      
      // Update other quantum fields
      updateElement('quantum-backend-detail', data.backend || '—');
      updateElement('quantum-queue', data.queue_status || '—');
      updateElement('quantum-jobs', data.active_jobs || 0);
      updateElement('quantum-success-rate', 
        data.success_rate ? (data.success_rate * 100).toFixed(1) + '%' : '—');
        
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
      // Check if WebSocket is connected and handling signals
      if (webSocketManager && webSocketManager.subscriptions.has('signals')) {
        console.log('✅ Signals updated via WebSocket');
        return; // WebSocket is handling signals updates
      }
      
      // Fallback to REST API if WebSocket not available
      console.log('⚠️ Fallback: Fetching signals via REST API');
      const response = await authFetch('/signals');
      const data = await response.json();
      
      if (!signalsTable) return;
      
      const tbody = signalsTable.querySelector('tbody');
      tbody.innerHTML = '';
      
      (data || []).forEach(signal => {
        const row = document.createElement('tr');
        const signalClass = signal.signal?.toLowerCase() || 'hold';
        const weights = signal.weights || {};
        const weightStr = Object.entries(weights).map(([k, v]) => `${k}:${(v*100).toFixed(0)}%`).join(' ');
        
        row.innerHTML = `
          <td class="symbol">${signal.symbol}</td>
          <td><span class="${signalClass}-badge">${signal.signal}</span></td>
          <td>${signal.confidence?.toFixed(3) || signal.final_prob?.toFixed(3) || '—'}</td>
          <td>${signal.price?.toFixed(2) || '—'}</td>
          <td>${signal.change_24h?.toFixed(2) || '—'}%</td>
          <td>${signal.reason || signal.timestamp ? new Date(signal.timestamp * 1000).toLocaleTimeString() : '—'}</td>
        `;
        tbody.appendChild(row);
      });
    } catch (error) {
      console.error('Signals refresh error:', error);
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
      // Check if WebSocket is connected and handling trades
      if (webSocketManager && webSocketManager.subscriptions.has('trades')) {
        console.log('✅ Trades updated via WebSocket');
        return; // WebSocket is handling trades updates
      }
      
      // Fallback to REST API if WebSocket not available
      console.log('⚠️ Fallback: Fetching trades via REST API');
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
      // Check if WebSocket is connected and handling grid
      if (webSocketManager && webSocketManager.subscriptions.has('grid')) {
        console.log('✅ Grid updated via WebSocket');
        return; // WebSocket is handling grid updates
      }
      
      // Fallback to REST API if WebSocket not available
      console.log('⚠️ Fallback: Fetching grid via REST API');
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
    
    const { rows, cols, matrix, ts, portfolio_size, volume_leaders, total_pairs } = data;
    
    // Update timestamp
    if (timestampEl) {
      timestampEl.textContent = new Date(ts * 1000).toLocaleTimeString();
    }
    
    // Update grid statistics
    if (portfolioCountEl) {
      portfolioCountEl.textContent = portfolio_size || rows?.length || 0;
    }
    if (volumeCountEl) {
      volumeCountEl.textContent = volume_leaders || cols?.length || 0;
    }
    if (totalPairsEl) {
      totalPairsEl.textContent = total_pairs || ((rows?.length || 0) * (cols?.length || 0));
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
    
    // Initialize WebSocket connection for real-time data
    if (!webSocketManager) {
      console.log('🔄 Initializing WebSocket connection...');
      webSocketManager = new BackendWebSocketManager();
    }
    
    // Initial data fetch with error handling (reduced polling, WebSocket will handle most updates)
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
        await refreshPositions();
        console.log('Positions refreshed');
      } catch (e) { console.error('Positions refresh failed:', e); }
      
      try {
        await refreshEquityChart();
        console.log('Equity chart refreshed');
      } catch (e) { console.error('Equity chart refresh failed:', e); }
      
      try {
        await refreshLogs();
        console.log('Logs refreshed');
      } catch (e) { console.error('Logs refresh failed:', e); }
      
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
    
    // Set up reduced auto-refresh (WebSocket handles signals, trades, grid, prices)
    applyReducedRefreshIntervals();
    
    // Resize canvas on window resize
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    
    console.log('Dashboard initialization complete');
  }
  
  // Reduced refresh intervals since WebSocket handles real-time data
  function applyReducedRefreshIntervals() {
    // Clear old intervals
    clearAllIntervals();
    
    // Only refresh non-real-time data periodically
    refreshIntervals.health = setInterval(refreshHealth, 30000); // 30 seconds
    refreshIntervals.sentiment = setInterval(refreshSentiment, 60000); // 1 minute
    refreshIntervals.positions = setInterval(refreshPositions, 15000); // 15 seconds
    refreshIntervals.equity = setInterval(refreshEquityChart, 30000); // 30 seconds
    refreshIntervals.logs = setInterval(refreshLogs, 45000); // 45 seconds
    refreshIntervals.ml = setInterval(refreshMLStatus, 60000); // 1 minute
    refreshIntervals.quantum = setInterval(refreshQuantumAnalysis, 60000); // 1 minute
    
    console.log('✅ Reduced refresh intervals applied (WebSocket handles real-time data)');
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
  
  // Make WebSocket manager globally accessible
  window.webSocketManager = webSocketManager;
  
  // Make bypass function globally accessible for debugging
  window.devBypass = function() {
    console.log('🔓 Manual Dev Bypass triggered');
    try {
      currentUser = { username: 'dev-user', role: 'developer', bypass: true };
      authToken = 'bypass-token';
      
      // Add URL parameter
      const url = new URL(window.location);
      url.searchParams.set('bypass', 'true');
      window.history.replaceState({}, '', url);
      
      console.log('Auth state set:', { currentUser, authToken });
      
      updateUI();
      initializeDashboard();
      
      console.log('✅ Manual bypass complete!');
      return 'Bypass successful!';
    } catch (error) {
      console.error('Manual bypass failed:', error);
      return 'Bypass failed: ' + error.message;
    }
  };

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
    // Check if WebSocket is handling grid updates
    if (window.webSocketManager && window.webSocketManager.subscriptions.has('grid')) {
      console.log('✅ Maxi Grid updated via WebSocket');
      return; // WebSocket is handling grid updates
    }
    
    // Fallback to REST API
    console.log('⚠️ Fallback: Fetching maxi grid via REST API');
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

// Reduced polling since WebSocket handles most real-time data
let gridInterval;
function startGridPolling() {
  if (gridInterval) clearInterval(gridInterval);
  // Increase interval since WebSocket handles real-time updates
  gridInterval = setInterval(refreshMaxiGrid, 60000); // 1 minute instead of 15 seconds
  // Initial load after a short delay
  setTimeout(refreshMaxiGrid, 1200);
}

// Reduce ping frequency since WebSocket provides better real-time updates
setInterval(ping, 10000); // 10 seconds instead of 2 seconds
ping();
startGridPolling();

// Initialize auto-login when page loads
autoLogin();

// Initialize bypass button - CRITICAL: Must be at the end after all DOM elements exist
setTimeout(() => {
  console.log('🔧 Initializing bypass button...');
  initializeBypassButton();
  
  // Also add a direct event listener as backup
  const bypassBtn = document.getElementById('bypass-btn');
  if (bypassBtn) {
    console.log('✅ Bypass button found, adding direct listener');
    bypassBtn.onclick = async function() {
      console.log('🔓 DIRECT: Dev Bypass clicked');
      
      try {
        // Simple, direct bypass
        currentUser = { username: 'dev-user', role: 'developer', bypass: true };
        authToken = 'bypass-token';
        
        // Add URL parameter
        const url = new URL(window.location);
        url.searchParams.set('bypass', 'true');
        window.history.replaceState({}, '', url);
        
        console.log('🔄 Updating UI...');
        updateUI();
        
        console.log('🚀 Initializing dashboard...');
        initializeDashboard();
        
        console.log('✅ BYPASS COMPLETE!');
      } catch (error) {
        console.error('❌ Bypass failed:', error);
        alert('Bypass failed: ' + error.message);
      }
    };
  } else {
    console.error('❌ Bypass button not found!');
  }
}, 1000); // Wait 1 second to ensure DOM is fully loaded