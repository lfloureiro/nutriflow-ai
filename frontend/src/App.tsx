import { useEffect, useState } from "react";
import { API_BASE_URL } from "./config";

type Recipe = {
  id: number;
  name: string;
  description: string | null;
};

type MealPlanItem = {
  id: number;
  plan_date: string;
  meal_type: string;
  notes: string | null;
  recipe: Recipe;
};

type ShoppingListSource = {
  recipe_id: number;
  recipe_name: string;
  plan_date: string;
  meal_type: string;
};

type ShoppingListItem = {
  ingredient_id: number;
  ingredient_name: string;
  quantity: string | null;
  unit: string | null;
  sources: ShoppingListSource[];
};

const styles = {
  page: {
    fontFamily: "Arial, sans-serif",
    padding: "24px",
    maxWidth: "1100px",
    margin: "0 auto",
    color: "#e5e7eb",
  } as const,
  header: {
    marginBottom: "24px",
  } as const,
  title: {
    fontSize: "56px",
    fontWeight: 700,
    marginBottom: "8px",
  } as const,
  subtitle: {
    fontSize: "18px",
    color: "#b8c1cc",
    marginBottom: "16px",
  } as const,
  button: {
    padding: "10px 16px",
    borderRadius: "8px",
    border: "1px solid #374151",
    background: "#111827",
    color: "#f9fafb",
    cursor: "pointer",
  } as const,
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "20px",
  } as const,
  card: {
    background: "#111827",
    border: "1px solid #374151",
    borderRadius: "12px",
    padding: "20px",
  } as const,
  sectionTitle: {
    fontSize: "28px",
    fontWeight: 700,
    marginBottom: "16px",
  } as const,
  list: {
    listStyle: "none",
    padding: 0,
    margin: 0,
  } as const,
  listItem: {
    padding: "10px 0",
    borderBottom: "1px solid #1f2937",
  } as const,
  sourceList: {
    listStyle: "none",
    paddingLeft: "12px",
    marginTop: "8px",
    marginBottom: 0,
  } as const,
  sourceItem: {
    fontSize: "14px",
    color: "#cbd5e1",
    padding: "2px 0",
  } as const,
  error: {
    color: "#f43f5e",
    marginTop: "12px",
  } as const,
  empty: {
    color: "#9ca3af",
  } as const,
};

function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [mealPlan, setMealPlan] = useState<MealPlanItem[]>([]);
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const [recipesRes, mealPlanRes, shoppingListRes] = await Promise.all([
        fetch(`${API_BASE_URL}/recipes/`),
        fetch(`${API_BASE_URL}/meal-plan/`),
        fetch(`${API_BASE_URL}/shopping-list/generate`),
      ]);

      if (!recipesRes.ok || !mealPlanRes.ok || !shoppingListRes.ok) {
        throw new Error("Falha ao carregar dados da API.");
      }

      const recipesData = await recipesRes.json();
      const mealPlanData = await mealPlanRes.json();
      const shoppingListData = await shoppingListRes.json();

      setRecipes(recipesData);
      setMealPlan(mealPlanData);
      setShoppingList(shoppingListData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.title}>NutriFlow AI</div>
        <div style={styles.subtitle}>Protótipo inicial do planeamento alimentar.</div>
        <button style={styles.button} onClick={loadData}>
          Atualizar
        </button>
        {loading && <p>A carregar dados...</p>}
        {error && <p style={styles.error}>Erro: {error}</p>}
      </header>

      {!loading && !error && (
        <div style={styles.grid}>
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
        </div>
      )}
    </div>
  );
}

export default App;