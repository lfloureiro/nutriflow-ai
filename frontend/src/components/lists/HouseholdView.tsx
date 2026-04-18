import { styles } from "../styles";

type Props = {
  onOpenHouseholds: () => void;
  onOpenMembers: () => void;
};

export function HouseholdView({ onOpenHouseholds, onOpenMembers }: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Agregados e membros</h2>

      <p style={styles.info}>
        Escolhe a área que queres gerir.
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
          Gerir agregados
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenMembers}
        >
          Gerir membros
        </button>
      </div>
    </section>
  );
}