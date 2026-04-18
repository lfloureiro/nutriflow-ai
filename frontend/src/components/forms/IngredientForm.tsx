import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { Ingredient } from "../types";

type Props = {
  ingredients: Ingredient[];
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

export function IngredientForm({
  ingredients,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [newName, setNewName] = useState("");
  const [selectedIngredientId, setSelectedIngredientId] = useState("");
  const [editName, setEditName] = useState("");

  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const selectedIngredient = useMemo(
    () =>
      ingredients.find(
        (ingredient) => String(ingredient.id) === selectedIngredientId
      ) ?? null,
    [ingredients, selectedIngredientId]
  );

  useEffect(() => {
    setEditName(selectedIngredient?.name ?? "");
  }, [selectedIngredient]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();

    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!newName.trim()) {
      setLocalError("O nome do ingrediente é obrigatório.");
      return;
    }

    try {
      setCreating(true);

      const res = await fetch(`${API_BASE_URL}/ingredients/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newName.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível criar o ingrediente.")
        );
      }

      setNewName("");
      setLocalMessage("Ingrediente criado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdate() {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedIngredient) {
      setLocalError("Seleciona um ingrediente.");
      return;
    }

    if (!editName.trim()) {
      setLocalError("O nome do ingrediente é obrigatório.");
      return;
    }

    try {
      setSaving(true);

      const res = await fetch(
        `${API_BASE_URL}/ingredients/${selectedIngredient.id}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: editName.trim(),
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível atualizar o ingrediente.")
        );
      }

      setLocalMessage("Ingrediente atualizado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedIngredient) {
      setLocalError("Seleciona um ingrediente.");
      return;
    }

    const confirmed = window.confirm(
      `Queres apagar o ingrediente "${selectedIngredient.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);

      const res = await fetch(
        `${API_BASE_URL}/ingredients/${selectedIngredient.id}`,
        {
          method: "DELETE",
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível apagar o ingrediente.")
        );
      }

      setSelectedIngredientId("");
      setEditName("");
      setLocalMessage("Ingrediente apagado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeleting(false);
    }
  }

  const busy = creating || saving || deleting;

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Gerir ingredientes</h2>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div style={{ display: "grid", gap: "24px" }}>
        <form style={styles.form} onSubmit={handleCreate}>
          <h3 style={styles.formTitle}>Novo ingrediente</h3>

          <input
            style={styles.input}
            placeholder="Nome do ingrediente"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            disabled={busy}
          />

          <button style={styles.button} type="submit" disabled={busy}>
            Adicionar ingrediente
          </button>
        </form>

        <div style={styles.form}>
          <h3 style={styles.formTitle}>Editar ou apagar ingrediente</h3>

          {ingredients.length === 0 ? (
            <p style={styles.empty}>Sem ingredientes disponíveis.</p>
          ) : (
            <>
              <select
                style={styles.select}
                value={selectedIngredientId}
                onChange={(e) => setSelectedIngredientId(e.target.value)}
                disabled={busy}
              >
                <option value="">Seleciona um ingrediente existente</option>
                {ingredients.map((ingredient) => (
                  <option key={ingredient.id} value={ingredient.id}>
                    {ingredient.name}
                  </option>
                ))}
              </select>

              {selectedIngredient && (
                <>
                  <input
                    style={styles.input}
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    disabled={busy}
                  />

                  <div
                    style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}
                  >
                    <button
                      type="button"
                      style={styles.button}
                      onClick={handleUpdate}
                      disabled={busy}
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
                      onClick={handleDelete}
                      disabled={busy}
                    >
                      Apagar
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}