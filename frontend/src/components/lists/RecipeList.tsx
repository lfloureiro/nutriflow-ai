import { useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { Recipe } from "../types";
import {
  RECIPE_CATEGORY_OPTIONS,
  RECIPE_MEAL_SUITABILITY_OPTIONS,
  RECIPE_PROTEIN_OPTIONS,
} from "../types";

type Props = {
  recipes: Recipe[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

type EditState = {
  name: string;
  description: string;
  categoria_alimentar: string;
  proteina_principal: string;
  adequado_refeicao: string;
  auto_plan_enabled: boolean;
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

function getOptionLabel(
  value: string | null,
  options: Array<{ value: string; label: string }>
) {
  if (!value) {
    return "Sem definir";
  }

  return options.find((option) => option.value === value)?.label ?? value;
}

export function RecipeList({
  recipes,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const [editState, setEditState] = useState<EditState>({
    name: "",
    description: "",
    categoria_alimentar: "",
    proteina_principal: "",
    adequado_refeicao: "",
    auto_plan_enabled: true,
  });

  const filteredRecipes = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return recipes;

    return recipes.filter((recipe) => {
      const haystack = [
        recipe.name,
        recipe.description ?? "",
        recipe.categoria_alimentar ?? "",
        recipe.proteina_principal ?? "",
        recipe.adequado_refeicao ?? "",
      ]
        .join(" ")
        .toLowerCase();

      return haystack.includes(term);
    });
  }, [recipes, search]);

  function startEditing(recipe: Recipe) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    setEditingId(recipe.id);
    setEditState({
      name: recipe.name,
      description: recipe.description ?? "",
      categoria_alimentar: recipe.categoria_alimentar ?? "",
      proteina_principal: recipe.proteina_principal ?? "",
      adequado_refeicao: recipe.adequado_refeicao ?? "",
      auto_plan_enabled: recipe.auto_plan_enabled,
    });
  }

  function cancelEditing() {
    setEditingId(null);
    setEditState({
      name: "",
      description: "",
      categoria_alimentar: "",
      proteina_principal: "",
      adequado_refeicao: "",
      auto_plan_enabled: true,
    });
  }

  async function handleSave(recipeId: number) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!editState.name.trim()) {
      setLocalError("O nome da receita é obrigatório.");
      return;
    }

    try {
      setSavingId(recipeId);

      const res = await fetch(`${API_BASE_URL}/recipes/${recipeId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editState.name.trim(),
          description: editState.description.trim() || null,
          categoria_alimentar: editState.categoria_alimentar || null,
          proteina_principal: editState.proteina_principal || null,
          adequado_refeicao: editState.adequado_refeicao || null,
          auto_plan_enabled: editState.auto_plan_enabled,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível atualizar a receita.")
        );
      }

      setLocalMessage("Receita atualizada com sucesso.");
      cancelEditing();
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleDelete(recipe: Recipe) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    const confirmed = window.confirm(
      `Queres apagar a receita "${recipe.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(recipe.id);

      const res = await fetch(`${API_BASE_URL}/recipes/${recipe.id}`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível apagar a receita.")
        );
      }

      if (editingId === recipe.id) {
        cancelEditing();
      }

      setLocalMessage("Receita apagada com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeletingId(null);
    }
  }

  const inlineButtonStyle = {
    ...styles.button,
    width: "auto" as const,
    minWidth: "120px",
  };

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Receitas</div>
        <h2 style={styles.sectionTitle}>Lista de receitas</h2>
        <p className="nf-menu-panel-text">
          Consulta e edita as receitas já com metadados mínimos para o futuro auto-planeamento.
        </p>
      </div>

      <div className="nf-pill-row" style={{ marginTop: "12px" }}>
        <span className="nf-context-meta-chip">
          {recipes.length} receita(s) no total
        </span>
        {search.trim() && (
          <span className="nf-context-meta-chip">
            {filteredRecipes.length} resultado(s)
          </span>
        )}
      </div>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div className="nf-panel-stack" style={{ marginTop: "14px" }}>
        <div>
          <label htmlFor="recipe-search" className="nf-field-label">
            Procurar receita
          </label>
          <input
            id="recipe-search"
            style={styles.input}
            placeholder="Ex.: frango, peixe, leguminosas..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {filteredRecipes.length === 0 ? (
          <p style={styles.empty}>
            {recipes.length === 0
              ? "Ainda não existem receitas."
              : "Nenhuma receita corresponde à pesquisa."}
          </p>
        ) : (
          <div className="nf-record-list">
            {filteredRecipes.map((recipe) => {
              const isEditing = editingId === recipe.id;
              const isSaving = savingId === recipe.id;
              const isDeleting = deletingId === recipe.id;
              const isBusy = isSaving || isDeleting;

              return (
                <div key={recipe.id} className="nf-record-card">
                  {!isEditing ? (
                    <div className="nf-record-card-head">
                      <div className="nf-record-card-main">
                        <div className="nf-record-title">{recipe.name}</div>

                        <div className="nf-record-description">
                          {recipe.description?.trim() || "Sem descrição."}
                        </div>

                        <div className="nf-pill-row">
                          <span className="nf-score-pill">
                            {getOptionLabel(
                              recipe.categoria_alimentar,
                              RECIPE_CATEGORY_OPTIONS
                            )}
                          </span>

                          <span className="nf-score-pill">
                            {getOptionLabel(
                              recipe.proteina_principal,
                              RECIPE_PROTEIN_OPTIONS
                            )}
                          </span>

                          <span className="nf-score-pill">
                            {getOptionLabel(
                              recipe.adequado_refeicao,
                              RECIPE_MEAL_SUITABILITY_OPTIONS
                            )}
                          </span>

                          <span className="nf-score-pill">
                            {recipe.auto_plan_enabled
                              ? "Auto-planeamento ativo"
                              : "Excluída do auto-planeamento"}
                          </span>
                        </div>
                      </div>

                      <div className="nf-record-actions">
                        <button
                          type="button"
                          style={inlineButtonStyle}
                          onClick={() => startEditing(recipe)}
                          disabled={isBusy}
                        >
                          Editar
                        </button>

                        <button
                          type="button"
                          style={{
                            ...inlineButtonStyle,
                            background: "#7f1d1d",
                            border: "1px solid #991b1b",
                          }}
                          onClick={() => handleDelete(recipe)}
                          disabled={isBusy}
                        >
                          {isDeleting ? "A apagar..." : "Apagar"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="nf-panel-stack">
                      <div className="nf-record-title">Editar receita</div>

                      <input
                        style={styles.input}
                        placeholder="Nome da receita"
                        value={editState.name}
                        onChange={(e) =>
                          setEditState((current) => ({
                            ...current,
                            name: e.target.value,
                          }))
                        }
                        disabled={isBusy}
                      />

                      <textarea
                        style={styles.textarea}
                        placeholder="Descrição"
                        value={editState.description}
                        onChange={(e) =>
                          setEditState((current) => ({
                            ...current,
                            description: e.target.value,
                          }))
                        }
                        disabled={isBusy}
                      />

                      <select
                        style={styles.select}
                        value={editState.categoria_alimentar}
                        onChange={(e) =>
                          setEditState((current) => ({
                            ...current,
                            categoria_alimentar: e.target.value,
                          }))
                        }
                        disabled={isBusy}
                      >
                        <option value="">Categoria alimentar</option>
                        {RECIPE_CATEGORY_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>

                      <select
                        style={styles.select}
                        value={editState.proteina_principal}
                        onChange={(e) =>
                          setEditState((current) => ({
                            ...current,
                            proteina_principal: e.target.value,
                          }))
                        }
                        disabled={isBusy}
                      >
                        <option value="">Proteína principal</option>
                        {RECIPE_PROTEIN_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>

                      <select
                        style={styles.select}
                        value={editState.adequado_refeicao}
                        onChange={(e) =>
                          setEditState((current) => ({
                            ...current,
                            adequado_refeicao: e.target.value,
                          }))
                        }
                        disabled={isBusy}
                      >
                        <option value="">Adequado para</option>
                        {RECIPE_MEAL_SUITABILITY_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>

                      <label
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          fontSize: "14px",
                          color: "#cbd5e1",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={editState.auto_plan_enabled}
                          onChange={(e) =>
                            setEditState((current) => ({
                              ...current,
                              auto_plan_enabled: e.target.checked,
                            }))
                          }
                          disabled={isBusy}
                        />
                        Incluir esta receita no auto-planeamento
                      </label>

                      <div className="nf-actions-inline">
                        <button
                          type="button"
                          style={inlineButtonStyle}
                          onClick={() => handleSave(recipe.id)}
                          disabled={isBusy}
                        >
                          {isSaving ? "A guardar..." : "Guardar"}
                        </button>

                        <button
                          type="button"
                          style={inlineButtonStyle}
                          onClick={cancelEditing}
                          disabled={isBusy}
                        >
                          Cancelar
                        </button>

                        <button
                          type="button"
                          style={{
                            ...inlineButtonStyle,
                            background: "#7f1d1d",
                            border: "1px solid #991b1b",
                          }}
                          onClick={() => handleDelete(recipe)}
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
        )}
      </div>
    </section>
  );
}