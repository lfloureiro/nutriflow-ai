import { useEffect, useState } from "react";
import { API_BASE_URL } from "../../config";
import type { Recipe } from "../types";
import { styles } from "../styles";

type Props = {
  householdId: string;
  householdName: string | null;
  recipes: Recipe[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

function getErrorMessage(data: unknown, fallback: string) {
  if (
    data &&
    typeof data === "object" &&
    "detail" in data &&
    typeof (data as { detail?: unknown }).detail === "string"
  ) {
    return (data as { detail: string }).detail;
  }

  return fallback;
}

export function MealPlanForm({
  householdId,
  householdName,
  recipes,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [mealPlanDate, setMealPlanDate] = useState("");
  const [mealPlanType, setMealPlanType] = useState("jantar");
  const [mealPlanNotes, setMealPlanNotes] = useState("");
  const [mealPlanRecipeId, setMealPlanRecipeId] = useState("");
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  async function loadNextSlot() {
    if (!householdId) {
      setMealPlanDate("");
      setMealPlanType("jantar");
      return;
    }

    try {
      setLoadingSuggestion(true);
      setLocalError(null);
      setFormMessage(null);
      setFormError(null);

      const res = await fetch(
        `${API_BASE_URL}/meal-plan/next-slot?household_id=${householdId}`
      );
      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Erro ao obter a próxima refeição.")
        );
      }

      setMealPlanDate(data.plan_date);
      setMealPlanType(data.meal_type);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoadingSuggestion(false);
    }
  }

  useEffect(() => {
    setMealPlanNotes("");
    setMealPlanRecipeId("");
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);
    loadNextSlot();
  }, [householdId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!householdId) {
      setLocalError("Seleciona primeiro um agregado ativo.");
      return;
    }

    if (!mealPlanDate) {
      setLocalError("Seleciona a data.");
      return;
    }

    if (!mealPlanRecipeId) {
      setLocalError("Seleciona a receita.");
      return;
    }

    try {
      const recipeId = Number(mealPlanRecipeId);

      const res = await fetch(`${API_BASE_URL}/meal-plan/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          household_id: Number(householdId),
          plan_date: mealPlanDate,
          meal_type: mealPlanType,
          notes: mealPlanNotes.trim() ? mealPlanNotes : null,
          recipe_id: recipeId,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Erro ao criar item do plano.")
        );
      }

      setMealPlanNotes("");
      setMealPlanRecipeId("");

      await onSuccess();
      await loadNextSlot();

      setLocalMessage("Plano semanal atualizado.");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Planear refeição manualmente</h2>

      <p style={styles.info}>
        Agregado ativo: <strong>{householdName ?? "-"}</strong>
      </p>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      {loadingSuggestion ? (
        <p style={styles.info}>A obter a próxima refeição disponível...</p>
      ) : (
        <p style={styles.info}>
          A data e o tipo de refeição foram sugeridos automaticamente para o agregado ativo. Podes ajustar manualmente antes de guardar.
        </p>
      )}

      <form style={styles.form} onSubmit={handleSubmit}>
        <input
          style={styles.input}
          type="date"
          value={mealPlanDate}
          onChange={(e) => setMealPlanDate(e.target.value)}
          disabled={!householdId}
        />

        <select
          style={styles.select}
          value={mealPlanType}
          onChange={(e) => setMealPlanType(e.target.value)}
          disabled={!householdId}
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
          disabled={!householdId}
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
          disabled={!householdId}
        />

        <button style={styles.button} type="submit" disabled={!householdId}>
          Adicionar ao plano
        </button>
      </form>
    </section>
  );
}