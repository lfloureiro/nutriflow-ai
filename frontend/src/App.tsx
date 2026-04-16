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
import { Modal } from "./components/Modal";

type ActiveModal =
  | null
  | "meal-plan"
  | "manage-recipes"
  | "weekly-plan"
  | "shopping-list";

function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [mealPlan, setMealPlan] = useState<MealPlanItem[]>([]);
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formMessage, setFormMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [activeModal, setActiveModal] = useState<ActiveModal>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const [recipesRes, ingredientsRes, mealPlanRes, shoppingListRes] =
        await Promise.all([
          fetch(`${API_BASE_URL}/recipes/`),
          fetch(`${API_BASE_URL}/ingredients/`),
          fetch(`${API_BASE_URL}/meal-plan/`),
          fetch(`${API_BASE_URL}/shopping-list/generate`),
        ]);

      if (
        !recipesRes.ok ||
        !ingredientsRes.ok ||
        !mealPlanRes.ok ||
        !shoppingListRes.ok
      ) {
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

  function openModal(modal: ActiveModal) {
    setFormMessage(null);
    setFormError(null);
    setActiveModal(modal);
  }

  function closeModal() {
    setActiveModal(null);
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.title}>NutriFlow AI</div>
        <div style={styles.subtitle}>
          Protótipo inicial do planeamento alimentar.
        </div>

        {loading && <p>A carregar dados...</p>}
        {error && <p style={styles.error}>Erro: {error}</p>}
        {formMessage && <p style={styles.success}>{formMessage}</p>}
        {formError && <p style={styles.error}>Erro: {formError}</p>}
      </header>

      {!loading && !error && (
        <>
          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <div style={styles.statValue}>{recipes.length}</div>
              <div style={styles.statLabel}>Receitas</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statValue}>{mealPlan.length}</div>
              <div style={styles.statLabel}>Refeições planeadas</div>
            </div>

            <div style={styles.statCard}>
              <div style={styles.statValue}>{shoppingList.length}</div>
              <div style={styles.statLabel}>Itens na lista de compras</div>
            </div>
          </div>

          <div style={styles.actionGrid}>
            <div style={styles.actionCard} onClick={() => openModal("meal-plan")}>
              <div style={styles.actionTitle}>Planear próxima refeição</div>
              <div style={styles.actionText}>
                Sugere automaticamente a próxima data e tipo de refeição livres,
                permitindo ajuste antes de guardar.
              </div>
            </div>

            <div
              style={styles.actionCard}
              onClick={() => openModal("manage-recipes")}
            >
              <div style={styles.actionTitle}>Gerir receitas</div>
              <div style={styles.actionText}>
                Criar receitas, ingredientes e associar ingredientes às receitas.
              </div>
            </div>

            <div
              style={styles.actionCard}
              onClick={() => openModal("weekly-plan")}
            >
              <div style={styles.actionTitle}>Ver plano semanal</div>
              <div style={styles.actionText}>
                Consultar as refeições já planeadas para os próximos dias.
              </div>
            </div>

            <div
              style={styles.actionCard}
              onClick={() => openModal("shopping-list")}
            >
              <div style={styles.actionTitle}>Ver lista de compras</div>
              <div style={styles.actionText}>
                Consultar a lista agregada com origem dos ingredientes.
              </div>
            </div>
          </div>
        </>
      )}

      {activeModal === "meal-plan" && (
        <Modal title="Planear próxima refeição" onClose={closeModal}>
          <MealPlanForm
            recipes={recipes}
            mealPlan={mealPlan}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "manage-recipes" && (
        <Modal title="Gerir receitas e ingredientes" onClose={closeModal}>
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

            <RecipeList recipes={recipes} />
          </div>
        </Modal>
      )}

      {activeModal === "weekly-plan" && (
        <Modal title="Plano semanal" onClose={closeModal}>
          <MealPlanList mealPlan={mealPlan} />
        </Modal>
      )}

      {activeModal === "shopping-list" && (
        <Modal title="Lista de compras" onClose={closeModal}>
          <ShoppingListView shoppingList={shoppingList} />
        </Modal>
      )}
    </div>
  );
}

export default App;