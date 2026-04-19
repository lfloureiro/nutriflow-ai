import { styles } from "../styles";

type Props = {
  onOpenCreateRecipe: () => void;
  onOpenManageIngredients: () => void;
  onOpenLinkIngredient: () => void;
  onOpenRecipeList: () => void;
};

type MenuTile = {
  id: string;
  title: string;
  description: string;
  meta: string;
  onOpen: () => void;
};

export function RecipeToolsMenu({
  onOpenCreateRecipe,
  onOpenManageIngredients,
  onOpenLinkIngredient,
  onOpenRecipeList,
}: Props) {
  const items: MenuTile[] = [
    {
      id: "recipe-create",
      title: "Nova receita",
      description: "Criar uma nova receita base com nome e descrição.",
      meta: "Receitas",
      onOpen: onOpenCreateRecipe,
    },
    {
      id: "ingredient-manage",
      title: "Gerir ingredientes",
      description: "Adicionar, editar ou limpar a lista global de ingredientes.",
      meta: "Ingredientes",
      onOpen: onOpenManageIngredients,
    },
    {
      id: "recipe-ingredient-link",
      title: "Associar ingredientes",
      description:
        "Ligar ingredientes a receitas com quantidade e unidade.",
      meta: "Composição",
      onOpen: onOpenLinkIngredient,
    },
    {
      id: "recipe-list",
      title: "Ver receitas",
      description: "Abrir a lista de receitas para consulta e manutenção.",
      meta: "Consulta",
      onOpen: onOpenRecipeList,
    },
  ];

  return (
    <section className="nf-menu-panel">
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Receitas</div>
        <h3 style={styles.sectionTitle}>Ferramentas de receitas</h3>
        <p className="nf-menu-panel-text">
          Escolhe a operação que queres fazer sem abrir um ecrã demasiado comprido.
        </p>
      </div>

      <div className="nf-menu-grid">
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