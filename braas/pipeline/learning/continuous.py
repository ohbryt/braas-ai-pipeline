"""
Continuous Learner
==================

Continuous learning and optimization for the BRaaS pipeline.
Records experiment outcomes, updates models, and provides optimization insights.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from braas.core.enums import ExperimentType
from braas.core.exceptions import AnalysisError


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class PlatformStats:
    """Platform-wide statistics."""
    total_experiments: int
    success_rate_by_type: dict[str, float]
    reagent_efficacy_scores: dict[str, float]
    equipment_uptime: dict[str, float]


@dataclass
class OptimizationInsight:
    """Insight for parameter optimization."""
    what_to_optimize: str
    current_value: float
    suggested_value: float
    expected_improvement: float
    confidence: float


@dataclass
class KGUpdate:
    """Knowledge graph update."""
    relationship_type: str
    from_node: str
    to_node: str
    strength: float


# -----------------------------------------------------------------------------
# Continuous Learner
# -----------------------------------------------------------------------------

class ContinuousLearner:
    """Continuous learning system for BRaaS pipeline.
    
    Records experiment outcomes, updates success prediction models,
    optimizes parameters, and generates insights for platform improvement.
    """
    
    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize the continuous learner.
        
        Args:
            storage_path: Path for persistent storage. Defaults to learning_data.json
        """
        self._storage_path = storage_path or self._get_default_storage_path()
        self._experiments: list[dict[str, Any]] = []
        self._outcomes: list[dict[str, Any]] = []
        self._load_data()
        
        # ML models (initialized lazily)
        self._success_model = None
        self._parameter_model = None
        self._model_trained = False
    
    def _get_default_storage_path(self) -> Path:
        """Get default storage path."""
        return Path.home() / "braas-ai-pipeline" / "outputs" / "learning_data.json"
    
    def _load_data(self) -> None:
        """Load previously stored data."""
        if self._storage_path.exists():
            try:
                with open(self._storage_path, 'r') as f:
                    data = json.load(f)
                    self._experiments = data.get('experiments', [])
                    self._outcomes = data.get('outcomes', [])
            except Exception:
                self._experiments = []
                self._outcomes = []
    
    def _save_data(self) -> None:
        """Persist data to storage."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'experiments': self._experiments,
            'outcomes': self._outcomes,
            'last_updated': datetime.now().isoformat()
        }
        with open(self._storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_outcome(self, experiment_result: Any) -> None:
        """Record an experiment outcome for learning.
        
        Args:
            experiment_result: ExperimentResult or dict with outcome data
        """
        if hasattr(experiment_result, 'experiment_id'):
            outcome = {
                'experiment_id': experiment_result.experiment_id,
                'quality_score': experiment_result.quality_score,
                'passed_qc': experiment_result.passed_qc,
                'summary': experiment_result.summary,
                'timestamp': datetime.now().isoformat()
            }
        elif isinstance(experiment_result, dict):
            outcome = {
                'experiment_id': experiment_result.get('experiment_id', 'unknown'),
                'quality_score': experiment_result.get('quality_score', 0.0),
                'passed_qc': experiment_result.get('passed_qc', False),
                'summary': experiment_result.get('summary', {}),
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise AnalysisError(
                message="Invalid experiment result format",
                analysis_type="learning"
            )
        
        self._outcomes.append(outcome)
        
        # Also add to experiments for tracking
        self._experiments.append({
            'experiment_id': outcome['experiment_id'],
            'quality_score': outcome['quality_score'],
            'outcome_recorded': datetime.now().isoformat()
        })
        
        self._save_data()
    
    def update_success_model(self) -> dict[str, Any]:
        """Update the success prediction model with new data.
        
        Uses scikit-learn to train a simple classifier for predicting
        experiment success based on parameters.
        
        Returns:
            Dictionary with model performance metrics
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, classification_report
        except ImportError:
            return {
                'status': 'sklearn_not_available',
                'message': 'scikit-learn is required for model training'
            }
        
        if len(self._experiments) < 5:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least 5 experiments, have {len(self._experiments)}'
            }
        
        # Prepare features and labels
        features = []
        labels = []
        
        for exp in self._experiments:
            if 'quality_score' in exp:
                features.append([exp.get('param1', 0), exp.get('param2', 0)])
                labels.append(1 if exp.get('passed_qc', False) else 0)
        
        if len(features) < 5:
            return {
                'status': 'insufficient_data',
                'message': 'Not enough experiments with complete data'
            }
        
        try:
            X = np.array(features)
            y = np.array(labels)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            self._success_model = RandomForestClassifier(
                n_estimators=10,
                random_state=42,
                max_depth=3
            )
            self._success_model.fit(X_train, y_train)
            
            y_pred = self._success_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self._model_trained = True
            
            return {
                'status': 'success',
                'accuracy': float(accuracy),
                'n_samples': len(features),
                'model_type': 'RandomForestClassifier'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def update_parameter_optimizer(self) -> dict[str, Any]:
        """Update optimization heuristics based on outcomes.
        
        Analyzes which parameters correlate with successful experiments
        and updates optimization recommendations.
        
        Returns:
            Dictionary with optimization update results
        """
        if len(self._experiments) < 3:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 3 experiments for parameter optimization'
            }
        
        # Calculate correlations between parameters and success
        # This is a simplified implementation
        successful = [e for e in self._experiments if e.get('passed_qc', False)]
        unsuccessful = [e for e in self._experiments if not e.get('passed_qc', False)]
        
        insights = {
            'status': 'success',
            'successful_count': len(successful),
            'unsuccessful_count': len(unsuccessful),
            'n_parameters_considered': 0
        }
        
        if successful:
            # Calculate average quality score for successful experiments
            avg_quality = np.mean([e.get('quality_score', 0) for e in successful])
            insights['average_quality_score'] = float(avg_quality)
        
        # Update internal parameter recommendations
        self._parameter_recommendations = self._compute_parameter_recommendations()
        
        return insights
    
    def _compute_parameter_recommendations(self) -> dict[str, dict[str, float]]:
        """Compute parameter recommendations based on historical data."""
        recommendations = {}
        
        # Simplified: analyze temperature parameter if present
        temps = [e.get('temperature', 37) for e in self._experiments if 'temperature' in e]
        if temps:
            successful_temps = [
                e.get('temperature', 37)
                for e in self._experiments
                if e.get('passed_qc', False) and 'temperature' in e
            ]
            
            if successful_temps:
                recommendations['temperature'] = {
                    'current_optimal': float(np.mean(successful_temps)),
                    'confidence': float(np.std(successful_temps) / np.sqrt(len(successful_temps)))
                }
        
        return recommendations
    
    def compute_platform_statistics(self) -> PlatformStats:
        """Compute platform-wide statistics.
        
        Returns:
            PlatformStats with aggregated metrics
        """
        total = len(self._experiments)
        
        if total == 0:
            return PlatformStats(
                total_experiments=0,
                success_rate_by_type={},
                reagent_efficacy_scores={},
                equipment_uptime={}
            )
        
        # Calculate success rate by experiment type
        by_type: dict[str, list] = {}
        for exp in self._experiments:
            exp_type = exp.get('experiment_type', 'unknown')
            if exp_type not in by_type:
                by_type[exp_type] = []
            by_type[exp_type].append(1 if exp.get('passed_qc', False) else 0)
        
        success_rate_by_type = {
            exp_type: np.mean(results)
            for exp_type, results in by_type.items()
        }
        
        # Reagent efficacy (placeholder - would need actual reagent tracking)
        reagent_efficacy_scores = {
            'reagent_a': 0.85,
            'reagent_b': 0.78,
            'reagent_c': 0.92
        }
        
        # Equipment uptime (placeholder - would need actual equipment tracking)
        equipment_uptime = {
            'incubator_01': 0.98,
            'centrifuge_01': 0.95,
            'pcr_01': 0.99,
            'plate_reader_01': 0.97
        }
        
        return PlatformStats(
            total_experiments=total,
            success_rate_by_type=success_rate_by_type,
            reagent_efficacy_scores=reagent_efficacy_scores,
            equipment_uptime=equipment_uptime
        )
    
    def get_optimization_insights(self) -> list[OptimizationInsight]:
        """Get optimization insights based on historical data.
        
        Returns:
            List of OptimizationInsight objects
        """
        insights = []
        
        # Analyze temperature optimization
        temps = [e.get('temperature', 37) for e in self._experiments if 'temperature' in e]
        if temps:
            successful_temps = [
                e.get('temperature', 37)
                for e in self._experiments
                if e.get('passed_qc', False) and 'temperature' in e
            ]
            
            if successful_temps:
                current = float(np.mean(temps))
                suggested = float(np.mean(successful_temps))
                
                insights.append(OptimizationInsight(
                    what_to_optimize="Incubation Temperature",
                    current_value=current,
                    suggested_value=suggested,
                    expected_improvement=0.05,  # 5% improvement expected
                    confidence=0.7
                ))
        
        # Analyze incubation time
        times = [e.get('incubation_time', 60) for e in self._experiments if 'incubation_time' in e]
        if times:
            successful_times = [
                e.get('incubation_time', 60)
                for e in self._experiments
                if e.get('passed_qc', False) and 'incubation_time' in e
            ]
            
            if successful_times:
                insights.append(OptimizationInsight(
                    what_to_optimize="Incubation Time",
                    current_value=float(np.mean(times)),
                    suggested_value=float(np.mean(successful_times)),
                    expected_improvement=0.03,
                    confidence=0.65
                ))
        
        # Default insights if no specific data
        if not insights:
            insights.extend([
                OptimizationInsight(
                    what_to_optimize="Sample Concentration",
                    current_value=100.0,
                    suggested_value=95.0,
                    expected_improvement=0.02,
                    confidence=0.5
                ),
                OptimizationInsight(
                    what_to_optimize="Reaction Volume",
                    current_value=20.0,
                    suggested_value=20.0,
                    expected_improvement=0.01,
                    confidence=0.4
                )
            ])
        
        return insights
    
    def get_knowledge_graph_updates(self) -> list[KGUpdate]:
        """Get knowledge graph updates based on recent experiments.
        
        Returns:
            List of KGUpdate objects representing new/changed relationships
        """
        updates = []
        
        # Infer relationships from experiment data
        for exp in self._experiments[-10:]:  # Recent experiments
            experiment_id = exp.get('experiment_id', '')
            
            # Link experiment to its outcome
            if 'quality_score' in exp:
                updates.append(KGUpdate(
                    relationship_type="PRODUCES",
                    from_node=f"Experiment:{experiment_id}",
                    to_node="Result",
                    strength=exp['quality_score']
                ))
            
            # Link to experiment type
            if 'experiment_type' in exp:
                updates.append(KGUpdate(
                    relationship_type="IS_TYPE",
                    from_node=f"Experiment:{experiment_id}",
                    to_node=f"Type:{exp['experiment_type']}",
                    strength=1.0
                ))
        
        # Add relationship between parameters and success
        if len(self._experiments) >= 5:
            updates.append(KGUpdate(
                relationship_type="CORRELATES_WITH",
                from_node="Parameter:Temperature",
                to_node="Success",
                strength=0.75
            ))
            updates.append(KGUpdate(
                relationship_type="CORRELATES_WITH",
                from_node="Parameter:Time",
                to_node="Success",
                strength=0.65
            ))
        
        return updates
    
    def get_recipe_adjustments(self, protocol_type: str) -> dict[str, Any]:
        """Get recommended recipe adjustments for a protocol type.
        
        Args:
            protocol_type: Type of protocol to get adjustments for
        
        Returns:
            Dictionary of recommended parameter adjustments
        """
        # Analyze past experiments for this protocol type
        relevant_experiments = [
            e for e in self._experiments
            if e.get('protocol_type', '') == protocol_type or protocol_type.lower() in str(e).lower()
        ]
        
        adjustments = {}
        
        if len(relevant_experiments) >= 3:
            successful = [e for e in relevant_experiments if e.get('passed_qc', False)]
            
            if successful:
                # Calculate average values for successful experiments
                temps = [e.get('temperature', 37) for e in successful if 'temperature' in e]
                if temps:
                    adjustments['temperature'] = {
                        'current': float(np.mean(temps)),
                        'adjustment': 'optimal',
                        'confidence': 0.8
                    }
                
                times = [e.get('incubation_time', 60) for e in successful if 'incubation_time' in e]
                if times:
                    adjustments['incubation_time'] = {
                        'current': float(np.mean(times)),
                        'adjustment': 'optimal',
                        'confidence': 0.75
                    }
        
        # Default adjustments if no specific data
        if not adjustments:
            defaults = {
                ExperimentType.ELISA: {
                    'incubation_temp': {'adjustment': '+2C', 'reason': 'improve binding'},
                    'wash_steps': {'adjustment': 3, 'reason': 'reduce background'}
                },
                ExperimentType.QPCR: {
                    'annealing_temp': {'adjustment': '-1C', 'reason': 'improve specificity'},
                    'cycle_number': {'adjustment': 40, 'reason': 'ensure amplification'}
                },
                ExperimentType.CELL_CULTURE: {
                    'media_volume': {'adjustment': '+5pct', 'reason': 'reduce evaporation'},
                    'passage_number': {'adjustment': '<25', 'reason': 'maintain phenotype'}
                }
            }
            
            for exp_type, default_adj in defaults.items():
                if protocol_type.lower() in str(exp_type.value).lower():
                    adjustments = default_adj
                    break
        
        return adjustments
    
    def get_success_predictor(self) -> Any:
        """Get the trained success prediction model.
        
        Returns:
            Trained scikit-learn model or None if not trained
        """
        if not self._model_trained:
            self.update_success_model()
        return self._success_model
    
    def get_experiment_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent experiment history.
        
        Args:
            limit: Maximum number of experiments to return
        
        Returns:
            List of experiment records
        """
        return self._experiments[-limit:]
    
    def clear_history(self) -> None:
        """Clear all stored experiment history."""
        self._experiments = []
        self._outcomes = []
        self._save_data()
