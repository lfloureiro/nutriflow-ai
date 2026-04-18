import { styles } from "../styles";

type Props = {
  onOpenBackup: () => void;
  onOpenRestore: () => void;
  onOpenImport: () => void;
};

export function DataToolsMenu({
  onOpenBackup,
  onOpenRestore,
  onOpenImport,
}: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Ferramentas de dados</h2>

      <p style={styles.info}>
        Escolhe a ação que queres executar.
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
          onClick={onOpenBackup}
        >
          Guardar snapshot
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenRestore}
        >
          Repor snapshot
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenImport}
        >
          Importação bulk JSON
        </button>
      </div>
    </section>
  );
}