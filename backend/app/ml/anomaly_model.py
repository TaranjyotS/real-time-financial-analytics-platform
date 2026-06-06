from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"


class AnomalyDetector:
    def __init__(self) -> None:
        self.model = self._load_or_train()

    def _load_or_train(self):
        if MODEL_PATH.exists():
            return joblib.load(MODEL_PATH)
        rng = np.random.default_rng(42)
        normal = np.column_stack([
            rng.normal(500, 250, 1000),
            rng.normal(10, 5, 1000),
            rng.normal(50, 20, 1000),
            rng.integers(0, 24, 1000),
            rng.normal(365, 120, 1000),
        ])
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(normal)
        joblib.dump(model, MODEL_PATH)
        return model

    def score(self, features: list[float]) -> tuple[float, bool]:
        arr = np.array(features).reshape(1, -1)
        raw = float(self.model.decision_function(arr)[0])
        prediction = int(self.model.predict(arr)[0])
        score = max(0.0, min(1.0, 0.5 - raw))
        return round(score, 4), prediction == -1
