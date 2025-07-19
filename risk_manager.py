from adaptive_risk_system import AdaptiveRiskManager

class RiskManager(AdaptiveRiskManager):
    """Wrapper around AdaptiveRiskManager to provide a consistent API for the dashboard."""

    def _risk_below_position_limit(self, symbol: str, quantity: float) -> bool:
        """Basic risk validation placeholder – extend with real logic later."""
        # TODO: Implement position sizing check
        return True
