import { useEffect, useMemo, useState } from "react";
import { styles } from "../styles";
import type { Household } from "../types";
import {
  listHouseholdRecipeSummaries,
  type RecipePreferenceSummary,
} from "../../services/recipePreferences";

type Props = {
  household: Household | null;
};

function renderStars(value: number) {
  const rounded = Math.round(value);
  return `${"★".repeat(rounded)}${"☆".repeat(5 - rounded)}`;
}

export function HouseholdRecipeScoresView({ household }: Props) {
  const [summaries, setSummaries] = useState<RecipePreferenceSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!household) {
        setSummaries([]);
        return;
      }

      try {
        setLoading(true);
        setLocalError(null);

        const data = await listHouseholdRecipeSummaries(household.id);
        setSummaries(data);
      } catch (err) {
        setLocalError(
          err instanceof Error ? err.message : "Erro inesperado ao carregar scores."
        );
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [household]);

  const ratedSummaries = useMemo(() => {
    return [...summaries]
      .filter((item) => item.ratings_count > 0)
      .sort((a, b) => {
        if (b.average_rating !== a.average_rating) {
          return b.average_rating - a.average_rating;
        }
        return b.ratings_count - a.ratings_count;
      });
  }, [summaries]);

  if (!household) {
    return (
      <section style={styles.card}>
        <h2 style={styles.sectionTitle}>Scores da família</h2>
        <p style={styles.empty}>Seleciona primeiro um agregado ativo.</p>
      </section>
    );
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Scores da família</h2>

      <p style={styles.info}>Agregado ativo: {household.name}</p>

      {loading ? (
        <p style={styles.info}>A carregar scores...</p>
      ) : localError ? (
        <p style={styles.error}>Erro: {localError}</p>
      ) : ratedSummaries.length === 0 ? (
        <p style={styles.empty}>Ainda não existem avaliações nesta família.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "16px",
          }}
        >
          {ratedSummaries.map((summary) => (
            <div
              key={summary.recipe_id}
              style={{
                border: "1px solid #374151",
                borderRadius: "12px",
                background: "#111827",
                padding: "14px",
                display: "grid",
                gap: "10px",
              }}
            >
              <div>
                <strong>{summary.recipe_name}</strong>
              </div>

              <div>
                <strong>Média:</strong> {summary.average_rating.toFixed(2)} / 5
              </div>

              <div>{renderStars(summary.average_rating)}</div>

              <div>
                <strong>Número de avaliações:</strong> {summary.ratings_count}
              </div>

              <div>
                <strong>Detalhe:</strong>
                <ul style={{ margin: "8px 0 0 18px" }}>
                  {summary.ratings.map((item) => (
                    <li key={item.id}>
                      {item.family_member.name}: {item.rating}/5
                      {item.note ? ` — ${item.note}` : ""}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}