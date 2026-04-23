from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.recipe import Recipe
from backend.app.services.auto_meal_plan_training_dataset import (
    build_recipe_feature_profiles,
    empty_recipe_feature_profile,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = PROJECT_ROOT / "data" / "ml_models"
AUTO_MEAL_PLAN_MODEL_FILENAME = "auto_meal_plan_latest.joblib"

HEURISTIC_ENGINE_VERSION = "heuristic_v1"
AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION = "hybrid_ml_v1"

ML_ACCEPTANCE_SCORE_WEIGHT = 20.0
ML_HIGH_CONFIDENCE_THRESHOLD = 0.70
ML_LOW_CONFIDENCE_THRESHOLD = 0.35

_cached_model_artifact: dict[str, Any] | None = None
_cached_model_mtime: float | None = None


@dataclass
class ModelScoreResult:
    acceptance_probability: float
    blended_score: float
    engine_version: str
    reason: str | None = None


@dataclass
class AutoMealPlanModelScorer:
    artifact: dict[str, Any] | None
    recipe_feature_profiles: dict[int, dict[str, int]]

    @property
    def is_active(self) -> bool:
        return self.artifact is not None

    @property
    def engine_version(self) -> str:
        if not self.artifact:
            return HEURISTIC_ENGINE_VERSION
        return str(self.artifact.get("engine_version") or AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION)

    def score_candidate(
        self,
        *,
        household_id: int,
        plan_date: date,
        meal_type: str,
        recipe: Recipe,
        heuristic_score: float,
        average_rating: float | None,
        ratings_count: int,
    ) -> ModelScoreResult | None:
        if not self.artifact:
            return None

        profile = self.recipe_feature_profiles.get(recipe.id, empty_recipe_feature_profile())
        row = build_candidate_feature_row(
            household_id=household_id,
            plan_date=plan_date,
            meal_type=meal_type,
            recipe=recipe,
            heuristic_score=heuristic_score,
            average_rating=average_rating,
            ratings_count=ratings_count,
            recipe_profile=profile,
        )
        acceptance_probability = score_candidate_acceptance_probability(self.artifact, row)
        if acceptance_probability is None:
            return None

        blended_score = round(
            float(heuristic_score) + (float(acceptance_probability) - 0.5) * ML_ACCEPTANCE_SCORE_WEIGHT,
            2,
        )
        return ModelScoreResult(
            acceptance_probability=float(acceptance_probability),
            blended_score=blended_score,
            engine_version=self.engine_version,
            reason=build_model_reason(float(acceptance_probability)),
        )


def ensure_model_dir() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def get_published_model_path() -> Path:
    return MODEL_DIR / AUTO_MEAL_PLAN_MODEL_FILENAME


def clear_published_auto_meal_plan_model_cache() -> None:
    global _cached_model_artifact, _cached_model_mtime
    _cached_model_artifact = None
    _cached_model_mtime = None


def save_published_auto_meal_plan_model_artifact(artifact: dict[str, Any]) -> Path:
    ensure_model_dir()
    destination = get_published_model_path()
    temp_path = destination.with_suffix(".tmp")
    joblib.dump(artifact, temp_path)
    temp_path.replace(destination)
    clear_published_auto_meal_plan_model_cache()
    return destination


def load_published_auto_meal_plan_model_artifact(
    *,
    force_reload: bool = False,
) -> dict[str, Any] | None:
    global _cached_model_artifact, _cached_model_mtime

    path = get_published_model_path()
    if not path.exists():
        clear_published_auto_meal_plan_model_cache()
        return None

    mtime = path.stat().st_mtime
    if (
        force_reload
        or _cached_model_artifact is None
        or _cached_model_mtime is None
        or _cached_model_mtime != mtime
    ):
        _cached_model_artifact = joblib.load(path)
        _cached_model_mtime = mtime

    return _cached_model_artifact


def summarize_published_auto_meal_plan_artifact(
    artifact: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not artifact:
        return None

    return {
        "engine_version": artifact.get("engine_version"),
        "model_name": artifact.get("model_name"),
        "target_column": artifact.get("target_column"),
        "scoring_label": artifact.get("scoring_label"),
        "feature_set_key": artifact.get("feature_set_key"),
        "feature_set_label": artifact.get("feature_set_label"),
        "evaluation_strategy": artifact.get("evaluation_strategy"),
        "cv_n_splits": artifact.get("cv_n_splits"),
        "published_at_utc": artifact.get("published_at_utc"),
        "source_report_path": artifact.get("source_report_path"),
        "source_dataset_path": artifact.get("source_dataset_path"),
        "feature_count": len(artifact.get("feature_columns_used") or []),
    }


def build_candidate_feature_row(
    *,
    household_id: int,
    plan_date: date,
    meal_type: str,
    recipe: Recipe,
    heuristic_score: float,
    average_rating: float | None,
    ratings_count: int,
    recipe_profile: dict[str, int],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "household_id": household_id,
        "meal_type": meal_type,
        "suggestion_action": "suggest",
        "suggested_recipe_id": recipe.id,
        "suggested_categoria_alimentar": recipe.categoria_alimentar,
        "suggested_proteina_principal": recipe.proteina_principal,
        "suggested_adequado_refeicao": recipe.adequado_refeicao,
        "weekday_index": plan_date.weekday(),
        "is_weekend": int(plan_date.weekday() >= 5),
        "score": heuristic_score,
        "average_rating": average_rating,
        "ratings_count": ratings_count,
    }
    row.update(recipe_profile)
    return row


def build_inference_frame(
    feature_columns: list[str],
    raw_row: dict[str, Any],
) -> pd.DataFrame:
    prepared_row = {column: raw_row.get(column) for column in feature_columns}
    return pd.DataFrame([prepared_row], columns=feature_columns)


def resolve_scoring_class_index(classes: list[Any], scoring_label: Any) -> int | None:
    for index, class_value in enumerate(classes):
        if class_value == scoring_label:
            return index
        if str(class_value) == str(scoring_label):
            return index
    return None


def score_candidate_acceptance_probability(
    artifact: dict[str, Any],
    raw_row: dict[str, Any],
) -> float | None:
    pipeline = artifact.get("pipeline")
    feature_columns = artifact.get("feature_columns_used") or []
    scoring_label = artifact.get("scoring_label")

    if pipeline is None or not feature_columns or scoring_label is None:
        return None

    if not hasattr(pipeline, "predict_proba"):
        return None

    classes = [item for item in pipeline.named_steps["model"].classes_]
    class_index = resolve_scoring_class_index(classes, scoring_label)
    if class_index is None:
        return None

    inference_frame = build_inference_frame(feature_columns, raw_row)
    probabilities = pipeline.predict_proba(inference_frame)[0]
    return float(probabilities[class_index])


def build_model_reason(acceptance_probability: float) -> str:
    if acceptance_probability >= ML_HIGH_CONFIDENCE_THRESHOLD:
        return f"modelo prevê elevada aceitação ({acceptance_probability:.2f})"
    if acceptance_probability <= ML_LOW_CONFIDENCE_THRESHOLD:
        return f"modelo prevê maior risco de troca ({acceptance_probability:.2f})"
    return f"modelo prevê aceitação intermédia ({acceptance_probability:.2f})"


def build_auto_meal_plan_model_scorer(db: Session) -> AutoMealPlanModelScorer:
    artifact = load_published_auto_meal_plan_model_artifact()
    if artifact is None:
        return AutoMealPlanModelScorer(artifact=None, recipe_feature_profiles={})

    recipe_feature_profiles = build_recipe_feature_profiles(db)
    return AutoMealPlanModelScorer(
        artifact=artifact,
        recipe_feature_profiles=recipe_feature_profiles,
    )
