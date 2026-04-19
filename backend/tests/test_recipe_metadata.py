def test_create_recipe_with_metadata(client):
    payload = {
        "name": "Frango grelhado",
        "description": "Receita simples de teste",
        "categoria_alimentar": "carne",
        "proteina_principal": "frango",
        "adequado_refeicao": "jantar",
        "auto_plan_enabled": True,
    }

    response = client.post("/recipes/", json=payload)

    assert response.status_code == 201, response.text
    body = response.json()

    assert body["name"] == "Frango grelhado"
    assert body["categoria_alimentar"] == "carne"
    assert body["proteina_principal"] == "frango"
    assert body["adequado_refeicao"] == "jantar"
    assert body["auto_plan_enabled"] is True


def test_update_recipe_can_clear_and_toggle_metadata(client):
    create_response = client.post(
        "/recipes/",
        json={
            "name": "Atum com massa",
            "description": "Receita inicial",
            "categoria_alimentar": "peixe",
            "proteina_principal": "peixe",
            "adequado_refeicao": "almoco",
            "auto_plan_enabled": True,
        },
    )
    assert create_response.status_code == 201, create_response.text
    recipe_id = create_response.json()["id"]

    update_response = client.patch(
        f"/recipes/{recipe_id}",
        json={
            "categoria_alimentar": None,
            "proteina_principal": "nenhuma",
            "adequado_refeicao": "ambos",
            "auto_plan_enabled": False,
        },
    )

    assert update_response.status_code == 200, update_response.text
    body = update_response.json()

    assert body["categoria_alimentar"] is None
    assert body["proteina_principal"] == "nenhuma"
    assert body["adequado_refeicao"] == "ambos"
    assert body["auto_plan_enabled"] is False