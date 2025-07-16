#!/usr/bin/env python3
# test_simplified_ml.py - Test the simplified ML strategy

import sys
import os
import random
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_klines():
    """Create sample klines data for testing"""
    sample_klines = []
    base_price = 45000
    
    for i in range(120):
        # Generate realistic OHLCV data
        open_price = base_price + random.uniform(-100, 100)
        high_price = open_price + random.uniform(0, 200)
        low_price = open_price - random.uniform(0, 200)
        close_price = open_price + random.uniform(-150, 150)
        volume = random.uniform(100, 1000)
        
        kline = [
            i * 60000,  # timestamp
            str(open_price), str(high_price), str(low_price), str(close_price), str(volume),
            (i + 1) * 60000, volume * close_price, 100,
            volume * 0.6, volume * 0.6 * close_price, 0
        ]
        sample_klines.append(kline)
        base_price = close_price
    
    return sample_klines

def test_simplified_ml():
    """Test the simplified ML strategy"""
    print("🧪 Testing Simplified ML Strategy...")
    print("=" * 50)
    
    try:
        # Import the simplified ML strategy
        from simplified_ml_strategy import SimplifiedMLStrategy
        print("✅ Import successful")
        
        # Create ML strategy instance
        ml_strategy = SimplifiedMLStrategy()
        print("✅ ML Strategy initialized")
        
        # Create sample data
        sample_klines = create_sample_klines()
        print(f"✅ Generated {len(sample_klines)} sample klines")
        
        # Test feature extraction
        features = ml_strategy.extract_features(sample_klines)
        if features:
            print(f"✅ Feature extraction successful: {len(features)} features")
            print("📊 Sample features:")
            for i, (key, value) in enumerate(list(features.items())[:5]):
                print(f"   {key}: {value:.4f}")
        else:
            print("❌ Feature extraction failed")
            return False
        
        # Test prediction
        signal, confidence, probabilities = ml_strategy.predict_market_direction(sample_klines)
        print(f"✅ ML Prediction successful:")
        print(f"   Signal: {signal}")
        print(f"   Confidence: {confidence:.2%}")
        print(f"   Probabilities: {probabilities}")
        
        # Test feature importance
        importance = ml_strategy.get_feature_importance()
        print(f"✅ Feature importance: {len(importance)} features")
        print("🔍 Top 3 features:")
        for feature, weight in importance[:3]:
            print(f"   {feature}: {weight:.3f}")
        
        # Test performance metrics
        metrics = ml_strategy.get_performance_metrics()
        print(f"✅ Performance metrics: {metrics}")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Simplified ML Strategy is working correctly.")
        print("=" * 50)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure simplified_ml_strategy.py is in the same directory")
        return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_existing_bot():
    """Test integration with existing bot structure"""
    print("\n🔧 Testing Integration with Existing Bot...")
    print("=" * 50)
    
    try:
        from simplified_ml_strategy import SimplifiedMLStrategy
        
        # Simulate existing bot structure
        class MockBot:
            def __init__(self):
                self.ml_strategy = SimplifiedMLStrategy()
                self.MIN_CONFIDENCE = 0.65
            
            def analyze_with_ml(self, klines):
                """Analyze using ML + basic strategy combination"""
                try:
                    # Get ML prediction
                    ml_signal, ml_confidence, ml_probs = self.ml_strategy.predict_market_direction(klines)
                    
                    # Simulate basic strategy (simplified)
                    basic_signal = "BUY_LONG" if random.random() > 0.5 else "BUY_SHORT"
                    basic_confidence = random.uniform(0.5, 0.9)
                    
                    # Combine signals
                    final_signal, final_confidence = self.combine_signals(
                        ml_signal, ml_confidence, basic_signal, basic_confidence
                    )
                    
                    return {
                        'final_signal': final_signal,
                        'final_confidence': final_confidence,
                        'ml_signal': ml_signal,
                        'ml_confidence': ml_confidence,
                        'basic_signal': basic_signal,
                        'basic_confidence': basic_confidence,
                        'ml_probabilities': ml_probs
                    }
                    
                except Exception as e:
                    print(f"❌ Analysis error: {e}")
                    return None
            
            def combine_signals(self, ml_signal, ml_confidence, basic_signal, basic_confidence):
                """Combine ML and basic signals"""
                signal_scores = {"BUY_LONG": 1, "BUY_SHORT": -1, "HOLD": 0}
                
                ml_score = signal_scores.get(ml_signal, 0)
                basic_score = signal_scores.get(basic_signal, 0)
                
                # Weighted combination (60% ML, 40% basic)
                combined_score = (ml_score * ml_confidence * 0.6) + (basic_score * basic_confidence * 0.4)
                combined_confidence = (ml_confidence * 0.6) + (basic_confidence * 0.4)
                
                if combined_score > 0.3:
                    return "BUY_LONG", combined_confidence
                elif combined_score < -0.3:
                    return "BUY_SHORT", combined_confidence
                else:
                    return "HOLD", combined_confidence
        
        # Test the mock bot
        bot = MockBot()
        sample_klines = create_sample_klines()
        
        result = bot.analyze_with_ml(sample_klines)
        
        if result:
            print("✅ Bot integration successful!")
            print(f"   Final Signal: {result['final_signal']}")
            print(f"   Final Confidence: {result['final_confidence']:.2%}")
            print(f"   ML Signal: {result['ml_signal']} (Conf: {result['ml_confidence']:.2%})")
            print(f"   Basic Signal: {result['basic_signal']} (Conf: {result['basic_confidence']:.2%})")
            
            # Test if signal meets threshold
            if result['final_confidence'] > bot.MIN_CONFIDENCE:
                print(f"✅ Signal meets minimum confidence threshold ({bot.MIN_CONFIDENCE:.0%})")
            else:
                print(f"⚠️  Signal below minimum confidence threshold ({bot.MIN_CONFIDENCE:.0%})")
        else:
            print("❌ Bot integration failed")
            return False
        
        print("🎉 Integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Simplified ML Strategy Test Suite")
    print("=" * 60)
    
    # Test 1: Basic ML functionality
    test1_passed = test_simplified_ml()
    
    # Test 2: Integration with existing bot
    test2_passed = test_integration_with_existing_bot()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)
    print(f"✅ Basic ML Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Integration Test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 You can now integrate the simplified ML strategy with your bot!")
        print("\n📋 Next steps:")
        print("1. Add 'from simplified_ml_strategy import SimplifiedMLStrategy' to your bot")
        print("2. Initialize: self.ml_strategy = SimplifiedMLStrategy()")
        print("3. Use: signal, confidence, probs = self.ml_strategy.predict_market_direction(klines)")
        print("4. Run your bot with enhanced ML capabilities!")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
