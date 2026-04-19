import { styles } from "../styles";

type Props = {
  onOpenHouseholds: () => void;
  onOpenMembers: () => void;
};

export function HouseholdView({ onOpenHouseholds, onOpenMembers }: Props) {
  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Estrutura</div>
        <h2 style={styles.sectionTitle}>Agregados e membros</h2>
        <p className="nf-menu-panel-text">
          Escolhe a área que queres gerir sem abrir listas longas desnecessárias.
        </p>
      </div>

      <div className="nf-menu-grid nf-menu-grid--three" style={{ marginTop: "14px" }}>
        <div
          className="nf-clickable-card nf-clickable-card--compact"
          role="button"
          tabIndex={0}
          onClick={onOpenHouseholds}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onOpenHouseholds();
            }
          }}
          title="Gerir agregados"
        >
          <div className="nf-card-kicker">Agregados</div>
          <div className="nf-card-title">Gerir agregados</div>
          <div className="nf-card-body">
            Criar, renomear ou apagar agregados familiares.
          </div>
        </div>

        <div
          className="nf-clickable-card nf-clickable-card--compact"
          role="button"
          tabIndex={0}
          onClick={onOpenMembers}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onOpenMembers();
            }
          }}
          title="Gerir membros"
        >
          <div className="nf-card-kicker">Membros</div>
          <div className="nf-card-title">Gerir membros</div>
          <div className="nf-card-body">
            Adicionar, editar e remover membros de cada agregado.
          </div>
        </div>
      </div>
    </section>
  );
}