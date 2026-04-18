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

const seedRequests = [
  {
    endpoint: "/bulk/households/import",
    payload: {
      items: [{ name: "Família Loureiro" }],
      skip_existing: true,
    },
  },
  {
    endpoint: "/bulk/family-members/import",
    payload: {
      items: [
        { household_id: 1, name: "Luis" },
        { household_id: 1, name: "Patricia" },
        { household_id: 1, name: "Tiago" },
        { household_id: 1, name: "Diogo" },
      ],
      skip_existing: true,
    },
  },
  {
    endpoint: "/bulk/ingredients/import",
    payload: {
      items: [
        { name: "Atum" },
        { name: "Massa" },
        { name: "Milho" },
        { name: "Tomate" },
        { name: "Cebola" },
        { name: "Arroz" },
        { name: "Feijão" },
        { name: "Carne picada" },
      ],
      skip_existing: true,
    },
  },
  {
    endpoint: "/bulk/recipes/import",
    payload: {
      items: [
        { name: "Massa com atum", description: "Receita base" },
        { name: "Salada de atum", description: "Receita rápida" },
        { name: "Chili Beans", description: "Chili com carne picada" },
      ],
      skip_existing: true,
    },
  },
  {
    endpoint: "/bulk/recipe-ingredients/import",
    payload: {
      items: [
        { recipe_id: 1, ingredient_id: 2, quantity: "250", unit: "g" },
        { recipe_id: 1, ingredient_id: 1, quantity: "2", unit: "latas" },
        { recipe_id: 2, ingredient_id: 1, quantity: "1", unit: "lata" },
        { recipe_id: 2, ingredient_id: 4, quantity: "2", unit: "unidades" },
        { recipe_id: 3, ingredient_id: 6, quantity: "250", unit: "g" },
        { recipe_id: 3, ingredient_id: 7, quantity: "250", unit: "g" },
        { recipe_id: 3, ingredient_id: 8, quantity: "500", unit: "g" },
        { recipe_id: 3, ingredient_id: 5, quantity: "1", unit: "unidade" },
      ],
      skip_existing: true,
    },
  },
  {
    endpoint: "/bulk/meal-plan/import",
    payload: {
      items: [
        {
          plan_date: "2026-04-20",
          meal_type: "jantar",
          notes: "Segunda",
          recipe_id: 1,
        },
        {
          plan_date: "2026-04-21",
          meal_type: "almoco",
          notes: "Terça",
          recipe_id: 2,
        },
        {
          plan_date: "2026-04-21",
          meal_type: "jantar",
          notes: "Terça à noite",
          recipe_id: 3,
        },
      ],
      skip_existing: true,
    },
  },
  {
    endpoint: "/bulk/feedback/import",
    payload: {
      items: [
        {
          meal_plan_item_id: 1,
          family_member_id: 1,
          reaction: "gostou",
          note: "Quero repetir",
        },
        {
          meal_plan_item_id: 1,
          family_member_id: 2,
          reaction: "neutro",
          note: "Aceitável",
        },
        {
          meal_plan_item_id: 2,
          family_member_id: 3,
          reaction: "nao_gostou",
          note: "Não gostou do tomate",
        },
        {
          meal_plan_item_id: 3,
          family_member_id: 4,
          reaction: "gostou",
          note: "Gostou bastante",
        },
      ],
      skip_existing: true,
    },
  },
];

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

  async function handleLoadSeed() {
    setFormMessage(null);
    setFormError(null);

    try {
      setLoading(true);

      for (const request of seedRequests) {
        const res = await fetch(`${API_BASE_URL}${request.endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request.payload),
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(
            typeof data.detail === "string"
              ? data.detail
              : `Erro ao carregar seed em ${request.endpoint}`
          );
        }
      }

      setFormMessage("Dataset base carregado com sucesso.");
      await onSuccess();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Importação e seed</h2>

      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "16px" }}>
        <button style={styles.button} onClick={handleLoadSeed} disabled={loading}>
          Carregar dataset base
        </button>
      </div>

      <p style={styles.info}>
        Podes carregar o dataset completo ou executar importações bulk por recurso.
      </p>

      <div style={{ height: "12px" }} />

      <div style={styles.form}>
        <select
          style={styles.select}
          value={selectedOption}
          onChange={(e) => handleOptionChange(e.target.value as ImportOptionKey)}
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