def test_shopping_list_returns_in_cart_false_by_default(client, sample_data):
    response = client.get(
        "/shopping-list/generate",
        params={"household_id": sample_data["household_1_id"]},
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assert len(body) >= 1
    assert all(item["in_cart"] is False for item in body)


def test_shopping_list_item_state_can_be_marked_and_unmarked(client, sample_data):
    initial_response = client.get(
        "/shopping-list/generate",
        params={"household_id": sample_data["household_1_id"]},
    )
    assert initial_response.status_code == 200, initial_response.text

    initial_items = initial_response.json()
    first_item = initial_items[0]

    mark_payload = {
        "household_id": sample_data["household_1_id"],
        "ingredient_id": first_item["ingredient_id"],
        "unit": first_item["unit"],
        "in_cart": True,
    }

    mark_response = client.put("/shopping-list/item-state", json=mark_payload)
    assert mark_response.status_code == 200, mark_response.text
    assert mark_response.json()["in_cart"] is True

    refreshed_response = client.get(
        "/shopping-list/generate",
        params={"household_id": sample_data["household_1_id"]},
    )
    assert refreshed_response.status_code == 200, refreshed_response.text

    refreshed_items = refreshed_response.json()
    refreshed_target = next(
        item
        for item in refreshed_items
        if item["ingredient_id"] == first_item["ingredient_id"]
        and item["unit"] == first_item["unit"]
    )
    assert refreshed_target["in_cart"] is True

    unmark_payload = {
        "household_id": sample_data["household_1_id"],
        "ingredient_id": first_item["ingredient_id"],
        "unit": first_item["unit"],
        "in_cart": False,
    }

    unmark_response = client.put("/shopping-list/item-state", json=unmark_payload)
    assert unmark_response.status_code == 200, unmark_response.text
    assert unmark_response.json()["in_cart"] is False