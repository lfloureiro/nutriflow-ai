def test_meal_plan_allows_same_slot_in_different_households(client, sample_data):
    payload_1 = {
        "household_id": sample_data["household_1_id"],
        "plan_date": "2026-06-01",
        "meal_type": "jantar",
        "notes": "Mesmo slot HH1",
        "recipe_id": sample_data["recipe_1_id"],
    }

    payload_2 = {
        "household_id": sample_data["household_2_id"],
        "plan_date": "2026-06-01",
        "meal_type": "jantar",
        "notes": "Mesmo slot HH2",
        "recipe_id": sample_data["recipe_1_id"],
    }

    response_1 = client.post("/meal-plan/", json=payload_1)
    response_2 = client.post("/meal-plan/", json=payload_2)

    assert response_1.status_code == 201, response_1.text
    assert response_2.status_code == 201, response_2.text

    body_1 = response_1.json()
    body_2 = response_2.json()

    assert body_1["id"] != body_2["id"]
    assert body_1["plan_date"] == "2026-06-01"
    assert body_2["plan_date"] == "2026-06-01"
    assert body_1["meal_type"] == "jantar"
    assert body_2["meal_type"] == "jantar"

    list_hh1 = client.get(
        "/meal-plan/",
        params={"household_id": sample_data["household_1_id"]},
    )
    list_hh2 = client.get(
        "/meal-plan/",
        params={"household_id": sample_data["household_2_id"]},
    )

    assert list_hh1.status_code == 200, list_hh1.text
    assert list_hh2.status_code == 200, list_hh2.text

    hh1_ids = {item["id"] for item in list_hh1.json()}
    hh2_ids = {item["id"] for item in list_hh2.json()}

    assert body_1["id"] in hh1_ids
    assert body_1["id"] not in hh2_ids
    assert body_2["id"] in hh2_ids
    assert body_2["id"] not in hh1_ids


def test_meal_plan_blocks_same_slot_in_same_household(client, sample_data):
    payload = {
        "household_id": sample_data["household_1_id"],
        "plan_date": "2026-06-02",
        "meal_type": "almoco",
        "notes": "Primeiro registo",
        "recipe_id": sample_data["recipe_1_id"],
    }

    response_1 = client.post("/meal-plan/", json=payload)
    response_2 = client.post("/meal-plan/", json=payload)

    assert response_1.status_code == 201, response_1.text
    assert response_2.status_code == 400
    assert "Já existe uma refeição planeada" in response_2.json()["detail"]


def test_bulk_meal_plan_allows_same_slot_in_different_households(client, sample_data):
    payload_1 = {
        "items": [
            {
                "household_id": sample_data["household_1_id"],
                "plan_date": "2026-06-03",
                "meal_type": "jantar",
                "notes": "Bulk HH1",
                "recipe_id": sample_data["recipe_1_id"],
            }
        ],
        "skip_existing": False,
    }

    payload_2 = {
        "items": [
            {
                "household_id": sample_data["household_2_id"],
                "plan_date": "2026-06-03",
                "meal_type": "jantar",
                "notes": "Bulk HH2",
                "recipe_id": sample_data["recipe_1_id"],
            }
        ],
        "skip_existing": False,
    }

    response_1 = client.post("/bulk/meal-plan/import", json=payload_1)
    response_2 = client.post("/bulk/meal-plan/import", json=payload_2)

    assert response_1.status_code == 200, response_1.text
    assert response_2.status_code == 200, response_2.text

    assert response_1.json()["created"] == 1
    assert response_1.json()["skipped"] == 0
    assert response_2.json()["created"] == 1
    assert response_2.json()["skipped"] == 0