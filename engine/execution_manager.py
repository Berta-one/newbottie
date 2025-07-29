# engine/execution_manager.py

import logging

class ExecutionManager:
    def __init__(self, mode='paper'):
        self.mode = mode
        self.logger = logging.getLogger(__name__)
        self.executed_orders = []

    def execute_orders(self, positions, prices):
        """
        positions: dict of asset -> amount
        prices: dict of asset -> current price
        """
        for asset, qty in positions.items():
            price = prices.get(asset)
            if price:
                trade_value = qty * price
                order = {
                    'asset': asset,
                    'qty': qty,
                    'price': price,
                    'value': trade_value,
                    'type': 'market',
                    'mode': self.mode
                }
                self.logger.info(f"Executed {self.mode} trade: {order}")
                self.executed_orders.append(order)
            else:
                self.logger.warning(f"No price for {asset}, skipping execution.")