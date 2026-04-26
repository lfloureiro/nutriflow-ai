from datetime import date

from backend.app.models.recipe import Recipe
from backend.app.services.auto_meal_planner import score_recipe_for_slot


def build_recipe(recipe_id: int, name: str, categoria: str, proteina: str) -> Recipe:
    return Recipe(
        id=recipe_id,
        name=name,
        categoria_alimentar=categoria,
        proteina_principal=proteina,
        adequado_refeicao="jantar",
        auto_plan_enabled=True,
    )


def score_for(recipe: Recipe, protein_balance_mode: str, meal_type_history):
    score, reasons, _, _, _ = score_recipe_for_slot(
        recipe=recipe,
        meal_type="jantar",
        slot_date=date(2026, 5, 20),
        preference_map={},
        weekly_category_counts={},
        weekly_meat_protein_counts={},
        history_by_recipe={},
        meal_type_history=meal_type_history,
        planned_recipe_ids=set(),
        last_category=None,
        last_protein=None,
        protein_balance_mode=protein_balance_mode,
    )
    return score, reasons


def test_ratio_1_1_prefers_fish_after_one_meat():
    meat_recipe = build_recipe(1, "Frango", "carne", "frango")
    fish_recipe = build_recipe(2, "Peixe", "peixe", "peixe")
    history = {"jantar": [(date(2026, 5, 19), "carne", "frango", 10)]}

    meat_score, _ = score_for(meat_recipe, "ratio_1_1", history)
    fish_score, fish_reasons = score_for(fish_recipe, "ratio_1_1", history)

    assert fish_score > meat_score
    assert any("1:1" in reason for reason in fish_reasons)


def test_ratio_2_1_prefers_second_meat_before_switching_to_fish():
    meat_recipe = build_recipe(1, "Frango", "carne", "frango")
    fish_recipe = build_recipe(2, "Peixe", "peixe", "peixe")
    history = {"jantar": [(date(2026, 5, 19), "carne", "vaca", 10)]}

    meat_score, meat_reasons = score_for(meat_recipe, "ratio_2_1", history)
    fish_score, _ = score_for(fish_recipe, "ratio_2_1", history)

    assert meat_score > fish_score
    assert any("2:1" in reason for reason in meat_reasons)


def test_ratio_3_1_prefers_fish_after_three_meats():
    meat_recipe = build_recipe(1, "Frango", "carne", "frango")
    fish_recipe = build_recipe(2, "Peixe", "peixe", "peixe")
    history = {
        "jantar": [
            (date(2026, 5, 17), "carne", "vaca", 7),
            (date(2026, 5, 18), "carne", "porco", 8),
            (date(2026, 5, 19), "carne", "peru", 9),
        ]
    }

    meat_score, _ = score_for(meat_recipe, "ratio_3_1", history)
    fish_score, fish_reasons = score_for(fish_recipe, "ratio_3_1", history)

    assert fish_score > meat_score
    assert any("3:1" in reason for reason in fish_reasons)
