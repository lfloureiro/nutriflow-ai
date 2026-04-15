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
    <div style={{ fontFamily: "Arial, sans-serif", padding: "24px", maxWidth: "1100px", margin: "0 auto" }}>
      <h1>NutriFlow AI</h1>
      <p>Protótipo inicial do planeamento alimentar.</p>

      {loading && <p>A carregar dados...</p>}
      {error && <p style={{ color: "crimson" }}>Erro: {error}</p>}

      {!loading && !error && (
        <>
          <section style={{ marginBottom: "32px" }}>
            <h2>Receitas</h2>
            {recipes.length === 0 ? (
              <p>Sem receitas.</p>
            ) : (
              <ul>
                {recipes.map((recipe) => (
                  <li key={recipe.id}>
                    <strong>{recipe.name}</strong>
                    {recipe.description ? ` — ${recipe.description}` : ""}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section style={{ marginBottom: "32px" }}>
            <h2>Plano semanal</h2>
            {mealPlan.length === 0 ? (
              <p>Sem itens no plano.</p>
            ) : (
              <ul>
                {mealPlan.map((item) => (
                  <li key={item.id}>
                    <strong>{item.plan_date}</strong> — {item.meal_type} — {item.recipe.name}
                    {item.notes ? ` (${item.notes})` : ""}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2>Lista de compras</h2>
            {shoppingList.length === 0 ? (
              <p>Sem itens na lista.</p>
            ) : (
              <ul>
                {shoppingList.map((item) => (
                  <li key={`${item.ingredient_id}-${item.unit ?? "sem-unidade"}`}>
                    <strong>{item.ingredient_name}</strong>
                    {item.quantity ? ` — ${item.quantity}` : ""}
                    {item.unit ? ` ${item.unit}` : ""}
                    <ul>
                      {item.sources.map((source, index) => (
                        <li key={`${source.recipe_id}-${index}`}>
                          {source.plan_date} — {source.meal_type} — {source.recipe_name}
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}

export default App;