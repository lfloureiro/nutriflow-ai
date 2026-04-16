import { styles } from "../styles";
import type { RecipeFeedbackSummary } from "../types";

type Props = {
  summaries: RecipeFeedbackSummary[];
};

export function RecipeScoresView({ summaries }: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Scores de aceitação</h2>

      {summaries.length === 0 ? (
        <p style={styles.empty}>Sem scores ainda.</p>
      ) : (
        <ul style={styles.list}>
          {summaries.map((summary) => (
            <li key={summary.recipe_id} style={styles.listItem}>
              <strong>{summary.recipe_name}</strong>
              <div style={styles.sourceList}>
                <div style={styles.sourceItem}>Feedback total: {summary.total_feedback}</div>
                <div style={styles.sourceItem}>Gostou: {summary.liked_count}</div>
                <div style={styles.sourceItem}>Neutro: {summary.neutral_count}</div>
                <div style={styles.sourceItem}>Não gostou: {summary.disliked_count}</div>
                <div style={styles.sourceItem}>
                  Score de aceitação: {summary.acceptance_score}%
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}