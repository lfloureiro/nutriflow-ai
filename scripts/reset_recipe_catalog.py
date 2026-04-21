from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

DB_PATH = Path("nutriflow.db")


def main() -> int:
    if not DB_PATH.exists():
        print(f"ERRO: base de dados não encontrada: {DB_PATH}")
        return 1

    engine = create_engine(f"sqlite:///{DB_PATH}")

    statements = [
        "DELETE FROM meal_feedback;",
        "DELETE FROM meal_plan_items;",
        "DELETE FROM recipe_preferences;",
        "DELETE FROM recipe_ingredients;",
        "DELETE FROM shopping_list_item_states;",
        "DELETE FROM recipes;",
        "DELETE FROM ingredients;",
    ]

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF;"))
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                print(f"OK: {stmt}")
            except Exception as exc:
                print(f"AVISO: falhou '{stmt}' -> {exc}")
        conn.execute(text("PRAGMA foreign_keys = ON;"))

    print("")
    print("Catálogo de receitas limpo com sucesso.")
    print("Mantidos: households e family_members.")
    print("Apagados: recipes, ingredients, recipe_ingredients, recipe_preferences, meal_plan_items, meal_feedback, shopping_list_item_states.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())