# engine/portfolio_manager.py

import logging

class PortfolioManager:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.holdings = {}  # {symbol: {'quantity': float, 'avg_price': float}}
        self.logger = logging.getLogger(__name__)

    def update_balance(self, amount):
        self.balance += amount
        self.logger.info(f"Balance updated: ${self.balance:.2f}")

    def buy(self, symbol, price, quantity):
        cost = price * quantity
        if self.balance >= cost:
            self.balance -= cost
            if symbol not in self.holdings:
                self.holdings[symbol] = {'quantity': 0.0, 'avg_price': 0.0}
            position = self.holdings[symbol]
            total_cost = position['quantity'] * position['avg_price'] + cost
            position['quantity'] += quantity
            position['avg_price'] = total_cost / position['quantity']
            self.logger.info(f"Bought {quantity} {symbol} at {price}. New holding: {position}")
            return True
        else:
            self.logger.warning("Insufficient balance to execute buy.")
            return False

    def sell(self, symbol, price, quantity):
        if symbol in self.holdings and self.holdings[symbol]['quantity'] >= quantity:
            self.holdings[symbol]['quantity'] -= quantity
            proceeds = price * quantity
            self.balance += proceeds
            self.logger.info(f"Sold {quantity} {symbol} at {price}. New balance: {self.balance:.2f}")
            if self.holdings[symbol]['quantity'] == 0:
                del self.holdings[symbol]
            return True
        else:
            self.logger.warning("Insufficient holdings to execute sell.")
            return False

    def get_portfolio_value(self, current_prices: dict):
        value = self.balance
        for symbol, data in self.holdings.items():
            price = current_prices.get(symbol, 0)
            value += data['quantity'] * price
        return value

    def summary(self, current_prices: dict):
        summary_data = {
            "balance": self.balance,
            "positions": [],
            "total_value": self.get_portfolio_value(current_prices)
        }
        for symbol, data in self.holdings.items():
            price = current_prices.get(symbol, 0)
            summary_data["positions"].append({
                "symbol": symbol,
                "quantity": data['quantity'],
                "avg_price": data['avg_price'],
                "current_price": price,
                "value": data['quantity'] * price
            })
        return summary_data