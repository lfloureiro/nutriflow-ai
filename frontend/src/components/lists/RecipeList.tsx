import { useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { Recipe } from "../types";

type Props = {
  recipes: Recipe[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

type EditState = {
  name: string;
  description: string;
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
  });

  const filteredRecipes = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return recipes;

    return recipes.filter((recipe) => {
      const haystack = `${recipe.name} ${recipe.description ?? ""}`.toLowerCase();
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
    });
  }

  function cancelEditing() {
    setEditingId(null);
    setEditState({
      name: "",
      description: "",
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

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Receitas</div>
        <h2 style={styles.sectionTitle}>Lista de receitas</h2>
        <p className="nf-menu-panel-text">
          Consulta, procura e edita receitas sem cair numa lista longa e feia.
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
            placeholder="Ex.: atum, frango, sopa..."
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
                    <>
                      <div className="nf-record-card-head">
                        <div className="nf-record-card-main">
                          <div className="nf-record-title">{recipe.name}</div>
                          <div className="nf-record-description">
                            {recipe.description?.trim() || "Sem descrição."}
                          </div>
                        </div>

                        <div className="nf-record-actions">
                          <button
                            type="button"
                            style={styles.button}
                            onClick={() => startEditing(recipe)}
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
                            onClick={() => handleDelete(recipe)}
                            disabled={isBusy}
                          >
                            {isDeleting ? "A apagar..." : "Apagar"}
                          </button>
                        </div>
                      </div>
                    </>
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

                      <div className="nf-actions-inline">
                        <button
                          type="button"
                          style={styles.button}
                          onClick={() => handleSave(recipe.id)}
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