"""
smart_imports.py
===============
Smart import manager that uses real modules when available, fallbacks otherwise
"""

import sys
import importlib


class SmartImportManager:
    """Manages imports with fallbacks for Railway deployment"""

    def __init__(self):
        self.available_modules = {}
        self.check_dependencies()

    def check_dependencies(self):
        """Check which advanced dependencies are available"""

        # Check for Qiskit
        try:
            import qiskit
            import qiskit_aer

            self.available_modules["qiskit"] = True
            print("Qiskit available - using real quantum computing")
        except ImportError:
            self.available_modules["qiskit"] = False
            print("Qiskit unavailable - using mathematical quantum simulation")

        # Check for scikit-learn
        try:
            import sklearn

            self.available_modules["sklearn"] = True
            print("Scikit-learn available - using real ML")
        except ImportError:
            self.available_modules["sklearn"] = False
            print("Scikit-learn unavailable - using statistical ML simulation")

    def get_quantum_engine(self):
        """Get quantum engine - real or fallback"""
        if self.available_modules.get("qiskit", False):
            try:
                from quantum_engine import QuantumAnalyzer

                return QuantumAnalyzer()
            except ImportError:
                pass

        from quantum_engine_fallback import QuantumAnalyzer

        return QuantumAnalyzer()

    def get_ml_strategy(self):
        """Get ML strategy - real or fallback"""
        if self.available_modules.get("sklearn", False):
            try:
                from enhanced_ml_strategy import MLEnhancedStrategy

                return MLEnhancedStrategy()
            except ImportError:
                pass

        from ml_strategy_fallback import MLEnhancedStrategy

        return MLEnhancedStrategy()

    def get_capabilities(self):
        """Return current system capabilities"""
        return {
            "quantum_computing": self.available_modules.get("qiskit", False),
            "machine_learning": self.available_modules.get("sklearn", False),
            "quantum_mode": (
                "Real" if self.available_modules.get("qiskit") else "Simulated"
            ),
            "ml_mode": (
                "Real" if self.available_modules.get("sklearn") else "Statistical"
            ),
        }


# Global instance
smart_imports = SmartImportManager()
