import csv
import warnings
from pathlib import Path

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.services import admin_test_reset
from backend.app.services import auto_meal_plan_baseline_training
from backend.app.services import auto_meal_plan_training_dataset


def write_auto_plan_training_dataset_for_feature_comparison(dataset_path: Path) -> None:
    rows = [
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 101,
            "suggested_categoria_alimentar": "refeicao",
            "suggested_proteina_principal": "mista",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 0,
            "is_weekend": 0,
            "score": 10.0,
            "average_rating": 4.0,
            "ratings_count": 3,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 101,
            "suggested_categoria_alimentar": "refeicao",
            "suggested_proteina_principal": "mista",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 1,
            "is_weekend": 0,
            "score": 10.0,
            "average_rating": 4.0,
            "ratings_count": 3,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 101,
            "suggested_categoria_alimentar": "refeicao",
            "suggested_proteina_principal": "mista",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 2,
            "is_weekend": 0,
            "score": 10.0,
            "average_rating": 4.0,
            "ratings_count": 3,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 202,
            "suggested_categoria_alimentar": "refeicao",
            "suggested_proteina_principal": "mista",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 3,
            "is_weekend": 0,
            "score": 10.0,
            "average_rating": 4.0,
            "ratings_count": 3,
            "outcome_label": "accepted_with_recipe_change",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 202,
            "suggested_categoria_alimentar": "refeicao",
            "suggested_proteina_principal": "mista",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 4,
            "is_weekend": 0,
            "score": 10.0,
            "average_rating": 4.0,
            "ratings_count": 3,
            "outcome_label": "accepted_with_recipe_change",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 202,
            "suggested_categoria_alimentar": "refeicao",
            "suggested_proteina_principal": "mista",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 5,
            "is_weekend": 1,
            "score": 10.0,
            "average_rating": 4.0,
            "ratings_count": 3,
            "outcome_label": "accepted_with_recipe_change",
        },
    ]

    fieldnames = list(rows[0].keys())
    with dataset_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_auto_plan_training_dataset_for_grouped_evaluation(dataset_path: Path) -> None:
    rows = [
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 501,
            "suggested_categoria_alimentar": "carne",
            "suggested_proteina_principal": "frango",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 0,
            "is_weekend": 0,
            "score": 8.0,
            "average_rating": 4.0,
            "ratings_count": 5,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 501,
            "suggested_categoria_alimentar": "carne",
            "suggested_proteina_principal": "frango",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 1,
            "is_weekend": 0,
            "score": 7.0,
            "average_rating": 3.0,
            "ratings_count": 5,
            "outcome_label": "accepted_with_recipe_change",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 502,
            "suggested_categoria_alimentar": "peixe",
            "suggested_proteina_principal": "peixe",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 2,
            "is_weekend": 0,
            "score": 9.0,
            "average_rating": 4.0,
            "ratings_count": 4,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 502,
            "suggested_categoria_alimentar": "peixe",
            "suggested_proteina_principal": "peixe",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 3,
            "is_weekend": 0,
            "score": 6.0,
            "average_rating": 2.0,
            "ratings_count": 4,
            "outcome_label": "accepted_with_recipe_change",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 503,
            "suggested_categoria_alimentar": "carne",
            "suggested_proteina_principal": "porco",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 4,
            "is_weekend": 0,
            "score": 8.5,
            "average_rating": 4.0,
            "ratings_count": 6,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "jantar",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 503,
            "suggested_categoria_alimentar": "carne",
            "suggested_proteina_principal": "porco",
            "suggested_adequado_refeicao": "jantar",
            "weekday_index": 5,
            "is_weekend": 1,
            "score": 6.5,
            "average_rating": 2.0,
            "ratings_count": 6,
            "outcome_label": "accepted_with_recipe_change",
        },
        {
            "household_id": 1,
            "meal_type": "almoco",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 504,
            "suggested_categoria_alimentar": "vegetariano",
            "suggested_proteina_principal": "leguminosas",
            "suggested_adequado_refeicao": "ambos",
            "weekday_index": 0,
            "is_weekend": 0,
            "score": 8.0,
            "average_rating": 4.0,
            "ratings_count": 3,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "almoco",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 504,
            "suggested_categoria_alimentar": "vegetariano",
            "suggested_proteina_principal": "leguminosas",
            "suggested_adequado_refeicao": "ambos",
            "weekday_index": 1,
            "is_weekend": 0,
            "score": 5.5,
            "average_rating": 2.0,
            "ratings_count": 3,
            "outcome_label": "accepted_with_recipe_change",
        },
        {
            "household_id": 1,
            "meal_type": "almoco",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 505,
            "suggested_categoria_alimentar": "ovos",
            "suggested_proteina_principal": "ovos",
            "suggested_adequado_refeicao": "ambos",
            "weekday_index": 2,
            "is_weekend": 0,
            "score": 8.0,
            "average_rating": 4.0,
            "ratings_count": 2,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "almoco",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 505,
            "suggested_categoria_alimentar": "ovos",
            "suggested_proteina_principal": "ovos",
            "suggested_adequado_refeicao": "ambos",
            "weekday_index": 3,
            "is_weekend": 0,
            "score": 5.0,
            "average_rating": 2.0,
            "ratings_count": 2,
            "outcome_label": "accepted_with_recipe_change",
        },
        {
            "household_id": 1,
            "meal_type": "almoco",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 506,
            "suggested_categoria_alimentar": "peixe",
            "suggested_proteina_principal": "peixe",
            "suggested_adequado_refeicao": "ambos",
            "weekday_index": 4,
            "is_weekend": 0,
            "score": 8.5,
            "average_rating": 5.0,
            "ratings_count": 2,
            "outcome_label": "accepted_as_suggested",
        },
        {
            "household_id": 1,
            "meal_type": "almoco",
            "suggestion_action": "suggest",
            "suggested_recipe_id": 506,
            "suggested_categoria_alimentar": "peixe",
            "suggested_proteina_principal": "peixe",
            "suggested_adequado_refeicao": "ambos",
            "weekday_index": 5,
            "is_weekend": 1,
            "score": 5.5,
            "average_rating": 2.0,
            "ratings_count": 2,
            "outcome_label": "accepted_with_recipe_change",
        },
    ]

    fieldnames = list(rows[0].keys())
    with dataset_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_admin_export_dataset_endpoint_writes_csv(
    client,
    sample_data,
    monkeypatch,
    tmp_path,
):
    dataset_dir = tmp_path / "ml_datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(auto_meal_plan_training_dataset, "DATASET_DIR", dataset_dir)

    apply_payload = {
      "household_id": sample_data["household_2_id"],
      "start_date": "2026-05-19",
      "end_date": "2026-05-19",
      "meal_types": ["jantar"],
      "skip_existing": True,
    }

    apply_response = client.post("/meal-plan/auto-plan/apply", json=apply_payload)
    assert apply_response.status_code == 200, apply_response.text

    export_response = client.post("/admin-tools/ml/export-auto-plan-dataset")
    assert export_response.status_code == 200, export_response.text

    body = export_response.json()
    assert body["row_count"] == 1
    assert Path(body["dataset_path"]).exists()


def test_admin_train_baseline_endpoint_handles_single_class_dataset(
    client,
    sample_data,
    monkeypatch,
    tmp_path,
):
    dataset_dir = tmp_path / "ml_datasets"
    results_dir = tmp_path / "ml_results"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(auto_meal_plan_training_dataset, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)

    apply_payload = {
      "household_id": sample_data["household_2_id"],
      "start_date": "2026-05-20",
      "end_date": "2026-05-20",
      "meal_types": ["almoco"],
      "skip_existing": True,
    }

    apply_response = client.post("/meal-plan/auto-plan/apply", json=apply_payload)
    assert apply_response.status_code == 200, apply_response.text

    export_response = client.post("/admin-tools/ml/export-auto-plan-dataset")
    assert export_response.status_code == 200, export_response.text

    train_response = client.post("/admin-tools/ml/train-auto-plan-baseline")
    assert train_response.status_code == 200, train_response.text

    body = train_response.json()
    assert body["status"] == "not_enough_classes"
    assert Path(body["report_path"]).exists()


def test_admin_reset_testing_state_endpoint_clears_plan_events_and_files(
    client,
    db_session,
    sample_data,
    monkeypatch,
    tmp_path,
):
    dataset_dir = tmp_path / "ml_datasets"
    results_dir = tmp_path / "ml_results"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    (dataset_dir / "dummy.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (results_dir / "dummy.json").write_text('{"ok": true}', encoding="utf-8")

    monkeypatch.setattr(admin_test_reset, "DATASET_DIR", dataset_dir)
    monkeypatch.setattr(admin_test_reset, "RESULTS_DIR", results_dir)

    apply_payload = {
      "household_id": sample_data["household_2_id"],
      "start_date": "2026-05-21",
      "end_date": "2026-05-21",
      "meal_types": ["jantar"],
      "skip_existing": True,
    }

    apply_response = client.post("/meal-plan/auto-plan/apply", json=apply_payload)
    assert apply_response.status_code == 200, apply_response.text

    reset_response = client.post("/admin-tools/testing/reset-meal-plan-ml-state")
    assert reset_response.status_code == 200, reset_response.text

    body = reset_response.json()
    assert body["deleted_meal_plan_count"] >= 1
    assert body["deleted_auto_event_count"] >= 1
    assert body["deleted_dataset_file_count"] == 1
    assert body["deleted_result_file_count"] == 1

    db_session.expire_all()

    assert db_session.query(MealPlanItem).count() == 0
    assert db_session.query(AutoMealPlanEvent).count() == 0
    assert not (dataset_dir / "dummy.csv").exists()
    assert not (results_dir / "dummy.json").exists()


def test_train_auto_plan_baseline_compares_with_and_without_suggested_recipe_id(
    monkeypatch,
    tmp_path,
):
    results_dir = tmp_path / "ml_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = tmp_path / "auto_plan_training.csv"
    write_auto_plan_training_dataset_for_feature_comparison(dataset_path)

    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)

    with warnings.catch_warnings():
        warnings.simplefilter("error")

        report_path, report = auto_meal_plan_baseline_training.train_auto_meal_plan_baseline(
            dataset_path=str(dataset_path),
            target="outcome_label",
            compare_suggested_recipe_id=True,
            random_state=42,
        )

    assert report["status"] == "ok"
    assert report_path.exists()
    assert report["feature_set_key_primary"] == "with_suggested_recipe_id"
    assert len(report["feature_set_reports"]) == 2

    reports_by_key = {
        item["feature_set_key"]: item
        for item in report["feature_set_reports"]
    }

    with_feature = reports_by_key["with_suggested_recipe_id"]
    without_feature = reports_by_key["without_suggested_recipe_id"]

    assert "suggested_recipe_id" in with_feature["categorical_features_used"]
    assert "suggested_recipe_id" not in without_feature["categorical_features_used"]

    assert report["comparison_summary"] is not None
    assert report["comparison_summary"]["compared_feature"] == "suggested_recipe_id"
    assert (
        report["comparison_summary"]["best_variant"]["feature_set_key"]
        == "with_suggested_recipe_id"
    )

    assert (
        with_feature["best_model"]["balanced_accuracy"]
        >= without_feature["best_model"]["balanced_accuracy"]
    )


def test_train_auto_plan_baseline_supports_primary_run_without_suggested_recipe_id(
    monkeypatch,
    tmp_path,
):
    results_dir = tmp_path / "ml_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = tmp_path / "auto_plan_training.csv"
    write_auto_plan_training_dataset_for_feature_comparison(dataset_path)

    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)

    with warnings.catch_warnings():
        warnings.simplefilter("error")

        report_path, report = auto_meal_plan_baseline_training.train_auto_meal_plan_baseline(
            dataset_path=str(dataset_path),
            target="outcome_label",
            include_suggested_recipe_id=False,
            compare_suggested_recipe_id=False,
            random_state=42,
        )

    assert report["status"] == "ok"
    assert report_path.exists()
    assert report["feature_set_key_primary"] == "without_suggested_recipe_id"
    assert report["comparison_summary"] is None
    assert len(report["feature_set_reports"]) == 1
    assert "suggested_recipe_id" not in report["categorical_features_used"]
    assert report["feature_set_reports"][0]["feature_set_key"] == "without_suggested_recipe_id"


def test_train_auto_plan_baseline_supports_grouped_evaluation_by_recipe_id(
    monkeypatch,
    tmp_path,
):
    results_dir = tmp_path / "ml_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = tmp_path / "auto_plan_training_grouped.csv"
    write_auto_plan_training_dataset_for_grouped_evaluation(dataset_path)

    monkeypatch.setattr(auto_meal_plan_baseline_training, "RESULTS_DIR", results_dir)

    with warnings.catch_warnings():
        warnings.simplefilter("error")

        report_path, report = auto_meal_plan_baseline_training.train_auto_meal_plan_baseline(
            dataset_path=str(dataset_path),
            target="outcome_label",
            evaluation_strategy="grouped_by_suggested_recipe_id",
            compare_suggested_recipe_id=True,
            random_state=42,
        )

    assert report["status"] == "ok"
    assert report_path.exists()
    assert report["evaluation_strategy"] == "grouped_by_suggested_recipe_id"
    assert report["grouping_feature"] == "suggested_recipe_id"
    assert report["group_count"] == 6
    assert report["cv_n_splits"] >= 2
    assert len(report["feature_set_reports"]) == 2

    first_feature_set = report["feature_set_reports"][0]
    first_model = first_feature_set["model_results"][0]
    first_fold = first_model["fold_results"][0]

    assert "train_group_count" in first_fold
    assert "test_group_count" in first_fold
    assert "train_groups" in first_fold
    assert "test_groups" in first_fold
    assert set(first_fold["train_groups"]).isdisjoint(set(first_fold["test_groups"]))