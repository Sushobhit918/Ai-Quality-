from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from backend.services.config import MODELS_DIR
from ml.preprocess import load_and_union_defect_datasets


def build_model_candidates(random_state: int = 42) -> dict[str, Pipeline]:
    shared_steps = [
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("smote", SMOTE(random_state=random_state)),
    ]
    return {
        "random_forest": Pipeline(
            shared_steps
            + [
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=400,
                        min_samples_leaf=2,
                        class_weight="balanced_subsample",
                        random_state=random_state,
                        n_jobs=1,
                    ),
                )
            ]
        ),
        "svm": Pipeline(
            shared_steps
            + [
                (
                    "classifier",
                    SVC(
                        C=1.5,
                        kernel="rbf",
                        probability=True,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                )
            ]
        ),
        "logistic_regression": Pipeline(
            shared_steps
            + [
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        solver="lbfgs",
                    ),
                )
            ]
        ),
        "ann": Pipeline(
            shared_steps
            + [
                (
                    "classifier",
                    MLPClassifier(
                        hidden_layer_sizes=(128, 64),
                        activation="relu",
                        learning_rate="adaptive",
                        max_iter=300,
                        early_stopping=True,
                        random_state=random_state,
                    ),
                )
            ]
        ),
    }


def _evaluate_model(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict:
    probabilities = model.predict_proba(x_test)[:, 1]
    threshold = 0.40
    predictions = (probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, predictions, average="binary", zero_division=0)
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "threshold": threshold,
        "report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
    }


def train_and_persist_models(output_dir: Path | None = None, max_training_rows: int = 12000) -> dict:
    target_dir = output_dir or MODELS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    prepared = load_and_union_defect_datasets()
    if len(prepared.features) > max_training_rows:
        full_frame = prepared.features.assign(target=prepared.target)
        sample_fraction = max_training_rows / len(full_frame)
        sampled = (
            pd.concat(
                [
                    group.sample(frac=sample_fraction, random_state=42)
                    for _, group in full_frame.groupby("target")
                ],
                ignore_index=True,
            )
            .sample(frac=1.0, random_state=42)
            .reset_index(drop=True)
        )
        prepared.features = sampled.drop(columns=["target"])
        prepared.target = sampled["target"]

    x_train, x_test, y_train, y_test = train_test_split(
        prepared.features,
        prepared.target,
        test_size=0.2,
        stratify=prepared.target,
        random_state=42,
    )

    candidates = build_model_candidates()
    evaluation: dict[str, dict] = {}
    best_name = ""
    best_score = -np.inf

    for name, model in candidates.items():
        model.fit(x_train, y_train)
        metrics = _evaluate_model(model, x_test, y_test)
        evaluation[name] = metrics
        if metrics["recall"] > best_score or (
            np.isclose(metrics["recall"], best_score) and metrics["f1"] > evaluation.get(best_name, {}).get("f1", -1)
        ):
            best_name = name
            best_score = metrics["recall"]
        joblib.dump(model, target_dir / f"{name}.joblib")

    model_card = {
        "best_model": best_name,
        "feature_names": prepared.feature_names,
        "dataset_summary": prepared.source_summary,
        "metrics": evaluation,
        "optimization_goal": "maximize defect recall while retaining reasonable precision",
    }
    (target_dir / "model_card.json").write_text(json.dumps(model_card, indent=2), encoding="utf-8")
    return model_card


if __name__ == "__main__":
    result = train_and_persist_models()
    print(json.dumps(result, indent=2))
