import { styles } from "../styles";
import type { Recipe } from "../types";

type Props = {
  recipes: Recipe[];
};

export function RecipeList({ recipes }: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Receitas</h2>
      {recipes.length === 0 ? (
        <p style={styles.empty}>Sem receitas.</p>
      ) : (
        <ul style={styles.list}>
          {recipes.map((recipe) => (
            <li key={recipe.id} style={styles.listItem}>
              <strong>{recipe.name}</strong>
              {recipe.description ? ` — ${recipe.description}` : ""}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}