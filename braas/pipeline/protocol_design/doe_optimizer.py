"""
BRaaS Pipeline Stage 2 - Design of Experiments (DoE) Optimizer.

Uses scipy and numpy for factorial design, parameter space exploration,
and Bayesian-style optimization with a surrogate model to find optimal
experimental parameters with minimal runs.
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from braas.core.models import DoEDesign


class DoEOptimizer:
    """
    Design of Experiments optimizer with surrogate-model-based Bayesian optimization.

    Supports full factorial, fractional factorial, and adaptive Bayesian
    optimization for finding optimal experimental parameters.
    """

    def __init__(self, random_seed: int = 42) -> None:
        """
        Initialize the DoE optimizer.

        Args:
            random_seed: Random seed for reproducibility.
        """
        self._rng = np.random.default_rng(random_seed)
        self._design: Optional[DoEDesign] = None
        self._observed_X: List[np.ndarray] = []
        self._observed_y: List[float] = []
        self._factor_names: List[str] = []
        self._factor_bounds: Dict[str, Tuple[float, float]] = {}

    def define_parameter_space(
        self,
        factors: Dict[str, Tuple[float, float]],
        response_variable: str = "yield",
    ) -> None:
        """
        Define the parameter space for optimization.

        Args:
            factors: Dict mapping factor name to (min_value, max_value) bounds.
            response_variable: Name of the response variable to optimize.

        Example:
            optimizer.define_parameter_space({
                "temperature_celsius": (20.0, 45.0),
                "ph": (6.0, 9.0),
                "concentration_ug_ml": (0.1, 10.0),
                "incubation_time_min": (30.0, 120.0),
            })
        """
        self._factor_names = list(factors.keys())
        self._factor_bounds = dict(factors)
        self._design = DoEDesign(
            factors={name: [lo, hi] for name, (lo, hi) in factors.items()},
            response_variable=response_variable,
        )
        self._observed_X = []
        self._observed_y = []

    async def suggest_experiments(
        self,
        n_experiments: Optional[int] = None,
        design_type: str = "full_factorial",
        levels: int = 3,
    ) -> List[Dict[str, float]]:
        """
        Suggest a set of experiments based on DoE methodology.

        Args:
            n_experiments: Number of experiments to suggest. If None, determined by design.
            design_type: One of 'full_factorial', 'fractional_factorial',
                         'latin_hypercube', 'bayesian'.
            levels: Number of levels per factor (for factorial designs).

        Returns:
            List of experiment parameter dicts.
        """
        if self._design is None:
            raise ValueError("Parameter space not defined. Call define_parameter_space() first.")

        if design_type == "full_factorial":
            experiments = self._full_factorial(levels)
        elif design_type == "fractional_factorial":
            experiments = self._fractional_factorial(levels)
        elif design_type == "latin_hypercube":
            n = n_experiments or (len(self._factor_names) * 5)
            experiments = self._latin_hypercube(n)
        elif design_type == "bayesian":
            n = n_experiments or 5
            experiments = self._bayesian_suggest(n)
        else:
            raise ValueError(f"Unknown design type: {design_type}")

        # Limit to n_experiments if specified
        if n_experiments is not None and len(experiments) > n_experiments:
            indices = self._rng.choice(len(experiments), n_experiments, replace=False)
            experiments = [experiments[i] for i in sorted(indices)]

        # Store in design
        if self._design:
            self._design.experiment_matrix = experiments

        return experiments

    async def analyze_round(
        self,
        experiments: List[Dict[str, float]],
        results: List[float],
    ) -> Dict[str, Any]:
        """
        Analyze results from a round of experiments.

        Fits a surrogate model (polynomial regression) and computes
        factor importance and interaction effects.

        Args:
            experiments: The experiment parameter dicts that were run.
            results: Corresponding response values.

        Returns:
            Analysis dict with model fit, factor importance, and predictions.
        """
        if len(experiments) != len(results):
            raise ValueError("experiments and results must have the same length")

        # Store observations
        for exp, res in zip(experiments, results):
            x = np.array([exp[name] for name in self._factor_names])
            self._observed_X.append(x)
            self._observed_y.append(res)

        X = np.array(self._observed_X)
        y = np.array(self._observed_y)

        # Normalize X to [0, 1]
        X_norm = self._normalize(X)

        # Fit quadratic surrogate model
        # Features: [x1, x2, ..., x1^2, x2^2, ..., x1*x2, ...]
        X_features = self._build_features(X_norm)
        coeffs, r_squared, residuals = self._fit_linear_model(X_features, y)

        if self._design:
            self._design.results = list(y)
            self._design.model_r_squared = r_squared

        # Factor importance (based on coefficient magnitudes)
        n_factors = len(self._factor_names)
        factor_importance: Dict[str, float] = {}
        for i, name in enumerate(self._factor_names):
            # Linear coefficient importance
            importance = abs(coeffs[i + 1]) if i + 1 < len(coeffs) else 0.0
            factor_importance[name] = round(float(importance), 4)

        # Interaction effects
        interactions: Dict[str, float] = {}
        interaction_idx = 1 + n_factors + n_factors  # after intercept + linear + quadratic
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                if interaction_idx < len(coeffs):
                    key = f"{self._factor_names[i]} x {self._factor_names[j]}"
                    interactions[key] = round(float(coeffs[interaction_idx]), 4)
                    interaction_idx += 1

        return {
            "r_squared": round(r_squared, 4),
            "n_observations": len(y),
            "factor_importance": factor_importance,
            "interactions": interactions,
            "best_observed": {
                "params": {
                    name: float(X[np.argmax(y), i])
                    for i, name in enumerate(self._factor_names)
                },
                "response": float(np.max(y)),
            },
            "worst_observed": {
                "params": {
                    name: float(X[np.argmin(y), i])
                    for i, name in enumerate(self._factor_names)
                },
                "response": float(np.min(y)),
            },
            "mean_response": round(float(np.mean(y)), 4),
            "std_response": round(float(np.std(y)), 4),
        }

    async def get_optimal_params(
        self,
        n_candidates: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find optimal parameters using the surrogate model.

        Generates random candidates and evaluates them with the
        fitted surrogate model to find the predicted optimum.

        Args:
            n_candidates: Number of random candidates to evaluate.

        Returns:
            Dict with optimal parameters, predicted response, and confidence.
        """
        if len(self._observed_X) < 3:
            raise ValueError(
                "Need at least 3 observations to fit surrogate model. "
                "Run analyze_round() first."
            )

        X = np.array(self._observed_X)
        y = np.array(self._observed_y)
        X_norm = self._normalize(X)
        X_features = self._build_features(X_norm)
        coeffs, r_squared, _ = self._fit_linear_model(X_features, y)

        # Generate random candidates in normalized space
        candidates_norm = self._rng.random((n_candidates, len(self._factor_names)))

        # Evaluate with surrogate model
        candidates_features = self._build_features(candidates_norm)
        predictions = candidates_features @ coeffs

        # Find best candidate
        best_idx = np.argmax(predictions)
        best_norm = candidates_norm[best_idx]

        # Denormalize to original scale
        optimal_params: Dict[str, float] = {}
        for i, name in enumerate(self._factor_names):
            lo, hi = self._factor_bounds[name]
            optimal_params[name] = round(float(lo + best_norm[i] * (hi - lo)), 4)

        predicted_response = float(predictions[best_idx])

        # Estimate confidence from model R² and distance to observed data
        confidence = min(r_squared * 0.9 + 0.1, 0.99)

        # Store optimal in design
        if self._design:
            self._design.optimal_params = optimal_params

        return {
            "optimal_params": optimal_params,
            "predicted_response": round(predicted_response, 4),
            "confidence": round(confidence, 4),
            "model_r_squared": round(r_squared, 4),
            "n_observations_used": len(y),
            "search_candidates": n_candidates,
        }

    def get_design(self) -> Optional[DoEDesign]:
        """Get the current DoE design object."""
        return self._design

    # ── Private Methods ────────────────────────────────────────────────

    def _full_factorial(self, levels: int) -> List[Dict[str, float]]:
        """Generate full factorial design."""
        level_values: List[List[float]] = []
        for name in self._factor_names:
            lo, hi = self._factor_bounds[name]
            level_values.append(
                np.linspace(lo, hi, levels).tolist()
            )

        experiments: List[Dict[str, float]] = []
        for combo in itertools.product(*level_values):
            exp = {
                name: round(val, 6)
                for name, val in zip(self._factor_names, combo)
            }
            experiments.append(exp)

        return experiments

    def _fractional_factorial(self, levels: int) -> List[Dict[str, float]]:
        """
        Generate fractional factorial design (resolution III+).

        Uses a half-fraction of the full factorial by confounding
        the highest-order interaction.
        """
        full = self._full_factorial(levels)
        # Take half-fraction: select experiments where sum of normalized
        # coded values has the same parity
        half: List[Dict[str, float]] = []
        for exp in full:
            coded_sum = 0
            for name in self._factor_names:
                lo, hi = self._factor_bounds[name]
                mid = (lo + hi) / 2.0
                coded_sum += 1 if exp[name] >= mid else 0
            if coded_sum % 2 == 0:
                half.append(exp)

        return half if half else full

    def _latin_hypercube(self, n: int) -> List[Dict[str, float]]:
        """Generate Latin Hypercube Sampling design."""
        k = len(self._factor_names)
        experiments: List[Dict[str, float]] = []

        # Create LHS intervals
        for j in range(k):
            perm = self._rng.permutation(n)
            lo, hi = self._factor_bounds[self._factor_names[j]]
            intervals = np.linspace(lo, hi, n + 1)

            if j == 0:
                # Initialize experiment list
                for i in range(n):
                    val = self._rng.uniform(intervals[perm[i]], intervals[perm[i] + 1])
                    experiments.append({self._factor_names[j]: round(float(val), 6)})
            else:
                for i in range(n):
                    val = self._rng.uniform(intervals[perm[i]], intervals[perm[i] + 1])
                    experiments[i][self._factor_names[j]] = round(float(val), 6)

        return experiments

    def _bayesian_suggest(self, n: int) -> List[Dict[str, float]]:
        """
        Suggest next experiments using Bayesian-style acquisition.

        Uses Upper Confidence Bound (UCB) strategy with the surrogate model.
        Falls back to Latin Hypercube if not enough observations exist.
        """
        if len(self._observed_X) < 3:
            # Not enough data for surrogate — use space-filling design
            return self._latin_hypercube(n)

        X = np.array(self._observed_X)
        y = np.array(self._observed_y)
        X_norm = self._normalize(X)
        X_features = self._build_features(X_norm)
        coeffs, r_squared, _ = self._fit_linear_model(X_features, y)

        # Generate many random candidates
        n_candidates = max(n * 1000, 5000)
        candidates_norm = self._rng.random((n_candidates, len(self._factor_names)))
        candidates_features = self._build_features(candidates_norm)

        # Predicted mean
        mu = candidates_features @ coeffs

        # Estimate uncertainty as distance to nearest observed point
        sigma = np.zeros(n_candidates)
        for i in range(n_candidates):
            dists = np.linalg.norm(X_norm - candidates_norm[i], axis=1)
            sigma[i] = np.min(dists) * np.std(y)

        # UCB acquisition: mu + kappa * sigma
        kappa = 2.0
        ucb = mu + kappa * sigma

        # Select top-n candidates
        top_indices = np.argsort(ucb)[-n:][::-1]

        experiments: List[Dict[str, float]] = []
        for idx in top_indices:
            exp: Dict[str, float] = {}
            for j, name in enumerate(self._factor_names):
                lo, hi = self._factor_bounds[name]
                exp[name] = round(float(lo + candidates_norm[idx, j] * (hi - lo)), 6)
            experiments.append(exp)

        return experiments

    def _normalize(self, X: np.ndarray) -> np.ndarray:
        """Normalize X to [0, 1] based on factor bounds."""
        X_norm = np.zeros_like(X, dtype=float)
        for j, name in enumerate(self._factor_names):
            lo, hi = self._factor_bounds[name]
            if hi > lo:
                X_norm[:, j] = (X[:, j] - lo) / (hi - lo)
            else:
                X_norm[:, j] = 0.5
        return X_norm

    def _build_features(self, X_norm: np.ndarray) -> np.ndarray:
        """
        Build polynomial feature matrix: intercept + linear + quadratic + interactions.
        """
        n_samples, n_factors = X_norm.shape

        # Intercept
        features = [np.ones((n_samples, 1))]

        # Linear terms
        features.append(X_norm)

        # Quadratic terms
        features.append(X_norm ** 2)

        # Interaction terms
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                features.append(
                    (X_norm[:, i] * X_norm[:, j]).reshape(-1, 1)
                )

        return np.hstack(features)

    def _fit_linear_model(
        self,
        X_features: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, float, np.ndarray]:
        """
        Fit linear regression model using least squares.

        Returns:
            Tuple of (coefficients, R², residuals).
        """
        # Use pseudoinverse for numerical stability
        coeffs, residuals_sum, rank, sv = np.linalg.lstsq(X_features, y, rcond=None)

        # Calculate R²
        y_pred = X_features @ coeffs
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r_squared = max(0.0, min(1.0, r_squared))

        residuals = y - y_pred

        return coeffs, r_squared, residuals
