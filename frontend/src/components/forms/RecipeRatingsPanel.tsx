import { useEffect, useMemo, useState } from "react";
import { styles } from "../styles";
import type { Household, Recipe } from "../types";
import {
  deleteRecipePreference,
  listRecipePreferences,
  upsertRecipePreference,
  type RecipePreference,
} from "../../services/recipePreferences";

type Props = {
  household: Household | null;
  recipes: Recipe[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

type MemberDraft = {
  rating: string;
  note: string;
};

function buildEmptyDrafts(household: Household | null): Record<number, MemberDraft> {
  if (!household) return {};

  const result: Record<number, MemberDraft> = {};

  household.members.forEach((member) => {
    result[member.id] = {
      rating: "",
      note: "",
    };
  });

  return result;
}

export function RecipeRatingsPanel({
  household,
  recipes,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [selectedRecipeId, setSelectedRecipeId] = useState("");
  const [preferences, setPreferences] = useState<RecipePreference[]>([]);
  const [drafts, setDrafts] = useState<Record<number, MemberDraft>>({});
  const [loading, setLoading] = useState(false);
  const [savingMemberId, setSavingMemberId] = useState<number | null>(null);
  const [deletingMemberId, setDeletingMemberId] = useState<number | null>(null);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const preferenceByMemberId = useMemo(() => {
    const map = new Map<number, RecipePreference>();

    preferences.forEach((item) => {
      map.set(item.family_member.id, item);
    });

    return map;
  }, [preferences]);

  async function loadPreferences(householdId: number, recipeId: number) {
    try {
      setLoading(true);

      const data = await listRecipePreferences(householdId, recipeId);
      setPreferences(data);
    } catch (err) {
      setLocalError(
        err instanceof Error ? err.message : "Erro inesperado ao carregar avaliações."
      );
      setPreferences([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);
    setDrafts(buildEmptyDrafts(household));
  }, [household]);

  useEffect(() => {
    if (!household || !selectedRecipeId) {
      setPreferences([]);
      setDrafts(buildEmptyDrafts(household));
      return;
    }

    loadPreferences(household.id, Number(selectedRecipeId));
  }, [household, selectedRecipeId]);

  useEffect(() => {
    if (!household) {
      setDrafts({});
      return;
    }

    const nextDrafts = buildEmptyDrafts(household);

    household.members.forEach((member) => {
      const existing = preferenceByMemberId.get(member.id);
      if (existing) {
        nextDrafts[member.id] = {
          rating: String(existing.rating),
          note: existing.note ?? "",
        };
      }
    });

    setDrafts(nextDrafts);
  }, [household, preferenceByMemberId]);

  async function handleSave(memberId: number) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!household) {
      setLocalError("Seleciona primeiro um agregado.");
      return;
    }

    if (!selectedRecipeId) {
      setLocalError("Seleciona uma receita.");
      return;
    }

    const draft = drafts[memberId];
    if (!draft || draft.rating === "") {
      setLocalError("Seleciona uma classificação entre 0 e 5.");
      return;
    }

    try {
      setSavingMemberId(memberId);

      await upsertRecipePreference(household.id, Number(selectedRecipeId), memberId, {
        rating: Number(draft.rating),
        note: draft.note.trim() || null,
      });

      setLocalMessage("Avaliação guardada com sucesso.");
      await loadPreferences(household.id, Number(selectedRecipeId));
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingMemberId(null);
    }
  }

  async function handleDelete(memberId: number) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!household) {
      setLocalError("Seleciona primeiro um agregado.");
      return;
    }

    if (!selectedRecipeId) {
      setLocalError("Seleciona uma receita.");
      return;
    }

    const existing = preferenceByMemberId.get(memberId);
    if (!existing) {
      setLocalError("Este membro ainda não tem avaliação para esta receita.");
      return;
    }

    const confirmed = window.confirm(
      `Apagar a avaliação atual de "${existing.family_member.name}" para esta receita?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingMemberId(memberId);

      await deleteRecipePreference(household.id, Number(selectedRecipeId), memberId);

      setLocalMessage("Avaliação apagada com sucesso.");
      await loadPreferences(household.id, Number(selectedRecipeId));
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeletingMemberId(null);
    }
  }

  if (!household) {
    return (
      <section style={styles.card}>
        <h2 style={styles.sectionTitle}>Avaliar receitas</h2>
        <p style={styles.empty}>Seleciona primeiro um agregado ativo.</p>
      </section>
    );
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Avaliar receitas</h2>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div style={styles.form}>
        <select
          style={styles.select}
          value={selectedRecipeId}
          onChange={(e) => setSelectedRecipeId(e.target.value)}
        >
          <option value="">Seleciona uma receita</option>
          {recipes.map((recipe) => (
            <option key={recipe.id} value={recipe.id}>
              {recipe.name}
            </option>
          ))}
        </select>
      </div>

      <div style={{ height: "16px" }} />

      {!selectedRecipeId ? (
        <p style={styles.empty}>Seleciona uma receita para avaliar.</p>
      ) : loading ? (
        <p style={styles.info}>A carregar avaliações atuais...</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "16px",
          }}
        >
          {household.members.map((member) => {
            const draft = drafts[member.id] ?? { rating: "", note: "" };
            const hasSavedValue = preferenceByMemberId.has(member.id);
            const isSaving = savingMemberId === member.id;
            const isDeleting = deletingMemberId === member.id;
            const isBusy = isSaving || isDeleting;

            return (
              <div
                key={member.id}
                style={{
                  border: "1px solid #374151",
                  borderRadius: "12px",
                  background: "#111827",
                  padding: "14px",
                  display: "grid",
                  gap: "12px",
                }}
              >
                <div>
                  <strong>{member.name}</strong>
                </div>

                <select
                  style={styles.select}
                  value={draft.rating}
                  onChange={(e) =>
                    setDrafts((current) => ({
                      ...current,
                      [member.id]: {
                        ...current[member.id],
                        rating: e.target.value,
                      },
                    }))
                  }
                  disabled={isBusy}
                >
                  <option value="">Classificação 0 a 5</option>
                  <option value="0">0</option>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                  <option value="5">5</option>
                </select>

                <textarea
                  style={{ ...styles.textarea, minHeight: "90px" }}
                  placeholder="Nota opcional"
                  value={draft.note}
                  onChange={(e) =>
                    setDrafts((current) => ({
                      ...current,
                      [member.id]: {
                        ...current[member.id],
                        note: e.target.value,
                      },
                    }))
                  }
                  disabled={isBusy}
                />

                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                  <button
                    type="button"
                    style={styles.button}
                    onClick={() => handleSave(member.id)}
                    disabled={isBusy}
                  >
                    Guardar
                  </button>

                  <button
                    type="button"
                    style={{
                      ...styles.button,
                      background: "#7f1d1d",
                      border: "1px solid #991b1b",
                    }}
                    onClick={() => handleDelete(member.id)}
                    disabled={isBusy || !hasSavedValue}
                  >
                    Apagar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}