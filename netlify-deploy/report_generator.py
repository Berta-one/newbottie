#!/usr/bin/env python3
"""
Report Generator Service for Trading Dashboard
Generates comprehensive reports for trading, ML performance, backtesting, and sentiment analysis.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import requests

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from reporting import generate_basic_report, save_trade_log_json, save_trade_log_csv

logger = logging.getLogger("ReportGenerator")
logging.basicConfig(level=logging.INFO)

@dataclass
class ReportRequest:
    report_type: str
    time_range: str
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class ReportResult:
    id: str
    type: str
    title: str
    created_at: str
    summary: Dict[str, Any]
    data: Dict[str, Any]
    status: str
    file_path: Optional[str] = None

class ReportGenerator:
    def __init__(self, api_url: str = "https://bottie-1.onrender.com/api"):
        self.api_url = api_url.rstrip('/')
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
    async def generate_report(self, request: ReportRequest) -> ReportResult:
        """Generate a report based on the request type and parameters"""
        logger.info(f"Generating {request.report_type} report for {request.time_range}")
        
        report_id = f"{request.report_type}_{int(datetime.now().timestamp())}"
        title = request.name or f"{request.report_type.title()} Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            if request.report_type == "trading":
                return await self.generate_trading_report(report_id, title, request.time_range)
            elif request.report_type == "ml":
                return await self.generate_ml_report(report_id, title, request.time_range)
            elif request.report_type == "backtest":
                return await self.generate_backtest_report(report_id, title, request.time_range, request.parameters)
            elif request.report_type == "sentiment":
                return await self.generate_sentiment_report(report_id, title, request.time_range)
            elif request.report_type == "portfolio":
                return await self.generate_portfolio_report(report_id, title, request.time_range)
            else:
                raise ValueError(f"Unknown report type: {request.report_type}")
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ReportResult(
                id=report_id,
                type=request.report_type,
                title=title,
                created_at=datetime.now().isoformat(),
                summary={"error": str(e)},
                data={},
                status="failed"
            )
    
    async def generate_trading_report(self, report_id: str, title: str, time_range: str) -> ReportResult:
        """Generate a comprehensive trading performance report"""
        try:
            # Fetch trading data from API
            trades_data = await self.fetch_trading_data(time_range)
            
            if not trades_data:
                # Generate sample data for demonstration
                trades_data = self.generate_sample_trades(time_range)
            
            # Calculate summary statistics
            summary = generate_basic_report(trades_data)
            
            # Add additional metrics
            summary.update({
                "time_range": time_range,
                "best_trade": max(trades_data, key=lambda x: x.get("profit", 0))["profit"] if trades_data else 0,
                "worst_trade": min(trades_data, key=lambda x: x.get("profit", 0))["profit"] if trades_data else 0,
                "total_volume": sum(t.get("qty", 0) * t.get("price", 0) for t in trades_data),
                "unique_symbols": len(set(t.get("symbol", "") for t in trades_data))
            })
            
            # Save detailed trade log
            file_path = self.reports_dir / f"{report_id}_trades.json"
            save_trade_log_json(trades_data, file_path)
            
            # Also save as CSV for easy analysis
            csv_path = self.reports_dir / f"{report_id}_trades.csv"
            save_trade_log_csv(trades_data, csv_path)
            
            return ReportResult(
                id=report_id,
                type="trading",
                title=title,
                created_at=datetime.now().isoformat(),
                summary=summary,
                data={
                    "trades": trades_data[:50],  # Limit for frontend display
                    "total_trades": len(trades_data),
                    "performance_metrics": self.calculate_performance_metrics(trades_data)
                },
                status="completed",
                file_path=str(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error generating trading report: {e}")
            raise
    
    async def generate_ml_report(self, report_id: str, title: str, time_range: str) -> ReportResult:
        """Generate ML performance analysis report"""
        try:
            # Fetch ML performance data
            ml_data = await self.fetch_ml_performance_data(time_range)
            
            if not ml_data:
                # Generate sample ML performance data
                ml_data = self.generate_sample_ml_data(time_range)
            
            summary = {
                "accuracy": ml_data.get("accuracy", 0),
                "precision": ml_data.get("precision", 0),
                "recall": ml_data.get("recall", 0),
                "f1_score": ml_data.get("f1_score", 0),
                "brier_score": ml_data.get("brier_score", 0),
                "sample_count": ml_data.get("sample_count", 0),
                "quantum_importance": ml_data.get("quantum_importance", 0),
                "model_version": ml_data.get("model_version", "1.0")
            }
            
            # Save ML report data
            file_path = self.reports_dir / f"{report_id}_ml_performance.json"
            with open(file_path, 'w') as f:
                json.dump(ml_data, f, indent=2)
            
            return ReportResult(
                id=report_id,
                type="ml",
                title=title,
                created_at=datetime.now().isoformat(),
                summary=summary,
                data=ml_data,
                status="completed",
                file_path=str(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error generating ML report: {e}")
            raise
    
    async def generate_backtest_report(self, report_id: str, title: str, time_range: str, parameters: Dict[str, Any] = None) -> ReportResult:
        """Generate backtesting results report"""
        try:
            # Run backtest with specified parameters
            backtest_data = await self.run_backtest(time_range, parameters or {})
            
            if not backtest_data:
                # Generate sample backtest data
                backtest_data = self.generate_sample_backtest_data(time_range, parameters)
            
            summary = {
                "total_return": backtest_data.get("total_return", 0),
                "annualized_return": backtest_data.get("annualized_return", 0),
                "sharpe_ratio": backtest_data.get("sharpe_ratio", 0),
                "max_drawdown": backtest_data.get("max_drawdown", 0),
                "win_rate": backtest_data.get("win_rate", 0),
                "profit_factor": backtest_data.get("profit_factor", 0),
                "total_trades": backtest_data.get("total_trades", 0)
            }
            
            # Save backtest results
            file_path = self.reports_dir / f"{report_id}_backtest.json"
            with open(file_path, 'w') as f:
                json.dump(backtest_data, f, indent=2)
            
            return ReportResult(
                id=report_id,
                type="backtest",
                title=title,
                created_at=datetime.now().isoformat(),
                summary=summary,
                data=backtest_data,
                status="completed",
                file_path=str(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error generating backtest report: {e}")
            raise
    
    async def generate_sentiment_report(self, report_id: str, title: str, time_range: str) -> ReportResult:
        """Generate sentiment analysis report"""
        try:
            # Fetch sentiment data
            sentiment_data = await self.fetch_sentiment_data(time_range)
            
            if not sentiment_data:
                # Generate sample sentiment data
                sentiment_data = self.generate_sample_sentiment_data(time_range)
            
            summary = {
                "avg_sentiment": sentiment_data.get("avg_sentiment", 0),
                "sentiment_volatility": sentiment_data.get("sentiment_volatility", 0),
                "positive_signals": sentiment_data.get("positive_signals", 0),
                "negative_signals": sentiment_data.get("negative_signals", 0),
                "neutral_signals": sentiment_data.get("neutral_signals", 0),
                "correlation_with_price": sentiment_data.get("correlation_with_price", 0),
                "data_sources": len(sentiment_data.get("sources", []))
            }
            
            # Save sentiment report
            file_path = self.reports_dir / f"{report_id}_sentiment.json"
            with open(file_path, 'w') as f:
                json.dump(sentiment_data, f, indent=2)
            
            return ReportResult(
                id=report_id,
                type="sentiment",
                title=title,
                created_at=datetime.now().isoformat(),
                summary=summary,
                data=sentiment_data,
                status="completed",
                file_path=str(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error generating sentiment report: {e}")
            raise
    
    async def generate_portfolio_report(self, report_id: str, title: str, time_range: str) -> ReportResult:
        """Generate portfolio overview report"""
        try:
            # Fetch portfolio data
            portfolio_data = await self.fetch_portfolio_data(time_range)
            
            if not portfolio_data:
                # Generate sample portfolio data
                portfolio_data = self.generate_sample_portfolio_data(time_range)
            
            summary = {
                "total_value": portfolio_data.get("total_value", 0),
                "total_pnl": portfolio_data.get("total_pnl", 0),
                "pnl_percentage": portfolio_data.get("pnl_percentage", 0),
                "active_positions": len(portfolio_data.get("positions", [])),
                "top_performer": portfolio_data.get("top_performer", "N/A"),
                "worst_performer": portfolio_data.get("worst_performer", "N/A"),
                "diversification_score": portfolio_data.get("diversification_score", 0)
            }
            
            # Save portfolio report
            file_path = self.reports_dir / f"{report_id}_portfolio.json"
            with open(file_path, 'w') as f:
                json.dump(portfolio_data, f, indent=2)
            
            return ReportResult(
                id=report_id,
                type="portfolio",
                title=title,
                created_at=datetime.now().isoformat(),
                summary=summary,
                data=portfolio_data,
                status="completed",
                file_path=str(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error generating portfolio report: {e}")
            raise
    
    async def fetch_trading_data(self, time_range: str) -> List[Dict[str, Any]]:
        """Fetch trading data from the API"""
        try:
            response = requests.get(f"{self.api_url}/trading/history", 
                                  params={"time_range": time_range}, 
                                  timeout=10)
            if response.ok:
                data = response.json()
                return data.get("trades", [])
        except Exception as e:
            logger.warning(f"Could not fetch trading data: {e}")
        return []
    
    async def fetch_ml_performance_data(self, time_range: str) -> Dict[str, Any]:
        """Fetch ML performance data from the API"""
        try:
            response = requests.get(f"{self.api_url}/ml/performance", 
                                  params={"time_range": time_range}, 
                                  timeout=10)
            if response.ok:
                return response.json()
        except Exception as e:
            logger.warning(f"Could not fetch ML data: {e}")
        return {}
    
    async def run_backtest(self, time_range: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run a backtest with specified parameters"""
        try:
            response = requests.post(f"{self.api_url}/backtest/run", 
                                   json={"time_range": time_range, **parameters}, 
                                   timeout=30)
            if response.ok:
                return response.json()
        except Exception as e:
            logger.warning(f"Could not run backtest: {e}")
        return {}
    
    async def fetch_sentiment_data(self, time_range: str) -> Dict[str, Any]:
        """Fetch sentiment analysis data"""
        try:
            response = requests.get(f"{self.api_url}/sentiment/analysis", 
                                  params={"time_range": time_range}, 
                                  timeout=10)
            if response.ok:
                return response.json()
        except Exception as e:
            logger.warning(f"Could not fetch sentiment data: {e}")
        return {}
    
    async def fetch_portfolio_data(self, time_range: str) -> Dict[str, Any]:
        """Fetch portfolio data"""
        try:
            response = requests.get(f"{self.api_url}/portfolio/overview", 
                                  params={"time_range": time_range}, 
                                  timeout=10)
            if response.ok:
                return response.json()
        except Exception as e:
            logger.warning(f"Could not fetch portfolio data: {e}")
        return {}
    
    def generate_sample_trades(self, time_range: str) -> List[Dict[str, Any]]:
        """Generate sample trading data for demonstration"""
        count = self.get_sample_count_for_range(time_range)
        trades = []
        symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'MATIC/USDT']
        
        for i in range(count):
            timestamp = datetime.now() - timedelta(minutes=i * 30)
            symbol = np.random.choice(symbols)
            side = np.random.choice(['BUY', 'SELL'])
            qty = np.random.uniform(0.1, 10.0)
            price = np.random.uniform(100, 50000)
            profit = np.random.normal(0, 50)  # Normal distribution around 0
            
            trades.append({
                "ts": timestamp.isoformat(),
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price,
                "profit": profit,
                "fee": abs(profit) * 0.001  # Small fee
            })
        
        return trades
    
    def generate_sample_ml_data(self, time_range: str) -> Dict[str, Any]:
        """Generate sample ML performance data"""
        return {
            "accuracy": np.random.uniform(0.65, 0.95),
            "precision": np.random.uniform(0.6, 0.9),
            "recall": np.random.uniform(0.6, 0.9),
            "f1_score": np.random.uniform(0.6, 0.9),
            "brier_score": np.random.uniform(0.05, 0.25),
            "sample_count": np.random.randint(1000, 10000),
            "quantum_importance": np.random.uniform(0.1, 0.8),
            "model_version": "2.1.0",
            "feature_importance": {
                "price_momentum": np.random.uniform(0.1, 0.9),
                "volume_trend": np.random.uniform(0.1, 0.9),
                "sentiment_score": np.random.uniform(0.1, 0.9),
                "technical_indicators": np.random.uniform(0.1, 0.9),
                "quantum_features": np.random.uniform(0.1, 0.9),
                "market_regime": np.random.uniform(0.1, 0.9)
            },
            "confusion_matrix": [[85, 15], [12, 88]],
            "training_time": f"{np.random.randint(5, 120)} minutes",
            "last_updated": datetime.now().isoformat()
        }
    
    def generate_sample_backtest_data(self, time_range: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sample backtesting data"""
        initial_capital = parameters.get("initial_capital", 10000)
        total_return_pct = np.random.uniform(-30, 150)  # -30% to +150%
        
        return {
            "strategy_name": parameters.get("strategy", "Quantum Grid Trading"),
            "time_range": time_range,
            "initial_capital": initial_capital,
            "final_capital": initial_capital * (1 + total_return_pct / 100),
            "total_return": total_return_pct,
            "annualized_return": total_return_pct * (365 / self.get_days_for_range(time_range)),
            "sharpe_ratio": np.random.uniform(0.5, 3.5),
            "max_drawdown": -np.random.uniform(5, 25),
            "win_rate": np.random.uniform(0.45, 0.75),
            "profit_factor": np.random.uniform(1.1, 2.8),
            "total_trades": np.random.randint(50, 500),
            "avg_trade_duration": f"{np.random.randint(30, 480)} minutes",
            "best_trade": np.random.uniform(50, 500),
            "worst_trade": -np.random.uniform(50, 300),
            "parameters": parameters,
            "equity_curve": self.generate_equity_curve(initial_capital, total_return_pct, 100),
            "monthly_returns": self.generate_monthly_returns(12),
            "completed_at": datetime.now().isoformat()
        }
    
    def generate_sample_sentiment_data(self, time_range: str) -> Dict[str, Any]:
        """Generate sample sentiment analysis data"""
        signals = np.random.randint(50, 200, 3)  # positive, negative, neutral
        
        return {
            "time_range": time_range,
            "avg_sentiment": np.random.uniform(-0.3, 0.7),
            "sentiment_volatility": np.random.uniform(0.1, 0.5),
            "positive_signals": int(signals[0]),
            "negative_signals": int(signals[1]),
            "neutral_signals": int(signals[2]),
            "correlation_with_price": np.random.uniform(-0.2, 0.6),
            "sources": ["Twitter", "Reddit", "News", "Telegram", "Discord"],
            "top_keywords": ["bullish", "moon", "dip", "hodl", "pump", "dump"],
            "sentiment_by_source": {
                "Twitter": np.random.uniform(-0.5, 0.8),
                "Reddit": np.random.uniform(-0.3, 0.6),
                "News": np.random.uniform(-0.2, 0.4),
                "Telegram": np.random.uniform(-0.4, 0.9),
                "Discord": np.random.uniform(-0.3, 0.7)
            },
            "hourly_sentiment": [np.random.uniform(-0.5, 0.8) for _ in range(24)],
            "last_updated": datetime.now().isoformat()
        }
    
    def generate_sample_portfolio_data(self, time_range: str) -> Dict[str, Any]:
        """Generate sample portfolio data"""
        positions = []
        symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT']
        total_value = 0
        
        for symbol in symbols[:np.random.randint(3, 6)]:
            qty = np.random.uniform(0.1, 5.0)
            avg_price = np.random.uniform(100, 50000)
            current_price = avg_price * np.random.uniform(0.8, 1.3)
            pnl = (current_price - avg_price) * qty
            
            positions.append({
                "symbol": symbol,
                "quantity": qty,
                "avg_price": avg_price,
                "current_price": current_price,
                "market_value": current_price * qty,
                "pnl": pnl,
                "pnl_percentage": (pnl / (avg_price * qty)) * 100
            })
            total_value += current_price * qty
        
        total_pnl = sum(p["pnl"] for p in positions)
        best_position = max(positions, key=lambda x: x["pnl_percentage"]) if positions else None
        worst_position = min(positions, key=lambda x: x["pnl_percentage"]) if positions else None
        
        return {
            "time_range": time_range,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "pnl_percentage": (total_pnl / total_value) * 100 if total_value > 0 else 0,
            "positions": positions,
            "active_positions": len(positions),
            "top_performer": best_position["symbol"] if best_position else "N/A",
            "worst_performer": worst_position["symbol"] if worst_position else "N/A",
            "diversification_score": min(1.0, len(positions) / 10),  # Simple diversification metric
            "allocation": {p["symbol"]: (p["market_value"] / total_value) * 100 for p in positions} if total_value > 0 else {},
            "last_updated": datetime.now().isoformat()
        }
    
    def calculate_performance_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate additional performance metrics"""
        if not trades:
            return {}
        
        profits = [t.get("profit", 0) for t in trades]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p < 0]
        
        return {
            "avg_winning_trade": np.mean(winning_trades) if winning_trades else 0,
            "avg_losing_trade": np.mean(losing_trades) if losing_trades else 0,
            "largest_win": max(profits) if profits else 0,
            "largest_loss": min(profits) if profits else 0,
            "consecutive_wins": self.calculate_max_consecutive(profits, lambda x: x > 0),
            "consecutive_losses": self.calculate_max_consecutive(profits, lambda x: x < 0),
            "profit_factor": abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else float('inf'),
            "expectancy": np.mean(profits) if profits else 0,
            "volatility": np.std(profits) if profits else 0
        }
    
    def calculate_max_consecutive(self, values: List[float], condition) -> int:
        """Calculate maximum consecutive occurrences of a condition"""
        max_consecutive = 0
        current_consecutive = 0
        
        for value in values:
            if condition(value):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def generate_equity_curve(self, initial_capital: float, total_return_pct: float, points: int) -> List[float]:
        """Generate a realistic equity curve"""
        returns = np.random.normal(total_return_pct / points / 100, 0.02, points)
        equity = [initial_capital]
        
        for ret in returns:
            equity.append(equity[-1] * (1 + ret))
        
        return equity
    
    def generate_monthly_returns(self, months: int) -> List[float]:
        """Generate monthly returns"""
        return [np.random.uniform(-15, 25) for _ in range(months)]
    
    def get_sample_count_for_range(self, time_range: str) -> int:
        """Get appropriate sample count based on time range"""
        range_counts = {
            "1h": 5,
            "24h": 20,
            "7d": 50,
            "30d": 100,
            "90d": 200,
            "1y": 500
        }
        return range_counts.get(time_range, 50)
    
    def get_days_for_range(self, time_range: str) -> int:
        """Get number of days for time range"""
        range_days = {
            "1h": 1/24,
            "24h": 1,
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365
        }
        return range_days.get(time_range, 30)

# CLI interface for manual report generation
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate trading reports")
    parser.add_argument("--type", required=True, choices=["trading", "ml", "backtest", "sentiment", "portfolio"])
    parser.add_argument("--range", default="24h", choices=["1h", "24h", "7d", "30d", "90d", "1y"])
    parser.add_argument("--name", help="Custom report name")
    parser.add_argument("--output", help="Output directory", default="reports")
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    request = ReportRequest(
        report_type=args.type,
        time_range=args.range,
        name=args.name
    )
    
    print(f"Generating {args.type} report for {args.range}...")
    result = await generator.generate_report(request)
    
    print(f"Report generated: {result.title}")
    print(f"Status: {result.status}")
    print(f"File: {result.file_path}")
    print(f"Summary: {json.dumps(result.summary, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())