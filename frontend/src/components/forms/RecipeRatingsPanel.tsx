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

function formatUpdatedAt(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Data desconhecida";
  }

  return date.toLocaleString("pt-PT", {
    dateStyle: "short",
    timeStyle: "short",
  });
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

  const selectedRecipe = useMemo(
    () => recipes.find((recipe) => String(recipe.id) === selectedRecipeId) ?? null,
    [recipes, selectedRecipeId]
  );

  async function loadPreferences(householdId: number, recipeId: number) {
    try {
      setLoading(true);
      setLocalError(null);

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
  }, [household, setFormError, setFormMessage]);

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
      const message = "Seleciona primeiro um agregado.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    if (!selectedRecipeId) {
      const message = "Seleciona uma receita.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    const draft = drafts[memberId];
    if (!draft || draft.rating === "") {
      const message = "Seleciona uma classificação entre 0 e 5.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    try {
      setSavingMemberId(memberId);

      await upsertRecipePreference(household.id, Number(selectedRecipeId), memberId, {
        rating: Number(draft.rating),
        note: draft.note.trim() || null,
      });

      const message = "Avaliação guardada com sucesso.";
      setLocalMessage(message);
      setFormMessage(message);
      await loadPreferences(household.id, Number(selectedRecipeId));
      await onSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro inesperado.";
      setLocalError(message);
      setFormError(message);
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
      const message = "Seleciona primeiro um agregado.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    if (!selectedRecipeId) {
      const message = "Seleciona uma receita.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    const existing = preferenceByMemberId.get(memberId);
    if (!existing) {
      const message = "Este membro ainda não tem avaliação para esta receita.";
      setLocalError(message);
      setFormError(message);
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

      const message = "Avaliação apagada com sucesso.";
      setLocalMessage(message);
      setFormMessage(message);
      await loadPreferences(household.id, Number(selectedRecipeId));
      await onSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro inesperado.";
      setLocalError(message);
      setFormError(message);
    } finally {
      setDeletingMemberId(null);
    }
  }

  if (!household) {
    return (
      <section style={styles.card}>
        <div className="nf-menu-panel-head">
          <div className="nf-kicker">Preferências</div>
          <h2 style={styles.sectionTitle}>Avaliar receitas</h2>
          <p className="nf-menu-panel-text">
            Seleciona primeiro um agregado ativo para começares a classificar.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Preferências</div>
        <h2 style={styles.sectionTitle}>Avaliar receitas</h2>
        <p className="nf-menu-panel-text">
          Regista classificações individuais por membro para o agregado ativo.
        </p>
      </div>

      <div className="nf-pill-row" style={{ marginTop: "12px" }}>
        <span className="nf-context-meta-chip">{household.name}</span>
        <span className="nf-context-meta-chip">
          {household.members.length} membros
        </span>
        {selectedRecipe && (
          <span className="nf-context-meta-chip">{selectedRecipe.name}</span>
        )}
      </div>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div className="nf-panel-stack" style={{ marginTop: "14px" }}>
        <div>
          <label htmlFor="recipe-ratings-select" className="nf-field-label">
            Receita a avaliar
          </label>
          <select
            id="recipe-ratings-select"
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

        {!selectedRecipeId ? (
          <p style={styles.empty}>Seleciona uma receita para mostrar as avaliações.</p>
        ) : loading ? (
          <p style={styles.info}>A carregar avaliações atuais...</p>
        ) : (
          <div className="nf-rating-grid">
            {household.members.map((member) => {
              const draft = drafts[member.id] ?? { rating: "", note: "" };
              const existing = preferenceByMemberId.get(member.id);
              const hasSavedValue = existing !== undefined;
              const isSaving = savingMemberId === member.id;
              const isDeleting = deletingMemberId === member.id;
              const isBusy = isSaving || isDeleting;

              return (
                <div key={member.id} className="nf-rating-card">
                  <div className="nf-rating-card-head">
                    <div>
                      <div className="nf-card-title">{member.name}</div>
                        <div className="nf-card-body">
                        {existing
                            ? `Avaliação guardada · ${formatUpdatedAt(existing.updated_at)}`
                            : "Ainda sem avaliação guardada"}
                        </div>
                    </div>

                    <div className="nf-pill-row">
                      {hasSavedValue ? (
                        <span className="nf-rating-chip nf-rating-chip--saved">
                          Guardado
                        </span>
                      ) : (
                        <span className="nf-rating-chip">Novo</span>
                      )}
                    </div>
                  </div>

                  <div className="nf-panel-stack">
                    <div>
                      <label
                        htmlFor={`rating-${member.id}`}
                        className="nf-field-label"
                      >
                        Classificação
                      </label>
                      <select
                        id={`rating-${member.id}`}
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
                        <option value="">Seleciona</option>
                        <option value="0">0 - Rejeitada</option>
                        <option value="1">1 - Muito fraca</option>
                        <option value="2">2 - Fraca</option>
                        <option value="3">3 - Aceitável</option>
                        <option value="4">4 - Boa</option>
                        <option value="5">5 - Excelente</option>
                      </select>
                    </div>

                    <div>
                      <label
                        htmlFor={`note-${member.id}`}
                        className="nf-field-label"
                      >
                        Nota opcional
                      </label>
                      <textarea
                        id={`note-${member.id}`}
                        style={styles.textarea}
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
                        placeholder="Ex.: gostou muito, mas preferia menos picante"
                      />
                    </div>

                    <div className="nf-actions-inline">
                      <button
                        type="button"
                        style={styles.button}
                        onClick={() => handleSave(member.id)}
                        disabled={isBusy}
                      >
                        {isSaving ? "A guardar..." : hasSavedValue ? "Atualizar" : "Guardar"}
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
                        {isDeleting ? "A apagar..." : "Apagar"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}