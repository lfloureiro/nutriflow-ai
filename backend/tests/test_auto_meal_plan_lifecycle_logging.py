from datetime import date

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.models.meal_plan_item import MealPlanItem


def test_auto_plan_update_logs_post_apply_update(db_session, client, sample_data):
    apply_payload = {
        "household_id": sample_data["household_2_id"],
        "start_date": "2026-05-14",
        "end_date": "2026-05-14",
        "meal_types": ["jantar"],
        "skip_existing": True,
    }

    apply_response = client.post("/meal-plan/auto-plan/apply", json=apply_payload)
    assert apply_response.status_code == 200, apply_response.text

    apply_row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.event_kind == "apply",
            AutoMealPlanEvent.execution_status == "created",
            AutoMealPlanEvent.household_id == sample_data["household_2_id"],
            AutoMealPlanEvent.plan_date == date(2026, 5, 14),
            AutoMealPlanEvent.meal_type == "jantar",
        )
        .order_by(AutoMealPlanEvent.id.desc())
        .first()
    )
    assert apply_row is not None
    assert apply_row.meal_plan_item_id is not None

    replacement_recipe_id = (
        sample_data["recipe_2_id"]
        if apply_row.final_recipe_id != sample_data["recipe_2_id"]
        else sample_data["recipe_1_id"]
    )

    update_payload = {
        "recipe_id": replacement_recipe_id,
        "notes": "Receita alterada manualmente",
    }

    update_response = client.patch(
        f"/meal-plan/{apply_row.meal_plan_item_id}",
        json=update_payload,
    )
    assert update_response.status_code == 200, update_response.text

    db_session.expire_all()

    update_row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.event_kind == "post_apply_update",
            AutoMealPlanEvent.meal_plan_item_id == apply_row.meal_plan_item_id,
        )
        .order_by(AutoMealPlanEvent.id.desc())
        .first()
    )

    assert update_row is not None
    assert update_row.run_id == apply_row.run_id
    assert update_row.execution_status == "recipe_replaced"
    assert update_row.suggested_recipe_id == apply_row.suggested_recipe_id
    assert update_row.final_recipe_id == replacement_recipe_id
    assert "recipe_changed" in update_row.reasons
    assert "notes_changed" in update_row.reasons


def test_auto_plan_delete_detaches_old_logs_and_logs_delete_event(
    db_session,
    client,
    sample_data,
):
    apply_payload = {
        "household_id": sample_data["household_2_id"],
        "start_date": "2026-05-15",
        "end_date": "2026-05-15",
        "meal_types": ["almoco"],
        "skip_existing": True,
    }

    apply_response = client.post("/meal-plan/auto-plan/apply", json=apply_payload)
    assert apply_response.status_code == 200, apply_response.text

    apply_row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.event_kind == "apply",
            AutoMealPlanEvent.execution_status == "created",
            AutoMealPlanEvent.household_id == sample_data["household_2_id"],
            AutoMealPlanEvent.plan_date == date(2026, 5, 15),
            AutoMealPlanEvent.meal_type == "almoco",
        )
        .order_by(AutoMealPlanEvent.id.desc())
        .first()
    )
    assert apply_row is not None
    assert apply_row.meal_plan_item_id is not None

    apply_row_id = apply_row.id
    meal_plan_item_id = apply_row.meal_plan_item_id
    run_id = apply_row.run_id

    delete_response = client.delete(f"/meal-plan/{meal_plan_item_id}")
    assert delete_response.status_code == 200, delete_response.text

    db_session.expire_all()

    deleted_item = (
        db_session.query(MealPlanItem)
        .filter(MealPlanItem.id == meal_plan_item_id)
        .first()
    )
    assert deleted_item is None

    detached_apply_row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.id == apply_row_id,
        )
        .first()
    )
    assert detached_apply_row is not None
    assert detached_apply_row.meal_plan_item_id is None

    delete_row = (
        db_session.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.event_kind == "post_apply_delete",
            AutoMealPlanEvent.run_id == run_id,
        )
        .order_by(AutoMealPlanEvent.id.desc())
        .first()
    )
    assert delete_row is not None
    assert delete_row.execution_status == "deleted"
    assert delete_row.meal_plan_item_id is None
    assert delete_row.final_recipe_id is None
    assert "item_deleted" in delete_row.reasons
    assert f"deleted_meal_plan_item_id={meal_plan_item_id}" in delete_row.reasons