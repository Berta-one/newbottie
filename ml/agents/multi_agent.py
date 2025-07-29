# ml/agents/multi_agent.py

import numpy as np
import logging

class BaseAgent:
    def __init__(self, name):
        self.name = name

    def act(self, observation):
        raise NotImplementedError("Each agent must implement its own act method.")

class TrendFollowingAgent(BaseAgent):
    def act(self, observation):
        # Simple moving average crossover
        short_ma = observation['short_ma']
        long_ma = observation['long_ma']
        if short_ma > long_ma:
            return 'buy'
        elif short_ma < long_ma:
            return 'sell'
        return 'hold'

class MeanReversionAgent(BaseAgent):
    def act(self, observation):
        # Mean reversion signal using z-score
        price = observation['price']
        mean = observation['mean']
        std = observation['std']
        z = (price - mean) / std if std > 0 else 0
        if z > 1:
            return 'sell'
        elif z < -1:
            return 'buy'
        return 'hold'

class RiskManagementAgent(BaseAgent):
    def act(self, observation):
        # Avoid trading in high volatility conditions
        volatility = observation['volatility']
        if volatility > observation.get('vol_threshold', 0.05):
            return 'hold'
        return 'pass'  # defer to other agents

class MultiAgentController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents = [
            TrendFollowingAgent("TrendAgent"),
            MeanReversionAgent("MeanRevertAgent"),
            RiskManagementAgent("RiskAgent")
        ]

    def decide(self, observation):
        votes = {"buy": 0, "sell": 0, "hold": 0}
        for agent in self.agents:
            action = agent.act(observation)
            if action in votes:
                votes[action] += 1
            self.logger.debug(f"{agent.name} voted: {action}")

        decision = max(votes, key=votes.get)
        self.logger.info(f"Multi-agent consensus: {decision.upper()} ({votes})")
        return decision