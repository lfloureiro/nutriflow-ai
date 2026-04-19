import { useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { MealPlanItem, Recipe } from "../types";

type Props = {
  mealPlan: MealPlanItem[];
  recipes: Recipe[];
  onSuccess: () => Promise<void>;
};

type EditState = {
  plan_date: string;
  meal_type: string;
  recipe_id: string;
  notes: string;
};

const mealTypeOptions = [
  { value: "pequeno-almoco", label: "Pequeno-almoço" },
  { value: "almoco", label: "Almoço" },
  { value: "lanche", label: "Lanche" },
  { value: "jantar", label: "Jantar" },
];

function formatMealType(mealType: string) {
  const found = mealTypeOptions.find((option) => option.value === mealType);
  if (found) return found.label;
  return mealType.replaceAll("-", " ");
}

function formatPlanDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("pt-PT", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
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

export function MealPlanList({ mealPlan, recipes, onSuccess }: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const [editState, setEditState] = useState<EditState>({
    plan_date: "",
    meal_type: "jantar",
    recipe_id: "",
    notes: "",
  });

  const groupedByDate = useMemo(() => {
    const grouped = new Map<string, MealPlanItem[]>();

    mealPlan.forEach((item) => {
      const current = grouped.get(item.plan_date) ?? [];
      current.push(item);
      grouped.set(item.plan_date, current);
    });

    return [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [mealPlan]);

  function startEditing(item: MealPlanItem) {
    setLocalMessage(null);
    setLocalError(null);
    setEditingId(item.id);
    setEditState({
      plan_date: item.plan_date,
      meal_type: item.meal_type,
      recipe_id: String(item.recipe.id),
      notes: item.notes ?? "",
    });
  }

  function cancelEditing() {
    setEditingId(null);
    setEditState({
      plan_date: "",
      meal_type: "jantar",
      recipe_id: "",
      notes: "",
    });
  }

  async function handleSave(itemId: number) {
    setLocalMessage(null);
    setLocalError(null);

    if (!editState.plan_date) {
      setLocalError("A data é obrigatória.");
      return;
    }

    if (!editState.meal_type.trim()) {
      setLocalError("O tipo de refeição é obrigatório.");
      return;
    }

    if (!editState.recipe_id) {
      setLocalError("Tens de selecionar uma receita.");
      return;
    }

    try {
      setSavingId(itemId);

      const res = await fetch(`${API_BASE_URL}/meal-plan/${itemId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          plan_date: editState.plan_date,
          meal_type: editState.meal_type,
          recipe_id: Number(editState.recipe_id),
          notes: editState.notes.trim() ? editState.notes : null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível atualizar a refeição.")
        );
      }

      setLocalMessage("Refeição atualizada com sucesso.");
      cancelEditing();
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleDelete(item: MealPlanItem) {
    setLocalMessage(null);
    setLocalError(null);

    const confirmed = window.confirm(
      `Queres apagar a refeição "${item.recipe.name}" de ${item.plan_date} (${formatMealType(
        item.meal_type
      )})?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(item.id);

      const res = await fetch(`${API_BASE_URL}/meal-plan/${item.id}`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível apagar a refeição.")
        );
      }

      if (editingId === item.id) {
        cancelEditing();
      }

      setLocalMessage("Refeição apagada com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Plano semanal</div>
        <h2 style={styles.sectionTitle}>Refeições planeadas</h2>
        <p className="nf-menu-panel-text">
          Vista organizada por data, com edição simples e mais legível.
        </p>
      </div>

      <div className="nf-pill-row" style={{ marginTop: "12px" }}>
        <span className="nf-context-meta-chip">
          {mealPlan.length} item(ns) planeado(s)
        </span>
      </div>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      {mealPlan.length === 0 ? (
        <p style={styles.empty}>Sem itens no plano.</p>
      ) : (
        <div className="nf-date-group-list" style={{ marginTop: "14px" }}>
          {groupedByDate.map(([planDate, items]) => (
            <div key={planDate} className="nf-date-group">
              <div className="nf-date-group-head">
                <div className="nf-card-title">{formatPlanDate(planDate)}</div>
                <div className="nf-card-body">{items.length} refeição(ões)</div>
              </div>

              <div className="nf-record-list">
                {items.map((item) => {
                  const isEditing = editingId === item.id;
                  const isSaving = savingId === item.id;
                  const isDeleting = deletingId === item.id;
                  const isBusy = isSaving || isDeleting;

                  return (
                    <div key={item.id} className="nf-record-card">
                      {!isEditing ? (
                        <div className="nf-record-card-head">
                          <div className="nf-record-card-main">
                            <div className="nf-pill-row">
                              <span className="nf-score-pill">
                                {formatMealType(item.meal_type)}
                              </span>
                            </div>

                            <div className="nf-record-title">{item.recipe.name}</div>

                            <div className="nf-record-description">
                              {item.notes?.trim() || "Sem notas adicionais."}
                            </div>
                          </div>

                          <div className="nf-record-actions">
                            <button
                              type="button"
                              style={styles.button}
                              onClick={() => startEditing(item)}
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
                              onClick={() => handleDelete(item)}
                              disabled={isBusy}
                            >
                              {isDeleting ? "A apagar..." : "Apagar"}
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="nf-panel-stack">
                          <div className="nf-record-title">Editar refeição</div>

                          <input
                            type="date"
                            style={styles.input}
                            value={editState.plan_date}
                            onChange={(e) =>
                              setEditState((current) => ({
                                ...current,
                                plan_date: e.target.value,
                              }))
                            }
                            disabled={isBusy}
                          />

                          <select
                            style={styles.select}
                            value={editState.meal_type}
                            onChange={(e) =>
                              setEditState((current) => ({
                                ...current,
                                meal_type: e.target.value,
                              }))
                            }
                            disabled={isBusy}
                          >
                            {mealTypeOptions.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <select
                            style={styles.select}
                            value={editState.recipe_id}
                            onChange={(e) =>
                              setEditState((current) => ({
                                ...current,
                                recipe_id: e.target.value,
                              }))
                            }
                            disabled={isBusy}
                          >
                            <option value="">Seleciona uma receita</option>
                            {recipes.map((recipe) => (
                              <option key={recipe.id} value={recipe.id}>
                                {recipe.name}
                              </option>
                            ))}
                          </select>

                          <textarea
                            style={styles.textarea}
                            value={editState.notes}
                            onChange={(e) =>
                              setEditState((current) => ({
                                ...current,
                                notes: e.target.value,
                              }))
                            }
                            disabled={isBusy}
                            placeholder="Notas opcionais"
                          />

                          <div className="nf-actions-inline">
                            <button
                              type="button"
                              style={styles.button}
                              onClick={() => handleSave(item.id)}
                              disabled={isBusy}
                            >
                              {isSaving ? "A guardar..." : "Guardar"}
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
                              onClick={() => handleDelete(item)}
                              disabled={isBusy}
                            >
                              {isDeleting ? "A apagar..." : "Apagar"}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}