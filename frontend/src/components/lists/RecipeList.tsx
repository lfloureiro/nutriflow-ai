import { useState } from "react";
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

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const [editState, setEditState] = useState<EditState>({
    name: "",
    description: "",
  });

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
      <h2 style={styles.sectionTitle}>Receitas</h2>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      {recipes.length === 0 ? (
        <p style={styles.empty}>Sem receitas.</p>
      ) : (
        <ul style={styles.list}>
          {recipes.map((recipe) => {
            const isEditing = editingId === recipe.id;
            const isSaving = savingId === recipe.id;
            const isDeleting = deletingId === recipe.id;
            const isBusy = isSaving || isDeleting;

            return (
              <li
                key={recipe.id}
                style={{
                  ...styles.listItem,
                  padding: "16px 0",
                }}
              >
                {!isEditing ? (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "18px",
                      flexWrap: "wrap",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        gap: "10px",
                        flexWrap: "wrap",
                        minWidth: "170px",
                      }}
                    >
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
                        Apagar
                      </button>
                    </div>

                    <div
                      style={{
                        flex: 1,
                        minWidth: "280px",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "15px",
                          lineHeight: 1.5,
                        }}
                      >
                        <strong>{recipe.name}</strong>
                        {recipe.description ? ` — ${recipe.description}` : ""}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={styles.form}>
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

                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        style={styles.button}
                        onClick={() => handleSave(recipe.id)}
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
                        onClick={() => handleDelete(recipe)}
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