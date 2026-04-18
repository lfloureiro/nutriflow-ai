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

type ReactionValue = "gostou" | "neutro" | "nao_gostou";

function formatReaction(value: ReactionValue) {
  if (value === "gostou") return "Gostou";
  if (value === "neutro") return "Neutro";
  return "Não gostou";
}

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

export function MealFeedbackForm({
  mealPlan,
  members,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [selectedMealPlanId, setSelectedMealPlanId] = useState("");
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [reaction, setReaction] = useState<ReactionValue>("gostou");
  const [note, setNote] = useState("");

  const [feedbackList, setFeedbackList] = useState<MealFeedback[]>([]);
  const [loadingFeedback, setLoadingFeedback] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editMemberId, setEditMemberId] = useState("");
  const [editReaction, setEditReaction] = useState<ReactionValue>("gostou");
  const [editNote, setEditNote] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

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
        throw new Error(getErrorMessage(data, "Erro ao carregar feedback."));
      }

      setFeedbackList(data);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoadingFeedback(false);
    }
  }

  useEffect(() => {
    setEditingId(null);
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);
    loadFeedback(selectedMealPlanId);
  }, [selectedMealPlanId]);

  function startEditing(entry: MealFeedback) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    setEditingId(entry.id);
    setEditMemberId(String(entry.family_member.id));
    setEditReaction(entry.reaction);
    setEditNote(entry.note ?? "");
  }

  function cancelEditing() {
    setEditingId(null);
    setEditMemberId("");
    setEditReaction("gostou");
    setEditNote("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedMealPlanId) {
      setLocalError("Seleciona uma refeição.");
      return;
    }

    if (!selectedMemberId) {
      setLocalError("Seleciona o membro da família.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/feedback/meal-plan/${selectedMealPlanId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          family_member_id: Number(selectedMemberId),
          reaction,
          note: note.trim() ? note : null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Erro ao registar feedback."));
      }

      setSelectedMemberId("");
      setReaction("gostou");
      setNote("");
      setLocalMessage("Feedback registado com sucesso.");

      await loadFeedback(selectedMealPlanId);
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

  async function handleUpdate(feedbackId: number) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!editMemberId) {
      setLocalError("Seleciona o membro da família.");
      return;
    }

    try {
      setSavingId(feedbackId);

      const res = await fetch(`${API_BASE_URL}/feedback/${feedbackId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          family_member_id: Number(editMemberId),
          reaction: editReaction,
          note: editNote.trim() ? editNote : null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Erro ao atualizar feedback."));
      }

      setLocalMessage("Feedback atualizado com sucesso.");
      cancelEditing();

      await loadFeedback(selectedMealPlanId);
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleDelete(entry: MealFeedback) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    const confirmed = window.confirm(
      `Apagar o feedback de "${entry.family_member.name}" para esta refeição?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(entry.id);

      const res = await fetch(`${API_BASE_URL}/feedback/${entry.id}`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Erro ao apagar feedback."));
      }

      if (editingId === entry.id) {
        cancelEditing();
      }

      setLocalMessage("Feedback apagado com sucesso.");

      await loadFeedback(selectedMealPlanId);
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Registar feedback</h2>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

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
          onChange={(e) => setReaction(e.target.value as ReactionValue)}
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
          {feedbackList.map((entry) => {
            const isEditing = editingId === entry.id;
            const isSaving = savingId === entry.id;
            const isDeleting = deletingId === entry.id;
            const isBusy = isSaving || isDeleting;

            return (
              <li key={entry.id} style={styles.listItem}>
                {!isEditing ? (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    }}
                  >
                    <div>
                      <strong>{entry.family_member.name}</strong> —{" "}
                      {formatReaction(entry.reaction)}
                      {entry.note ? ` — ${entry.note}` : ""}
                    </div>

                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        style={styles.button}
                        onClick={() => startEditing(entry)}
                        disabled={isBusy}
                      >
                        Editar
                      </button>

                      <button
                        type="button"
                        style={{
                          ...styles.button,
                          background: "#7f1d1d",
                          border: "1px solid #991b1b",
                        }}
                        onClick={() => handleDelete(entry)}
                        disabled={isBusy}
                      >
                        Apagar
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={styles.form}>
                    <select
                      style={styles.select}
                      value={editMemberId}
                      onChange={(e) => setEditMemberId(e.target.value)}
                      disabled={isBusy}
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
                      value={editReaction}
                      onChange={(e) =>
                        setEditReaction(e.target.value as ReactionValue)
                      }
                      disabled={isBusy}
                    >
                      <option value="gostou">Gostou</option>
                      <option value="neutro">Neutro</option>
                      <option value="nao_gostou">Não gostou</option>
                    </select>

                    <textarea
                      style={styles.textarea}
                      value={editNote}
                      onChange={(e) => setEditNote(e.target.value)}
                      placeholder="Nota opcional"
                      disabled={isBusy}
                    />

                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        style={styles.button}
                        onClick={() => handleUpdate(entry.id)}
                        disabled={isBusy}
                      >
                        Guardar
                      </button>

                      <button
                        type="button"
                        style={styles.button}
                        onClick={cancelEditing}
                        disabled={isBusy}
                      >
                        Cancelar
                      </button>

                      <button
                        type="button"
                        style={{
                          ...styles.button,
                          background: "#7f1d1d",
                          border: "1px solid #991b1b",
                        }}
                        onClick={() => handleDelete(entry)}
                        disabled={isBusy}
                      >
                        Apagar
                      </button>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}