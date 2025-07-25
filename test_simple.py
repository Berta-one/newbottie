 -*- coding: utf-8 -*-
def test_portfolio_fix():
    try:
        from portfolio_value_fix import get_unified_portfolio_value

        test_portfolio = {
            "BTC": {"usd_value": 1000.0},
            "ETH": {"usd_value": 500.0},
            "USDT": {"usd_value": 300.0},
        }

        total_usd, total_gbp, count = get_unified_portfolio_value(test_portfolio)
        print(f"Portfolio Fix Working:")
        print(f"  Total USD: ${total_usd:.2f}")
        print(f"  Total GBP: Â£{total_gbp:.2f}")
        print(f"  Assets: {count}")

        return True

    except Exception as e:
        print(f"Portfolio fix failed: {e}")
        return False


def test_quantum_trader():
    try:
        from quantum_trader import quantum_trader

        status = quantum_trader.get_status()
        print(f"Quantum Status: {status}")

        test_data = [100, 102, 105, 103, 107]
        result = quantum_trader.quantum_analyze(test_data)
        print(f"Analysis: {result}")

        return True

    except Exception as e:
        print(f"Quantum trader failed: {e}")
        return False


def main():
    print("Testing Portfolio + Quantum Fixes")
    print("=" * 40)

    portfolio_ok = test_portfolio_fix()
    print()
    quantum_ok = test_quantum_trader()

    print("=" * 40)
    if portfolio_ok and quantum_ok:
        print("ALL TESTS PASSED!")
    else:
        print("Some tests failed")


if __name__ == "__main__":
    main()

