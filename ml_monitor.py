#!/usr/bin/env python3
"""
Bottie ML Learning Monitor
Analyzes and interprets machine learning performance in real-time.

Usage:
    python ml_monitor.py --api-url http://localhost:8000
    python ml_monitor.py --continuous  # Auto-refresh every 30s
    python ml_monitor.py --report       # Generate detailed report
"""

import argparse
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
import os
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn

console = Console()

@dataclass
class LearningMetrics:
    ml_brier: Optional[float] = None
    quantum_brier: Optional[float] = None
    sample_count: int = 0
    quantum_importance: Optional[float] = None
    quantum_rank: Optional[int] = None
    feature_importance: Dict[str, float] = field(default_factory=dict)
    quantum_mode: str = "unknown"
    quantum_weight: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

class MLMonitor:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip('/')
        self.history: List[LearningMetrics] = []
        self.console = Console()

    async def fetch_data(self) -> Optional[LearningMetrics]:
        """Fetch current learning metrics from API"""
        try:
            # Fetch ML status
            ml_response = requests.get(f"{self.api_url}/ml/status", timeout=10)
            
            if ml_response.status_code != 200:
                self.console.print(f"[yellow]ML status endpoint returned {ml_response.status_code}[/yellow]")
                return None

            ml_data = ml_response.json()
            
            # Try to fetch component metrics (optional)
            components_data = {}
            try:
                components_response = requests.get(f"{self.api_url}/metrics/components", timeout=10)
                if components_response.status_code == 200:
                    components_data = components_response.json()
            except:
                pass  # Optional endpoint

            # Extract metrics from ML status
            return LearningMetrics(
                ml_brier=ml_data.get('brier_score'),
                quantum_brier=components_data.get('performance', {}).get('brier_loss', {}).get('q'),
                sample_count=ml_data.get('sample_count', 0),
                quantum_importance=ml_data.get('quantum_importance'),
                quantum_rank=ml_data.get('quantum_feature_rank'),
                feature_importance=ml_data.get('feature_importance', {}),
                quantum_mode=ml_data.get('quantum_mode', 'unknown'),
                quantum_weight=components_data.get('weights', {}).get('current', {}).get('q'),
            )

        except Exception as e:
            self.console.print(f"[red]Error fetching data: {e}[/red]")
            return None

    def analyze_learning_health(self, metrics: LearningMetrics) -> Dict[str, Any]:
        """Analyze overall learning health"""
        analysis = {
            'status': 'unknown',
            'score': 0,
            'issues': [],
            'recommendations': [],
            'interpretation': ''
        }

        if metrics.sample_count < 50:
            analysis['status'] = 'insufficient_data'
            analysis['score'] = 1
            analysis['interpretation'] = 'Need more training samples (minimum 50-100)'
            analysis['recommendations'].append('Wait for more trading signals to accumulate')
            return analysis

        if metrics.ml_brier is None:
            analysis['status'] = 'no_data'
            analysis['score'] = 0
            analysis['interpretation'] = 'No ML performance data available'
            return analysis

        # Score based on Brier score (lower is better)
        if metrics.ml_brier < 0.18:
            analysis['status'] = 'excellent'
            analysis['score'] = 5
            analysis['interpretation'] = 'Excellent learning! ML making high-quality predictions'
        elif metrics.ml_brier < 0.22:
            analysis['status'] = 'good'
            analysis['score'] = 4
            analysis['interpretation'] = 'Good learning progress, beating random guessing significantly'
        elif metrics.ml_brier < 0.25:
            analysis['status'] = 'moderate'
            analysis['score'] = 3
            analysis['interpretation'] = 'Moderate learning, model improving but slowly'
            analysis['recommendations'].append('Consider increasing data diversity')
        else:
            analysis['status'] = 'poor'
            analysis['score'] = 2
            analysis['interpretation'] = 'Poor learning, model struggling to find patterns'
            analysis['issues'].append('High prediction error rate')
            analysis['recommendations'].extend([
                'Check data quality and feature engineering',
                'Consider adjusting learning parameters'
            ])

        return analysis

    def analyze_quantum_impact(self, metrics: LearningMetrics) -> Dict[str, Any]:
        """Analyze quantum learning contribution"""
        analysis = {
            'impact': 'unknown',
            'score': 0,
            'interpretation': '',
            'recommendations': []
        }

        if not metrics.quantum_importance or not metrics.quantum_rank:
            analysis['impact'] = 'insufficient_data'
            analysis['interpretation'] = 'Need more data to assess quantum impact'
            return analysis

        # Analyze quantum feature rank
        if metrics.quantum_rank == 1:
            analysis['impact'] = 'critical'
            analysis['score'] = 5
            analysis['interpretation'] = 'Quantum is the #1 most important feature! ML heavily relies on quantum predictions'
            if metrics.quantum_mode == 'shadow':
                analysis['recommendations'].append('Consider enabling quantum for live trading (QUANTUM_MODE=live)')
        elif metrics.quantum_rank <= 3:
            analysis['impact'] = 'high'
            analysis['score'] = 4
            analysis['interpretation'] = f'Quantum ranks #{metrics.quantum_rank} - highly valuable for predictions'
            if metrics.quantum_mode == 'shadow':
                analysis['recommendations'].append('Quantum shows strong predictive power - consider live mode')
        elif metrics.quantum_rank <= 5:
            analysis['impact'] = 'moderate'
            analysis['score'] = 3
            analysis['interpretation'] = f'Quantum ranks #{metrics.quantum_rank} - provides moderate value'
        else:
            analysis['impact'] = 'low'
            analysis['score'] = 2
            analysis['interpretation'] = f'Quantum ranks #{metrics.quantum_rank} - other features more predictive'
            analysis['recommendations'].append('Quantum may not be adding much value - consider optimization')

        # Compare quantum vs other features
        if metrics.feature_importance:
            quantum_imp = metrics.quantum_importance
            other_features = {k: v for k, v in metrics.feature_importance.items() if k != 'quantum_prob'}
            if other_features:
                avg_other = sum(other_features.values()) / len(other_features)
                if quantum_imp > avg_other * 2:
                    analysis['recommendations'].append('Quantum significantly outperforms other features!')
                elif quantum_imp < avg_other * 0.5:
                    analysis['recommendations'].append('Quantum underperforming compared to classical features')

        return analysis

    def create_learning_dashboard(self, metrics: LearningMetrics) -> Layout:
        """Create rich dashboard layout"""
        layout = Layout()

        # Health analysis
        health = self.analyze_learning_health(metrics)
        quantum_analysis = self.analyze_quantum_impact(metrics)

        # Create status panels
        health_color = {
            'excellent': 'green',
            'good': 'blue', 
            'moderate': 'yellow',
            'poor': 'red',
            'insufficient_data': 'white'
        }.get(health['status'], 'white')

        health_panel = Panel(
            f"Status: {health['status'].replace('_', ' ').title()}\n"
            f"Score: {'⭐' * health['score']}\n"
            f"Samples: {metrics.sample_count:,}\n"
            f"Brier Score: {metrics.ml_brier:.3f if metrics.ml_brier else 'N/A'}\n\n"
            f"{health['interpretation']}",
            title="🧠 Learning Health",
            border_style=health_color
        )

        quantum_color = {
            'critical': 'bright_green',
            'high': 'green',
            'moderate': 'yellow', 
            'low': 'red',
            'insufficient_data': 'white'
        }.get(quantum_analysis['impact'], 'white')

        quantum_panel = Panel(
            f"Impact: {quantum_analysis['impact'].title()}\n"
            f"Rank: #{metrics.quantum_rank or 'N/A'}\n"
            f"Importance: {metrics.quantum_importance:.3f if metrics.quantum_importance else 'N/A'}\n"
            f"Mode: {metrics.quantum_mode}\n"
            f"Weight: {metrics.quantum_weight:.1%} if metrics.quantum_weight else 'N/A'}\n\n"
            f"{quantum_analysis['interpretation']}",
            title="⚡ Quantum Analysis", 
            border_style=quantum_color
        )

        # Feature importance table
        feature_table = Table(title="📊 Feature Importance")
        feature_table.add_column("Feature", style="cyan")
        feature_table.add_column("Importance", style="magenta")
        feature_table.add_column("Rank", style="green")

        if metrics.feature_importance:
            sorted_features = sorted(metrics.feature_importance.items(), key=lambda x: x[1], reverse=True)
            for rank, (feature, importance) in enumerate(sorted_features, 1):
                style = "bold green" if feature == "quantum_prob" else ""
                feature_table.add_row(
                    feature,
                    f"{importance:.3f}",
                    f"#{rank}",
                    style=style
                )

        # Recommendations
        recommendations = []
        recommendations.extend(health.get('recommendations', []))
        recommendations.extend(quantum_analysis.get('recommendations', []))

        rec_text = "\n".join([f"• {rec}" for rec in recommendations]) if recommendations else "No specific recommendations at this time."
        rec_panel = Panel(rec_text, title="💡 Recommendations", border_style="blue")

        # Layout structure
        layout.split_column(
            Layout(name="top", size=10),
            Layout(name="middle", size=15), 
            Layout(name="bottom")
        )

        layout["top"].split_row(health_panel, quantum_panel)
        layout["middle"] = feature_table
        layout["bottom"] = rec_panel

        return layout

    def generate_report(self) -> str:
        """Generate detailed text report"""
        if not self.history:
            return "No historical data available for report generation."

        latest = self.history[-1]
        health = self.analyze_learning_health(latest)
        quantum = self.analyze_quantum_impact(latest)

        report = f"""
# Bottie ML Learning Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Points: {len(self.history)}

## Executive Summary
- Learning Status: {health['status'].replace('_', ' ').title()}
- Quantum Impact: {quantum['impact'].title()}
- Sample Count: {latest.sample_count:,}
- ML Quality Score: {health['score']}/5 stars

## Learning Health Analysis
{health['interpretation']}

Brier Score: {latest.ml_brier:.3f if latest.ml_brier else 'N/A'}
(Lower is better - Random guessing = 0.25, Excellent < 0.18)

## Quantum Learning Impact
{quantum['interpretation']}

Feature Rank: #{latest.quantum_rank or 'N/A'} out of {len(latest.feature_importance)}
Importance Score: {latest.quantum_importance:.3f if latest.quantum_importance else 'N/A'}
Current Mode: {latest.quantum_mode}

## Feature Analysis
"""

        if latest.feature_importance:
            sorted_features = sorted(latest.feature_importance.items(), key=lambda x: x[1], reverse=True)
            for rank, (feature, importance) in enumerate(sorted_features, 1):
                marker = "🌟" if feature == "quantum_prob" else "  "
                report += f"{marker} #{rank:2d}. {feature:12s}: {importance:.3f}\n"

        if health.get('issues'):
            report += f"\n## Issues Identified\n"
            for issue in health['issues']:
                report += f"⚠️  {issue}\n"

        recommendations = []
        recommendations.extend(health.get('recommendations', []))
        recommendations.extend(quantum.get('recommendations', []))

        if recommendations:
            report += f"\n## Recommendations\n"
            for rec in recommendations:
                report += f"💡 {rec}\n"

        # Historical trend analysis
        if len(self.history) >= 5:
            recent_briers = [h.ml_brier for h in self.history[-5:] if h.ml_brier]
            if len(recent_briers) >= 3:
                trend = "improving" if recent_briers[-1] < recent_briers[0] else "declining"
                report += f"\n## Recent Trend\nML performance is {trend} over last {len(recent_briers)} samples.\n"

        return report

    async def continuous_monitor(self, interval: int = 30):
        """Run continuous monitoring with live dashboard"""
        self.console.print("[bold blue]Starting Bottie ML Monitor[/bold blue]")

        with Live(console=self.console, refresh_per_second=1) as live:
            while True:
                try:
                    metrics = await self.fetch_data()
                    if metrics:
                        self.history.append(metrics)

                        # Keep only last 100 data points
                        if len(self.history) > 100:
                            self.history = self.history[-100:]

                        dashboard = self.create_learning_dashboard(metrics)
                        live.update(dashboard)
                    else:
                        live.update(Panel("❌ Connection Failed", title="Status"))

                    await asyncio.sleep(interval)

                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Monitoring stopped by user[/yellow]")
                    break
                except Exception as e:
                    live.update(Panel(f"Error: {e}", title="❌ Error", border_style="red"))
                    await asyncio.sleep(interval)

    async def single_check(self):
        """Perform single analysis check"""
        metrics = await self.fetch_data()
        if not metrics:
            self.console.print("[red]Failed to fetch data from API[/red]")
            return

        self.history.append(metrics)
        dashboard = self.create_learning_dashboard(metrics)
        self.console.print(dashboard)

    def plot_trends(self, save_path: str = None):
        """Generate trend plots"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            self.console.print("[red]matplotlib not installed. Run: pip install matplotlib[/red]")
            return

        if len(self.history) < 3:
            self.console.print("[yellow]Need at least 3 data points for trend analysis[/yellow]")
            return

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Bottie ML Learning Trends', fontsize=16)

        timestamps = [h.timestamp for h in self.history]

        # Brier scores over time
        ml_briers = [h.ml_brier for h in self.history if h.ml_brier]
        quantum_briers = [h.quantum_brier for h in self.history if h.quantum_brier]

        if ml_briers:
            ax1.plot(timestamps[-len(ml_briers):], ml_briers, 'b-', label='ML Brier Score', linewidth=2)
        if quantum_briers:
            ax1.plot(timestamps[-len(quantum_briers):], quantum_briers, 'g-', label='Quantum Brier Score', linewidth=2)

        ax1.set_title('Prediction Quality (Lower = Better)')
        ax1.set_ylabel('Brier Score')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Sample count growth
        sample_counts = [h.sample_count for h in self.history]
        ax2.plot(timestamps, sample_counts, 'purple', linewidth=2)
        ax2.set_title('Learning Sample Growth')
        ax2.set_ylabel('Sample Count')
        ax2.grid(True, alpha=0.3)

        # Quantum importance over time
        quantum_importances = [h.quantum_importance for h in self.history if h.quantum_importance]
        if quantum_importances:
            ax3.plot(timestamps[-len(quantum_importances):], quantum_importances, 'orange', linewidth=2)
            ax3.set_title('Quantum Feature Importance')
            ax3.set_ylabel('Importance Score')
            ax3.grid(True, alpha=0.3)

        # Feature importance comparison (latest data)
        latest = self.history[-1]
        if latest.feature_importance:
            features = list(latest.feature_importance.keys())
            importances = list(latest.feature_importance.values())
            colors = ['red' if f == 'quantum_prob' else 'blue' for f in features]

            ax4.bar(features, importances, color=colors, alpha=0.7)
            ax4.set_title('Current Feature Importance')
            ax4.set_ylabel('Importance Score')
            ax4.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.console.print(f"[green]Trends plot saved to {save_path}[/green]")
        else:
            plt.show()

async def main():
    parser = argparse.ArgumentParser(description='Bottie ML Learning Monitor')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=30, help='Refresh interval in seconds')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--plot', action='store_true', help='Generate trend plots')
    parser.add_argument('--save-plot', help='Save plot to file')

    args = parser.parse_args()

    monitor = MLMonitor(args.api_url)

    if args.continuous:
        await monitor.continuous_monitor(args.interval)
    elif args.report:
        # Collect some data first
        for i in range(3):
            metrics = await monitor.fetch_data()
            if metrics:
                monitor.history.append(metrics)
            await asyncio.sleep(1)

        report = monitor.generate_report()
        console.print(Panel(report, title="📊 ML Learning Report"))

        # Save report to file
        with open('ml_learning_report.txt', 'w') as f:
            f.write(report)
        console.print("[green]Report saved to ml_learning_report.txt[/green]")

    elif args.plot:
        # Collect data for plotting
        console.print("Collecting data for trend analysis...")
        for i in range(10):
            metrics = await monitor.fetch_data()
            if metrics:
                monitor.history.append(metrics)
            await asyncio.sleep(2)

        monitor.plot_trends(args.save_plot)
    else:
        await monitor.single_check()

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import rich
    except ImportError:
        print("Installing required packages...")
        os.system("pip install rich matplotlib requests")
        import rich

    asyncio.run(main())
