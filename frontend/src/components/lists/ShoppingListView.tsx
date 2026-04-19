import { styles } from "../styles";
import type { ShoppingListItem } from "../types";

type Props = {
  shoppingList: ShoppingListItem[];
};

function formatMealType(mealType: string) {
  return mealType
    .replaceAll("-", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function ShoppingListView({ shoppingList }: Props) {
  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Compras</div>
        <h2 style={styles.sectionTitle}>Lista de compras</h2>
        <p className="nf-menu-panel-text">
          Vista mais limpa dos itens a comprar, com origem de cada ingrediente.
        </p>
      </div>

      <div className="nf-pill-row" style={{ marginTop: "12px" }}>
        <span className="nf-context-meta-chip">
          {shoppingList.length} item(ns) na lista
        </span>
      </div>

      {shoppingList.length === 0 ? (
        <p style={{ ...styles.empty, marginTop: "14px" }}>Sem itens na lista.</p>
      ) : (
        <div className="nf-shopping-grid" style={{ marginTop: "14px" }}>
          {shoppingList.map((item) => (
            <div
              key={`${item.ingredient_id}-${item.unit ?? "sem-unidade"}`}
              className="nf-shopping-card"
            >
              <div className="nf-shopping-card-head">
                <div className="nf-record-title">{item.ingredient_name}</div>
                <div className="nf-shopping-quantity">
                  {item.quantity ? item.quantity : "—"}
                  {item.unit ? ` ${item.unit}` : ""}
                </div>
              </div>

              <div className="nf-card-body">
                {item.sources.length} origem(ns) no plano
              </div>

              <div className="nf-pill-row" style={{ marginTop: "10px" }}>
                {item.sources.map((source, index) => (
                  <span
                    key={`${source.recipe_id}-${index}`}
                    className="nf-score-pill"
                    title={`${source.plan_date} · ${source.meal_type} · ${source.recipe_name}`}
                  >
                    {source.plan_date} · {formatMealType(source.meal_type)} ·{" "}
                    {source.recipe_name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}