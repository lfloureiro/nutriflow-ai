import { useState } from "react";
import { API_BASE_URL } from "../../config";
import type { Recipe } from "../types";
import { styles } from "../styles";

type Props = {
  recipes: Recipe[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

export function MealPlanForm({ recipes, onSuccess, setFormMessage, setFormError }: Props) {
  const [mealPlanDate, setMealPlanDate] = useState("");
  const [mealPlanType, setMealPlanType] = useState("jantar");
  const [mealPlanNotes, setMealPlanNotes] = useState("");
  const [mealPlanRecipeId, setMealPlanRecipeId] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormMessage(null);
    setFormError(null);

    try {
      const recipeId = Number(mealPlanRecipeId);

      const res = await fetch(`${API_BASE_URL}/meal-plan/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_date: mealPlanDate,
          meal_type: mealPlanType,
          notes: mealPlanNotes || null,
          recipe_id: recipeId,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao criar item do plano.");
      }

      setMealPlanDate("");
      setMealPlanType("jantar");
      setMealPlanNotes("");
      setMealPlanRecipeId("");
      setFormMessage("Plano semanal atualizado.");
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Adicionar ao plano semanal</h2>
      <form style={styles.form} onSubmit={handleSubmit}>
        <input
          style={styles.input}
          type="date"
          value={mealPlanDate}
          onChange={(e) => setMealPlanDate(e.target.value)}
        />

        <select
          style={styles.select}
          value={mealPlanType}
          onChange={(e) => setMealPlanType(e.target.value)}
        >
          <option value="pequeno-almoco">Pequeno-almoço</option>
          <option value="almoco">Almoço</option>
          <option value="lanche">Lanche</option>
          <option value="jantar">Jantar</option>
        </select>

        <select
          style={styles.select}
          value={mealPlanRecipeId}
          onChange={(e) => setMealPlanRecipeId(e.target.value)}
        >
          <option value="">Seleciona a receita</option>
          {recipes.map((recipe) => (
            <option key={recipe.id} value={recipe.id}>
              {recipe.name}
            </option>
          ))}
        </select>

        <textarea
          style={styles.textarea}
          placeholder="Notas"
          value={mealPlanNotes}
          onChange={(e) => setMealPlanNotes(e.target.value)}
        />

        <button style={styles.button} type="submit">
          Adicionar ao plano
        </button>
      </form>
    </section>
  );
}