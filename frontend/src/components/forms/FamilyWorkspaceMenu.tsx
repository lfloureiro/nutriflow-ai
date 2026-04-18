import { styles } from "../styles";
import type { Household } from "../types";

type Props = {
  household: Household | null;
  onOpenHouseholds: () => void;
  onOpenRatings: () => void;
  onOpenScores: () => void;
};

export function FamilyWorkspaceMenu({
  household,
  onOpenHouseholds,
  onOpenRatings,
  onOpenScores,
}: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Família e preferências</h2>

      <p style={styles.info}>
        {household
          ? `A trabalhar no agregado: ${household.name}`
          : "Seleciona primeiro um agregado ativo na página principal."}
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
          onClick={onOpenRatings}
          disabled={!household}
        >
          Avaliar receitas
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenScores}
          disabled={!household}
        >
          Scores da família
        </button>
      </div>
    </section>
  );
}