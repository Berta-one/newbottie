# ml/model_loader.py
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

logger = logging.getLogger("ModelLoader")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


# ---- config -----------------------------------------------------------------

# You can override where artifacts live:
#   export MODELS_DIR=/abs/path/to/models
MODELS_DIR = Path(os.getenv("MODELS_DIR", "models")).resolve()

# Search in this order; earlier wins.
SEARCH_DIRS: List[Path] = [
    MODELS_DIR,
    Path("ml/models").resolve(),
    Path(".").resolve(),
]

# For each logical model name, we’ll try these filename stems in order
# (without extension); extensions are resolved by PREFERRED_EXTS below.
DEFAULT_STEMS = {
    "lstm": ["lstm_model", "lstm", "model_lstm"],
    "xgb": ["xgboost_model", "xgb_model", "xgb"],
    "ensemble": ["ensemble_model", "ensemble"],
}

# Prefer modern, robust formats first
PREFERRED_EXTS = [
    ".pkl", ".joblib",              # joblib/sklearn/xgboost dumps
    ".keras", ".h5",                # keras models
    ".json",                        # legacy xgboost booster json
]


# ---- helpers ----------------------------------------------------------------

def _first_existing(paths: Iterable[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists() and p.is_file():
            return p
    return None


def _candidate_paths(stems: List[str], exts: List[str], search_dirs: List[Path]) -> List[Path]:
    cand: List[Path] = []
    for d in search_dirs:
        for s in stems:
            for e in exts:
                cand.append(d / f"{s}{e}")
    return cand


@dataclass
class LoadedModel:
    obj: Any
    path: Path
    kind: str  # "pickle" | "keras" | "xgb_json" | "unknown"

    def predict(self, X: Sequence) -> Any:
        pred = getattr(self.obj, "predict", None)
        if callable(pred):
            return pred(X)
        raise AttributeError(f"Loaded model at {self.path} has no predict(X)")

    def predict_proba(self, X: Sequence) -> Any:
        """
        Normalizes access: if the underlying model doesn't expose predict_proba,
        we synthesize a probability‑like output from predict.
        """
        proba = getattr(self.obj, "predict_proba", None)
        if callable(proba):
            return proba(X)

        # synthesize simple 3‑class distribution if only predict() exists.
        # map BUY/SELL/HOLD or 1/0 to a distribution as a safe fallback.
        logger.warning("Model %s lacks predict_proba(); synthesizing from predict()", self.path)
        labels = self.predict(X)
        dist = []
        for y in labels:
            if isinstance(y, str):
                y_up = y.upper()
                if y_up == "BUY":
                    dist.append([0.1, 0.8, 0.1])
                elif y_up == "SELL":
                    dist.append([0.8, 0.1, 0.1])
                else:  # HOLD / other
                    dist.append([0.2, 0.2, 0.6])
            else:
                # binary-ish fallback
                p = 0.8 if float(y) > 0 else 0.2
                dist.append([1 - p, p, 0.0])
        return dist


# ---- concrete loaders -------------------------------------------------------

def _load_pickle(path: Path) -> Any:
    import joblib  # lazy import
    return joblib.load(path)


def _load_keras(path: Path) -> Any:
    try:
        import tensorflow as tf  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            f"TensorFlow required to load Keras model: {path}\n{exc}"
        ) from exc
    from tensorflow import keras
    return keras.models.load_model(path)


def _load_xgb_json(path: Path) -> Any:
    """Load legacy xgboost Booster stored as JSON and wrap with a minimal API."""
    try:
        import xgboost as xgb  # noqa: F401
    except Exception as exc:
        raise RuntimeError("xgboost not installed but required for legacy JSON") from exc

    from xgboost import Booster, DMatrix

    booster = Booster()
    booster.load_model(str(path))

    class _XGBWrapper:
        def __init__(self, booster_: Booster):
            self._booster = booster_

        def predict(self, X: Sequence):
            dm = DMatrix(X)
            out = self._booster.predict(dm)
            return out

        # naive probability projection for multi‑class; refine if you know your training objective
        def predict_proba(self, X: Sequence):
            dm = DMatrix(X)
            out = self._booster.predict(dm)
            # ensure 2D list
            if hasattr(out, "tolist"):
                out = out.tolist()
            if out and isinstance(out[0], (int, float)):  # 1D -> replicate over 2 classes
                return [[1 - float(p), float(p)] for p in out]
            return out

    return _XGBWrapper(booster)


# ---- public API -------------------------------------------------------------

def load_model(
    name: str,
    stems: Optional[List[str]] = None,
    search_dirs: Optional[List[Path]] = None,
    prefer_exts: Optional[List[str]] = None,
) -> LoadedModel:
    """
    Load a model by logical name ("lstm", "xgb", "ensemble").

    Resolution order:
      1) iterate stems (defaults from DEFAULT_STEMS[name])
      2) for each stem, test extensions in PREFERRED_EXTS (or prefer_exts)
      3) return first file that exists across SEARCH_DIRS (or search_dirs)

    Returns a LoadedModel with normalized predict / predict_proba access.
    """
    if stems is None:
        if name not in DEFAULT_STEMS:
            raise ValueError(f"Unknown model name '{name}'. Provide stems=[...] explicitly.")
        stems = DEFAULT_STEMS[name]

    dirs = search_dirs or SEARCH_DIRS
    exts = prefer_exts or PREFERRED_EXTS

    candidates = _candidate_paths(stems, exts, dirs)
    found = _first_existing(candidates)
    if not found:
        pretty = "\n  ".join(str(p) for p in candidates)
        raise FileNotFoundError(
            f"No artifact found for model '{name}'. Looked in:\n  {pretty}"
        )

    suffix = found.suffix.lower()
    logger.info("Loading model '%s' from %s", name, found)

    if suffix in (".pkl", ".joblib"):
        obj = _load_pickle(found)
        return LoadedModel(obj=obj, path=found, kind="pickle")

    if suffix in (".keras", ".h5"):
        obj = _load_keras(found)
        return LoadedModel(obj=obj, path=found, kind="keras")

    if suffix == ".json":
        # detect xgboost JSON (quick heuristic)
        try:
            with open(found, "r", encoding="utf-8") as f:
                first = f.read(64)
                if "xgboost" in first.lower():
                    obj = _load_xgb_json(found)
                    return LoadedModel(obj=obj, path=found, kind="xgb_json")
        except Exception:
            # if reading fails, still try xgboost path
            obj = _load_xgb_json(found)
            return LoadedModel(obj=obj, path=found, kind="xgb_json")

        # else: raw JSON? try to reconstruct a trivial wrapper
        with open(found, "r", encoding="utf-8") as f:
            _ = json.load(f)  # just to validate
        raise RuntimeError(
            f"Unsupported JSON model at {found}. Expected XGBoost Booster JSON."
        )

    raise RuntimeError(f"Unsupported model extension '{suffix}' at {found}")


# Convenience top‑level getters

def load_lstm() -> LoadedModel:
    return load_model("lstm")


def load_xgb() -> LoadedModel:
    return load_model("xgb")


def load_ensemble() -> LoadedModel:
    return load_model("ensemble")