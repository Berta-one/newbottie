
// Add this to your existing dashboard JavaScript

// Cross-pair trading functions
async function refreshCrossPairData() {
  try {
    const [portfolio, opportunities, suggestions] = await Promise.all([
      fetch(`${API}/portfolio/cross-pairs`).then(r => r.json()),
      fetch(`${API}/cross-pairs/opportunities`).then(r => r.json()),
      fetch(`${API}/portfolio/rebalancing-suggestions`).then(r => r.json())
    ]);
    
    updatePortfolioOverview(portfolio);
    updateCrossPairOpportunities(opportunities);
    updateRebalancingSuggestions(suggestions);
    
  } catch (err) {
    console.error('Cross-pair data refresh failed', err);
  }
}

function updatePortfolioOverview(portfolio) {
  if (portfolio.enabled) {
    document.getElementById('portfolio-asset-count').textContent = portfolio.total_assets || '—';
    document.getElementById('cross-pair-count').textContent = portfolio.total_pairs || '—';
    document.getElementById('cross-pair-status').textContent = 'ACTIVE';
    document.getElementById('cross-pair-status').style.background = '#4caf50';
  } else {
    document.getElementById('cross-pair-status').textContent = 'DISABLED';
    document.getElementById('cross-pair-status').style.background = '#ff9800';
  }
}

function updateCrossPairOpportunities(data) {
  const container = document.getElementById('cross-pair-opportunities');
  const countEl = document.getElementById('cross-opportunities-count');
  
  if (!container) return;
  
  container.innerHTML = '';
  
  if (data.opportunities && data.opportunities.length > 0) {
    countEl.textContent = data.opportunities.length;
    
    data.opportunities.forEach(opp => {
      const row = document.createElement('tr');
      const profitClass = opp.estimated_profit_pct > 0 ? 'positive' : 'negative';
      const directionClass = opp.direction === 'buy' ? 'buy-badge' : 'sell-badge';
      
      row.innerHTML = `
        <td>
          <span style="color: #64ffda; font-weight: 600;">${opp.from_asset}</span>
          <span style="color: #8892b0;"> → </span>
          <span style="color: #4caf50; font-weight: 600;">${opp.to_asset}</span>
        </td>
        <td class="symbol">${opp.symbol}</td>
        <td><span class="${directionClass}">${opp.direction.toUpperCase()}</span></td>
        <td>${(opp.signal_strength * 100).toFixed(1)}%</td>
        <td class="${profitClass}">${(opp.estimated_profit_pct * 100).toFixed(2)}%</td>
        <td>${opp.current_price.toFixed(6)}</td>
        <td style="color: #8892b0; font-size: 11px;">Ready</td>
      `;
      container.appendChild(row);
    });
  } else {
    countEl.textContent = '0';
    container.innerHTML = '<tr><td colspan="7" style="color: #8892b0; text-align: center;">No cross-pair opportunities found</td></tr>';
  }
}

function updateRebalancingSuggestions(data) {
  const container = document.getElementById('rebalancing-suggestions');
  if (!container) return;
  
  container.innerHTML = '';
  
  if (data.enabled && data.suggestions && data.suggestions.length > 0) {
    data.suggestions.forEach((suggestion, index) => {
      const suggestionEl = document.createElement('div');
      suggestionEl.style.cssText = 'background: rgba(100, 255, 218, 0.05); border: 1px solid rgba(100, 255, 218, 0.2); border-radius: 6px; padding: 12px; margin-bottom: 8px;';
      
      suggestionEl.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="color: #64ffda; font-weight: 600; margin-bottom: 4px;">
              ${suggestion.action}
            </div>
            <div style="color: #8892b0; font-size: 11px;">
              ${suggestion.reasoning}
            </div>
          </div>
          <div style="text-align: right;">
            <div style="color: #4caf50; font-weight: 600;">
              +${(suggestion.expected_profit * 100).toFixed(2)}%
            </div>
            <div style="color: #8892b0; font-size: 10px;">
              ${(suggestion.confidence * 100).toFixed(0)}% confidence
            </div>
          </div>
        </div>
      `;
      container.appendChild(suggestionEl);
    });
  } else {
    container.innerHTML = '<div style="color: #8892b0; text-align: center; padding: 20px;">No rebalancing suggestions at this time</div>';
  }
}

// Add cross-pair refresh to your existing intervals
refreshIntervals.crossPairs = setInterval(refreshCrossPairData, 60000); // Every 60 seconds

// Initial load
setTimeout(refreshCrossPairData, 2000);
