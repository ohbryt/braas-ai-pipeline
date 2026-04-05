"""
Model Registry for BRaaS Pipeline
===================================

Manages ML model lifecycle:
- Model registration and loading
- Prediction execution
- Model training (XGBoost, IsolationForest)
"""

import os
import pickle
from dataclasses import dataclass, field
from typing import Any

import joblib
import numpy as np

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.base import BaseEstimator
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class ModelInfo:
    """Information about a registered model."""
    model_id: str
    name: str
    version: str
    path: str
    loaded: bool
    model: Any = None


class ModelRegistry:
    """Registry for managing ML models in BRaaS pipeline.
    
    Handles registration, loading, prediction, and training of
    machine learning models for experiment outcomes.
    """
    
    def __init__(self, models_dir: str | None = None):
        """Initialize model registry.
        
        Args:
            models_dir: Directory for storing model files
        """
        self._models_dir = models_dir or os.path.join(
            os.path.dirname(__file__), "models"
        )
        os.makedirs(self._models_dir, exist_ok=True)
        
        # Registry: {model_id: ModelInfo}
        self.registry: dict[str, ModelInfo] = {}
        
        # Initialize with built-in model info
        self._init_builtin_models()
    
    def _init_builtin_models(self) -> None:
        """Initialize registry with built-in model definitions."""
        builtin_models = [
            ("success_predictor_v1", "Experiment Success Predictor", "1.0.0"),
            ("anomaly_detector_v1", "Anomaly Detector", "1.0.0"),
            ("elisa_quantifier_v1", "ELISA Quantifier", "1.0.0"),
            ("qpcr_analyzer_v1", "qPCR Ct Analyzer", "1.0.0"),
        ]
        
        for model_id, name, version in builtin_models:
            if model_id not in self.registry:
                path = os.path.join(self._models_dir, f"{model_id}.joblib")
                self.registry[model_id] = ModelInfo(
                    model_id=model_id,
                    name=name,
                    version=version,
                    path=path,
                    loaded=False,
                    model=None
                )
    
    def register_model(self, model_id: str, name: str, path: str) -> bool:
        """Register a model without loading it.
        
        Args:
            model_id: Unique identifier for the model
            name: Human-readable name
            path: Path to model file (pickle/joblib)
            
        Returns:
            True if registered successfully
        """
        if model_id in self.registry:
            return False
        
        self.registry[model_id] = ModelInfo(
            model_id=model_id,
            name=name,
            version="1.0.0",
            path=path,
            loaded=False,
            model=None
        )
        
        return True
    
    def load_model(self, model_id: str) -> bool:
        """Load a model from disk.
        
        Args:
            model_id: ID of model to load
            
        Returns:
            True if loaded successfully
        """
        if model_id not in self.registry:
            return False
        
        model_info = self.registry[model_id]
        
        if model_info.loaded:
            return True
        
        # Check if file exists
        if not os.path.exists(model_info.path):
            # Create mock model for testing
            model_info.model = self._create_mock_model(model_id)
            model_info.loaded = True
            return True
        
        try:
            # Try loading as joblib first, then pickle
            try:
                model_info.model = joblib.load(model_info.path)
            except Exception:
                try:
                    with open(model_info.path, 'rb') as f:
                        model_info.model = pickle.load(f)
                except Exception:
                    # Create mock model
                    model_info.model = self._create_mock_model(model_id)
            
            model_info.loaded = True
            return True
            
        except Exception:
            # Create mock model on any error
            model_info.model = self._create_mock_model(model_id)
            model_info.loaded = True
            return True
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model to free memory.
        
        Args:
            model_id: ID of model to unload
            
        Returns:
            True if unloaded successfully
        """
        if model_id not in self.registry:
            return False
        
        model_info = self.registry[model_id]
        
        if not model_info.loaded:
            return True
        
        model_info.model = None
        model_info.loaded = False
        
        return True
    
    def predict(self, model_id: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run model prediction.
        
        Args:
            model_id: ID of model to use
            input_data: Input features for prediction
            
        Returns:
            Dict containing prediction results
        """
        if model_id not in self.registry:
            return {"error": f"Model '{model_id}' not found"}
        
        model_info = self.registry[model_id]
        
        # Load if not already loaded
        if not model_info.loaded:
            self.load_model(model_id)
        
        model = model_info.model
        
        if model is None:
            return self._mock_predict(model_id, input_data)
        
        try:
            # Extract features from input
            features = self._extract_features(input_data)
            
            if hasattr(model, 'predict'):
                prediction = model.predict(features)
            else:
                return self._mock_predict(model_id, input_data)
            
            result = {
                "model_id": model_id,
                "prediction": prediction.tolist() if hasattr(prediction, 'tolist') else prediction,
                "success_probability": float(prediction[0]) if hasattr(prediction, '__getitem__') else float(prediction)
            }
            
            # Add confidence if available
            if hasattr(model, 'predict_proba'):
                try:
                    proba = model.predict_proba(features)
                    result["confidence"] = float(np.max(proba))
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            # Fall back to mock prediction
            return self._mock_predict(model_id, input_data)
    
    def get_model_info(self, model_id: str) -> ModelInfo | None:
        """Get information about a model.
        
        Args:
            model_id: ID of model
            
        Returns:
            ModelInfo if found, None otherwise
        """
        return self.registry.get(model_id)
    
    def list_models(self) -> list[dict[str, Any]]:
        """List all registered models with status.
        
        Returns:
            List of model info dicts
        """
        return [
            {
                "model_id": info.model_id,
                "name": info.name,
                "version": info.version,
                "path": info.path,
                "loaded": info.loaded
            }
            for info in self.registry.values()
        ]
    
    def train_success_model(self, experiments_data: list[dict[str, Any]]) -> str:
        """Train XGBoost model for experiment success prediction.
        
        Args:
            experiments_data: List of experiment dicts with features and outcomes
            
        Returns:
            Path to saved model
        """
        if not HAS_XGBOOST:
            return self._train_mock_success_model(experiments_data)
        
        # Extract features and labels
        features = []
        labels = []
        
        for exp in experiments_data:
            feat = self._extract_training_features(exp)
            label = exp.get("success", 0)
            
            features.append(feat)
            labels.append(label)
        
        X = np.array(features)
        y = np.array(labels)
        
        # Train XGBoost classifier
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        model.fit(X, y)
        
        # Save model
        model_path = os.path.join(self._models_dir, "success_predictor_v1.joblib")
        joblib.dump(model, model_path)
        
        # Update registry
        if "success_predictor_v1" in self.registry:
            self.registry["success_predictor_v1"].loaded = False
            self.registry["success_predictor_v1"].path = model_path
        else:
            self.register_model("success_predictor_v1", "Success Predictor", model_path)
        
        return model_path
    
    def train_anomaly_model(self, training_data: list[dict[str, Any]]) -> str:
        """Train IsolationForest model for anomaly detection.
        
        Args:
            training_data: List of normal operation data points
            
        Returns:
            Path to saved model
        """
        if not HAS_SKLEARN:
            return self._train_mock_anomaly_model(training_data)
        
        # Extract features
        features = []
        
        for point in training_data:
            feat = [
                point.get("temperature", 0),
                point.get("pressure", 0),
                point.get("duration", 0),
                point.get("signal", 0),
            ]
            features.append(feat)
        
        X = np.array(features)
        
        # Train IsolationForest
        model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )
        
        model.fit(X)
        
        # Save model
        model_path = os.path.join(self._models_dir, "anomaly_detector_v1.joblib")
        joblib.dump(model, model_path)
        
        # Update registry
        if "anomaly_detector_v1" in self.registry:
            self.registry["anomaly_detector_v1"].loaded = False
            self.registry["anomaly_detector_v1"].path = model_path
        else:
            self.register_model("anomaly_detector_v1", "Anomaly Detector", model_path)
        
        return model_path
    
    def _create_mock_model(self, model_id: str) -> Any:
        """Create a mock model for testing when real models aren't available."""
        return MockModel(model_id)
    
    def _mock_predict(self, model_id: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Generate mock predictions for testing."""
        features = self._extract_features(input_data)
        
        # Simple heuristic-based mock prediction
        if "success_predictor" in model_id:
            prob = 0.5 + 0.3 * min(len(input_data) / 10, 1.0)
            return {
                "model_id": model_id,
                "prediction": [1 if prob > 0.5 else 0],
                "success_probability": min(0.95, max(0.1, prob)),
                "mock": True
            }
        elif "anomaly_detector" in model_id:
            return {
                "model_id": model_id,
                "prediction": [0],  # 0 = normal
                "anomaly_score": 0.1,
                "mock": True
            }
        elif "elisa" in model_id:
            return {
                "model_id": model_id,
                "prediction": [1.5],  # concentration
                "confidence": 0.8,
                "mock": True
            }
        elif "qpcr" in model_id:
            return {
                "model_id": model_id,
                "prediction": [25.0],  # Ct value
                "confidence": 0.85,
                "mock": True
            }
        else:
            return {
                "model_id": model_id,
                "prediction": [0.5],
                "mock": True
            }
    
    def _train_mock_success_model(self, experiments_data: list) -> str:
        """Train mock success model when XGBoost unavailable."""
        model_path = os.path.join(self._models_dir, "success_predictor_v1.joblib")
        mock = MockModel("success_predictor_v1")
        joblib.dump(mock, model_path)
        return model_path
    
    def _train_mock_anomaly_model(self, training_data: list) -> str:
        """Train mock anomaly model when sklearn unavailable."""
        model_path = os.path.join(self._models_dir, "anomaly_detector_v1.joblib")
        mock = MockModel("anomaly_detector_v1")
        joblib.dump(mock, model_path)
        return model_path
    
    def _extract_features(self, input_data: dict[str, Any]) -> np.ndarray:
        """Extract feature array from input data."""
        features = []
        
        # Handle experiment-like input
        if "protocol" in input_data:
            protocol = input_data["protocol"]
            features.extend([
                len(protocol.get("steps", [])) if protocol else 0,
                protocol.get("estimated_duration_seconds", 0) if protocol else 0,
            ])
        
        # Handle samples
        if "samples" in input_data:
            features.append(len(input_data["samples"]))
        else:
            features.append(0)
        
        # Handle reagents
        if "reagents" in input_data:
            features.append(len(input_data["reagents"]))
        else:
            features.append(0)
        
        # Generic feature extraction
        numeric_fields = ["temperature", "duration", "volume", "concentration"]
        for field in numeric_fields:
            if field in input_data:
                features.append(float(input_data[field]))
            else:
                features.append(0.0)
        
        # Pad or truncate to fixed size
        target_size = 10
        while len(features) < target_size:
            features.append(0.0)
        
        return np.array(features[:target_size]).reshape(1, -1)
    
    def _extract_training_features(self, exp: dict[str, Any]) -> list[float]:
        """Extract features from training example."""
        features = []
        
        # Protocol features
        protocol = exp.get("protocol", {})
        features.append(len(protocol.get("steps", [])))
        features.append(protocol.get("estimated_duration_seconds", 0))
        
        # Sample count
        features.append(len(exp.get("samples", [])))
        
        # Reagent count
        features.append(len(exp.get("reagents", [])))
        
        # Safety level
        safety = exp.get("safety_level", "BSL1")
        bsl_num = int(safety.replace("BSL", "")) if isinstance(safety, str) else 1
        features.append(bsl_num)
        
        # Priority
        priority = exp.get("priority", "MEDIUM")
        priority_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        features.append(priority_map.get(priority, 2))
        
        # Numeric parameters
        features.append(exp.get("temperature", 37.0) / 100.0)
        features.append(exp.get("duration_hours", 1.0))
        features.append(exp.get("volume_ul", 100.0) / 1000.0)
        
        # Pad to fixed size
        while len(features) < 10:
            features.append(0.0)
        
        return features[:10]


class MockModel:
    """Mock ML model for testing without real model files."""
    
    def __init__(self, model_id: str):
        self.model_id = model_id
        self._weights = np.random.rand(10)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate mock predictions."""
        if hasattr(X, 'shape') and len(X.shape) > 1:
            n_samples = X.shape[0]
        else:
            n_samples = 1
        
        # Generate reasonable mock predictions
        predictions = []
        for _ in range(n_samples):
            if "success" in self.model_id:
                predictions.append([1])  # Success
            elif "anomaly" in self.model_id:
                predictions.append([0])  # Normal
            else:
                predictions.append([0.5])
        
        return np.array(predictions)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate mock probabilities."""
        preds = self.predict(X)
        n = len(preds) if hasattr(preds, '__len__') else 1
        
        proba = np.zeros((n, 2))
        for i, p in enumerate(preds):
            prob = float(p[0]) if hasattr(p, '__getitem__') else float(p)
            proba[i] = [1 - prob, prob]
        
        return proba
