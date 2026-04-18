import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "./config";
import { styles } from "./components/styles";
import type {
  FamilyMember,
  Household,
  Ingredient,
  MealPlanItem,
  Recipe,
  RecipeFeedbackSummary,
  ShoppingListItem,
} from "./components/types";
import { RecipeForm } from "./components/forms/RecipeForm";
import { IngredientForm } from "./components/forms/IngredientForm";
import { RecipeIngredientForm } from "./components/forms/RecipeIngredientForm";
import { MealPlanForm } from "./components/forms/MealPlanForm";
import { RecipeList } from "./components/lists/RecipeList";
import { MealPlanList } from "./components/lists/MealPlanList";
import { ShoppingListView } from "./components/lists/ShoppingListView";
import { HouseholdView } from "./components/lists/HouseholdView";
import { MealFeedbackForm } from "./components/forms/MealFeedbackForm";
import { RecipeScoresView } from "./components/lists/RecipeScoresView";
import { BulkImportPanel } from "./components/forms/BulkImportPanel";
import { Modal } from "./components/Modal";

type ActiveModal =
  | null
  | "meal-plan"
  | "manage-recipes"
  | "weekly-plan"
  | "shopping-list"
  | "family-feedback"
  | "data-tools";

function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [mealPlan, setMealPlan] = useState<MealPlanItem[]>([]);
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [households, setHouseholds] = useState<Household[]>([]);
  const [recipeSummaries, setRecipeSummaries] = useState<RecipeFeedbackSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formMessage, setFormMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [activeModal, setActiveModal] = useState<ActiveModal>(null);

  const familyMembers: FamilyMember[] = useMemo(
    () => households.flatMap((household) => household.members),
    [households]
  );

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const [recipesRes, ingredientsRes, mealPlanRes, shoppingListRes, householdsRes] =
        await Promise.all([
          fetch(`${API_BASE_URL}/recipes/`),
          fetch(`${API_BASE_URL}/ingredients/`),
          fetch(`${API_BASE_URL}/meal-plan/`),
          fetch(`${API_BASE_URL}/shopping-list/generate`),
          fetch(`${API_BASE_URL}/households/`),
        ]);

      if (
        !recipesRes.ok ||
        !ingredientsRes.ok ||
        !mealPlanRes.ok ||
        !shoppingListRes.ok ||
        !householdsRes.ok
      ) {
        throw new Error("Falha ao carregar dados da API.");
      }

      const recipesData = await recipesRes.json();
      const ingredientsData = await ingredientsRes.json();
      const mealPlanData = await mealPlanRes.json();
      const shoppingListData = await shoppingListRes.json();
      const householdsData = await householdsRes.json();

      const householdsDetailData = await Promise.all(
        householdsData.map(async (household: { id: number }) => {
          const res = await fetch(`${API_BASE_URL}/households/${household.id}`);
          if (!res.ok) {
            throw new Error("Falha ao carregar detalhe do agregado.");
          }
          return res.json();
        })
      );

      const recipeSummaryData = await Promise.all(
        recipesData.map(async (recipe: { id: number }) => {
          const res = await fetch(`${API_BASE_URL}/feedback/recipes/${recipe.id}/summary`);
          if (!res.ok) {
            throw new Error("Falha ao carregar resumo de feedback.");
          }
          return res.json();
        })
      );

      setRecipes(recipesData);
      setIngredients(ingredientsData);
      setMealPlan(mealPlanData);
      setShoppingList(shoppingListData);
      setHouseholds(householdsDetailData);
      setRecipeSummaries(recipeSummaryData);
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

            <div style={styles.statCard}>
              <div style={styles.statValue}>{familyMembers.length}</div>
              <div style={styles.statLabel}>Membros da família</div>
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

            <div
              style={styles.actionCard}
              onClick={() => openModal("family-feedback")}
            >
              <div style={styles.actionTitle}>Família e feedback</div>
              <div style={styles.actionText}>
                Ver os membros da família, registar feedback por refeição e acompanhar
                os primeiros scores de aceitação.
              </div>
            </div>

            <div
              style={styles.actionCard}
              onClick={() => openModal("data-tools")}
            >
              <div style={styles.actionTitle}>Dados e importação</div>
              <div style={styles.actionText}>
                Carregar o dataset base e executar importações bulk por JSON.
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

      {activeModal === "family-feedback" && (
        <Modal title="Família e feedback" onClose={closeModal}>
          <div style={styles.grid}>
            <HouseholdView households={households} />

            <MealFeedbackForm
              mealPlan={mealPlan}
              members={familyMembers}
              onSuccess={loadData}
              setFormMessage={setFormMessage}
              setFormError={setFormError}
            />

            <RecipeScoresView summaries={recipeSummaries} />
          </div>
        </Modal>
      )}

      {activeModal === "data-tools" && (
        <Modal title="Dados e importação" onClose={closeModal}>
          <BulkImportPanel
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}
    </div>
  );
}

export default App;