# enhanced_ml_strategy.py - ML-Enhanced Trading Strategy
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
import pandas as pd

class MLEnhancedStrategy:
    def __init__(self, model_path='models/trading_model.pkl'):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.feature_columns = [
            'price_change_2h', 'volume_ratio', 'volatility', 'rsi',
            'sma_5_20_ratio', 'bb_position', 'macd_signal', 'volume_sma_ratio',
            'price_momentum', 'support_resistance_score'
        ]
        
        # Load existing model if available
        self.load_model()
    
    def extract_ml_features(self, klines):
        """Extract machine learning features from klines data"""
        if len(klines) < 120:
            return None
            
        # Convert to pandas for easier analysis
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        
        # Basic price features
        current_price = df['close'].iloc[-1]
        price_2h_ago = df['close'].iloc[0]
        price_change_2h = ((current_price - price_2h_ago) / price_2h_ago) * 100
        
        # Volume features
        volume_sma_20 = df['volume'].rolling(20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / volume_sma_20 if volume_sma_20 > 0 else 1
        volume_sma_ratio = df['volume'].rolling(5).mean().iloc[-1] / volume_sma_20 if volume_sma_20 > 0 else 1
        
        # Technical indicators
        volatility = df['close'].rolling(20).std().iloc[-1] / current_price
        rsi = self.calculate_rsi(df['close'])
        
        # Moving averages
        sma_5 = df['close'].rolling(5).mean().iloc[-1]
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_5_20_ratio = sma_5 / sma_20 if sma_20 > 0 else 1
        
        # Bollinger Bands
        bb_upper, bb_lower = self.calculate_bollinger_bands(df['close'])
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        
        # MACD
        macd_signal = self.calculate_macd_signal(df['close'])
        
        # Price momentum
        price_momentum = self.calculate_momentum(df['close'], periods=[3, 5, 10])
        
        # Support/Resistance
        support_resistance_score = self.calculate_support_resistance_score(df)
        
        features = {
            'price_change_2h': price_change_2h,
            'volume_ratio': volume_ratio,
            'volatility': volatility,
            'rsi': rsi,
            'sma_5_20_ratio': sma_5_20_ratio,
            'bb_position': bb_position,
            'macd_signal': macd_signal,
            'volume_sma_ratio': volume_sma_ratio,
            'price_momentum': price_momentum,
            'support_resistance_score': support_resistance_score
        }
        
        return features
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50
    
    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper.iloc[-1], lower.iloc[-1]
    
    def calculate_macd_signal(self, prices):
        """Calculate MACD signal"""
        exp1 = prices.ewm(span=12).mean()
        exp2 = prices.ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        return histogram.iloc[-1] if not histogram.empty else 0
    
    def calculate_momentum(self, prices, periods=[3, 5, 10]):
        """Calculate price momentum across multiple periods"""
        momentum_scores = []
        for period in periods:
            if len(prices) >= period:
                momentum = (prices.iloc[-1] / prices.iloc[-period] - 1) * 100
                momentum_scores.append(momentum)
        return np.mean(momentum_scores) if momentum_scores else 0
    
    def calculate_support_resistance_score(self, df):
        """Calculate support/resistance score based on recent price levels"""
        current_price = df['close'].iloc[-1]
        recent_highs = df['high'].rolling(10).max().dropna()
        recent_lows = df['low'].rolling(10).min().dropna()
        
        # Find nearby support/resistance levels
        support_levels = recent_lows[abs(recent_lows - current_price) / current_price < 0.02]
        resistance_levels = recent_highs[abs(recent_highs - current_price) / current_price < 0.02]
        
        # Score based on proximity to key levels
        score = 0
        if len(support_levels) > 0:
            score += 0.3  # Near support
        if len(resistance_levels) > 0:
            score -= 0.3  # Near resistance
            
        return score
    
    def get_ml_prediction(self, klines):
        """Get ML model prediction for trading signal"""
        if self.model is None:
            return None, 0.5  # Default confidence if no model
            
        features = self.extract_ml_features(klines)
        if features is None:
            return None, 0.5
            
        # Prepare feature vector
        feature_vector = np.array([[features[col] for col in self.feature_columns]])
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Get prediction and probability
        prediction = self.model.predict(feature_vector_scaled)[0]
        probabilities = self.model.predict_proba(feature_vector_scaled)[0]
        confidence = max(probabilities)
        
        # Convert prediction to signal
        signal_map = {0: "HOLD", 1: "BUY_LONG", 2: "BUY_SHORT"}
        signal = signal_map.get(prediction, "HOLD")
        
        return signal, confidence
    
    def combine_with_traditional_strategy(self, klines, traditional_signal, traditional_confidence):
        """Combine ML prediction with traditional strategy"""
        ml_signal, ml_confidence = self.get_ml_prediction(klines)
        
        if ml_signal is None:
            # Use traditional strategy if ML unavailable
            return traditional_signal, traditional_confidence
        
        # Weighted combination
        ml_weight = 0.4
        traditional_weight = 0.6
        
        # Signal agreement bonus
        agreement_bonus = 0.1 if ml_signal == traditional_signal else -0.1
        
        # Combined confidence
        combined_confidence = (
            ml_confidence * ml_weight + 
            traditional_confidence * traditional_weight + 
            agreement_bonus
        )
        combined_confidence = max(0.1, min(1.0, combined_confidence))
        
        # Final signal decision
        if ml_signal == traditional_signal:
            final_signal = ml_signal
        elif combined_confidence > 0.7:
            # High confidence - use traditional
            final_signal = traditional_signal
        else:
            # Low confidence - be conservative
            final_signal = "HOLD"
            
        return final_signal, combined_confidence
    
    def train_model(self, historical_data, labels):
        """Train ML model on historical data"""
        print("🧠 Training ML model...")
        
        # Prepare training data
        X = []
        y = labels
        
        for klines in historical_data:
            features = self.extract_ml_features(klines)
            if features:
                X.append([features[col] for col in self.feature_columns])
        
        if len(X) < 50:
            print("❌ Insufficient training data")
            return False
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_scaled, y)
        
        # Save model
        self.save_model()
        
        # Print feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("📊 Feature Importance:")
        print(feature_importance)
        
        return True
    
    def save_model(self):
        """Save trained model and scaler"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns
        }, self.model_path)
        print(f"💾 Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model and scaler"""
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.scaler = data['scaler']
                self.feature_columns = data['feature_columns']
                print(f"📂 Model loaded from {self.model_path}")
                return True
            except Exception as e:
                print(f"❌ Error loading model: {e}")
        return False

# Integration with existing strategy
def check_breakout_ml_enhanced(klines, ml_strategy=None):
    """Enhanced breakout strategy with ML integration"""
    from strategy import check_breakout_enhanced, get_strategy_confidence
    
    # Get traditional signals
    traditional_signal = check_breakout_enhanced(klines)
    traditional_confidence = get_strategy_confidence(klines)
    
    if ml_strategy is None:
        return traditional_signal, traditional_confidence
    
    # Combine with ML
    final_signal, final_confidence = ml_strategy.combine_with_traditional_strategy(
        klines, traditional_signal, traditional_confidence
    )
    
    return final_signal, final_confidence

# Global ML strategy instance
ml_strategy = MLEnhancedStrategy()

def get_ml_enhanced_signal(klines):
    """Convenience function for ML-enhanced signals"""
    return check_breakout_ml_enhanced(klines, ml_strategy)
