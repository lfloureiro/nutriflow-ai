import { styles } from "../styles";

type Props = {
  onOpenBackup: () => void;
  onOpenRestore: () => void;
  onOpenImport: () => void;
};

type MenuTile = {
  id: string;
  title: string;
  description: string;
  meta: string;
  onOpen: () => void;
};

export function DataToolsMenu({
  onOpenBackup,
  onOpenRestore,
  onOpenImport,
}: Props) {
  const items: MenuTile[] = [
    {
      id: "backup",
      title: "Guardar snapshot",
      description:
        "Criar um snapshot do dataset atual para guardar um ponto estável.",
      meta: "Backup",
      onOpen: onOpenBackup,
    },
    {
      id: "restore",
      title: "Repor snapshot",
      description:
        "Restaurar um snapshot previamente guardado para recuperar dados.",
      meta: "Reposição",
      onOpen: onOpenRestore,
    },
    {
      id: "import",
      title: "Importação bulk JSON",
      description:
        "Importar dados administrativos em lote através de payload JSON.",
      meta: "Importação",
      onOpen: onOpenImport,
    },
  ];

  return (
    <section className="nf-menu-panel">
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Administração</div>
        <h3 style={styles.sectionTitle}>Dados e importação</h3>
        <p className="nf-menu-panel-text">
          Ferramentas utilitárias e menos frequentes, mantidas fora da home principal.
        </p>
      </div>

      <div className="nf-menu-grid nf-menu-grid--three">
        {items.map((item) => (
          <div
            key={item.id}
            className="nf-clickable-card nf-clickable-card--compact"
            role="button"
            tabIndex={0}
            onClick={item.onOpen}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                item.onOpen();
              }
            }}
            title={item.title}
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