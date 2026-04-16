import { styles } from "../styles";
import type { ShoppingListItem } from "../types";

type Props = {
  shoppingList: ShoppingListItem[];
};

export function ShoppingListView({ shoppingList }: Props) {
  return (
    <section style={{ ...styles.card, gridColumn: "1 / -1" }}>
      <h2 style={styles.sectionTitle}>Lista de compras</h2>
      {shoppingList.length === 0 ? (
        <p style={styles.empty}>Sem itens na lista.</p>
      ) : (
        <ul style={styles.list}>
          {shoppingList.map((item) => (
            <li key={`${item.ingredient_id}-${item.unit ?? "sem-unidade"}`} style={styles.listItem}>
              <strong>{item.ingredient_name}</strong>
              {item.quantity ? ` — ${item.quantity}` : ""}
              {item.unit ? ` ${item.unit}` : ""}

              <ul style={styles.sourceList}>
                {item.sources.map((source, index) => (
                  <li key={`${source.recipe_id}-${index}`} style={styles.sourceItem}>
                    {source.plan_date} — {source.meal_type} — {source.recipe_name}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}