from datetime import date
import csv
from pathlib import Path

from backend.app.services import auto_meal_plan_baseline_training
from backend.app.services import auto_meal_plan_model_publishing
from backend.app.services import auto_meal_plan_model_runtime
from backend.app.services.auto_meal_plan_model_publishing import publish_auto_meal_plan_model
from backend.app.services.auto_meal_plan_model_runtime import (
    AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION,
    HEURISTIC_ENGINE_VERSION,
    build_auto_meal_plan_model_scorer,
    clear_published_auto_meal_plan_model_cache,
    load_published_auto_meal_plan_model_artifact,
)
from backend.app.services.auto_meal_planner import build_auto_meal_plan_preview


MINIMAL_DATASET_FIELDNAMES = [
    "household_id",
    "meal_type",
    "suggestion_action",
    "suggested_recipe_id",
    "suggested_categoria_alimentar",
    "suggested_proteina_principal",
    "suggested_adequado_refeicao",
    "weekday_index",
    "is_weekend",
    "score",
    "average_rating",
    "ratings_count",
    "suggested_recipe_ingredient_count",
    "suggested_recipe_distinct_ingredient_count",
    "suggested_recipe_profile_flag_count",
    "suggested_recipe_has_arroz_ingredient",
    "suggested_recipe_has_massa_ingredient",
    "suggested_recipe_has_batata_ingredient",
    "suggested_recipe_has_ovos_ingredient",
    "suggested_recipe_has_peixe_marisco_ingredient",
    "suggested_recipe_has_frango_aves_ingredient",
    "suggested_recipe_has_vaca_ingredient",
    "suggested_recipe_has_porco_ingredient",
    "suggested_recipe_has_queijo_lacticinios_ingredient",
    "suggested_recipe_has_leguminosas_ingredient",
    "suggested_recipe_has_tomate_ingredient",
    "suggested_recipe_has_cebola_alho_ingredient",
    "accepted_as_suggested",
]


def write_publishable_dataset(dataset_path: Path) -> None:
    rows = [
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 1001,
            "suggested_categoria_alimentar": "peixe",
            "suggested_proteina_principal": "peixe",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 0,
            "is_weekend": 0,
            "score": 45.0,
            "average_rating": 4.5,
            "ratings_count": 4,
            "suggested_recipe_ingredient_count": 2,
            "suggested_recipe_distinct_ingredient_count": 2,
            "suggested_recipe_profile_flag_count": 2,
            "suggested_recipe_has_arroz_ingredient": 0,
            "suggested_recipe_has_massa_ingredient": 1,
            "suggested_recipe_has_batata_ingredient": 0,
            "suggested_recipe_has_ovos_ingredient": 0,
            "suggested_recipe_has_peixe_marisco_ingredient": 1,
            "suggested_recipe_has_frango_aves_ingredient": 0,
            "suggested_recipe_has_vaca_ingredient": 0,
            "suggested_recipe_has_porco_ingredient": 0,
            "suggested_recipe_has_queijo_lacticinios_ingredient": 0,
            "suggested_recipe_has_leguminosas_ingredient": 0,
            "suggested_recipe_has_tomate_ingredient": 0,
            "suggested_recipe_has_cebola_alho_ingredient": 0,
            "accepted_as_suggested": 1,
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 1002,
            "suggested_categoria_alimentar": "peixe",
            "suggested_proteina_principal": "peixe",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 1,
            "is_weekend": 0,
            "score": 44.0,
            "average_rating": 4.0,
            "ratings_count": 4,
            "suggested_recipe_ingredient_count": 2,
            "suggested_recipe_distinct_ingredient_count": 2,
            "suggested_recipe_profile_flag_count": 2,
            "suggested_recipe_has_arroz_ingredient": 0,
            "suggested_recipe_has_massa_ingredient": 1,
            "suggested_recipe_has_batata_ingredient": 0,
            "suggested_recipe_has_ovos_ingredient": 0,
            "suggested_recipe_has_peixe_marisco_ingredient": 1,
            "suggested_recipe_has_frango_aves_ingredient": 0,
            "suggested_recipe_has_vaca_ingredient": 0,
            "suggested_recipe_has_porco_ingredient": 0,
            "suggested_recipe_has_queijo_lacticinios_ingredient": 0,
            "suggested_recipe_has_leguminosas_ingredient": 0,
            "suggested_recipe_has_tomate_ingredient": 0,
            "suggested_recipe_has_cebola_alho_ingredient": 0,
            "accepted_as_suggested": 1,
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 2001,
            "suggested_categoria_alimentar": "carne",
            "suggested_proteina_principal": "frango",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 2,
            "is_weekend": 0,
            "score": 35.0,
            "average_rating": 2.0,
            "ratings_count": 2,
            "suggested_recipe_ingredient_count": 0,
            "suggested_recipe_distinct_ingredient_count": 0,
            "suggested_recipe_profile_flag_count": 0,
            "suggested_recipe_has_arroz_ingredient": 0,
            "suggested_recipe_has_massa_ingredient": 0,
            "suggested_recipe_has_batata_ingredient": 0,
            "suggested_recipe_has_ovos_ingredient": 0,
            "suggested_recipe_has_peixe_marisco_ingredient": 0,
            "suggested_recipe_has_frango_aves_ingredient": 0,
            "suggested_recipe_has_vaca_ingredient": 0,
            "suggested_recipe_has_porco_ingredient": 0,
            "suggested_recipe_has_queijo_lacticinios_ingredient": 0,
            "suggested_recipe_has_leguminosas_ingredient": 0,
            "suggested_recipe_has_tomate_ingredient": 0,
            "suggested_recipe_has_cebola_alho_ingredient": 0,
            "accepted_as_suggested": 0,
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 2002,
            "suggested_categoria_alimentar": "carne",
            "suggested_proteina_principal": "frango",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 3,
            "is_weekend": 0,
            "score": 34.0,
            "average_rating": 2.0,
            "ratings_count": 2,
            "suggested_recipe_ingredient_count": 0,
            "suggested_recipe_distinct_ingredient_count": 0,
            "suggested_recipe_profile_flag_count": 0,
            "suggested_recipe_has_arroz_ingredient": 0,
            "suggested_recipe_has_massa_ingredient": 0,
            "suggested_recipe_has_batata_ingredient": 0,
            "suggested_recipe_has_ovos_ingredient": 0,
            "suggested_recipe_has_peixe_marisco_ingredient": 0,
            "suggested_recipe_has_frango_aves_ingredient": 0,
            "suggested_recipe_has_vaca_ingredient": 0,
            "suggested_recipe_has_porco_ingredient": 0,
            "suggested_recipe_has_queijo_lacticinios_ingredient": 0,
            "suggested_recipe_has_leguminosas_ingredient": 0,
            "suggested_recipe_has_tomate_ingredient": 0,
            "suggested_recipe_has_cebola_alho_ingredient": 0,
            "accepted_as_suggested": 0,
        },
    ]

    with dataset_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=MINIMAL_DATASET_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def test_publish_auto_meal_plan_model_creates_runtime_artifact(monkeypatch, tmp_path):
    model_dir = tmp_path / "ml_models"
    results_dir = tmp_path / "ml_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = tmp_path / "auto_plan_training_publish.csv"
    write_publishable_dataset(dataset_path)

    monkeypatch.setattr(auto_meal_plan_model_runtime, "MODEL_DIR", model_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)
    clear_published_auto_meal_plan_model_cache()

    model_path, report_path, metadata = publish_auto_meal_plan_model(
        dataset_path=str(dataset_path),
        target="accepted_as_suggested",
        include_suggested_recipe_id=False,
        evaluation_strategy="stratified_kfold",
        random_state=42,
    )

    assert model_path.exists()
    assert report_path.exists()
    assert metadata["engine_version"] == AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION
    assert metadata["target_column"] == "accepted_as_suggested"
    assert metadata["feature_set_key"] == "without_suggested_recipe_id"

    artifact = load_published_auto_meal_plan_model_artifact(force_reload=True)
    assert artifact is not None
    assert artifact["target_column"] == "accepted_as_suggested"
    assert artifact["scoring_label"] in (1, True, "1", "True", "true")


def test_preview_uses_published_model_score_when_available(
    monkeypatch,
    tmp_path,
    db_session,
    sample_data,
):
    model_dir = tmp_path / "ml_models"
    results_dir = tmp_path / "ml_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = tmp_path / "auto_plan_training_publish.csv"
    write_publishable_dataset(dataset_path)

    monkeypatch.setattr(auto_meal_plan_model_runtime, "MODEL_DIR", model_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)
    clear_published_auto_meal_plan_model_cache()

    preview_before = build_auto_meal_plan_preview(
        db=db_session,
        household_id=sample_data["household_2_id"],
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 10),
        meal_types=["jantar"],
        skip_existing=True,
    )
    assert preview_before[0].engine_version == HEURISTIC_ENGINE_VERSION
    assert preview_before[0].heuristic_score is not None
    assert preview_before[0].final_score == preview_before[0].score
    assert preview_before[0].model_acceptance_score is None

    publish_auto_meal_plan_model(
        dataset_path=str(dataset_path),
        target="accepted_as_suggested",
        include_suggested_recipe_id=False,
        evaluation_strategy="stratified_kfold",
        random_state=42,
    )

    scorer = build_auto_meal_plan_model_scorer(db_session)
    assert scorer.is_active is True
    assert scorer.engine_version == AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION

    preview_after = build_auto_meal_plan_preview(
        db=db_session,
        household_id=sample_data["household_2_id"],
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 10),
        meal_types=["jantar"],
        skip_existing=True,
    )

    assert preview_after[0].engine_version == AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION
    assert preview_after[0].heuristic_score is not None
    assert preview_after[0].final_score == preview_after[0].score
    assert preview_after[0].model_acceptance_score is not None
    assert any("modelo prevê" in reason for reason in preview_after[0].reasons)


def test_preview_endpoint_includes_score_breakdown_when_model_active(
    monkeypatch,
    tmp_path,
    client,
    sample_data,
):
    model_dir = tmp_path / "ml_models"
    results_dir = tmp_path / "ml_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = tmp_path / "auto_plan_training_publish.csv"
    write_publishable_dataset(dataset_path)

    monkeypatch.setattr(auto_meal_plan_model_runtime, "MODEL_DIR", model_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)
    clear_published_auto_meal_plan_model_cache()

    publish_auto_meal_plan_model(
        dataset_path=str(dataset_path),
        target="accepted_as_suggested",
        include_suggested_recipe_id=False,
        evaluation_strategy="stratified_kfold",
        random_state=42,
    )

    response = client.post(
        "/meal-plan/auto-plan/preview",
        json={
            "household_id": sample_data["household_2_id"],
            "start_date": "2026-06-10",
            "end_date": "2026-06-10",
            "meal_types": ["jantar"],
            "skip_existing": True,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["suggestions"]) == 1

    suggestion = body["suggestions"][0]
    assert "heuristic_score" in suggestion
    assert "ml_score" in suggestion
    assert "final_score" in suggestion
    assert "engine_version" in suggestion
    assert suggestion["engine_version"] == AUTO_MEAL_PLAN_MODEL_ENGINE_VERSION
    assert suggestion["heuristic_score"] is not None
    assert suggestion["ml_score"] is not None
    assert suggestion["final_score"] is not None
    assert suggestion["score"] == suggestion["final_score"]