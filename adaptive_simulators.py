#!/usr/bin/env python3
"""
Adaptive Trading Simulators - Competitive Learning System
Three independent simulators compete and adapt weights based on performance
"""

import time
import random
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SimulatorTrade:
    """Simulated trade record"""
    id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: float
    confidence: float
    simulator_type: str
    profitable: bool = False
    pnl: float = 0.0

class AdaptiveSimulator:
    """Base class for trading simulators"""
    
    def __init__(self, name: str, initial_weight: float):
        self.name = name
        self.weight = initial_weight
        self.trades = []
        self.balance = 10000.0  # Start each with $10k virtual
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.win_rate = 0.0
        self.avg_confidence = 0.0
        self.last_performance_check = time.time()
        
    def calculate_performance(self) -> Dict[str, float]:
        """Calculate performance metrics"""
        if self.total_trades == 0:
            return {
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl_per_trade': 0.0,
                'roi': 0.0,
                'sharpe_ratio': 0.0,
                'performance_score': 0.0
            }
        
        self.win_rate = self.winning_trades / self.total_trades
        avg_pnl_per_trade = self.total_pnl / self.total_trades
        roi = (self.balance - 10000) / 10000  # ROI from starting balance
        
        # Simple Sharpe ratio approximation
        sharpe_ratio = roi / max(0.1, abs(avg_pnl_per_trade)) if avg_pnl_per_trade != 0 else 0
        
        # Performance score (0-1) for weight adjustment
        performance_score = (self.win_rate * 0.6) + (min(roi, 0.5) * 0.4)  # Win rate 60%, ROI 40%
        
        return {
            'win_rate': round(self.win_rate, 3),
            'total_pnl': round(self.total_pnl, 2),
            'avg_pnl_per_trade': round(avg_pnl_per_trade, 2),
            'roi': round(roi, 3),
            'sharpe_ratio': round(sharpe_ratio, 3),
            'performance_score': round(performance_score, 3)
        }
    
    def execute_simulated_trade(self, signal: Dict[str, Any]) -> SimulatorTrade:
        """Execute a simulated trade based on signal"""
        try:
            symbol = signal['symbol']
            signal_type = signal['signal']
            price = signal['price']
            confidence = signal.get('conf', 0.5)
            
            # Calculate trade size (5% of balance)
            trade_value = self.balance * 0.05
            quantity = trade_value / price
            
            # Simulate trade outcome based on confidence and random market movement
            # Higher confidence = higher probability of success
            success_probability = confidence * 0.8 + 0.1  # 10-90% based on confidence
            market_movement = random.uniform(-0.05, 0.05)  # ±5% random movement
            
            # Determine if trade is profitable
            if signal_type == 'BUY':
                profitable = market_movement > -0.02  # Buy is profitable if price doesn't drop >2%
                pnl = quantity * price * market_movement if profitable else quantity * price * (-0.03)
            elif signal_type == 'SELL':
                profitable = market_movement < 0.02   # Sell is profitable if price doesn't rise >2%
                pnl = quantity * price * (-market_movement) if profitable else quantity * price * (-0.03)
            else:  # HOLD or SWAP
                profitable = abs(market_movement) < 0.01  # Hold is profitable in stable markets
                pnl = 0.0
            
            # Apply confidence factor to PnL
            if profitable:
                pnl *= (confidence + 0.5)  # Higher confidence = better profits
            
            # Update simulator state
            self.total_trades += 1
            if profitable:
                self.winning_trades += 1
            
            self.total_pnl += pnl
            self.balance += pnl
            
            # Create trade record
            trade = SimulatorTrade(
                id=f"{self.name}_{int(time.time())}_{self.total_trades}",
                symbol=symbol,
                side=signal_type.lower(),
                quantity=quantity,
                price=price,
                timestamp=time.time(),
                confidence=confidence,
                simulator_type=self.name,
                profitable=profitable,
                pnl=pnl
            )
            
            self.trades.append(trade)
            
            # Keep only recent trades
            if len(self.trades) > 100:
                self.trades = self.trades[-50:]
            
            return trade
            
        except Exception as e:
            print(f"❌ {self.name} simulation error: {e}")
            return None

class TraditionalSimulator(AdaptiveSimulator):
    """Simulator using only traditional technical analysis"""
    
    def __init__(self):
        super().__init__("Traditional", 0.4)  # Start with 40% weight
    
    def generate_signal(self, symbol: str, price: float, change_24h: float) -> Dict[str, Any]:
        """Generate signal using only traditional technical analysis"""
        try:
            # Pure technical analysis
            if change_24h > 3:
                signal = 'SELL'
                confidence = min(0.9, 0.6 + (change_24h - 3) * 0.04)
            elif change_24h < -3:
                signal = 'BUY'
                confidence = min(0.9, 0.6 + abs(change_24h + 3) * 0.04)
            else:
                signal = 'HOLD'
                confidence = 0.5 + abs(change_24h) * 0.03
            
            return {
                'symbol': symbol,
                'signal': signal,
                'conf': confidence,
                'price': price,
                'change': change_24h / 100,
                'method': 'traditional_only',
                'components': {'ema': confidence, 'technical': confidence}
            }
            
        except Exception as e:
            print(f"❌ Traditional signal error: {e}")
            return None

class SentimentSimulator(AdaptiveSimulator):
    """Simulator using only sentiment analysis"""
    
    def __init__(self):
        super().__init__("Sentiment", 0.1)  # Start with 10% weight
    
    def generate_signal(self, symbol: str, price: float, change_24h: float) -> Dict[str, Any]:
        """Generate signal using only sentiment analysis"""
        try:
            # Simulate sentiment-based signal
            # In real implementation, this would use actual news/social sentiment
            sentiment_score = random.uniform(-1, 1)
            news_volume = random.randint(1, 100)
            
            # Convert sentiment to trading signal
            if sentiment_score > 0.3 and news_volume > 20:
                signal = 'BUY'
                confidence = min(0.9, 0.5 + sentiment_score * 0.4)
            elif sentiment_score < -0.3 and news_volume > 20:
                signal = 'SELL'
                confidence = min(0.9, 0.5 + abs(sentiment_score) * 0.4)
            else:
                signal = 'HOLD'
                confidence = 0.5 + abs(sentiment_score) * 0.2
            
            return {
                'symbol': symbol,
                'signal': signal,
                'conf': confidence,
                'price': price,
                'change': change_24h / 100,
                'method': 'sentiment_only',
                'components': {'sentiment': sentiment_score, 'news_volume': news_volume}
            }
            
        except Exception as e:
            print(f"❌ Sentiment signal error: {e}")
            return None

class QuantumSimulator(AdaptiveSimulator):
    """Simulator using only quantum analysis"""
    
    def __init__(self):
        super().__init__("Quantum", 0.2)  # Start with 20% weight
    
    def generate_signal(self, symbol: str, price: float, change_24h: float) -> Dict[str, Any]:
        """Generate signal using only quantum analysis"""
        try:
            # Pure quantum analysis
            volatility = abs(change_24h) / 100
            
            # Quantum superposition states
            superposition_states = max(2, int(volatility * 20))
            
            # Quantum entanglement with market leaders
            btc_influence = 0.8 if 'BTC' in symbol else 0.3
            
            # Quantum probability
            if volatility > 0.05:
                quantum_prob = 0.7 + (volatility * 3)
            elif volatility < 0.01:
                quantum_prob = 0.3
            else:
                quantum_prob = 0.5 + volatility * 2
            
            # Apply quantum entanglement
            quantum_prob = quantum_prob * btc_influence + 0.5 * (1 - btc_influence)
            quantum_prob = max(0.1, min(0.9, quantum_prob))
            
            # Convert to signal
            if quantum_prob > 0.65:
                signal = 'BUY'
                confidence = quantum_prob
            elif quantum_prob < 0.35:
                signal = 'SELL'
                confidence = 1 - quantum_prob
            else:
                signal = 'HOLD'
                confidence = 0.5 + abs(quantum_prob - 0.5)
            
            return {
                'symbol': symbol,
                'signal': signal,
                'conf': confidence,
                'price': price,
                'change': change_24h / 100,
                'method': 'quantum_only',
                'components': {
                    'quantum_prob': quantum_prob,
                    'superposition_states': superposition_states,
                    'btc_influence': btc_influence,
                    'volatility': volatility
                }
            }
            
        except Exception as e:
            print(f"❌ Quantum signal error: {e}")
            return None

class AdaptiveWeightManager:
    """Manages weight adaptation based on simulator performance"""
    
    def __init__(self):
        self.traditional_sim = TraditionalSimulator()
        self.sentiment_sim = SentimentSimulator()
        self.quantum_sim = QuantumSimulator()
        
        self.current_weights = {
            'traditional': 0.4,  # 40%
            'sentiment': 0.1,     # 10% 
            'quantum': 0.2,       # 20%
            'ml': 0.3             # 30%
        }  # Total = 100%
        
        self.weight_history = []
        self.last_adaptation = time.time()
        
    def run_simulations(self, symbol: str, price: float, change_24h: float):
        """Run all three simulators on the same market data"""
        try:
            # Generate signals from each simulator
            traditional_signal = self.traditional_sim.generate_signal(symbol, price, change_24h)
            sentiment_signal = self.sentiment_sim.generate_signal(symbol, price, change_24h)
            quantum_signal = self.quantum_sim.generate_signal(symbol, price, change_24h)
            
            # Execute simulated trades
            results = {}
            
            if traditional_signal:
                trade = self.traditional_sim.execute_simulated_trade(traditional_signal)
                results['traditional'] = trade
            
            if sentiment_signal:
                trade = self.sentiment_sim.execute_simulated_trade(sentiment_signal)
                results['sentiment'] = trade
            
            if quantum_signal:
                trade = self.quantum_sim.execute_simulated_trade(quantum_signal)
                results['quantum'] = trade
            
            return results
            
        except Exception as e:
            print(f"❌ Simulation run error: {e}")
            return {}
    
    def adapt_weights(self):
        """Adapt weights based on simulator performance"""
        try:
            # Get performance from each simulator
            traditional_perf = self.traditional_sim.calculate_performance()
            sentiment_perf = self.sentiment_sim.calculate_performance()
            quantum_perf = self.quantum_sim.calculate_performance()
            
            # Extract performance scores
            traditional_score = traditional_perf['performance_score']
            sentiment_score = sentiment_perf['performance_score']
            quantum_score = quantum_perf['performance_score']
            
            # Calculate new weights based on relative performance
            total_score = traditional_score + sentiment_score + quantum_score
            
            if total_score > 0:
                # Redistribute ALL weights based on performance (total = 100%)
                # Include ML in the competition
                ml_score = 0.6  # Give ML a baseline score
                total_score_with_ml = traditional_score + sentiment_score + quantum_score + ml_score
                
                # Calculate new weights (total = 100%)
                new_traditional = (traditional_score / total_score_with_ml)
                new_sentiment = (sentiment_score / total_score_with_ml)
                new_quantum = (quantum_score / total_score_with_ml)
                new_ml = (ml_score / total_score_with_ml)
                
                # Apply gradual adaptation (don't change too quickly)
                adaptation_rate = 0.1  # 10% adaptation per cycle
                
                self.current_weights['traditional'] = self.current_weights['traditional'] * (1 - adaptation_rate) + new_traditional * adaptation_rate
                self.current_weights['sentiment'] = self.current_weights['sentiment'] * (1 - adaptation_rate) + new_sentiment * adaptation_rate
                self.current_weights['quantum'] = self.current_weights['quantum'] * (1 - adaptation_rate) + new_quantum * adaptation_rate
                self.current_weights['ml'] = self.current_weights['ml'] * (1 - adaptation_rate) + new_ml * adaptation_rate
                
                # Ensure weights total exactly 100%
                total_weight = sum(self.current_weights.values())
                if total_weight > 0:
                    for key in self.current_weights:
                        self.current_weights[key] /= total_weight
            
            # Record weight change
            self.weight_history.append({
                'timestamp': time.time(),
                'weights': dict(self.current_weights),
                'performance': {
                    'traditional': traditional_perf,
                    'sentiment': sentiment_perf,
                    'quantum': quantum_perf
                }
            })
            
            # Keep only recent history
            if len(self.weight_history) > 100:
                self.weight_history = self.weight_history[-50:]
            
            self.last_adaptation = time.time()
            
            print(f"🔄 Weight adaptation:")
            print(f"   Traditional: {self.current_weights['traditional']:.1%} (win rate: {traditional_perf['win_rate']:.1%})")
            print(f"   Sentiment: {self.current_weights['sentiment']:.1%} (win rate: {sentiment_perf['win_rate']:.1%})")
            print(f"   Quantum: {self.current_weights['quantum']:.1%} (win rate: {quantum_perf['win_rate']:.1%})")
            
        except Exception as e:
            print(f"❌ Weight adaptation error: {e}")
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """Get complete simulation summary"""
        return {
            'simulators': {
                'traditional': {
                    'performance': self.traditional_sim.calculate_performance(),
                    'current_weight': round(self.current_weights['traditional'], 3),
                    'total_trades': self.traditional_sim.total_trades,
                    'balance': round(self.traditional_sim.balance, 2),
                    'recent_trades': self.traditional_sim.trades[-5:]
                },
                'sentiment': {
                    'performance': self.sentiment_sim.calculate_performance(),
                    'current_weight': round(self.current_weights['sentiment'], 3),
                    'total_trades': self.sentiment_sim.total_trades,
                    'balance': round(self.sentiment_sim.balance, 2),
                    'recent_trades': self.sentiment_sim.trades[-5:]
                },
                'quantum': {
                    'performance': self.quantum_sim.calculate_performance(),
                    'current_weight': round(self.current_weights['quantum'], 3),
                    'total_trades': self.quantum_sim.total_trades,
                    'balance': round(self.quantum_sim.balance, 2),
                    'recent_trades': self.quantum_sim.trades[-5:]
                }
            },
            'current_weights': dict(self.current_weights),
            'weight_history': self.weight_history[-10:],
            'last_adaptation': self.last_adaptation,
            'total_simulations': len(self.weight_history)
        }

# Global adaptive weight manager
adaptive_manager = AdaptiveWeightManager()