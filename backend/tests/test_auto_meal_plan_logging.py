from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent


def test_auto_plan_preview_logs_suggestions(db_session, client, sample_data):
    payload = {
        "household_id": sample_data["household_2_id"],
        "start_date": "2026-05-12",
        "end_date": "2026-05-12",
        "meal_types": ["jantar"],
        "skip_existing": True,
    }

    response = client.post("/meal-plan/auto-plan/preview", json=payload)
    assert response.status_code == 200, response.text

    rows = db_session.query(AutoMealPlanEvent).order_by(AutoMealPlanEvent.id.asc()).all()

    assert len(rows) == 1
    row = rows[0]

    assert row.household_id == sample_data["household_2_id"]
    assert row.event_kind == "preview"
    assert row.plan_date.isoformat() == "2026-05-12"
    assert row.meal_type == "jantar"
    assert row.suggestion_action == "suggest"
    assert row.execution_status is None
    assert row.suggested_recipe_id is not None
    assert row.reasons
    assert row.request_meal_types == ["jantar"]
    assert row.skip_existing is True
    assert row.run_id


def test_auto_plan_apply_logs_created_rows(db_session, client, sample_data):
    payload = {
        "household_id": sample_data["household_2_id"],
        "start_date": "2026-05-13",
        "end_date": "2026-05-13",
        "meal_types": ["almoco"],
        "skip_existing": True,
    }

    response = client.post("/meal-plan/auto-plan/apply", json=payload)
    assert response.status_code == 200, response.text

    rows = db_session.query(AutoMealPlanEvent).order_by(AutoMealPlanEvent.id.asc()).all()

    assert len(rows) == 1
    row = rows[0]

    assert row.household_id == sample_data["household_2_id"]
    assert row.event_kind == "apply"
    assert row.plan_date.isoformat() == "2026-05-13"
    assert row.meal_type == "almoco"
    assert row.suggestion_action == "suggest"
    assert row.execution_status == "created"
    assert row.suggested_recipe_id is not None
    assert row.final_recipe_id == row.suggested_recipe_id
    assert row.meal_plan_item_id is not None
    assert row.reasons
    assert row.run_id