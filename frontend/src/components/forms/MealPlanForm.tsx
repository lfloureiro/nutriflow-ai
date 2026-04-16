import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import type { MealPlanItem, Recipe } from "../types";
import { styles } from "../styles";

type Props = {
  recipes: Recipe[];
  mealPlan: MealPlanItem[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

export function MealPlanForm({
  recipes,
  mealPlan,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [mealPlanDate, setMealPlanDate] = useState("");
  const [mealPlanType, setMealPlanType] = useState("jantar");
  const [mealPlanNotes, setMealPlanNotes] = useState("");
  const [mealPlanRecipeId, setMealPlanRecipeId] = useState("");
  const [loadingSuggestion, setLoadingSuggestion] = useState(true);

  useEffect(() => {
    async function loadNextSlot() {
      try {
        setLoadingSuggestion(true);

        const res = await fetch(`${API_BASE_URL}/meal-plan/next-slot`);
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.detail || "Erro ao obter a próxima refeição.");
        }

        setMealPlanDate(data.plan_date);
        setMealPlanType(data.meal_type);
      } catch (err) {
        setFormError(err instanceof Error ? err.message : "Erro inesperado.");
      } finally {
        setLoadingSuggestion(false);
      }
    }

    loadNextSlot();
  }, [setFormError]);

  const duplicateExists = useMemo(() => {
    return mealPlan.some(
      (item) => item.plan_date === mealPlanDate && item.meal_type === mealPlanType
    );
  }, [mealPlan, mealPlanDate, mealPlanType]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormMessage(null);
    setFormError(null);

    if (duplicateExists) {
      setFormError(
        "Já existe uma refeição planeada para essa data e esse tipo de refeição."
      );
      return;
    }

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
      <h2 style={styles.formTitle}>Planear próxima refeição</h2>

      {loadingSuggestion ? (
        <p style={styles.info}>A obter a próxima refeição disponível...</p>
      ) : (
        <p style={styles.info}>
          A data e o tipo de refeição foram sugeridos automaticamente. Podes ajustar antes de gravar.
        </p>
      )}

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

        {duplicateExists && (
          <p style={styles.warning}>
            Aviso: já existe uma refeição planeada para esta data e este tipo de refeição.
          </p>
        )}

        <button style={styles.button} type="submit">
          Adicionar ao plano
        </button>
      </form>
    </section>
  );
}