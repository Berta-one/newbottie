# ml/agents/multi_agent.py

class BaseAgent:
    def __init__(self, name):
        self.name = name

    def act(self, observation):
        raise NotImplementedError

class TrendAgent(BaseAgent):
    def act(self, obs):
        return "buy" if obs['trend_score'] > 0.7 else "hold"

class MeanReversionAgent(BaseAgent):
    def act(self, obs):
        return "sell" if obs['price'] > obs['mean'] * 1.1 else "buy"

class RiskAgent(BaseAgent):
    def act(self, obs):
        return "hold" if obs['drawdown'] > 0.2 else "buy"

class MultiAgentTrader:
    def __init__(self):
        self.agents = [
            TrendAgent("Trend"),
            MeanReversionAgent("Reversion"),
            RiskAgent("Risk")
        ]

    def vote(self, observation):
        votes = [agent.act(observation) for agent in self.agents]
        return max(set(votes), key=votes.count)