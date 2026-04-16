import { useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";

type Props = {
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

export function IngredientForm({ onSuccess, setFormMessage, setFormError }: Props) {
  const [ingredientName, setIngredientName] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormMessage(null);
    setFormError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/ingredients/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: ingredientName,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao criar ingrediente.");
      }

      setIngredientName("");
      setFormMessage("Ingrediente criado com sucesso.");
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Novo ingrediente</h2>
      <form style={styles.form} onSubmit={handleSubmit}>
        <input
          style={styles.input}
          placeholder="Nome do ingrediente"
          value={ingredientName}
          onChange={(e) => setIngredientName(e.target.value)}
        />
        <button style={styles.button} type="submit">
          Criar ingrediente
        </button>
      </form>
    </section>
  );
}