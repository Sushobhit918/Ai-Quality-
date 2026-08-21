from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from backend.services.config import MODELS_DIR
from ml.preprocess import export_prepared_dataset
from ml.train_model import train_and_persist_models


class DefectPredictionService:
    def __init__(self, model_dir: Path | None = None) -> None:
        self.model_dir = model_dir or MODELS_DIR
        self._model = None
        self._model_card = None

    @property
    def model_card(self) -> dict[str, Any]:
        if self._model_card is None:
            model_card_path = self.model_dir / "model_card.json"
            if not model_card_path.exists():
                self.train()
            self._model_card = json.loads(model_card_path.read_text(encoding="utf-8"))
        return self._model_card

    @property
    def model(self):
        if self._model is None:
            model_path = self.model_dir / f"{self.model_card['best_model']}.joblib"
            self._model = joblib.load(model_path)
        return self._model

    def train(self) -> dict[str, Any]:
        export_prepared_dataset()
        self._model_card = train_and_persist_models(self.model_dir)
        self._model = None
        return self._model_card

    def predict(self, feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not feature_rows:
            return []
        feature_names = self.model_card["feature_names"]
        frame = pd.DataFrame(feature_rows).reindex(columns=feature_names)
        probabilities = self.model.predict_proba(frame)[:, 1]
        threshold = self.model_card["metrics"][self.model_card["best_model"]]["threshold"]
        return [
            {
                "row_index": index,
                "defect_probability": float(probability),
                "is_high_risk": bool(probability >= threshold),
                "risk_level": "high" if probability >= 0.7 else "medium" if probability >= threshold else "low",
            }
            for index, probability in enumerate(probabilities)
        ]
