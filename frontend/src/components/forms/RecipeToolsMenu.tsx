import { styles } from "../styles";

type Props = {
  onOpenCreateRecipe: () => void;
  onOpenManageIngredients: () => void;
  onOpenLinkIngredient: () => void;
  onOpenRecipeList: () => void;
};

export function RecipeToolsMenu({
  onOpenCreateRecipe,
  onOpenManageIngredients,
  onOpenLinkIngredient,
  onOpenRecipeList,
}: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Receitas e ingredientes</h2>

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
          onClick={onOpenCreateRecipe}
        >
          Nova receita
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenManageIngredients}
        >
          Gerir ingredientes
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenLinkIngredient}
        >
          Associar ingrediente
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            minHeight: "72px",
            fontSize: "16px",
            fontWeight: 700,
          }}
          onClick={onOpenRecipeList}
        >
          Ver receitas
        </button>
      </div>
    </section>
  );
}