#!/usr/bin/env python3
"""
P&L Validation Tool for Trading Reports
Verifies P&L calculations against Binance data and detects potential errors.
"""

import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from pathlib import Path
import numpy as np

logger = logging.getLogger("PnLValidator")
logging.basicConfig(level=logging.INFO)

class PnLValidator:
    def __init__(self, api_url: str = "https://bottie-1.onrender.com/api"):
        self.api_url = api_url.rstrip('/')
        self.validation_results = {}
        
    def validate_pnl_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive P&L validation against multiple data sources
        """
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "report_id": report_data.get("id", "unknown"),
            "validation_status": "pending",
            "errors": [],
            "warnings": [],
            "checks_passed": 0,
            "total_checks": 0,
            "accuracy_score": 0.0,
            "detailed_results": {}
        }
        
        try:
            # Extract trades data
            trades = report_data.get("data", {}).get("trades", [])
            summary = report_data.get("summary", {})
            
            if not trades:
                validation_results["errors"].append("No trades data found in report")
                return validation_results
            
            # Run validation checks
            checks = [
                self.check_trade_data_integrity,
                self.check_fee_calculations,
                self.check_pnl_calculations,
                self.check_position_tracking,
                self.check_realized_unrealized_split,
                self.check_win_rate_calculation,
                self.cross_reference_binance_data,
                self.validate_cost_basis_logic
            ]
            
            for check in checks:
                try:
                    check_result = check(trades, summary)
                    validation_results["detailed_results"][check.__name__] = check_result
                    validation_results["total_checks"] += 1
                    
                    if check_result["passed"]:
                        validation_results["checks_passed"] += 1
                    else:
                        validation_results["errors"].extend(check_result.get("errors", []))
                        validation_results["warnings"].extend(check_result.get("warnings", []))
                        
                except Exception as e:
                    validation_results["errors"].append(f"Check {check.__name__} failed: {str(e)}")
                    validation_results["total_checks"] += 1
            
            # Calculate accuracy score
            if validation_results["total_checks"] > 0:
                validation_results["accuracy_score"] = (
                    validation_results["checks_passed"] / validation_results["total_checks"]
                ) * 100
            
            # Determine overall status
            if len(validation_results["errors"]) == 0:
                validation_results["validation_status"] = "passed"
            elif validation_results["accuracy_score"] >= 70:
                validation_results["validation_status"] = "passed_with_warnings"
            else:
                validation_results["validation_status"] = "failed"
                
        except Exception as e:
            validation_results["errors"].append(f"Validation process failed: {str(e)}")
            validation_results["validation_status"] = "error"
            
        return validation_results
    
    def check_trade_data_integrity(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Check for data integrity issues in trades"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        # Check for duplicate trades
        order_ids = [t.get("order_id") for t in trades if t.get("order_id")]
        if len(order_ids) != len(set(order_ids)):
            result["errors"].append("Duplicate order IDs found in trades data")
            result["passed"] = False
        
        # Check for missing required fields
        required_fields = ["symbol", "side", "qty", "price"]
        missing_fields = []
        
        for i, trade in enumerate(trades):
            for field in required_fields:
                if not trade.get(field):
                    missing_fields.append(f"Trade {i}: missing {field}")
        
        if missing_fields:
            result["warnings"].extend(missing_fields[:5])  # Limit to first 5
            if len(missing_fields) > 5:
                result["warnings"].append(f"... and {len(missing_fields) - 5} more missing fields")
        
        # Check for unrealistic values
        unrealistic_trades = []
        for i, trade in enumerate(trades):
            qty = float(trade.get("qty", 0))
            price = float(trade.get("price", 0))
            
            if qty <= 0 or price <= 0:
                unrealistic_trades.append(f"Trade {i}: invalid qty ({qty}) or price ({price})")
            elif price > 1000000:  # Unrealistically high price
                unrealistic_trades.append(f"Trade {i}: suspiciously high price ({price})")
        
        if unrealistic_trades:
            result["warnings"].extend(unrealistic_trades[:3])
            if len(unrealistic_trades) > 3:
                result["warnings"].append(f"... and {len(unrealistic_trades) - 3} more unrealistic trades")
        
        result["details"] = {
            "total_trades": len(trades),
            "unique_order_ids": len(set(order_ids)) if order_ids else 0,
            "trades_with_order_ids": len(order_ids),
            "missing_fields_count": len(missing_fields),
            "unrealistic_trades_count": len(unrealistic_trades)
        }
        
        return result
    
    def check_fee_calculations(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Validate fee calculations"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        total_fees_calculated = 0
        fee_discrepancies = []
        
        for i, trade in enumerate(trades):
            qty = float(trade.get("qty", 0))
            price = float(trade.get("price", 0))
            stated_fee = float(trade.get("fee", 0))
            
            # Calculate expected Binance fee (0.1%)
            trade_value = qty * price
            expected_fee = trade_value * 0.001
            
            total_fees_calculated += stated_fee
            
            # Check if fee is reasonable (within 0.05% - 0.15% range)
            if stated_fee > 0:
                fee_percentage = (stated_fee / trade_value) * 100
                if fee_percentage < 0.05 or fee_percentage > 0.25:
                    fee_discrepancies.append({
                        "trade_index": i,
                        "stated_fee": stated_fee,
                        "expected_fee": expected_fee,
                        "fee_percentage": fee_percentage
                    })
        
        # Check against summary total fees
        summary_fees = summary.get("total_fees", 0)
        if abs(total_fees_calculated - summary_fees) > 0.01:
            result["errors"].append(
                f"Fee mismatch: calculated {total_fees_calculated:.2f} vs summary {summary_fees:.2f}"
            )
            result["passed"] = False
        
        if fee_discrepancies:
            result["warnings"].append(f"Found {len(fee_discrepancies)} trades with unusual fee percentages")
        
        result["details"] = {
            "total_fees_from_trades": total_fees_calculated,
            "total_fees_from_summary": summary_fees,
            "unusual_fee_trades": len(fee_discrepancies),
            "fee_discrepancies": fee_discrepancies[:3]  # First 3 examples
        }
        
        return result
    
    def check_pnl_calculations(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Validate P&L calculation logic"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        # Recalculate P&L using proper FIFO method
        symbol_positions = {}
        realized_pnl = 0
        calculation_errors = []
        
        for i, trade in enumerate(trades):
            try:
                symbol = trade.get("symbol", "")
                side = str(trade.get("side", "")).upper()
                qty = float(trade.get("qty", 0))
                price = float(trade.get("price", 0))
                fee = float(trade.get("fee", 0))
                
                if symbol not in symbol_positions:
                    symbol_positions[symbol] = {"qty": 0.0, "cost_basis": 0.0}
                
                position = symbol_positions[symbol]
                
                if side == "BUY":
                    # Add to position
                    new_qty = position["qty"] + qty
                    new_cost = position["cost_basis"] + (qty * price) + fee
                    position["qty"] = new_qty
                    position["cost_basis"] = new_cost
                    
                elif side == "SELL":
                    if position["qty"] >= qty:
                        # Calculate P&L for this sell
                        avg_cost = position["cost_basis"] / position["qty"] if position["qty"] > 0 else 0
                        cost_of_sold = avg_cost * qty
                        revenue = (qty * price) - fee
                        trade_pnl = revenue - cost_of_sold
                        realized_pnl += trade_pnl
                        
                        # Update position
                        position["qty"] -= qty
                        if position["qty"] > 0:
                            position["cost_basis"] -= cost_of_sold
                        else:
                            position["cost_basis"] = 0.0
                    else:
                        calculation_errors.append(f"Trade {i}: Selling {qty} {symbol} but only have {position['qty']}")
                        
            except Exception as e:
                calculation_errors.append(f"Trade {i}: Calculation error - {str(e)}")
        
        # Compare with reported P&L
        reported_realized_pnl = summary.get("realized_pnl", summary.get("total_pnl", 0))
        pnl_difference = abs(realized_pnl - reported_realized_pnl)
        
        if pnl_difference > 1.0:  # Allow $1 tolerance
            result["errors"].append(
                f"P&L mismatch: calculated {realized_pnl:.2f} vs reported {reported_realized_pnl:.2f}"
            )
            result["passed"] = False
        elif pnl_difference > 0.1:  # Warn for smaller differences
            result["warnings"].append(
                f"Minor P&L difference: {pnl_difference:.2f}"
            )
        
        if calculation_errors:
            result["errors"].extend(calculation_errors[:3])
            result["passed"] = False
        
        result["details"] = {
            "calculated_realized_pnl": realized_pnl,
            "reported_realized_pnl": reported_realized_pnl,
            "difference": pnl_difference,
            "open_positions": {k: v for k, v in symbol_positions.items() if v["qty"] > 0},
            "calculation_errors_count": len(calculation_errors)
        }
        
        return result
    
    def check_position_tracking(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Validate position tracking accuracy"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        # Track positions through all trades
        position_history = {}
        negative_positions = []
        
        for i, trade in enumerate(trades):
            symbol = trade.get("symbol", "")
            side = str(trade.get("side", "")).upper()
            qty = float(trade.get("qty", 0))
            
            if symbol not in position_history:
                position_history[symbol] = []
            
            current_qty = position_history[symbol][-1] if position_history[symbol] else 0
            
            if side == "BUY":
                new_qty = current_qty + qty
            elif side == "SELL":
                new_qty = current_qty - qty
            else:
                continue
            
            position_history[symbol].append(new_qty)
            
            # Check for negative positions (short selling)
            if new_qty < -0.001:  # Small tolerance for rounding
                negative_positions.append({
                    "trade_index": i,
                    "symbol": symbol,
                    "position": new_qty
                })
        
        if negative_positions:
            result["warnings"].append(f"Found {len(negative_positions)} instances of negative positions (short selling)")
        
        # Check final positions make sense
        final_positions = {}
        for symbol, history in position_history.items():
            if history:
                final_positions[symbol] = history[-1]
        
        result["details"] = {
            "symbols_traded": len(position_history),
            "final_positions": final_positions,
            "negative_position_instances": len(negative_positions),
            "negative_positions": negative_positions[:3]
        }
        
        return result
    
    def check_realized_unrealized_split(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Validate realized vs unrealized P&L split"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        realized_pnl = summary.get("realized_pnl", 0)
        unrealized_pnl = summary.get("unrealized_pnl", 0)
        total_pnl = summary.get("total_pnl", 0)
        
        # Check if total equals realized + unrealized
        calculated_total = realized_pnl + unrealized_pnl
        difference = abs(total_pnl - calculated_total)
        
        if difference > 0.01:
            result["errors"].append(
                f"Total P&L ({total_pnl}) != Realized ({realized_pnl}) + Unrealized ({unrealized_pnl})"
            )
            result["passed"] = False
        
        # Check for reasonable proportions
        if total_pnl != 0:
            realized_percentage = (realized_pnl / total_pnl) * 100
            if abs(realized_percentage) > 150:  # More than 150% realized suggests calculation error
                result["warnings"].append(
                    f"Unusual realized P&L percentage: {realized_percentage:.1f}%"
                )
        
        result["details"] = {
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "calculated_total": calculated_total,
            "difference": difference,
            "realized_percentage": (realized_pnl / total_pnl * 100) if total_pnl != 0 else 0
        }
        
        return result
    
    def check_win_rate_calculation(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Validate win rate calculation"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        # Count profitable trades
        profitable_trades = 0
        total_completed_trades = 0
        
        for trade in trades:
            if trade.get("type") == "realized" or "profit" in trade:
                profit = float(trade.get("profit", 0))
                total_completed_trades += 1
                if profit > 0:
                    profitable_trades += 1
        
        if total_completed_trades > 0:
            calculated_win_rate = (profitable_trades / total_completed_trades) * 100
            reported_win_rate = summary.get("win_rate", 0)
            
            difference = abs(calculated_win_rate - reported_win_rate)
            if difference > 1.0:  # 1% tolerance
                result["errors"].append(
                    f"Win rate mismatch: calculated {calculated_win_rate:.1f}% vs reported {reported_win_rate:.1f}%"
                )
                result["passed"] = False
        
        result["details"] = {
            "total_completed_trades": total_completed_trades,
            "profitable_trades": profitable_trades,
            "calculated_win_rate": (profitable_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0,
            "reported_win_rate": summary.get("win_rate", 0)
        }
        
        return result
    
    def cross_reference_binance_data(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Cross-reference with Binance API data (if available)"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        try:
            # Try to fetch recent trades from API
            response = requests.get(f"{self.api_url}/binance/account", timeout=10)
            if response.ok:
                binance_data = response.json()
                
                # Compare trading volume
                our_volume = sum(float(t.get("qty", 0)) * float(t.get("price", 0)) for t in trades)
                binance_volume = binance_data.get("total_trading_volume", 0)
                
                if binance_volume > 0:
                    volume_difference = abs(our_volume - binance_volume) / binance_volume
                    if volume_difference > 0.1:  # 10% tolerance
                        result["warnings"].append(
                            f"Trading volume difference: {volume_difference:.1%}"
                        )
                
                result["details"] = {
                    "binance_data_available": True,
                    "our_volume": our_volume,
                    "binance_volume": binance_volume,
                    "volume_difference": volume_difference if binance_volume > 0 else None
                }
            else:
                result["details"] = {"binance_data_available": False}
                
        except Exception as e:
            result["warnings"].append(f"Could not cross-reference with Binance: {str(e)}")
            result["details"] = {"binance_data_available": False, "error": str(e)}
        
        return result
    
    def validate_cost_basis_logic(self, trades: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Validate cost basis calculation logic"""
        result = {"passed": True, "errors": [], "warnings": [], "details": {}}
        
        # Check for the problematic cost basis adjustment mentioned in the analysis
        cost_basis_issues = []
        
        # Group trades by symbol and check for proper FIFO handling
        symbol_trades = {}
        for trade in trades:
            symbol = trade.get("symbol", "")
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(trade)
        
        for symbol, symbol_trade_list in symbol_trades.items():
            # Sort by timestamp to ensure proper order
            symbol_trade_list.sort(key=lambda x: x.get("timestamp", x.get("ts", 0)))
            
            position_qty = 0
            position_cost = 0
            
            for i, trade in enumerate(symbol_trade_list):
                side = str(trade.get("side", "")).upper()
                qty = float(trade.get("qty", 0))
                price = float(trade.get("price", 0))
                fee = float(trade.get("fee", 0))
                
                if side == "BUY":
                    position_qty += qty
                    position_cost += (qty * price) + fee
                elif side == "SELL":
                    if position_qty < qty:
                        cost_basis_issues.append({
                            "symbol": symbol,
                            "trade_index": i,
                            "issue": f"Selling {qty} but only have {position_qty}",
                            "side": side
                        })
                    else:
                        # Check for proper cost basis reduction
                        if position_qty > 0:
                            avg_cost = position_cost / position_qty
                            cost_reduction = avg_cost * qty
                            position_qty -= qty
                            position_cost -= cost_reduction
                            
                            if position_cost < 0:
                                cost_basis_issues.append({
                                    "symbol": symbol,
                                    "trade_index": i,
                                    "issue": f"Negative cost basis: {position_cost}",
                                    "side": side
                                })
        
        if cost_basis_issues:
            result["errors"].extend([issue["issue"] for issue in cost_basis_issues[:3]])
            result["passed"] = False
        
        result["details"] = {
            "symbols_analyzed": len(symbol_trades),
            "cost_basis_issues": len(cost_basis_issues),
            "issues_detail": cost_basis_issues[:5]
        }
        
        return result
    
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable validation report"""
        report = []
        report.append("=" * 60)
        report.append("P&L VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {validation_results['timestamp']}")
        report.append(f"Report ID: {validation_results['report_id']}")
        report.append(f"Status: {validation_results['validation_status'].upper()}")
        report.append(f"Accuracy Score: {validation_results['accuracy_score']:.1f}%")
        report.append(f"Checks Passed: {validation_results['checks_passed']}/{validation_results['total_checks']}")
        report.append("")
        
        if validation_results["errors"]:
            report.append("🚨 ERRORS FOUND:")
            for error in validation_results["errors"]:
                report.append(f"  ❌ {error}")
            report.append("")
        
        if validation_results["warnings"]:
            report.append("⚠️  WARNINGS:")
            for warning in validation_results["warnings"]:
                report.append(f"  ⚠️  {warning}")
            report.append("")
        
        report.append("📊 DETAILED RESULTS:")
        for check_name, check_result in validation_results["detailed_results"].items():
            status = "✅ PASSED" if check_result["passed"] else "❌ FAILED"
            report.append(f"  {status} {check_name.replace('_', ' ').title()}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

# CLI interface for validation
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate P&L report accuracy")
    parser.add_argument("--report", required=True, help="Path to report JSON file")
    parser.add_argument("--output", help="Output validation report to file")
    
    args = parser.parse_args()
    
    validator = PnLValidator()
    
    # Load report data
    with open(args.report, 'r') as f:
        report_data = json.load(f)
    
    print("🔍 Validating P&L report...")
    validation_results = validator.validate_pnl_report(report_data)
    
    # Generate report
    validation_report = validator.generate_validation_report(validation_results)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(validation_report)
        print(f"📝 Validation report saved to {args.output}")
    else:
        print(validation_report)
    
    # Return appropriate exit code
    if validation_results["validation_status"] == "failed":
        exit(1)
    elif validation_results["validation_status"] == "error":
        exit(2)
    else:
        exit(0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())