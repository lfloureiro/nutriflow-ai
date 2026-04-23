from datetime import date

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.services.auto_meal_plan_training_dataset import (
    build_auto_plan_training_dataset,
    build_recipe_feature_profiles,
)


def get_row(rows, plan_date: str, meal_type: str):
    return next(
        row
        for row in rows
        if row["plan_date"] == plan_date and row["meal_type"] == meal_type
    )


def test_recipe_feature_profiles_extract_ingredient_patterns(db_session, sample_data):
    profiles = build_recipe_feature_profiles(db_session)

    recipe_1_profile = profiles[sample_data["recipe_1_id"]]

    assert recipe_1_profile["suggested_recipe_ingredient_count"] == 2
    assert recipe_1_profile["suggested_recipe_distinct_ingredient_count"] == 2
    assert recipe_1_profile["suggested_recipe_has_peixe_marisco_ingredient"] == 1
    assert recipe_1_profile["suggested_recipe_has_massa_ingredient"] == 1
    assert recipe_1_profile["suggested_recipe_has_batata_ingredient"] == 0
    assert recipe_1_profile["suggested_recipe_profile_flag_count"] >= 2


def test_training_dataset_marks_unchanged_apply_as_accepted(db_session, client, sample_data):
    apply_payload = {
        "household_id": sample_data["household_2_id"],
        "start_date": "2026-05-16",
        "end_date": "2026-05-16",
        "meal_types": ["jantar"],
        "skip_existing": True,
    }

    apply_response = client.post("/meal-plan/auto-plan/apply", json=apply_payload)
    assert apply_response.status_code == 200, apply_response.text

    db_session.expire_all()

    rows = build_auto_plan_training_dataset(
        db_session,
        household_id=sample_data["household_2_id"],
    )

    row = get_row(rows, "2026-05-16", "jantar")

    assert row["outcome_label"] == "accepted_as_suggested"
    assert row["accepted_as_suggested"] == 1
    assert row["changed_recipe"] == 0
    assert row["deleted_after_apply"] == 0
    assert row["lifecycle_count"] == 0
    assert row["suggested_recipe_id"] != ""
    assert row["final_recipe_id"] != ""
    assert "suggested_recipe_ingredient_count" in row
    assert "suggested_recipe_profile_flag_count" in row
    assert row["suggested_recipe_ingredient_count"] >= 0
    assert row["suggested_recipe_profile_flag_count"] >= 0


def test_training_dataset_marks_recipe_change_and_delete(db_session, client, sample_data):
    update_apply_payload = {
        "household_id": sample_data["household_2_id"],
        "start_date": "2026-05-17",
        "end_date": "2026-05-17",
        "meal_types": ["jantar"],
        "skip_existing": True,
    }

    update_apply_response = client.post("/meal-plan/auto-plan/apply", json=update_apply_payload)
    assert update_apply_response.status_code == 200, update_apply_response.text

    update_apply_row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.event_kind == "apply",
            AutoMealPlanEvent.execution_status == "created",
            AutoMealPlanEvent.household_id == sample_data["household_2_id"],
            AutoMealPlanEvent.plan_date == date(2026, 5, 17),
            AutoMealPlanEvent.meal_type == "jantar",
        )
        .order_by(AutoMealPlanEvent.id.desc())
        .first()
    )
    assert update_apply_row is not None
    assert update_apply_row.meal_plan_item_id is not None

    replacement_recipe_id = (
        sample_data["recipe_2_id"]
        if update_apply_row.final_recipe_id != sample_data["recipe_2_id"]
        else sample_data["recipe_1_id"]
    )

    update_response = client.patch(
        f"/meal-plan/{update_apply_row.meal_plan_item_id}",
        json={
            "recipe_id": replacement_recipe_id,
            "notes": "Troca para dataset supervisionado",
        },
    )
    assert update_response.status_code == 200, update_response.text

    delete_apply_payload = {
        "household_id": sample_data["household_2_id"],
        "start_date": "2026-05-18",
        "end_date": "2026-05-18",
        "meal_types": ["almoco"],
        "skip_existing": True,
    }

    delete_apply_response = client.post("/meal-plan/auto-plan/apply", json=delete_apply_payload)
    assert delete_apply_response.status_code == 200, delete_apply_response.text

    delete_apply_row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.event_kind == "apply",
            AutoMealPlanEvent.execution_status == "created",
            AutoMealPlanEvent.household_id == sample_data["household_2_id"],
            AutoMealPlanEvent.plan_date == date(2026, 5, 18),
            AutoMealPlanEvent.meal_type == "almoco",
        )
        .order_by(AutoMealPlanEvent.id.desc())
        .first()
    )
    assert delete_apply_row is not None
    assert delete_apply_row.meal_plan_item_id is not None

    delete_response = client.delete(f"/meal-plan/{delete_apply_row.meal_plan_item_id}")
    assert delete_response.status_code == 200, delete_response.text

    db_session.expire_all()

    rows = build_auto_plan_training_dataset(
        db_session,
        household_id=sample_data["household_2_id"],
    )

    updated_row = get_row(rows, "2026-05-17", "jantar")
    assert updated_row["outcome_label"] == "accepted_with_recipe_change"
    assert updated_row["accepted_as_suggested"] == 0
    assert updated_row["changed_recipe"] == 1
    assert updated_row["deleted_after_apply"] == 0
    assert updated_row["final_recipe_id"] == replacement_recipe_id
    assert "suggested_recipe_has_peixe_marisco_ingredient" in updated_row
    assert "suggested_recipe_has_massa_ingredient" in updated_row
    assert updated_row["suggested_recipe_ingredient_count"] >= 0

    deleted_row = get_row(rows, "2026-05-18", "almoco")
    assert deleted_row["outcome_label"] == "deleted_after_apply"
    assert deleted_row["accepted_as_suggested"] == 0
    assert deleted_row["changed_recipe"] == 0
    assert deleted_row["deleted_after_apply"] == 1
    assert deleted_row["final_recipe_id"] == ""
    assert "suggested_recipe_has_tomate_ingredient" in deleted_row
    assert "suggested_recipe_has_cebola_alho_ingredient" in deleted_row
    assert deleted_row["suggested_recipe_profile_flag_count"] >= 0