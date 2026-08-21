from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.io import arff

from backend.services.config import KAGGLE_DIR, PROCESSED_DIR


TARGET_CANDIDATES = ("defects", "defect_label", "defective", "bug", "bugs", "problems", "label", "class", "c")


@dataclass
class PreparedDefectDataset:
    features: pd.DataFrame
    target: pd.Series
    feature_names: list[str]
    source_summary: list[dict]


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, na_values=["?", "NA", "N/A", "null", "None"])


def _load_arff(path: Path) -> pd.DataFrame:
    data, _ = arff.loadarff(path)
    df = pd.DataFrame(data)
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].apply(
                lambda value: value.decode("utf-8") if isinstance(value, (bytes, bytearray)) else value
            )
    return df


def _normalize_column_name(name: str) -> str:
    return (
        name.strip()
        .replace("(", "_")
        .replace(")", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".", "_")
        .lower()
    )


def _normalize_target(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(int)
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({"1", "true", "yes", "y", "buggy", "defective"}).astype(int)


def _prepare_single_dataset(path: Path) -> tuple[pd.DataFrame, pd.Series, dict]:
    if path.suffix.lower() == ".csv":
        df = _load_csv(path)
    elif path.suffix.lower() == ".arff":
        df = _load_arff(path)
    else:
        raise ValueError(f"Unsupported dataset type: {path}")

    original_columns = list(df.columns)
    df.columns = [_normalize_column_name(col) for col in df.columns]

    target_column = next((candidate for candidate in TARGET_CANDIDATES if candidate in df.columns), None)
    if target_column is None:
        raise ValueError(f"Could not find target column in {path.name}")

    target = _normalize_target(df[target_column])
    features = df.drop(columns=[target_column], errors="ignore")
    features = features.drop(columns=["id", "name", "version"], errors="ignore")

    for column in features.columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")

    features = features.replace([np.inf, -np.inf], np.nan)
    summary = {
        "dataset": path.name,
        "rows": int(len(df)),
        "feature_count": int(features.shape[1]),
        "defect_rate": float(target.mean()) if len(target) else 0.0,
        "original_columns": original_columns,
    }
    return features, target, summary


def load_and_union_defect_datasets(extra_paths: Iterable[Path] | None = None) -> PreparedDefectDataset:
    base_paths = [
        KAGGLE_DIR / "cm1.csv",
        KAGGLE_DIR / "jm1.csv",
        KAGGLE_DIR / "SoftwareDefectDataset.csv",
    ]
    arff_dir = KAGGLE_DIR / "Dataset"
    arff_paths = sorted(arff_dir.glob("*.arff"))
    dataset_paths = [path for path in base_paths + arff_paths if path.exists()]
    if extra_paths:
        dataset_paths.extend(extra_paths)

    feature_frames: list[pd.DataFrame] = []
    targets: list[pd.Series] = []
    summaries: list[dict] = []

    for path in dataset_paths:
        features, target, summary = _prepare_single_dataset(path)
        feature_frames.append(features)
        targets.append(target)
        summaries.append(summary)

    union_features = sorted({column for frame in feature_frames for column in frame.columns})
    aligned_frames = [frame.reindex(columns=union_features) for frame in feature_frames]
    full_features = pd.concat(aligned_frames, ignore_index=True)
    full_target = pd.concat(targets, ignore_index=True)

    return PreparedDefectDataset(
        features=full_features,
        target=full_target,
        feature_names=union_features,
        source_summary=summaries,
    )


def export_prepared_dataset(path: Path | None = None) -> dict:
    prepared = load_and_union_defect_datasets()
    target_path = path or (PROCESSED_DIR / "defect_union_dataset.csv")
    export_df = prepared.features.copy()
    export_df["target"] = prepared.target
    export_df.to_csv(target_path, index=False)

    metadata = {
        "path": str(target_path),
        "row_count": int(len(export_df)),
        "feature_count": int(len(prepared.feature_names)),
        "sources": prepared.source_summary,
    }
    (PROCESSED_DIR / "defect_union_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
