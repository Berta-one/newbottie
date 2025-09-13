#!/usr/bin/env python3
"""
AI Market Bulletin Generator
Creates intelligent market analysis reports based on all trading data
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

class AIMarketBulletin:
    """AI-powered market bulletin generator"""
    
    def __init__(self):
        self.last_bulletin_time = 0
        self.bulletin_cache = {}
        self.bulletin_history = []
    
    def analyze_portfolio_performance(self, positions, balance: float) -> Dict:
        """Analyze portfolio performance"""
        try:
            # Handle case where positions might be int (position count) instead of dict
            if isinstance(positions, int):
                return {
                    'status': 'position_count_only',
                    'message': f'Detected {positions} positions but no details available',
                    'total_equity': balance,
                    'position_count': positions,
                    'diversification_score': min(10, positions)
                }
            
            if not positions or not isinstance(positions, dict):
                return {
                    'status': 'no_positions',
                    'message': 'No active positions to analyze',
                    'total_equity': balance,
                    'position_count': 0,
                    'diversification_score': 0
                }
            
            total_value = balance
            position_analysis = []
            
            for symbol, pos in positions.items():
                value = pos.get('value', 0)
                total_value += value
                
                position_analysis.append({
                    'symbol': symbol,
                    'value': value,
                    'percentage': (value / total_value) * 100 if total_value > 0 else 0,
                    'asset': pos.get('asset', symbol.split('/')[0])
                })
            
            # Sort by value
            position_analysis.sort(key=lambda x: x['value'], reverse=True)
            
            return {
                'total_equity': total_value,
                'position_count': len(positions),
                'largest_position': position_analysis[0] if position_analysis else None,
                'positions': position_analysis,
                'diversification_score': min(10, len(positions))
            }
            
        except Exception as e:
            return {'error': f'Portfolio analysis failed: {e}'}
    
    def analyze_market_signals(self, signals: List[Dict]) -> Dict:
        """Analyze trading signals for market insights"""
        try:
            if not signals:
                return {
                    'status': 'no_signals',
                    'message': 'No signals to analyze'
                }
            
            buy_signals = [s for s in signals if s.get('signal') == 'BUY']
            sell_signals = [s for s in signals if s.get('signal') == 'SELL']
            hold_signals = [s for s in signals if s.get('signal') == 'HOLD']
            
            avg_confidence = sum(s.get('conf', 0.5) for s in signals) / len(signals)
            
            # Determine market sentiment from signals
            if len(buy_signals) > len(sell_signals) * 1.5:
                market_mood = 'BULLISH'
                mood_strength = 'STRONG' if avg_confidence > 0.7 else 'MODERATE'
            elif len(sell_signals) > len(buy_signals) * 1.5:
                market_mood = 'BEARISH'
                mood_strength = 'STRONG' if avg_confidence > 0.7 else 'MODERATE'
            else:
                market_mood = 'NEUTRAL'
                mood_strength = 'STABLE'
            
            return {
                'total_signals': len(signals),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'hold_signals': len(hold_signals),
                'avg_confidence': round(avg_confidence, 3),
                'market_mood': market_mood,
                'mood_strength': mood_strength,
                'signal_quality': 'HIGH' if avg_confidence > 0.7 else 'MEDIUM' if avg_confidence > 0.6 else 'LOW'
            }
            
        except Exception as e:
            return {'error': f'Signal analysis failed: {e}'}
    
    def generate_market_insights(self, signals: List[Dict]) -> List[str]:
        """Generate AI insights from market data"""
        insights = []
        
        try:
            # Analyze BTC specifically (market leader)
            btc_signals = [s for s in signals if 'BTC' in s.get('symbol', '')]
            if btc_signals:
                latest_btc = btc_signals[-1]
                btc_price = latest_btc.get('price', 115000)
                btc_signal = latest_btc.get('signal', 'HOLD')
                btc_conf = latest_btc.get('conf', 0.5)
                
                if btc_price > 110000:
                    insights.append(f"🚀 BTC at ${btc_price:,.0f} - Strong bull market territory above $110K")
                elif btc_price > 100000:
                    insights.append(f"📈 BTC at ${btc_price:,.0f} - Healthy six-figure range, watch for breakout")
                else:
                    insights.append(f"⚠️ BTC at ${btc_price:,.0f} - Below psychological $100K level")
                
                if btc_signal == 'BUY' and btc_conf > 0.7:
                    insights.append(f"🎯 Strong BUY signal for BTC ({btc_conf:.0%} confidence) - Consider accumulation")
                elif btc_signal == 'SELL' and btc_conf > 0.7:
                    insights.append(f"⚠️ Strong SELL signal for BTC ({btc_conf:.0%} confidence) - Consider profit-taking")
            
            # Market structure analysis
            total_signals = len(signals)
            if total_signals > 0:
                buy_ratio = len([s for s in signals if s.get('signal') == 'BUY']) / total_signals
                if buy_ratio > 0.6:
                    insights.append("🟢 Market showing strong buying opportunities across multiple assets")
                elif buy_ratio < 0.3:
                    insights.append("🔴 Market showing risk-off sentiment with sell signals dominating")
                else:
                    insights.append("🟡 Mixed market signals - selective trading opportunities")
            
            # Confidence analysis
            high_conf_signals = [s for s in signals if s.get('conf', 0) > 0.8]
            if high_conf_signals:
                insights.append(f"⚡ {len(high_conf_signals)} high-confidence signals detected - strong conviction trades available")
            
            return insights
            
        except Exception as e:
            return [f"❌ Insight generation error: {e}"]
    
    def generate_trading_recommendations(self, portfolio: Dict, signals: List[Dict]) -> List[str]:
        """Generate specific trading recommendations"""
        recommendations = []
        
        try:
            # Portfolio-based recommendations
            if portfolio.get('largest_position'):
                largest = portfolio['largest_position']
                if largest['percentage'] > 40:
                    recommendations.append(f"⚠️ High concentration in {largest['symbol']} ({largest['percentage']:.1f}%) - Consider rebalancing")
            
            # Signal-based recommendations
            strong_buy_signals = [s for s in signals if s.get('signal') == 'BUY' and s.get('conf', 0) > 0.8]
            strong_sell_signals = [s for s in signals if s.get('signal') == 'SELL' and s.get('conf', 0) > 0.8]
            
            if strong_buy_signals:
                top_buy = max(strong_buy_signals, key=lambda x: x.get('conf', 0))
                recommendations.append(f"🚀 Top opportunity: {top_buy['symbol']} BUY signal ({top_buy['conf']:.0%} confidence)")
            
            if strong_sell_signals:
                top_sell = max(strong_sell_signals, key=lambda x: x.get('conf', 0))
                recommendations.append(f"💰 Profit-taking: {top_sell['symbol']} SELL signal ({top_sell['conf']:.0%} confidence)")
            
            # Risk management
            if portfolio.get('position_count', 0) > 8:
                recommendations.append("📊 Well-diversified portfolio - maintain current allocation strategy")
            elif portfolio.get('position_count', 0) < 3:
                recommendations.append("⚠️ Low diversification - consider spreading risk across more assets")
            
            if not recommendations:
                recommendations.append("📈 Continue current strategy - no immediate actions required")
            
            return recommendations
            
        except Exception as e:
            return [f"❌ Recommendation error: {e}"]
    
    def generate_bulletin(self, trading_data: Dict) -> Dict:
        """Generate complete AI market bulletin"""
        try:
            timestamp = datetime.now()
            
            # Extract data
            positions = trading_data.get('positions', {})
            balance = trading_data.get('balance', 0)
            signals = trading_data.get('signals', [])
            
            # Perform analysis
            portfolio_analysis = self.analyze_portfolio_performance(positions, balance)
            signal_analysis = self.analyze_market_signals(signals)
            market_insights = self.generate_market_insights(signals)
            recommendations = self.generate_trading_recommendations(portfolio_analysis, signals)
            
            # Generate bulletin text
            bulletin_text = f"""
🤖 AI MARKET BULLETIN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {timestamp.strftime('%A, %B %d, %Y at %H:%M UTC')}

💰 PORTFOLIO OVERVIEW
• Total Equity: ${portfolio_analysis.get('total_equity', 0):,.2f}
• Active Positions: {portfolio_analysis.get('position_count', 0)}
• Diversification Score: {portfolio_analysis.get('diversification_score', 0)}/10

🎯 SIGNAL ANALYSIS
• Market Mood: {signal_analysis.get('market_mood', 'UNKNOWN')} ({signal_analysis.get('mood_strength', 'UNKNOWN')})
• Signal Quality: {signal_analysis.get('signal_quality', 'UNKNOWN')}
• Average Confidence: {signal_analysis.get('avg_confidence', 0):.1%}
• Active Signals: {signal_analysis.get('buy_signals', 0)} BUY | {signal_analysis.get('sell_signals', 0)} SELL | {signal_analysis.get('hold_signals', 0)} HOLD

🧠 AI MARKET INSIGHTS
{chr(10).join(f'• {insight}' for insight in market_insights)}

💡 TRADING RECOMMENDATIONS
{chr(10).join(f'• {rec}' for rec in recommendations)}

⚠️ RISK ASSESSMENT
• Portfolio Risk: {self._assess_risk_level(portfolio_analysis, signal_analysis)}
• Next Review: {(timestamp + timedelta(hours=4)).strftime('%H:%M UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated by AI Trading Assistant | Based on Real Market Data
            """.strip()
            
            bulletin = {
                'id': f"bulletin_{int(timestamp.timestamp())}",
                'timestamp': timestamp.isoformat(),
                'title': f"AI Market Bulletin - {timestamp.strftime('%B %d, %Y')}",
                'content': bulletin_text,
                'portfolio_analysis': portfolio_analysis,
                'signal_analysis': signal_analysis,
                'insights': market_insights,
                'recommendations': recommendations,
                'data_quality': 'live' if signals else 'limited',
                'next_update': (timestamp + timedelta(hours=4)).isoformat()
            }
            
            # Cache the bulletin
            self.bulletin_cache = bulletin
            self.bulletin_history.append(bulletin)
            self.last_bulletin_time = time.time()
            
            # Keep only last 24 bulletins
            if len(self.bulletin_history) > 24:
                self.bulletin_history = self.bulletin_history[-12:]
            
            return bulletin
            
        except Exception as e:
            return {
                'error': f'Bulletin generation failed: {e}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _assess_risk_level(self, portfolio: Dict, signals: Dict) -> str:
        """Assess portfolio risk level"""
        try:
            risk_factors = 0
            
            # Concentration risk
            if portfolio.get('largest_position', {}).get('percentage', 0) > 50:
                risk_factors += 2
            elif portfolio.get('largest_position', {}).get('percentage', 0) > 30:
                risk_factors += 1
            
            # Signal quality risk
            if signals.get('signal_quality') == 'LOW':
                risk_factors += 1
            
            # Market mood risk
            if signals.get('market_mood') == 'BEARISH' and signals.get('mood_strength') == 'STRONG':
                risk_factors += 2
            
            if risk_factors >= 3:
                return 'HIGH'
            elif risk_factors >= 1:
                return 'MEDIUM'
            else:
                return 'LOW'
                
        except:
            return 'UNKNOWN'
    
    def should_generate_bulletin(self) -> bool:
        """Check if it's time to generate a new bulletin"""
        # Generate every 4 hours or on first run
        return (time.time() - self.last_bulletin_time) > 14400 or not self.bulletin_cache
    
    def get_latest_bulletin(self, trading_data: Dict) -> Dict:
        """Get latest bulletin, generate if needed"""
        if self.should_generate_bulletin():
            return self.generate_bulletin(trading_data)
        else:
            return self.bulletin_cache

# Global bulletin generator
bulletin_generator = AIMarketBulletin()