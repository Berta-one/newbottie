 -*- coding: utf-8 -*-
def get_unified_portfolio_value(portfolio_data):
    if not portfolio_data:
        return 0.0, 0.0, 0

    total_usd = 0.0

    for asset, data in portfolio_data.items():
        if isinstance(data, dict):
            usd_value = 0.0

            if "usd_value" in data:
                usd_value = float(data["usd_value"])
            elif "value" in data:
                usd_value = float(data["value"])
            elif "market_value" in data:
                usd_value = float(data["market_value"])
            elif "balance" in data and "price_usd" in data:
                usd_value = float(data["balance"]) * float(data["price_usd"])

            total_usd += usd_value

    try:
        import requests

        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=5
        )
        gbp_rate = response.json()["rates"]["GBP"]
    except:
        gbp_rate = 0.79

    total_gbp = total_usd * gbp_rate
    return total_usd, total_gbp, len(portfolio_data)


def debug_portfolio_calculation(portfolio_data, location="Unknown"):
    print(f"Portfolio Debug [{location}]")

    if not portfolio_data:
        print("Portfolio data is empty")
        return 0.0

    total = 0.0
    for asset, data in portfolio_data.items():
        if isinstance(data, dict):
            usd_value = data.get("usd_value", 0)
            print(f"{asset}: ${usd_value:.2f}")
            total += float(usd_value)

    print(f"Total: ${total:.2f}")
    return total

