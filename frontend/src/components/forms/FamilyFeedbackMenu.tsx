import { styles } from "../styles";

type Props = {
  onOpenHouseholds: () => void;
  onOpenMealFeedback: () => void;
  onOpenRecipeScores: () => void;
};

export function FamilyFeedbackMenu({
  onOpenHouseholds,
  onOpenMealFeedback,
  onOpenRecipeScores,
}: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Família e feedback</h2>

      <p style={styles.info}>
        Escolhe a área que queres consultar ou editar.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
          marginTop: "16px",
        }}
      >
        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenHouseholds}
        >
          Agregados e membros
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenMealFeedback}
        >
          Feedback por refeição
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenRecipeScores}
        >
          Scores por receita
        </button>
      </div>
    </section>
  );
}