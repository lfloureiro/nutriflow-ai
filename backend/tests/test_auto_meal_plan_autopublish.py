from datetime import date
from pathlib import Path

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.services import auto_meal_plan_autopublish
from backend.app.services import auto_meal_plan_baseline_training
from backend.app.services import auto_meal_plan_model_runtime
from backend.app.services import auto_meal_plan_training_dataset
from backend.app.services.auto_meal_plan_model_runtime import (
    clear_published_auto_meal_plan_model_cache,
    load_published_auto_meal_plan_model_artifact,
)


def configure_ml_artifact_paths(monkeypatch, tmp_path):
    dataset_dir = tmp_path / "ml_datasets"
    results_dir = tmp_path / "ml_results"
    model_dir = tmp_path / "ml_models"

    dataset_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(auto_meal_plan_training_dataset, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(auto_meal_plan_model_runtime, "MODEL_DIR", model_dir)

    monkeypatch.setattr(auto_meal_plan_autopublish, "AUTO_PUBLISH_MIN_DATASET_ROWS", 4)
    monkeypatch.setattr(auto_meal_plan_autopublish, "AUTO_PUBLISH_MIN_NEW_EVENTS", 1)
    monkeypatch.setattr(
        auto_meal_plan_autopublish,
        "AUTO_PUBLISH_EVALUATION_STRATEGY",
        "grouped_by_suggested_recipe_id",
    )
    monkeypatch.setattr(
        auto_meal_plan_autopublish,
        "AUTO_PUBLISH_FALLBACK_EVALUATION_STRATEGY",
        "stratified_kfold",
    )

    clear_published_auto_meal_plan_model_cache()

    return dataset_dir, results_dir, model_dir


def apply_one_day(client, household_id: int, day_iso: str, meal_type: str):
    response = client.post(
        "/meal-plan/auto-plan/apply",
        json={
            "household_id": household_id,
            "start_date": day_iso,
            "end_date": day_iso,
            "meal_types": [meal_type],
            "skip_existing": True,
        },
    )
    assert response.status_code == 200, response.text
    return response


def get_latest_apply_created_event(db_session, household_id: int, day_value: date, meal_type: str):
    row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.event_kind == "apply",
            AutoMealPlanEvent.execution_status == "created",
            AutoMealPlanEvent.household_id == household_id,
            AutoMealPlanEvent.plan_date == day_value,
            AutoMealPlanEvent.meal_type == meal_type,
        )
        .order_by(AutoMealPlanEvent.id.desc())
        .first()
    )
    assert row is not None
    assert row.meal_plan_item_id is not None
    return row


def replace_auto_planned_recipe(client, meal_plan_item_id: int, replacement_recipe_id: int):
    response = client.patch(
        f"/meal-plan/{meal_plan_item_id}",
        json={
            "recipe_id": replacement_recipe_id,
            "notes": "Troca para criar exemplo negativo",
        },
    )
    assert response.status_code == 200, response.text
    return response


def delete_auto_planned_item(client, meal_plan_item_id: int):
    response = client.delete(f"/meal-plan/{meal_plan_item_id}")
    assert response.status_code == 200, response.text
    return response


def assert_autopublish_metadata_is_coherent(artifact, trigger_reason: str):
    assert artifact is not None
    assert artifact["target_column"] == "accepted_as_suggested"
    assert artifact["source_dataset_row_count"] == 4
    assert artifact["source_max_auto_event_id"] >= 6
    assert artifact["auto_publish_trigger_reason"] == trigger_reason
    assert artifact["feature_set_key"] == "without_suggested_recipe_id"
    assert artifact["auto_publish_primary_strategy"] == "grouped_by_suggested_recipe_id"

    effective_strategy = artifact["auto_publish_effective_strategy"]
    assert effective_strategy in {"grouped_by_suggested_recipe_id", "stratified_kfold"}

    used_fallback = artifact["auto_publish_used_fallback"]
    assert used_fallback == (effective_strategy == "stratified_kfold")

    assert artifact["evaluation_strategy"] == effective_strategy


def test_apply_endpoint_auto_publishes_model_when_dataset_becomes_trainable(
    monkeypatch,
    tmp_path,
    db_session,
    client,
    sample_data,
):
    configure_ml_artifact_paths(monkeypatch, tmp_path)

    household_id = sample_data["household_2_id"]
    replacement_recipe_id = sample_data["recipe_2_id"]

    # Dia 1 -> negativo (troca)
    apply_one_day(client, household_id, "2026-06-01", "jantar")
    first_row = get_latest_apply_created_event(db_session, household_id, date(2026, 6, 1), "jantar")
    if first_row.final_recipe_id == replacement_recipe_id:
        replacement_recipe_id = sample_data["recipe_1_id"]
    replace_auto_planned_recipe(client, first_row.meal_plan_item_id, replacement_recipe_id)

    artifact_after_first_negative = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert artifact_after_first_negative is None

    # Dia 2 -> positivo (mantido)
    apply_one_day(client, household_id, "2026-06-02", "jantar")
    artifact_after_first_positive = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert artifact_after_first_positive is None

    # Dia 3 -> negativo (troca)
    apply_one_day(client, household_id, "2026-06-03", "jantar")
    third_row = get_latest_apply_created_event(db_session, household_id, date(2026, 6, 3), "jantar")
    replacement_recipe_id_day3 = sample_data["recipe_2_id"]
    if third_row.final_recipe_id == replacement_recipe_id_day3:
        replacement_recipe_id_day3 = sample_data["recipe_1_id"]
    replace_auto_planned_recipe(client, third_row.meal_plan_item_id, replacement_recipe_id_day3)

    artifact_after_second_negative = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert artifact_after_second_negative is None

    # Dia 4 -> positivo (mantido)
    apply_one_day(client, household_id, "2026-06-04", "jantar")

    artifact = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert_autopublish_metadata_is_coherent(artifact, "auto_plan_apply")


def test_delete_endpoint_auto_publishes_model_when_dataset_becomes_trainable(
    monkeypatch,
    tmp_path,
    db_session,
    client,
    sample_data,
):
    configure_ml_artifact_paths(monkeypatch, tmp_path)

    household_id = sample_data["household_2_id"]

    # Dia 1 -> positivo (mantido)
    apply_one_day(client, household_id, "2026-06-05", "almoco")
    artifact_after_first_positive = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert artifact_after_first_positive is None

    # Dia 2 -> negativo (apagado)
    apply_one_day(client, household_id, "2026-06-06", "almoco")
    second_row = get_latest_apply_created_event(db_session, household_id, date(2026, 6, 6), "almoco")
    delete_auto_planned_item(client, second_row.meal_plan_item_id)

    artifact_after_first_negative = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert artifact_after_first_negative is None

    # Dia 3 -> positivo (mantido)
    apply_one_day(client, household_id, "2026-06-07", "almoco")
    artifact_after_second_positive = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert artifact_after_second_positive is None

    # Dia 4 -> negativo (apagado)
    apply_one_day(client, household_id, "2026-06-08", "almoco")
    fourth_row = get_latest_apply_created_event(db_session, household_id, date(2026, 6, 8), "almoco")
    delete_auto_planned_item(client, fourth_row.meal_plan_item_id)

    artifact = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert_autopublish_metadata_is_coherent(artifact, "meal_plan_delete_from_auto_plan")


def test_autopublish_falls_back_to_stratified_when_grouped_is_not_supported(
    monkeypatch,
    tmp_path,
    db_session,
):
    dataset_dir = tmp_path / "ml_datasets"
    results_dir = tmp_path / "ml_results"
    model_dir = tmp_path / "ml_models"

    dataset_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(auto_meal_plan_training_dataset, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(auto_meal_plan_model_runtime, "MODEL_DIR", model_dir)

    monkeypatch.setattr(auto_meal_plan_autopublish, "AUTO_PUBLISH_MIN_DATASET_ROWS", 4)
    monkeypatch.setattr(auto_meal_plan_autopublish, "AUTO_PUBLISH_MIN_NEW_EVENTS", 1)
    monkeypatch.setattr(
        auto_meal_plan_autopublish,
        "AUTO_PUBLISH_EVALUATION_STRATEGY",
        "grouped_by_suggested_recipe_id",
    )
    monkeypatch.setattr(
        auto_meal_plan_autopublish,
        "AUTO_PUBLISH_FALLBACK_EVALUATION_STRATEGY",
        "stratified_kfold",
    )

    clear_published_auto_meal_plan_model_cache()

    monkeypatch.setattr(
        auto_meal_plan_autopublish,
        "get_latest_auto_event_id",
        lambda db: 10,
    )
    monkeypatch.setattr(
        auto_meal_plan_autopublish,
        "load_published_auto_meal_plan_model_artifact",
        lambda: None,
    )
    monkeypatch.setattr(
        auto_meal_plan_training_dataset,
        "export_auto_plan_training_dataset",
        lambda db, household_id=None, output_path=None: (
            Path(output_path),
            4,
        ),
    )

    calls: list[str] = []

    def fake_publish_auto_meal_plan_model(
        *,
        dataset_path=None,
        target=None,
        test_size=0.3,
        random_state=42,
        include_suggested_recipe_id=False,
        evaluation_strategy="grouped_by_suggested_recipe_id",
        additional_artifact_fields=None,
    ):
        calls.append(evaluation_strategy)

        if evaluation_strategy == "grouped_by_suggested_recipe_id":
            raise ValueError(
                "Não foi possível publicar o modelo porque o treino ficou com estado "
                "'insufficient_evaluation_support'."
            )

        return (
            model_dir / "auto_meal_plan_latest.joblib",
            results_dir / "auto_meal_plan_report.json",
            {
                "engine_version": "hybrid_ml_v1",
                "target_column": "accepted_as_suggested",
                "evaluation_strategy": evaluation_strategy,
                "feature_set_key": "without_suggested_recipe_id",
            },
        )

    monkeypatch.setattr(
        auto_meal_plan_autopublish,
        "publish_auto_meal_plan_model",
        fake_publish_auto_meal_plan_model,
    )

    result = auto_meal_plan_autopublish.maybe_auto_publish_auto_meal_plan_model(
        db_session,
        trigger_reason="test_fallback",
    )

    assert result.status == "published"
    assert calls == ["grouped_by_suggested_recipe_id", "stratified_kfold"]
    assert result.metadata is not None
    assert result.metadata["auto_publish_primary_strategy"] == "grouped_by_suggested_recipe_id"
    assert result.metadata["auto_publish_effective_strategy"] == "stratified_kfold"
    assert result.metadata["auto_publish_used_fallback"] is True