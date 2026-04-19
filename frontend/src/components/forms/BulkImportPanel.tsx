import { useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";

type Props = {
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

type ImportOptionKey =
  | "households"
  | "family-members"
  | "ingredients"
  | "recipes"
  | "recipe-ingredients"
  | "meal-plan"
  | "feedback";

const importOptions: Record<
  ImportOptionKey,
  { label: string; endpoint: string; example: string }
> = {
  households: {
    label: "Agregados",
    endpoint: "/bulk/households/import",
    example: JSON.stringify(
      {
        items: [{ name: "Família Loureiro" }],
        skip_existing: true,
      },
      null,
      2
    ),
  },
  "family-members": {
    label: "Membros da família",
    endpoint: "/bulk/family-members/import",
    example: JSON.stringify(
      {
        items: [
          { household_id: 1, name: "Luis" },
          { household_id: 1, name: "Patricia" },
        ],
        skip_existing: true,
      },
      null,
      2
    ),
  },
  ingredients: {
    label: "Ingredientes",
    endpoint: "/bulk/ingredients/import",
    example: JSON.stringify(
      {
        items: [{ name: "Atum" }, { name: "Massa" }],
        skip_existing: true,
      },
      null,
      2
    ),
  },
  recipes: {
    label: "Receitas",
    endpoint: "/bulk/recipes/import",
    example: JSON.stringify(
      {
        items: [
          {
            name: "Massa com atum",
            description: "Receita base",
          },
        ],
        skip_existing: true,
      },
      null,
      2
    ),
  },
  "recipe-ingredients": {
    label: "Ingredientes das receitas",
    endpoint: "/bulk/recipe-ingredients/import",
    example: JSON.stringify(
      {
        items: [
          { recipe_id: 1, ingredient_id: 2, quantity: "250", unit: "g" },
          { recipe_id: 1, ingredient_id: 1, quantity: "2", unit: "latas" },
        ],
        skip_existing: true,
      },
      null,
      2
    ),
  },
  "meal-plan": {
    label: "Plano semanal",
    endpoint: "/bulk/meal-plan/import",
    example: JSON.stringify(
      {
        items: [
          {
            household_id: 1,
            plan_date: "2026-04-20",
            meal_type: "jantar",
            notes: "Segunda",
            recipe_id: 1,
          },
        ],
        skip_existing: true,
      },
      null,
      2
    ),
  },
  feedback: {
    label: "Feedback",
    endpoint: "/bulk/feedback/import",
    example: JSON.stringify(
      {
        items: [
          {
            meal_plan_item_id: 1,
            family_member_id: 1,
            reaction: "gostou",
            note: "Quero repetir",
          },
        ],
        skip_existing: true,
      },
      null,
      2
    ),
  },
};

export function BulkImportPanel({
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [selectedOption, setSelectedOption] =
    useState<ImportOptionKey>("households");
  const [payload, setPayload] = useState(importOptions.households.example);
  const [loading, setLoading] = useState(false);

  const selectedConfig = useMemo(
    () => importOptions[selectedOption],
    [selectedOption]
  );

  function handleOptionChange(value: ImportOptionKey) {
    setSelectedOption(value);
    setPayload(importOptions[value].example);
  }

  async function handleRunImport() {
    setFormMessage(null);
    setFormError(null);

    try {
      setLoading(true);

      const parsedPayload = JSON.parse(payload);

      const res = await fetch(`${API_BASE_URL}${selectedConfig.endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsedPayload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro na importação.");
      }

      setFormMessage(
        `Importação concluída em ${selectedConfig.label}: criados ${data.created}, ignorados ${data.skipped}.`
      );
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Importação bulk por JSON</h2>

      <p style={styles.info}>
        Executa importações bulk manuais por recurso.
      </p>

      <div style={{ height: "12px" }} />

      <div style={styles.form}>
        <select
          style={styles.select}
          value={selectedOption}
          onChange={(e) => handleOptionChange(e.target.value as ImportOptionKey)}
          disabled={loading}
        >
          {Object.entries(importOptions).map(([key, option]) => (
            <option key={key} value={key}>
              {option.label}
            </option>
          ))}
        </select>

        <textarea
          style={{
            ...styles.textarea,
            minHeight: "320px",
            fontFamily: "Consolas, monospace",
            fontSize: "13px",
          }}
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
          disabled={loading}
        />

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            style={styles.button}
            type="button"
            onClick={() => setPayload(selectedConfig.example)}
            disabled={loading}
          >
            Repor exemplo
          </button>

          <button
            style={styles.button}
            type="button"
            onClick={handleRunImport}
            disabled={loading}
          >
            Executar importação
          </button>
        </div>
      </div>
    </section>
  );
}