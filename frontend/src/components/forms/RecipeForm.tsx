import { useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import {
  RECIPE_CATEGORY_OPTIONS,
  RECIPE_MEAL_SUITABILITY_OPTIONS,
  RECIPE_PROTEIN_OPTIONS,
} from "../types";

type Props = {
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

type FormState = {
  name: string;
  description: string;
  categoria_alimentar: string;
  proteina_principal: string;
  adequado_refeicao: string;
  auto_plan_enabled: boolean;
};

const initialState: FormState = {
  name: "",
  description: "",
  categoria_alimentar: "",
  proteina_principal: "",
  adequado_refeicao: "ambos",
  auto_plan_enabled: true,
};

export function RecipeForm({
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [form, setForm] = useState<FormState>(initialState);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    setFormMessage(null);
    setFormError(null);

    if (!form.name.trim()) {
      setFormError("O nome da receita é obrigatório.");
      return;
    }

    try {
      setIsSubmitting(true);

      const res = await fetch(`${API_BASE_URL}/recipes/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: form.name.trim(),
          description: form.description.trim() || null,
          categoria_alimentar: form.categoria_alimentar || null,
          proteina_principal: form.proteina_principal || null,
          adequado_refeicao: form.adequado_refeicao || null,
          auto_plan_enabled: form.auto_plan_enabled,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail ?? "Não foi possível criar a receita.");
      }

      setForm(initialState);
      setFormMessage("Receita criada com sucesso.");
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Receitas</div>
        <h2 style={styles.sectionTitle}>Nova receita</h2>
        <p className="nf-menu-panel-text">
          Cria a receita já com os metadados mínimos para o futuro auto-planeamento.
        </p>
      </div>

      <form style={{ ...styles.form, marginTop: "14px" }} onSubmit={handleSubmit}>
        <div>
          <label htmlFor="recipe-name" className="nf-field-label">
            Nome
          </label>
          <input
            id="recipe-name"
            style={styles.input}
            value={form.name}
            onChange={(e) => setForm((current) => ({ ...current, name: e.target.value }))}
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label htmlFor="recipe-description" className="nf-field-label">
            Descrição
          </label>
          <textarea
            id="recipe-description"
            style={styles.textarea}
            value={form.description}
            onChange={(e) =>
              setForm((current) => ({ ...current, description: e.target.value }))
            }
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label htmlFor="recipe-category" className="nf-field-label">
            Categoria alimentar
          </label>
          <select
            id="recipe-category"
            style={styles.select}
            value={form.categoria_alimentar}
            onChange={(e) =>
              setForm((current) => ({
                ...current,
                categoria_alimentar: e.target.value,
              }))
            }
            disabled={isSubmitting}
          >
            <option value="">Sem definir</option>
            {RECIPE_CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="recipe-protein" className="nf-field-label">
            Proteína principal
          </label>
          <select
            id="recipe-protein"
            style={styles.select}
            value={form.proteina_principal}
            onChange={(e) =>
              setForm((current) => ({
                ...current,
                proteina_principal: e.target.value,
              }))
            }
            disabled={isSubmitting}
          >
            <option value="">Sem definir</option>
            {RECIPE_PROTEIN_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="recipe-meal-suitability" className="nf-field-label">
            Adequado para
          </label>
          <select
            id="recipe-meal-suitability"
            style={styles.select}
            value={form.adequado_refeicao}
            onChange={(e) =>
              setForm((current) => ({
                ...current,
                adequado_refeicao: e.target.value,
              }))
            }
            disabled={isSubmitting}
          >
            <option value="">Sem definir</option>
            {RECIPE_MEAL_SUITABILITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

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
            checked={form.auto_plan_enabled}
            onChange={(e) =>
              setForm((current) => ({
                ...current,
                auto_plan_enabled: e.target.checked,
              }))
            }
            disabled={isSubmitting}
          />
          Incluir esta receita no auto-planeamento
        </label>

        <button
          type="submit"
          style={styles.button}
          disabled={isSubmitting}
        >
          {isSubmitting ? "A criar..." : "Criar receita"}
        </button>
      </form>
    </section>
  );
}