def test_feedback_rejects_member_from_other_household(client, sample_data):
    payload = {
        "family_member_id": sample_data["member_3_id"],
        "reaction": "gostou",
        "note": "Teste cruzado",
    }

    response = client.post(
        f"/feedback/meal-plan/{sample_data['meal_household_1_id']}",
        json=payload,
    )

    assert response.status_code == 400
    assert "mesmo agregado" in response.json()["detail"]


def test_bulk_feedback_rejects_member_from_other_household(client, sample_data):
    payload = {
        "items": [
            {
                "meal_plan_item_id": sample_data["meal_household_1_id"],
                "family_member_id": sample_data["member_3_id"],
                "reaction": "gostou",
                "note": "Teste bulk cruzado",
            }
        ],
        "skip_existing": False,
    }

    response = client.post("/bulk/feedback/import", json=payload)

    assert response.status_code == 400
    assert "mesmo agregado" in response.json()["detail"]


def test_delete_member_with_recipe_preferences_is_blocked(client, sample_data):
    response = client.delete(
        f"/households/{sample_data['household_1_id']}/members/{sample_data['member_1_id']}"
    )

    assert response.status_code == 400
    assert "avaliações de receitas" in response.json()["detail"]


def test_delete_household_with_meal_plan_and_no_members_is_blocked(client, sample_data):
    response = client.delete(f"/households/{sample_data['household_3_id']}")

    assert response.status_code == 400
    assert "refeições planeadas" in response.json()["detail"]


def test_delete_empty_household_succeeds(client, sample_data):
    response = client.delete(f"/households/{sample_data['household_4_id']}")

    assert response.status_code == 200
    assert response.json()["message"] == "Agregado apagado com sucesso."