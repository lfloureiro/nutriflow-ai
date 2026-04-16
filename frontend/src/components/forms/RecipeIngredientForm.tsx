import { useState } from "react";
import { API_BASE_URL } from "../../config";
import type { Ingredient, Recipe } from "../types";
import { styles } from "../styles";

type Props = {
  recipes: Recipe[];
  ingredients: Ingredient[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

export function RecipeIngredientForm({
  recipes,
  ingredients,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [selectedRecipeId, setSelectedRecipeId] = useState("");
  const [selectedIngredientId, setSelectedIngredientId] = useState("");
  const [ingredientQuantity, setIngredientQuantity] = useState("");
  const [ingredientUnit, setIngredientUnit] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormMessage(null);
    setFormError(null);

    try {
      const recipeId = Number(selectedRecipeId);
      const ingredientId = Number(selectedIngredientId);

      const res = await fetch(`${API_BASE_URL}/recipes/${recipeId}/ingredients`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ingredient_id: ingredientId,
          quantity: ingredientQuantity || null,
          unit: ingredientUnit || null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao associar ingrediente.");
      }

      setSelectedRecipeId("");
      setSelectedIngredientId("");
      setIngredientQuantity("");
      setIngredientUnit("");
      setFormMessage("Ingrediente associado à receita.");
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Associar ingrediente a receita</h2>
      <form style={styles.form} onSubmit={handleSubmit}>
        <select
          style={styles.select}
          value={selectedRecipeId}
          onChange={(e) => setSelectedRecipeId(e.target.value)}
        >
          <option value="">Seleciona a receita</option>
          {recipes.map((recipe) => (
            <option key={recipe.id} value={recipe.id}>
              {recipe.name}
            </option>
          ))}
        </select>

        <select
          style={styles.select}
          value={selectedIngredientId}
          onChange={(e) => setSelectedIngredientId(e.target.value)}
        >
          <option value="">Seleciona o ingrediente</option>
          {ingredients.map((ingredient) => (
            <option key={ingredient.id} value={ingredient.id}>
              {ingredient.name}
            </option>
          ))}
        </select>

        <input
          style={styles.input}
          placeholder="Quantidade"
          value={ingredientQuantity}
          onChange={(e) => setIngredientQuantity(e.target.value)}
        />

        <input
          style={styles.input}
          placeholder="Unidade"
          value={ingredientUnit}
          onChange={(e) => setIngredientUnit(e.target.value)}
        />

        <button style={styles.button} type="submit">
          Associar
        </button>
      </form>
    </section>
  );
}