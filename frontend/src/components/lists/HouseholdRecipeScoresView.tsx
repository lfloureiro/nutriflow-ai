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

function formatAverage(value: number) {
  return value.toFixed(1).replace(".", ",");
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
        <div className="nf-menu-panel-head">
          <div className="nf-kicker">Análise</div>
          <h2 style={styles.sectionTitle}>Scores da família</h2>
          <p className="nf-menu-panel-text">
            Seleciona primeiro um agregado ativo.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Análise</div>
        <h2 style={styles.sectionTitle}>Scores da família</h2>
        <p className="nf-menu-panel-text">
          Visão consolidada das receitas já avaliadas pelo agregado ativo.
        </p>
      </div>

      <div className="nf-pill-row" style={{ marginTop: "12px" }}>
        <span className="nf-context-meta-chip">{household.name}</span>
        <span className="nf-context-meta-chip">
          {household.members.length} membros
        </span>
      </div>

      {loading ? (
        <p style={styles.info}>A carregar scores...</p>
      ) : localError ? (
        <p style={styles.error}>Erro: {localError}</p>
      ) : ratedSummaries.length === 0 ? (
        <p style={styles.empty}>Ainda não existem avaliações nesta família.</p>
      ) : (
        <div className="nf-score-grid" style={{ marginTop: "14px" }}>
          {ratedSummaries.map((summary) => (
            <div key={summary.recipe_id} className="nf-score-card">
              <div className="nf-score-card-head">
                <div className="nf-card-title">{summary.recipe_name}</div>
                <div className="nf-score-value">
                  {formatAverage(summary.average_rating)}
                </div>
              </div>

              <div className="nf-score-stars">
                {renderStars(summary.average_rating)}
              </div>

              <div className="nf-card-body">
                {summary.ratings_count} avaliação(ões) registadas
              </div>

              <div className="nf-pill-row" style={{ marginTop: "10px" }}>
                {summary.ratings.map((rating) => (
                  <span key={rating.id} className="nf-score-pill">
                    {rating.family_member.name}: {rating.rating}/5
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}