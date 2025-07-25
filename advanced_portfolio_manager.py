 -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import logging


@dataclass
class Position:
    symbol: str
    strategy: str
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    trailing_stop: float
    max_hold_time: int
    confidence: float
    risk_amount: float
    current_pnl: float = 0.0
    max_pnl: float = 0.0
    min_pnl: float = 0.0


@dataclass
class StrategyAllocation:
    strategy_name: str
    allocation_percent: float
    max_positions: int
    risk_per_trade: float
    active_positions: List[Position]


class AdvancedPortfolioManager:
    def __init__(self, total_capital: float, max_portfolio_risk: float = 0.02):
        self.total_capital = total_capital
        self.available_capital = total_capital
        self.max_portfolio_risk = max_portfolio_risk
        self.positions: Dict[str, Position] = {}
        self.strategy_allocations: Dict[str, StrategyAllocation] = {}
        self.performance_metrics = {}
        self.trade_history = []
        self._initialize_strategies()

    # ...existing code for all methods and logic...
    # (Paste the full class code you provided here)

