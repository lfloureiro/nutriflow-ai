import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import type { Ingredient, Recipe } from "../types";
import { styles } from "../styles";

type Props = {
  recipes: Recipe[];
  ingredients: Ingredient[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

type RecipeIngredientLink = {
  id: number;
  quantity: string | null;
  unit: string | null;
  ingredient: {
    id: number;
    name: string;
  };
};

type RecipeDetailResponse = {
  id: number;
  name: string;
  description: string | null;
  ingredient_links: RecipeIngredientLink[];
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

export function RecipeIngredientForm({
  recipes,
  ingredients,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [selectedRecipeId, setSelectedRecipeId] = useState("");
  const [selectedIngredientId, setSelectedIngredientId] = useState("");
  const [ingredientQuantity, setIngredientQuantity] = useState("");
  const [ingredientUnit, setIngredientUnit] = useState("");

  const [recipeDetail, setRecipeDetail] = useState<RecipeDetailResponse | null>(null);
  const [loadingLinks, setLoadingLinks] = useState(false);

  const [editingLinkId, setEditingLinkId] = useState<number | null>(null);
  const [editIngredientId, setEditIngredientId] = useState("");
  const [editQuantity, setEditQuantity] = useState("");
  const [editUnit, setEditUnit] = useState("");

  const [creating, setCreating] = useState(false);
  const [savingLinkId, setSavingLinkId] = useState<number | null>(null);
  const [deletingLinkId, setDeletingLinkId] = useState<number | null>(null);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const selectedRecipe = useMemo(
    () => recipes.find((recipe) => String(recipe.id) === selectedRecipeId) ?? null,
    [recipes, selectedRecipeId]
  );

  async function loadRecipeDetail(recipeId: string) {
    if (!recipeId) {
      setRecipeDetail(null);
      return;
    }

    try {
      setLoadingLinks(true);

      const res = await fetch(`${API_BASE_URL}/recipes/${recipeId}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível carregar os ingredientes da receita.")
        );
      }

      setRecipeDetail(data);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
      setRecipeDetail(null);
    } finally {
      setLoadingLinks(false);
    }
  }

  useEffect(() => {
    setEditingLinkId(null);
    setEditIngredientId("");
    setEditQuantity("");
    setEditUnit("");
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);
    loadRecipeDetail(selectedRecipeId);
  }, [selectedRecipeId]);

  function startEditing(link: RecipeIngredientLink) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    setEditingLinkId(link.id);
    setEditIngredientId(String(link.ingredient.id));
    setEditQuantity(link.quantity ?? "");
    setEditUnit(link.unit ?? "");
  }

  function cancelEditing() {
    setEditingLinkId(null);
    setEditIngredientId("");
    setEditQuantity("");
    setEditUnit("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedRecipeId) {
      setLocalError("Seleciona a receita.");
      return;
    }

    if (!selectedIngredientId) {
      setLocalError("Seleciona o ingrediente.");
      return;
    }

    try {
      setCreating(true);

      const recipeId = Number(selectedRecipeId);
      const ingredientId = Number(selectedIngredientId);

      const res = await fetch(`${API_BASE_URL}/recipes/${recipeId}/ingredients`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ingredient_id: ingredientId,
          quantity: ingredientQuantity.trim() || null,
          unit: ingredientUnit.trim() || null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao associar ingrediente.");
      }

      setSelectedIngredientId("");
      setIngredientQuantity("");
      setIngredientUnit("");
      setLocalMessage("Ingrediente associado à receita.");

      await loadRecipeDetail(selectedRecipeId);
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdate(linkId: number) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedRecipeId) {
      setLocalError("Seleciona a receita.");
      return;
    }

    if (!editIngredientId) {
      setLocalError("Seleciona o ingrediente.");
      return;
    }

    try {
      setSavingLinkId(linkId);

      const res = await fetch(
        `${API_BASE_URL}/recipes/${selectedRecipeId}/ingredients/${linkId}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ingredient_id: Number(editIngredientId),
            quantity: editQuantity.trim() || null,
            unit: editUnit.trim() || null,
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível atualizar a ligação ingrediente-receita.")
        );
      }

      setLocalMessage("Ligação ingrediente-receita atualizada com sucesso.");
      cancelEditing();

      await loadRecipeDetail(selectedRecipeId);
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingLinkId(null);
    }
  }

  async function handleDelete(link: RecipeIngredientLink) {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedRecipeId) {
      setLocalError("Seleciona a receita.");
      return;
    }

    const confirmed = window.confirm(
      `Queres remover "${link.ingredient.name}" da receita "${selectedRecipe?.name ?? ""}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingLinkId(link.id);

      const res = await fetch(
        `${API_BASE_URL}/recipes/${selectedRecipeId}/ingredients/${link.id}`,
        {
          method: "DELETE",
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível remover o ingrediente da receita.")
        );
      }

      if (editingLinkId === link.id) {
        cancelEditing();
      }

      setLocalMessage("Ingrediente removido da receita com sucesso.");

      await loadRecipeDetail(selectedRecipeId);
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeletingLinkId(null);
    }
  }

  const busy = creating || loadingLinks;

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Associar ingrediente a receita</h2>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <form style={styles.form} onSubmit={handleSubmit}>
        <select
          style={styles.select}
          value={selectedRecipeId}
          onChange={(e) => setSelectedRecipeId(e.target.value)}
          disabled={busy}
        >
          <option value="">Seleciona a receita</option>
          {recipes.map((recipe) => (
            <option key={recipe.id} value={recipe.id}>
              {recipe.name}
            </option>
          ))}
        </select>

        <select
          style={styles.select}
          value={selectedIngredientId}
          onChange={(e) => setSelectedIngredientId(e.target.value)}
          disabled={busy || !selectedRecipeId}
        >
          <option value="">Seleciona o ingrediente</option>
          {ingredients.map((ingredient) => (
            <option key={ingredient.id} value={ingredient.id}>
              {ingredient.name}
            </option>
          ))}
        </select>

        <input
          style={styles.input}
          placeholder="Quantidade"
          value={ingredientQuantity}
          onChange={(e) => setIngredientQuantity(e.target.value)}
          disabled={busy || !selectedRecipeId}
        />

        <input
          style={styles.input}
          placeholder="Unidade"
          value={ingredientUnit}
          onChange={(e) => setIngredientUnit(e.target.value)}
          disabled={busy || !selectedRecipeId}
        />

        <button style={styles.button} type="submit" disabled={busy || !selectedRecipeId}>
          Associar
        </button>
      </form>

      <div style={{ height: "20px" }} />

      <h3 style={styles.formTitle}>Ingredientes da receita selecionada</h3>

      {!selectedRecipeId ? (
        <p style={styles.empty}>Seleciona uma receita para ver os ingredientes associados.</p>
      ) : loadingLinks ? (
        <p style={styles.info}>A carregar ingredientes da receita...</p>
      ) : !recipeDetail || recipeDetail.ingredient_links.length === 0 ? (
        <p style={styles.empty}>Esta receita ainda não tem ingredientes associados.</p>
      ) : (
        <ul style={styles.list}>
          {recipeDetail.ingredient_links.map((link) => {
            const isEditing = editingLinkId === link.id;
            const isSaving = savingLinkId === link.id;
            const isDeleting = deletingLinkId === link.id;
            const rowBusy = isSaving || isDeleting;

            return (
              <li
                key={link.id}
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
                        onClick={() => startEditing(link)}
                        disabled={rowBusy}
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
                        onClick={() => handleDelete(link)}
                        disabled={rowBusy}
                      >
                        Apagar
                      </button>
                    </div>

                    <div
                      style={{
                        flex: 1,
                        minWidth: "280px",
                        fontSize: "15px",
                        lineHeight: 1.5,
                      }}
                    >
                      <strong>{link.ingredient.name}</strong>
                      {link.quantity ? ` — ${link.quantity}` : ""}
                      {link.unit ? ` ${link.unit}` : ""}
                    </div>
                  </div>
                ) : (
                  <div style={styles.form}>
                    <select
                      style={styles.select}
                      value={editIngredientId}
                      onChange={(e) => setEditIngredientId(e.target.value)}
                      disabled={rowBusy}
                    >
                      <option value="">Seleciona o ingrediente</option>
                      {ingredients.map((ingredient) => (
                        <option key={ingredient.id} value={ingredient.id}>
                          {ingredient.name}
                        </option>
                      ))}
                    </select>

                    <input
                      style={styles.input}
                      value={editQuantity}
                      onChange={(e) => setEditQuantity(e.target.value)}
                      placeholder="Quantidade"
                      disabled={rowBusy}
                    />

                    <input
                      style={styles.input}
                      value={editUnit}
                      onChange={(e) => setEditUnit(e.target.value)}
                      placeholder="Unidade"
                      disabled={rowBusy}
                    />

                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        style={styles.button}
                        onClick={() => handleUpdate(link.id)}
                        disabled={rowBusy}
                      >
                        Guardar
                      </button>

                      <button
                        type="button"
                        style={styles.button}
                        onClick={cancelEditing}
                        disabled={rowBusy}
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
                        onClick={() => handleDelete(link)}
                        disabled={rowBusy}
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