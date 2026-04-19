import { styles } from "../styles";
import type { Household } from "../types";

type Props = {
  household: Household | null;
  onOpenHouseholds: () => void;
  onOpenRatings: () => void;
  onOpenScores: () => void;
};

type MenuTile = {
  id: string;
  title: string;
  description: string;
  meta: string;
  onOpen: () => void;
  disabled?: boolean;
};

export function FamilyWorkspaceMenu({
  household,
  onOpenHouseholds,
  onOpenRatings,
  onOpenScores,
}: Props) {
  const hasHousehold = Boolean(household);

  const items: MenuTile[] = [
    {
      id: "households",
      title: "Agregados e membros",
      description:
        "Criar agregados, editar nomes e gerir os membros de cada família.",
      meta: "Estrutura",
      onOpen: onOpenHouseholds,
    },
    {
      id: "ratings",
      title: "Avaliar receitas",
      description:
        "Registar ratings por membro para o agregado atualmente ativo.",
      meta: "Preferências",
      onOpen: onOpenRatings,
      disabled: !hasHousehold,
    },
    {
      id: "scores",
      title: "Scores da família",
      description:
        "Consultar as médias e avaliações já registadas para o agregado ativo.",
      meta: "Análise",
      onOpen: onOpenScores,
      disabled: !hasHousehold,
    },
  ];

  return (
    <section className="nf-menu-panel">
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Família</div>
        <h3 style={styles.sectionTitle}>Preferências e agregado</h3>
        <p className="nf-menu-panel-text">
          {household
            ? `Agregado ativo: ${household.name}.`
            : "Seleciona primeiro um agregado para abrir ratings e scores."}
        </p>
      </div>

      <div className="nf-menu-grid nf-menu-grid--three">
        {items.map((item) => (
          <div
            key={item.id}
            className={`nf-clickable-card nf-clickable-card--compact${item.disabled ? " nf-clickable-card--disabled" : ""}`}
            role="button"
            tabIndex={item.disabled ? -1 : 0}
            aria-disabled={item.disabled ? "true" : "false"}
            onClick={() => {
              if (!item.disabled) {
                item.onOpen();
              }
            }}
            onKeyDown={(event) => {
              if (item.disabled) {
                return;
              }

              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                item.onOpen();
              }
            }}
            title={
              item.disabled
                ? "Seleciona primeiro um agregado"
                : item.title
            }
          >
            <div className="nf-card-kicker">{item.meta}</div>
            <div className="nf-card-title">{item.title}</div>
            <div className="nf-card-body">{item.description}</div>
          </div>
        ))}
      </div>
    </section>
  );
}