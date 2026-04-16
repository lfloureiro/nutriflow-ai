import { useEffect, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { FamilyMember, MealPlanItem, MealFeedback } from "../types";

type Props = {
  mealPlan: MealPlanItem[];
  members: FamilyMember[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

export function MealFeedbackForm({
  mealPlan,
  members,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [selectedMealPlanId, setSelectedMealPlanId] = useState("");
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [reaction, setReaction] = useState<"gostou" | "neutro" | "nao_gostou">("gostou");
  const [note, setNote] = useState("");
  const [feedbackList, setFeedbackList] = useState<MealFeedback[]>([]);
  const [loadingFeedback, setLoadingFeedback] = useState(false);

  async function loadFeedback(mealPlanItemId: string) {
    if (!mealPlanItemId) {
      setFeedbackList([]);
      return;
    }

    try {
      setLoadingFeedback(true);

      const res = await fetch(`${API_BASE_URL}/feedback/meal-plan/${mealPlanItemId}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao carregar feedback.");
      }

      setFeedbackList(data);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoadingFeedback(false);
    }
  }

  useEffect(() => {
    loadFeedback(selectedMealPlanId);
  }, [selectedMealPlanId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormMessage(null);
    setFormError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/feedback/meal-plan/${selectedMealPlanId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          family_member_id: Number(selectedMemberId),
          reaction,
          note: note || null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao registar feedback.");
      }

      setSelectedMemberId("");
      setReaction("gostou");
      setNote("");
      setFormMessage("Feedback registado com sucesso.");
      await loadFeedback(selectedMealPlanId);
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Registar feedback</h2>

      <form style={styles.form} onSubmit={handleSubmit}>
        <select
          style={styles.select}
          value={selectedMealPlanId}
          onChange={(e) => setSelectedMealPlanId(e.target.value)}
        >
          <option value="">Seleciona a refeição</option>
          {mealPlan.map((item) => (
            <option key={item.id} value={item.id}>
              {item.plan_date} — {item.meal_type} — {item.recipe.name}
            </option>
          ))}
        </select>

        <select
          style={styles.select}
          value={selectedMemberId}
          onChange={(e) => setSelectedMemberId(e.target.value)}
        >
          <option value="">Seleciona o membro</option>
          {members.map((member) => (
            <option key={member.id} value={member.id}>
              {member.name}
            </option>
          ))}
        </select>

        <select
          style={styles.select}
          value={reaction}
          onChange={(e) =>
            setReaction(e.target.value as "gostou" | "neutro" | "nao_gostou")
          }
        >
          <option value="gostou">Gostou</option>
          <option value="neutro">Neutro</option>
          <option value="nao_gostou">Não gostou</option>
        </select>

        <textarea
          style={styles.textarea}
          placeholder="Nota opcional"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />

        <button style={styles.button} type="submit">
          Guardar feedback
        </button>
      </form>

      <div style={{ height: "20px" }} />

      <h3 style={styles.formTitle}>Feedback da refeição selecionada</h3>

      {!selectedMealPlanId ? (
        <p style={styles.empty}>Seleciona uma refeição para ver o feedback.</p>
      ) : loadingFeedback ? (
        <p style={styles.info}>A carregar feedback...</p>
      ) : feedbackList.length === 0 ? (
        <p style={styles.empty}>Ainda sem feedback.</p>
      ) : (
        <ul style={styles.list}>
          {feedbackList.map((entry) => (
            <li key={entry.id} style={styles.listItem}>
              <strong>{entry.family_member.name}</strong> — {entry.reaction}
              {entry.note ? ` — ${entry.note}` : ""}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}