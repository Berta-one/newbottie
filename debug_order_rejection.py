 -*- coding: utf-8 -*-
# Binance Order Rejection Debugger
# This script diagnoses exactly why your orders are being rejected

import os
import json
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

load_dotenv()


def debug_order_rejection(symbol="BTCUSDT", quantity=0.001):
    """
    Comprehensive order rejection debugging
    """
    print("ðŸ” BINANCE ORDER REJECTION DEBUGGER")
    print("=" * 60)

    # Initialize client
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing API credentials")
        return

    # Start with testnet
    client = Client(api_key, api_secret, testnet=True)
    print(f"ðŸ§ª Testing with TESTNET for safety")

    try:
        # Step 1: Test connection and permissions
        print("\n1. Testing API Connection & Permissions...")
        account = client.get_account()
        print(f"   ✔️ Connected successfully")
        print(f"   Account Type: {account.get('accountType', 'Unknown')}")
        print(f"   Can Trade: {account.get('canTrade', False)}")
        print(f"   Can Withdraw: {account.get('canWithdraw', False)}")

        # Check API key permissions
        api_perms = []
        if account.get("canTrade"):
            api_perms.append("TRADING")
        if account.get("canWithdraw"):
            api_perms.append("WITHDRAWAL")
        print(
            f"   API Permissions: {', '.join(api_perms) if api_perms else 'READ-ONLY'}"
        )

        if not account.get("canTrade"):
            print("   ❌ CRITICAL: API key doesn't have TRADING permissions!")
            print("   ðŸ”§ FIX: Enable 'Spot & Margin Trading' in Binance API settings")
            return

        # Step 2: Check account balances
        print("\n2. Checking Account Balances...")
        balances = {
            b["asset"]: float(b["free"])
            for b in account["balances"]
            if float(b["free"]) > 0
        }

        print(f"   Available Assets: {list(balances.keys())}")
        usdt_balance = balances.get("USDT", 0)
        print(f"   USDT Balance: ${usdt_balance:,.2f}")

        if usdt_balance < 10:
            print("   ❌ CRITICAL: Insufficient USDT balance for trading!")
            print("   ðŸ”§ FIX: Add testnet funds from https://testnet.binance.vision/")
            if usdt_balance == 0:
                return

        # Step 3: Get symbol information and validate
        print(f"\n3. Validating Symbol: {symbol}...")
        exchange_info = client.get_exchange_info()
        symbol_info = next(
            (s for s in exchange_info["symbols"] if s["symbol"] == symbol), None
        )

        if not symbol_info:
            print(f"   ❌ Symbol {symbol} not found!")
            print("   ðŸ”§ Available symbols include: BTCUSDT, ETHUSDT, BNBUSDT, etc.")
            return

        print(f"   ✔️ Symbol found: {symbol}")
        print(f"   Status: {symbol_info['status']}")
        print(f"   Base Asset: {symbol_info['baseAsset']}")
        print(f"   Quote Asset: {symbol_info['quoteAsset']}")

        if symbol_info["status"] != "TRADING":
            print(f"   ❌ Symbol status is {symbol_info['status']}, not TRADING")
            return

        # Extract trading filters
        filters = {f["filterType"]: f for f in symbol_info["filters"]}

        # LOT_SIZE filter (quantity limits)
        lot_size = filters.get("LOT_SIZE", {})
        min_qty = float(lot_size.get("minQty", 0))
        max_qty = float(lot_size.get("maxQty", 0))
        step_size = float(lot_size.get("stepSize", 0))

        # MIN_NOTIONAL filter (minimum order value)
        min_notional = filters.get("MIN_NOTIONAL", {})
        min_notional_value = float(min_notional.get("minNotional", 0))

        # PRICE_FILTER
        price_filter = filters.get("PRICE_FILTER", {})
        min_price = float(price_filter.get("minPrice", 0))
        max_price = float(price_filter.get("maxPrice", 0))
        tick_size = float(price_filter.get("tickSize", 0))

        print(f"\n4. Symbol Trading Limits:")
        print(f"   Min Quantity: {min_qty}")
        print(f"   Max Quantity: {max_qty}")
        print(f"   Step Size: {step_size}")
        print(f"   Min Notional: ${min_notional_value}")
        print(f"   Min Price: ${min_price}")
        print(f"   Max Price: ${max_price}")
        print(f"   Tick Size: ${tick_size}")

        # Step 4: Validate proposed quantity
        print(f"\n5. Validating Quantity: {quantity}...")

        if quantity < min_qty:
            print(f"   ❌ Quantity {quantity} is below minimum {min_qty}")
            suggested_qty = min_qty
            print(f"   ðŸ”§ FIX: Use minimum quantity {suggested_qty}")
            quantity = suggested_qty

        if quantity > max_qty:
            print(f"   ❌ Quantity {quantity} is above maximum {max_qty}")
            return

        # Check step size compliance
        if step_size > 0:
            remainder = (quantity - min_qty) % step_size
            if remainder != 0:
                print(
                    f"   ❌ Quantity {quantity} doesn't comply with step size {step_size}"
                )
                # Round to nearest valid quantity
                steps = round((quantity - min_qty) / step_size)
                corrected_qty = min_qty + (steps * step_size)
                print(f"   ðŸ”§ FIX: Corrected quantity: {corrected_qty}")
                quantity = corrected_qty

        print(f"   ✔️ Final quantity: {quantity}")

        # Step 5: Check minimum notional value
        print(f"\n6. Checking Order Value...")
        current_price = float(client.get_symbol_ticker(symbol=symbol)["price"])
        order_value = quantity * current_price

        print(f"   Current {symbol} price: ${current_price:,.2f}")
        print(f"   Order value: ${order_value:.2f}")
        print(f"   Required minimum: ${min_notional_value}")

        if order_value < min_notional_value:
            print(
                f"   ❌ Order value ${order_value:.2f} below minimum ${min_notional_value}"
            )
            required_qty = min_notional_value / current_price
            print(f"   ðŸ”§ FIX: Need quantity of at least {required_qty:.8f}")
            quantity = required_qty
            order_value = quantity * current_price
            print(f"   ðŸ”§ Adjusted: quantity={quantity:.8f}, value=${order_value:.2f}")

        # Check if we have enough balance for this order
        required_usdt = order_value * 1.001  # Add small buffer for fees
        if usdt_balance < required_usdt:
            print(
                f"   ❌ Insufficient balance: need ${required_usdt:.2f}, have ${usdt_balance:.2f}"
            )
            max_affordable_qty = (
                usdt_balance * 0.99
            ) / current_price  # 99% to account for fees
            print(f"   ðŸ”§ FIX: Maximum affordable quantity: {max_affordable_qty:.8f}")
            return

        print(f"   ✔️ Order value and balance check passed")

        # Step 6: Test order placement (ONLY in testnet!)
        print(f"\n7. Testing Order Placement (TESTNET ONLY)...")

        try:
            # Create a small test order
            test_order = client.create_test_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity,
            )
            print("   ✔️ TEST ORDER SUCCESSFUL!")
            print("   ✔️ Your order parameters are valid")

            # Now try a real order if in testnet
            print(f"\n8. Placing REAL testnet order...")
            real_order = client.order_market_buy(symbol=symbol, quantity=quantity)

            print("   ðŸŽ‰ REAL ORDER SUCCESSFUL!")
            print(f"   Order ID: {real_order['orderId']}")
            print(f"   Status: {real_order['status']}")
            print(f"   Executed Qty: {real_order.get('executedQty', 'N/A')}")

            # Log the successful order
            with open("logs/successful_test_order.json", "w") as f:
                json.dump(real_order, f, indent=2)

            return True

        except BinanceAPIException as e:
            print(f"   ❌ ORDER REJECTED!")
            print(f"   Error Code: {e.code}")
            print(f"   Error Message: {e.message}")

            # Common error codes and fixes
            error_fixes = {
                -1013: "Invalid quantity - check decimal places and step size",
                -1021: "Order would immediately match and take - use limit order",
                -1022: "Reduce-Only order rejected - not allowed for new positions",
                -2010: "Insufficient balance",
                -1111: "Precision over maximum - reduce decimal places",
                -1116: "Invalid order type for symbol",
                -1003: "Unknown order type",
                -1015: "Too many orders - cancel some existing orders",
            }

            if e.code in error_fixes:
                print(f"   ðŸ”§ SUGGESTED FIX: {error_fixes[e.code]}")

            return False

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def test_multiple_symbols():
    """Test order validation for multiple common symbols"""
    print("\n" + "=" * 60)
    print("ðŸ§ª TESTING MULTIPLE SYMBOLS")
    print("=" * 60)

    test_symbols = [
        ("BTCUSDT", 0.001),
        ("ETHUSDT", 0.01),
        ("BNBUSDT", 0.1),
        ("ADAUSDT", 10.0),
        ("DOGEUSDT", 100.0),
    ]

    for symbol, qty in test_symbols:
        print(f"\nðŸ” Testing {symbol} with quantity {qty}...")
        try:
            success = debug_order_rejection(symbol, qty)
            if success:
                print(f"   ✔️ {symbol}: Working!")
            else:
                print(f"   ❌ {symbol}: Has issues")
        except Exception as e:
            print(f"   ❌ {symbol}: Error - {e}")


def quick_balance_check():
    """Quick check of current balances"""
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing API credentials")
        return

    client = Client(api_key, api_secret, testnet=True)

    try:
        account = client.get_account()
        balances = {
            b["asset"]: float(b["free"])
            for b in account["balances"]
            if float(b["free"]) > 0
        }

        print("💰 CURRENT TESTNET BALANCES:")
        for asset, balance in balances.items():
            if balance > 0.001:  # Only show meaningful balances
                print(f"   {asset}: {balance:,.8f}")

        if not balances:
            print("   No balances found - need testnet funds!")

    except Exception as e:
        print(f"❌ Error checking balances: {e}")


if __name__ == "__main__":
    print("ðŸš€ Choose an option:")
    print("1. Debug specific order rejection")
    print("2. Test multiple symbols")
    print("3. Quick balance check")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        symbol = input("Enter symbol (default BTCUSDT): ").strip() or "BTCUSDT"
        qty = input("Enter quantity (default 0.001): ").strip()
        qty = float(qty) if qty else 0.001
        debug_order_rejection(symbol, qty)
    elif choice == "2":
        test_multiple_symbols()
    elif choice == "3":
        quick_balance_check()
    else:
        print("Running default debug...")
        debug_order_rejection()

