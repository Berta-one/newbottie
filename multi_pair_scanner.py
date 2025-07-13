# multi_pair_scanner.py - Multi-Pair Crypto Scanner
import time
from binance.client import Client
from strategy import check_breakout_enhanced, get_strategy_confidence, analyze_pair_strength
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime
import os

class CryptoPairScanner:
    def __init__(self, client):
        self.client = client
        self.active_positions = {}
        self.scan_history = []
        
    def get_all_usdt_pairs(self, min_volume_24h=2000000, exclude_leveraged=True):
        """
        Get all USDT trading pairs with minimum 24h volume
        """
        try:
            print(f"?? Fetching all USDT pairs with volume > ${min_volume_24h:,.0f}...")
            ticker_24h = self.client.get_ticker()
            
            usdt_pairs = []
            excluded_keywords = ['UP', 'DOWN', 'BEAR', 'BULL'] if exclude_leveraged else []
            
            for ticker in ticker_24h:
                symbol = ticker['symbol']
                volume = float(ticker['quoteVolume'])
                price_change_24h = float(ticker['priceChangePercent'])
                
                # Filter criteria
                if (symbol.endswith('USDT') and 
                    volume >= min_volume_24h and
                    not any(keyword in symbol for keyword in excluded_keywords)):
                    
                    usdt_pairs.append({
                        'symbol': symbol,
                        'volume_24h': volume,
                        'price_change_24h': price_change_24h,
                        'category': 'Market',
                        'base_qty': self._estimate_base_quantity(symbol, float(ticker['lastPrice']))
                    })
            
            # Sort by 24h volume (highest first)
            usdt_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            print(f"?? Found {len(usdt_pairs)} qualifying USDT pairs")
            return usdt_pairs
            
        except Exception as e:
            print(f"? Error fetching USDT pairs: {e}")
            return []

    def get_selected_pairs(self):
        """
        Curated list of quality crypto pairs across different categories
        """
        selected_pairs = [
            # Major cryptocurrencies (highest liquidity, lowest risk)
            {'symbol': 'BTCUSDT', 'category': 'Major', 'base_qty': 0.001, 'risk_multiplier': 1.0},
            {'symbol': 'ETHUSDT', 'category': 'Major', 'base_qty': 0.01, 'risk_multiplier': 1.0},
            {'symbol': 'BNBUSDT', 'category': 'Major', 'base_qty': 0.1, 'risk_multiplier': 1.0},
            
            # Large cap altcoins (established projects)
            {'symbol': 'ADAUSDT', 'category': 'Large Cap', 'base_qty': 10, 'risk_multiplier': 0.8},
            {'symbol': 'SOLUSDT', 'category': 'Large Cap', 'base_qty': 0.1, 'risk_multiplier': 0.8},
            {'symbol': 'XRPUSDT', 'category': 'Large Cap', 'base_qty': 20, 'risk_multiplier': 0.8},
            {'symbol': 'DOTUSDT', 'category': 'Large Cap', 'base_qty': 2, 'risk_multiplier': 0.8},
            {'symbol': 'AVAXUSDT', 'category': 'Large Cap', 'base_qty': 0.5, 'risk_multiplier': 0.8},
            {'symbol': 'POLYUSDT', 'category': 'Large Cap', 'base_qty': 20, 'risk_multiplier': 0.8},
            
            # Mid cap with strong fundamentals
            {'symbol': 'LINKUSDT', 'category': 'Mid Cap', 'base_qty': 1, 'risk_multiplier': 0.7},
            {'symbol': 'UNIUSDT', 'category': 'Mid Cap', 'base_qty': 2, 'risk_multiplier': 0.7},
            {'symbol': 'LTCUSDT', 'category': 'Mid Cap', 'base_qty': 0.2, 'risk_multiplier': 0.7},
            {'symbol': 'ATOMUSDT', 'category': 'Mid Cap', 'base_qty': 1, 'risk_multiplier': 0.7},
            {'symbol': 'NEARUSDT', 'category': 'Mid Cap', 'base_qty': 5, 'risk_multiplier': 0.7},
            
            # DeFi tokens (higher volatility, focused use case)
            {'symbol': 'AAVEUSDT', 'category': 'DeFi', 'base_qty': 0.1, 'risk_multiplier': 0.6},
            {'symbol': 'COMPUSDT', 'category': 'DeFi', 'base_qty': 0.2, 'risk_multiplier': 0.6},
            {'symbol': 'MKRUSDT', 'category': 'DeFi', 'base_qty': 0.01, 'risk_multiplier': 0.6},
            
            # Gaming/Metaverse (speculative but trending)
            {'symbol': 'SANDUSDT', 'category': 'Gaming', 'base_qty': 20, 'risk_multiplier': 0.5},
            {'symbol': 'MANAUSDT', 'category': 'Gaming', 'base_qty': 30, 'risk_multiplier': 0.5},
            
            # Meme coins (high risk, high reward potential)
            {'symbol': 'DOGEUSDT', 'category': 'Meme', 'base_qty': 200, 'risk_multiplier': 0.4},
            {'symbol': 'SHIBUSDT', 'category': 'Meme', 'base_qty': 2000000, 'risk_multiplier': 0.4},
        ]
        
        print(f"?? Selected {len(selected_pairs)} curated crypto pairs across {len(set([p['category'] for p in selected_pairs]))} categories")
        return selected_pairs

    def get_custom_pairs(self, symbols):
        """
        Convert custom symbol list to standard pair format
        """
        custom_pairs = []
        for symbol in symbols:
            # Estimate base quantity based on current price
            try:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                base_qty = self._estimate_base_quantity(symbol, price)
            except:
                base_qty = 0.001  # Default fallback
            
            custom_pairs.append({
                'symbol': symbol,
                'category': 'Custom',
                'base_qty': base_qty,
                'risk_multiplier': 0.8
            })
        
        print(f"?? Created custom pair list with {len(custom_pairs)} symbols")
        return custom_pairs

    def _estimate_base_quantity(self, symbol, price):
        """
        Estimate appropriate base quantity based on price
        Aims for ~$25-50 position sizes
        """
        target_value = 35  # Target $35 position
        base_qty = target_value / price
        
        # Round to appropriate decimal places
        if base_qty >= 1:
            return round(base_qty, 2)
        elif base_qty >= 0.1:
            return round(base_qty, 3)
        elif base_qty >= 0.01:
            return round(base_qty, 4)
        elif base_qty >= 0.001:
            return round(base_qty, 5)
        else:
            return round(base_qty, 6)

    def analyze_single_pair(self, pair_info):
        """
        Analyze a single trading pair for opportunities
        """
        symbol = pair_info['symbol']
        
        try:
            # Get 2 hours of 1-minute candlestick data
            klines = self.client.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=120
            )
            
            if len(klines) < 120:
                return None
            
            # Get trading decision and confidence
            decision = check_breakout_enhanced(klines)
            confidence = get_strategy_confidence(klines)
            
            # Get detailed pair analysis
            pair_analysis = analyze_pair_strength(klines, symbol)
            
            if not pair_analysis:
                return None
            
            # Combine all data
            result = {
                **pair_analysis,
                'decision': decision,
                'confidence': confidence,
                'category': pair_info.get('category', 'Unknown'),
                'base_qty': pair_info.get('base_qty', 0.001),
                'risk_multiplier': pair_info.get('risk_multiplier', 1.0),
                'timestamp': datetime.now(),
                'in_position': symbol in self.active_positions,
                'scan_score': self._calculate_scan_score(decision, confidence, pair_analysis)
            }
            
            return result
            
        except Exception as e:
            print(f"? Error analyzing {symbol}: {e}")
            return None

    def _calculate_scan_score(self, decision, confidence, analysis):
        """
        Calculate overall scan score for ranking opportunities
        """
        if decision == "HOLD":
            return 0.0
        
        score = confidence * 0.6  # Base score from confidence
        
        # Volume bonus
        volume_ratio = analysis.get('volume_ratio', 0)
        if volume_ratio > 2.0:
            score += 0.2
        elif volume_ratio > 1.5:
            score += 0.1
        
        # RSI bonus (not too extreme)
        rsi = analysis.get('rsi', 50)
        if 30 < rsi < 70:
            score += 0.1
        
        # Volatility penalty (too high is risky)
        volatility = analysis.get('volatility', 0)
        if volatility > 0.05:
            score -= 0.1
        
        # Trading time bonus
        if analysis.get('trading_time_quality', False):
            score += 0.1
        
        return min(1.0, max(0.0, score))
    def scan_multiple_pairs(self, pairs_list, max_workers=8):
        """
        Scan multiple pairs concurrently for trading opportunities
        """
        print(f"?? Scanning {len(pairs_list)} pairs for opportunities...")
        start_time = datetime.now()
        
        opportunities = []
        failed_scans = []
        
        # Use ThreadPoolExecutor for concurrent API calls
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analysis tasks
            future_to_pair = {
                executor.submit(self.analyze_single_pair, pair): pair 
                for pair in pairs_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_pair):
                pair = future_to_pair[future]
                try:
                    result = future.result(timeout=30)  # 30 second timeout per pair
                    if result:
                        opportunities.append(result)
                except Exception as e:
                    failed_scans.append(pair['symbol'])
                    print(f"?? Failed to scan {pair['symbol']}: {e}")
        
        # Sort by scan score (best opportunities first)
        opportunities.sort(key=lambda x: x['scan_score'], reverse=True)
        
        scan_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"? Scan completed in {scan_duration:.1f}s")
        print(f"   Successful: {len(opportunities)}")
        print(f"   Failed: {len(failed_scans)}")
        
        # Save scan history
        scan_record = {
            'timestamp': datetime.now().isoformat(),
            'pairs_scanned': len(pairs_list),
            'opportunities_found': len(opportunities),
            'scan_duration': scan_duration,
            'failed_scans': failed_scans
        }
        self.scan_history.append(scan_record)
        
        return opportunities

    def filter_opportunities(self, opportunities, min_confidence=0.6, max_positions=5):
        """
        Filter opportunities based on trading criteria
        """
        trading_opportunities = []
        
        for opp in opportunities:
            # Skip if already in position
            if opp['in_position']:
                continue
                
            # Must have trading signal
            if opp['decision'] not in ['BUY_LONG', 'BUY_SHORT']:
                continue
                
            # Must meet minimum confidence
            if opp['confidence'] < min_confidence:
                continue
            
            # Must have reasonable volume
            if opp.get('volume_ratio', 0) < 1.2:
                continue
            
            trading_opportunities.append(opp)
        
        # Limit to max positions
        return trading_opportunities[:max_positions]

    def display_scan_results(self, opportunities, show_all=False, top_n=10):
        """
        Display scan results in formatted tables
        """
        print(f"\n{'='*85}")
        print(f"?? CRYPTO PAIR SCAN RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*85}")
        
        # Filter for trading opportunities
        trading_opps = self.filter_opportunities(opportunities, min_confidence=0.5)
        
        if trading_opps:
            print(f"\n?? TOP TRADING OPPORTUNITIES ({len(trading_opps)} found):")
            print(f"{'Symbol':<12} {'Price':<12} {'Signal':<10} {'Conf':<6} {'Score':<6} {'2h Chg':<8} {'Vol':<6} {'Category':<10}")
            print("-" * 85)
            
            for opp in trading_opps[:top_n]:
                symbol = opp['symbol']
                price = f"${opp['current_price']:.4f}"
                signal = opp['decision']
                confidence = f"{opp['confidence']:.2f}"
                score = f"{opp['scan_score']:.2f}"
                change_2h = f"{opp['price_change_2h']:+.1f}%"
                volume_ratio = f"{opp.get('volume_ratio', 0):.1f}x"
                category = opp['category']
                
                print(f"{symbol:<12} {price:<12} {signal:<10} {confidence:<6} {score:<6} {change_2h:<8} {volume_ratio:<6} {category:<10}")
        else:
            print("\n?? No trading opportunities found meeting criteria")

    def save_scan_results(self, opportunities, filename=None):
        """
        Save scan results to JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'logs/scan_results_{timestamp}.json'
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Convert datetime objects to strings for JSON serialization
        serializable_data = []
        for opp in opportunities:
            opp_copy = opp.copy()
            if isinstance(opp_copy.get('timestamp'), datetime):
                opp_copy['timestamp'] = opp_copy['timestamp'].isoformat()
            serializable_data.append(opp_copy)
        
        # Save data
        with open(filename, 'w') as f:
            json.dump({
                'scan_timestamp': datetime.now().isoformat(),
                'total_opportunities': len(opportunities),
                'trading_opportunities': len(self.filter_opportunities(opportunities)),
                'scan_history': self.scan_history,
                'opportunities': serializable_data
            }, f, indent=2, default=str)
        
        print(f"?? Scan results saved to {filename}")
        return filename

# Convenience functions for different scan modes
def scan_all_pairs(client, min_volume=2000000, top_n=50):
    """Scan all USDT pairs with minimum volume"""
    scanner = CryptoPairScanner(client)
    all_pairs = scanner.get_all_usdt_pairs(min_volume_24h=min_volume)
    top_pairs = all_pairs[:top_n]  # Limit to avoid rate limits
    opportunities = scanner.scan_multiple_pairs(top_pairs)
    scanner.display_scan_results(opportunities)
    scanner.save_scan_results(opportunities)
    return opportunities

def scan_selected_pairs(client):
    """Scan curated list of quality pairs"""
    scanner = CryptoPairScanner(client)
    selected_pairs = scanner.get_selected_pairs()
    opportunities = scanner.scan_multiple_pairs(selected_pairs)
    scanner.display_scan_results(opportunities, show_all=True)
    scanner.save_scan_results(opportunities, 'logs/selected_scan_results.json')
    return opportunities

def scan_custom_pairs(client, custom_symbols):
    """Scan custom list of symbols"""
    scanner = CryptoPairScanner(client)
    custom_pairs = scanner.get_custom_pairs(custom_symbols)
    opportunities = scanner.scan_multiple_pairs(custom_pairs)
    scanner.display_scan_results(opportunities, show_all=True)
    scanner.save_scan_results(opportunities, 'logs/custom_scan_results.json')
    return opportunities
