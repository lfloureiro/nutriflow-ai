from pathlib import Path

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.services import admin_test_reset
from backend.app.services import auto_meal_plan_baseline_training
from backend.app.services import auto_meal_plan_training_dataset


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