from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.services.auto_meal_plan_baseline_training import (
    DEFAULT_EVALUATION_STRATEGY,
    DEFAULT_TARGET,
    GROUPED_EVALUATION_STRATEGY,
    find_latest_dataset,
    load_dataset,
    make_models,
    prepare_features,
    prepare_target,
    train_auto_meal_plan_baseline,
)
from backend.app.services.auto_meal_plan_model_runtime import (
    AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION,
    save_published_auto_meal_plan_model_artifact,
    summarize_published_auto_meal_plan_artifact,
)

DEFAULT_PUBLISH_TARGET = "accepted_as_suggested"
DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID = False
DEFAULT_PUBLISH_EVALUATION_STRATEGY = GROUPED_EVALUATION_STRATEGY


def normalize_scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def resolve_scoring_label(classes: list[Any], target: str) -> Any:
    normalized_classes = [normalize_scalar(item) for item in classes]

    if target == "accepted_as_suggested":
        for candidate in (1, True, "1", "True", "true"):
            for class_value in normalized_classes:
                if class_value == candidate or str(class_value) == str(candidate):
                    return class_value
        raise ValueError(
            "O modelo treinado não contém uma classe positiva reconhecível para accepted_as_suggested."
        )

    if target == "outcome_label":
        for class_value in normalized_classes:
            if str(class_value) == "accepted_as_suggested":
                return class_value
        raise ValueError(
            "O modelo treinado não contém a classe 'accepted_as_suggested' para score de aceitação."
        )

    raise ValueError(
        "A publicação online suporta apenas os targets 'accepted_as_suggested' e 'outcome_label'."
    )


def publish_auto_meal_plan_model(
    *,
    dataset_path: str | None = None,
    target: str = DEFAULT_PUBLISH_TARGET,
    test_size: float = 0.3,
    random_state: int = 42,
    include_suggested_recipe_id: bool = DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID,
    evaluation_strategy: str = DEFAULT_PUBLISH_EVALUATION_STRATEGY,
    additional_artifact_fields: dict[str, Any] | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    report_path, report = train_auto_meal_plan_baseline(
        dataset_path=dataset_path,
        target=target,
        test_size=test_size,
        random_state=random_state,
        include_suggested_recipe_id=include_suggested_recipe_id,
        compare_suggested_recipe_id=False,
        evaluation_strategy=evaluation_strategy,
    )

    if report["status"] != "ok":
        raise ValueError(
            f"Não foi possível publicar o modelo porque o treino ficou com estado '{report['status']}'."
        )

    if not report.get("best_model"):
        raise ValueError("O treino não produziu um melhor modelo publicável.")

    feature_set_reports = report.get("feature_set_reports") or []
    if not feature_set_reports:
        raise ValueError("O relatório não contém feature_set_reports para publicação.")

    feature_set_report = feature_set_reports[0]
    best_model_name = feature_set_report["best_model"]["model_name"]

    resolved_dataset_path = Path(dataset_path) if dataset_path else find_latest_dataset()
    df = load_dataset(resolved_dataset_path)
    y = prepare_target(df, target)
    x, categorical_features, numeric_features, _dropped_numeric_features = prepare_features(
        df,
        excluded_features=feature_set_report["excluded_features"],
    )

    models = make_models(
        categorical_features=categorical_features,
        numeric_features=numeric_features,
        random_state=random_state,
    )
    pipeline = models[best_model_name]
    pipeline.fit(x, y)

    model_classes = [normalize_scalar(item) for item in pipeline.named_steps["model"].classes_]
    scoring_label = resolve_scoring_label(model_classes, target)

    artifact = {
        "engine_version": AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION,
        "published_at_utc": datetime.now(UTC).isoformat(),
        "target_column": target,
        "model_name": best_model_name,
        "evaluation_strategy": report["evaluation_strategy"],
        "cv_n_splits": report["cv_n_splits"],
        "feature_set_key": feature_set_report["feature_set_key"],
        "feature_set_label": feature_set_report["feature_set_label"],
        "excluded_features": feature_set_report["excluded_features"],
        "feature_columns_used": feature_set_report["feature_columns_used"],
        "categorical_features_used": feature_set_report["categorical_features_used"],
        "numeric_features_used": feature_set_report["numeric_features_used"],
        "model_classes": model_classes,
        "scoring_label": normalize_scalar(scoring_label),
        "source_dataset_path": str(resolved_dataset_path),
        "source_report_path": str(report_path),
        "pipeline": pipeline,
    }

    if additional_artifact_fields:
        artifact.update(additional_artifact_fields)

    model_path = save_published_auto_meal_plan_model_artifact(artifact)
    metadata = summarize_published_auto_meal_plan_artifact(artifact) or {}
    metadata.update(
        {
            "status": report["status"],
            "best_model": report["best_model"],
        }
    )

    return model_path, report_path, metadata