import { useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";

type Props = {
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

export function RecipeForm({ onSuccess, setFormMessage, setFormError }: Props) {
  const [recipeName, setRecipeName] = useState("");
  const [recipeDescription, setRecipeDescription] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormMessage(null);
    setFormError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/recipes/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: recipeName,
          description: recipeDescription || null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao criar receita.");
      }

      setRecipeName("");
      setRecipeDescription("");
      setFormMessage("Receita criada com sucesso.");
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.formTitle}>Nova receita</h2>
      <form style={styles.form} onSubmit={handleSubmit}>
        <input
          style={styles.input}
          placeholder="Nome da receita"
          value={recipeName}
          onChange={(e) => setRecipeName(e.target.value)}
        />
        <textarea
          style={styles.textarea}
          placeholder="Descrição"
          value={recipeDescription}
          onChange={(e) => setRecipeDescription(e.target.value)}
        />
        <button style={styles.button} type="submit">
          Criar receita
        </button>
      </form>
    </section>
  );
}