from __future__ import annotations

import logging
from collections import Counter

import numpy as np
import pandas as pd

from .config import DBSCAN_EPS, DBSCAN_MIN_DATASET_SIZE, DBSCAN_MIN_SAMPLES
from .preprocessing import COMPARISON_METRICS, impute_fund_metrics

try:
    from sklearn.cluster import DBSCAN
    from sklearn.decomposition import PCA
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import RobustScaler
except ImportError:  # pragma: no cover - only for minimal environments
    DBSCAN = None
    PCA = None
    cosine_similarity = None
    NearestNeighbors = None
    RobustScaler = None


logger = logging.getLogger(__name__)

DBSCAN_FEATURES = [
    "return_3y",
    "return_5y",
    "sharpe_ratio",
    "sortino_ratio",
    "alpha",
    "beta",
    "calmar_ratio",
    "standard_deviation",
    "downside_deviation",
    "max_drawdown",
    "expense_ratio",
    "info_ratio",
    "tracking_error",
    "capture_ratio",
    "turnover",
]


def _standardize(matrix: np.ndarray) -> np.ndarray:
    if RobustScaler is not None:
        return np.clip(RobustScaler().fit_transform(matrix), -4, 4)
    median = np.nanmedian(matrix, axis=0)
    q1 = np.nanpercentile(matrix, 25, axis=0)
    q3 = np.nanpercentile(matrix, 75, axis=0)
    iqr = q3 - q1
    iqr[iqr == 0] = 1.0
    matrix = np.where(np.isnan(matrix), median, matrix)
    return np.clip((matrix - median) / iqr, -4, 4)


def behavior_feature_matrix(df: pd.DataFrame, metrics: list[str] | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Return only fund-behavior metrics for DBSCAN.

    NAV, AMC, fund name, lock-in, exit-load, fund id, and minimum investment are
    intentionally excluded because DBSCAN is grouping behavior, not suitability.
    """
    metrics = [m for m in (metrics or DBSCAN_FEATURES) if m in df.columns]
    numeric = df[metrics].apply(pd.to_numeric, errors="coerce")
    return numeric.fillna(numeric.median()).fillna(0), metrics


def tune_dbscan_eps(matrix: np.ndarray, min_samples: int = DBSCAN_MIN_SAMPLES) -> float:
    """Estimate eps with the kth-distance method.

    This is a helper, not a training target: for small dummy datasets the
    configured eps remains the stable default, while this gives advisors a
    data-driven value to inspect when replacing synthetic data.
    """
    if len(matrix) <= min_samples or NearestNeighbors is None:
        return DBSCAN_EPS
    neighbors = NearestNeighbors(n_neighbors=min_samples).fit(matrix)
    distances, _ = neighbors.kneighbors(matrix)
    kth_distances = np.sort(distances[:, -1])
    return float(np.percentile(kth_distances, 75))


def _pca_2d(matrix: np.ndarray) -> np.ndarray:
    if matrix.shape[1] == 0 or len(matrix) == 0:
        return np.zeros((len(matrix), 2))
    if PCA is not None and len(matrix) >= 2:
        return PCA(n_components=2, random_state=42).fit_transform(matrix)
    centered = matrix - matrix.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vt[:2].T
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    return coords[:, :2]


def _simple_dbscan(matrix: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    labels = np.full(len(matrix), -1, dtype=int)
    cluster_id = 0
    for i in range(len(matrix)):
        if labels[i] != -1:
            continue
        distances = np.linalg.norm(matrix - matrix[i], axis=1)
        neighbors = np.where(distances <= eps)[0]
        if len(neighbors) < min_samples:
            continue
        labels[neighbors] = cluster_id
        seeds = list(neighbors)
        while seeds:
            point = seeds.pop()
            point_neighbors = np.where(np.linalg.norm(matrix - matrix[point], axis=1) <= eps)[0]
            if len(point_neighbors) >= min_samples:
                for n in point_neighbors:
                    if labels[n] == -1:
                        labels[n] = cluster_id
                        seeds.append(n)
        cluster_id += 1
    return labels


def _dominant(values: pd.Series) -> str:
    clean = [str(v) for v in values.dropna().tolist() if str(v)]
    return Counter(clean).most_common(1)[0][0] if clean else ""


def _cluster_summaries(df: pd.DataFrame) -> dict[int, dict[str, object]]:
    summaries: dict[int, dict[str, object]] = {}
    for label, group in df.groupby("dbscan_cluster_id"):
        metrics = {
            key: round(float(pd.to_numeric(group[key], errors="coerce").mean()), 3)
            for key in [
                "return_3y",
                "return_5y",
                "sharpe_ratio",
                "sortino_ratio",
                "standard_deviation",
                "max_drawdown",
                "expense_ratio",
            ]
            if key in group.columns
        }
        avg_risk = pd.to_numeric(group.get("standard_deviation", pd.Series(0, index=group.index)), errors="coerce").mean()
        risk_profile = "stable" if avg_risk < 8 else "moderate" if avg_risk < 15 else "high volatility"
        summaries[int(label)] = {
            **metrics,
            "dominant_category": _dominant(group.get("category", pd.Series(dtype=str))),
            "dominant_sub_category": _dominant(group.get("sub_category", pd.Series(dtype=str))),
            "risk_profile": risk_profile,
            "cluster_size": int(len(group)),
        }
    return summaries


def cluster_funds(
    df: pd.DataFrame,
    eps: float = DBSCAN_EPS,
    min_samples: int = DBSCAN_MIN_SAMPLES,
) -> tuple[pd.DataFrame, dict[str, object]]:
    if df.empty:
        return df.copy(), {"algorithm": "DBSCAN", "selected_metrics": [], "warnings": ["No funds available for clustering."]}

    prepared = impute_fund_metrics(df)
    matrix_df, selected = behavior_feature_matrix(prepared)
    matrix = _standardize(matrix_df.to_numpy(dtype=float))
    coords = _pca_2d(matrix)

    warnings: list[str] = []
    effective_eps = eps
    if len(prepared) < DBSCAN_MIN_DATASET_SIZE or DBSCAN is None:
        labels = np.zeros(len(prepared), dtype=int)
        warnings.append("Dataset is too small for reliable DBSCAN; assigned all funds to one provisional cluster.")
    else:
        labels = DBSCAN(eps=effective_eps, min_samples=min_samples).fit_predict(matrix)
        for factor in [1.25, 1.5, 1.75, 2.0]:
            noise_ratio = float((labels == -1).sum()) / len(labels)
            cluster_count = len(set(labels) - {-1})
            if cluster_count > 0 and noise_ratio <= 0.60:
                break
            effective_eps = eps * factor
            labels = DBSCAN(eps=effective_eps, min_samples=min_samples).fit_predict(matrix)
        if len(set(labels) - {-1}) == 0:
            warnings.append("DBSCAN marked all funds as noise; consider increasing eps.")
        elif effective_eps != eps:
            warnings.append(
                f"DBSCAN eps auto-adjusted from {eps:g} to {effective_eps:g} because the starting value produced too many outliers."
            )
        elif len(set(labels) - {-1}) == 1 and (labels != -1).sum() > len(labels) * 0.85:
            warnings.append("DBSCAN produced one large cluster; consider decreasing eps.")

    clustered = prepared.copy()
    clustered["dbscan_cluster_id"] = labels.astype(int)
    clustered["cluster_id"] = clustered["dbscan_cluster_id"]
    clustered["is_outlier"] = clustered["dbscan_cluster_id"].eq(-1)
    cluster_sizes = clustered.groupby("dbscan_cluster_id")["dbscan_cluster_id"].transform("size")
    clustered["cluster_size"] = cluster_sizes.astype(int)
    clustered["pca_x"] = coords[:, 0]
    clustered["pca_y"] = coords[:, 1]

    summaries = _cluster_summaries(clustered)
    clustered["cluster_summary"] = clustered["dbscan_cluster_id"].map(lambda label: summaries.get(int(label), {}))

    cluster_count = len(set(labels) - {-1})
    noise_count = int((labels == -1).sum())
    logger.info("DBSCAN produced %s clusters with %s noise/outlier funds", cluster_count, noise_count)
    diagnostics = {
        "algorithm": "DBSCAN",
        "configured_eps": eps,
        "eps": effective_eps,
        "min_samples": min_samples,
        "tuned_eps_suggestion": round(tune_dbscan_eps(matrix, min_samples), 4),
        "selected_metrics": selected,
        "cluster_count": cluster_count,
        "noise_count": noise_count,
        "cluster_summaries": summaries,
        "warnings": warnings,
    }
    return clustered, diagnostics


def cosine_similar_funds(clustered: pd.DataFrame, fund_id: int | float, top_n: int = 3) -> list[dict[str, object]]:
    if clustered.empty or "fund_id" not in clustered.columns:
        return []
    matrix_df, selected = behavior_feature_matrix(clustered)
    if not selected:
        return []
    matrix = _standardize(matrix_df.to_numpy(dtype=float))
    ids = clustered["fund_id"].tolist()
    try:
        index = ids.index(fund_id)
    except ValueError:
        return []

    target_label = int(clustered.iloc[index].get("dbscan_cluster_id", clustered.iloc[index].get("cluster_id", -1)))
    target_is_outlier = target_label == -1
    if target_is_outlier:
        candidate_positions = [i for i in range(len(clustered)) if i != index]
    else:
        candidate_positions = [
            i
            for i, row in enumerate(clustered.itertuples())
            if int(getattr(row, "dbscan_cluster_id", getattr(row, "cluster_id", -1))) == target_label and i != index
        ]
        if not candidate_positions:
            candidate_positions = [i for i in range(len(clustered)) if i != index]

    if cosine_similarity is not None:
        similarity = cosine_similarity(matrix[index].reshape(1, -1), matrix).ravel()
    else:
        target = matrix[index]
        denom = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(target) or 1.0)
        similarity = np.divide(matrix @ target, denom, out=np.zeros(len(matrix)), where=denom != 0)

    order = sorted(candidate_positions, key=lambda pos: similarity[pos], reverse=True)
    output = []
    for pos in order[:top_n]:
        row = clustered.iloc[pos]
        output.append(
            {
                "fund_id": row.get("fund_id"),
                "mutual_fund_name": row.get("mutual_fund_name"),
                "category": row.get("category"),
                "sub_category": row.get("sub_category"),
                "dbscan_cluster_id": int(row.get("dbscan_cluster_id", -1)),
                "cluster_id": int(row.get("dbscan_cluster_id", -1)),
                "is_outlier": bool(row.get("is_outlier", False)),
                "similarity": round(float(similarity[pos]), 4),
                "similarity_scope": "global_approximate" if target_is_outlier else "same_dbscan_cluster",
            }
        )
    return output
