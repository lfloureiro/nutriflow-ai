import { useEffect, useState } from "react";
import { API_BASE_URL } from "./config";
import { styles } from "./components/styles";
import type {
  Ingredient,
  MealPlanItem,
  Recipe,
  ShoppingListItem,
} from "./components/types";
import { RecipeForm } from "./components/forms/RecipeForm";
import { IngredientForm } from "./components/forms/IngredientForm";
import { RecipeIngredientForm } from "./components/forms/RecipeIngredientForm";
import { MealPlanForm } from "./components/forms/MealPlanForm";
import { RecipeList } from "./components/lists/RecipeList";
import { MealPlanList } from "./components/lists/MealPlanList";
import { ShoppingListView } from "./components/lists/ShoppingListView";

function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [mealPlan, setMealPlan] = useState<MealPlanItem[]>([]);
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formMessage, setFormMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const [recipesRes, ingredientsRes, mealPlanRes, shoppingListRes] = await Promise.all([
        fetch(`${API_BASE_URL}/recipes/`),
        fetch(`${API_BASE_URL}/ingredients/`),
        fetch(`${API_BASE_URL}/meal-plan/`),
        fetch(`${API_BASE_URL}/shopping-list/generate`),
      ]);

      if (!recipesRes.ok || !ingredientsRes.ok || !mealPlanRes.ok || !shoppingListRes.ok) {
        throw new Error("Falha ao carregar dados da API.");
      }

      const recipesData = await recipesRes.json();
      const ingredientsData = await ingredientsRes.json();
      const mealPlanData = await mealPlanRes.json();
      const shoppingListData = await shoppingListRes.json();

      setRecipes(recipesData);
      setIngredients(ingredientsData);
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
        {formMessage && <p style={styles.success}>{formMessage}</p>}
        {formError && <p style={styles.error}>Erro: {formError}</p>}
      </header>

      {!loading && !error && (
        <>
          <div style={styles.grid}>
            <RecipeForm
              onSuccess={loadData}
              setFormMessage={setFormMessage}
              setFormError={setFormError}
            />

            <IngredientForm
              onSuccess={loadData}
              setFormMessage={setFormMessage}
              setFormError={setFormError}
            />

            <RecipeIngredientForm
              recipes={recipes}
              ingredients={ingredients}
              onSuccess={loadData}
              setFormMessage={setFormMessage}
              setFormError={setFormError}
            />

            <MealPlanForm
              recipes={recipes}
              onSuccess={loadData}
              setFormMessage={setFormMessage}
              setFormError={setFormError}
            />
          </div>

          <div style={{ height: "24px" }} />

          <div style={styles.grid}>
            <RecipeList recipes={recipes} />
            <MealPlanList mealPlan={mealPlan} />
            <ShoppingListView shoppingList={shoppingList} />
          </div>
        </>
      )}
    </div>
  );
}

export default App;