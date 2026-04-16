import { styles } from "../styles";
import type { MealPlanItem } from "../types";

type Props = {
  mealPlan: MealPlanItem[];
};

export function MealPlanList({ mealPlan }: Props) {
  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Plano semanal</h2>
      {mealPlan.length === 0 ? (
        <p style={styles.empty}>Sem itens no plano.</p>
      ) : (
        <ul style={styles.list}>
          {mealPlan.map((item) => (
            <li key={item.id} style={styles.listItem}>
              <strong>{item.plan_date}</strong> — {item.meal_type} — {item.recipe.name}
              {item.notes ? ` (${item.notes})` : ""}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}