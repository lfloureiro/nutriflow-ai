import { useEffect, useMemo, useRef, useState } from "react";
import { API_BASE_URL } from "./config";
import { styles } from "./components/styles";
import type {
  Household,
  Ingredient,
  MealPlanItem,
  Recipe,
  ShoppingListItem,
} from "./components/types";

import { RecipeForm } from "./components/forms/RecipeForm";
import { IngredientForm } from "./components/forms/IngredientForm";
import { RecipeIngredientForm } from "./components/forms/RecipeIngredientForm";
import { MealPlanForm } from "./components/forms/MealPlanForm";
import { BulkImportPanel } from "./components/forms/BulkImportPanel";
import { DataToolsMenu } from "./components/forms/DataToolsMenu";
import { SnapshotBackupPanel } from "./components/forms/SnapshotBackupPanel";
import { SnapshotRestorePanel } from "./components/forms/SnapshotRestorePanel";
import { RecipeToolsMenu } from "./components/forms/RecipeToolsMenu";
import { HouseholdContextSelector } from "./components/forms/HouseholdContextSelector";
import { FamilyWorkspaceMenu } from "./components/forms/FamilyWorkspaceMenu";
import { RecipeRatingsPanel } from "./components/forms/RecipeRatingsPanel";

import { RecipeList } from "./components/lists/RecipeList";
import { MealPlanList } from "./components/lists/MealPlanList";
import { ShoppingListView } from "./components/lists/ShoppingListView";
import { HouseholdView } from "./components/lists/HouseholdView";
import { HouseholdManageView } from "./components/lists/HouseholdManageView";
import { FamilyMemberManageView } from "./components/lists/FamilyMemberManageView";
import { HouseholdRecipeScoresView } from "./components/lists/HouseholdRecipeScoresView";

import { Modal } from "./components/Modal";

type ActiveModal =
  | null
  | "meal-plan"
  | "manage-recipes"
  | "recipe-create"
  | "ingredient-manage"
  | "recipe-ingredient-link"
  | "recipe-list"
  | "weekly-plan"
  | "shopping-list"
  | "family-feedback"
  | "family-households"
  | "family-household-manage"
  | "family-member-manage"
  | "family-ratings"
  | "family-scores"
  | "data-tools"
  | "data-backup"
  | "data-restore"
  | "data-import";

function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [mealPlan, setMealPlan] = useState<MealPlanItem[]>([]);
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [households, setHouseholds] = useState<Household[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formMessage, setFormMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const [activeModal, setActiveModal] = useState<ActiveModal>(null);
  const [selectedHouseholdId, setSelectedHouseholdId] = useState<string>("");

  const householdScopedRequestRef = useRef(0);

  const selectedHousehold = useMemo(
    () =>
      households.find((household) => String(household.id) === selectedHouseholdId) ??
      null,
    [households, selectedHouseholdId]
  );

  async function loadBaseData(): Promise<string> {
    const [recipesRes, ingredientsRes, householdsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/recipes/`),
      fetch(`${API_BASE_URL}/ingredients/`),
      fetch(`${API_BASE_URL}/households/`),
    ]);

    if (!recipesRes.ok || !ingredientsRes.ok || !householdsRes.ok) {
      throw new Error("Falha ao carregar dados base da API.");
    }

    const recipesData = await recipesRes.json();
    const ingredientsData = await ingredientsRes.json();
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

    const nextHouseholdId =
      selectedHouseholdId &&
      householdsDetailData.some(
        (item: { id: number }) => String(item.id) === selectedHouseholdId
      )
        ? selectedHouseholdId
        : householdsDetailData.length > 0
          ? String(householdsDetailData[0].id)
          : "";

    setRecipes(recipesData);
    setIngredients(ingredientsData);
    setHouseholds(householdsDetailData);
    setSelectedHouseholdId(nextHouseholdId);

    return nextHouseholdId;
  }

  async function loadHouseholdScopedData(householdId: string) {
    const requestId = ++householdScopedRequestRef.current;

    if (!householdId) {
      if (requestId === householdScopedRequestRef.current) {
        setMealPlan([]);
        setShoppingList([]);
      }
      return;
    }

    const [mealPlanRes, shoppingListRes] = await Promise.all([
      fetch(`${API_BASE_URL}/meal-plan/?household_id=${householdId}`),
      fetch(`${API_BASE_URL}/shopping-list/generate?household_id=${householdId}`),
    ]);

    if (!mealPlanRes.ok || !shoppingListRes.ok) {
      throw new Error("Falha ao carregar dados do agregado ativo.");
    }

    const mealPlanData = await mealPlanRes.json();
    const shoppingListData = await shoppingListRes.json();

    if (requestId !== householdScopedRequestRef.current) {
      return;
    }

    setMealPlan(mealPlanData);
    setShoppingList(shoppingListData);
  }

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const householdId = await loadBaseData();
      await loadHouseholdScopedData(householdId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  async function handleChangeHousehold(value: string) {
    try {
      setLoading(true);
      setError(null);
      setFormMessage(null);
      setFormError(null);

      setSelectedHouseholdId(value);
      setMealPlan([]);
      setShoppingList([]);

      await loadHouseholdScopedData(value);
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
            <button
              type="button"
              onClick={() => openModal("manage-recipes")}
              style={{
                ...styles.statCard,
                cursor: "pointer",
                textAlign: "center",
              }}
              aria-label="Abrir gestão de receitas"
              title="Abrir gestão de receitas"
            >
              <div style={styles.statValue}>{recipes.length}</div>
              <div style={styles.statLabel}>Receitas</div>
            </button>

            <button
              type="button"
              onClick={() => openModal("weekly-plan")}
              style={{
                ...styles.statCard,
                cursor: "pointer",
                textAlign: "center",
              }}
              aria-label="Abrir plano semanal"
              title="Abrir plano semanal"
            >
              <div style={styles.statValue}>{mealPlan.length}</div>
              <div style={styles.statLabel}>Refeições planeadas</div>
            </button>

            <button
              type="button"
              onClick={() => openModal("shopping-list")}
              style={{
                ...styles.statCard,
                cursor: "pointer",
                textAlign: "center",
              }}
              aria-label="Abrir lista de compras"
              title="Abrir lista de compras"
            >
              <div style={styles.statValue}>{shoppingList.length}</div>
              <div style={styles.statLabel}>Itens na lista de compras</div>
            </button>
          </div>

          <div style={{ height: "16px" }} />

          <HouseholdContextSelector
            households={households}
            selectedHouseholdId={selectedHouseholdId}
            onChange={handleChangeHousehold}
          />

          <div style={{ height: "16px" }} />

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
                Consultar as refeições já planeadas para o agregado ativo.
              </div>
            </div>

            <div
              style={styles.actionCard}
              onClick={() => openModal("shopping-list")}
            >
              <div style={styles.actionTitle}>Ver lista de compras</div>
              <div style={styles.actionText}>
                Consultar a lista agregada do agregado ativo.
              </div>
            </div>

            <div
              style={styles.actionCard}
              onClick={() => openModal("family-feedback")}
            >
              <div style={styles.actionTitle}>Família e preferências</div>
              <div style={styles.actionText}>
                Gerir agregados, avaliar receitas de 0 a 5 e consultar scores por agregado.
              </div>
            </div>

            <div
              style={styles.actionCard}
              onClick={() => openModal("data-tools")}
            >
              <div style={styles.actionTitle}>Dados e importação</div>
              <div style={styles.actionText}>
                Gerir snapshots de dados e executar importações bulk por JSON.
              </div>
            </div>
          </div>
        </>
      )}

      {activeModal === "meal-plan" && (
        <Modal title="Planear próxima refeição" onClose={closeModal}>
          <MealPlanForm
            householdId={selectedHouseholdId}
            householdName={selectedHousehold?.name ?? null}
            recipes={recipes}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "manage-recipes" && (
        <Modal title="Gerir receitas e ingredientes" onClose={closeModal}>
          <RecipeToolsMenu
            onOpenCreateRecipe={() => openModal("recipe-create")}
            onOpenManageIngredients={() => openModal("ingredient-manage")}
            onOpenLinkIngredient={() => openModal("recipe-ingredient-link")}
            onOpenRecipeList={() => openModal("recipe-list")}
          />
        </Modal>
      )}

      {activeModal === "recipe-create" && (
        <Modal title="Nova receita" onClose={closeModal}>
          <RecipeForm
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "ingredient-manage" && (
        <Modal title="Gerir ingredientes" onClose={closeModal}>
          <IngredientForm
            ingredients={ingredients}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "recipe-ingredient-link" && (
        <Modal title="Associar ingrediente a receita" onClose={closeModal}>
          <RecipeIngredientForm
            recipes={recipes}
            ingredients={ingredients}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "recipe-list" && (
        <Modal title="Receitas" onClose={closeModal}>
          <RecipeList
            recipes={recipes}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "weekly-plan" && (
        <Modal title="Plano semanal" onClose={closeModal}>
          <MealPlanList
            mealPlan={mealPlan}
            recipes={recipes}
            onSuccess={loadData}
          />
        </Modal>
      )}

      {activeModal === "shopping-list" && (
        <Modal title="Lista de compras" onClose={closeModal}>
          <ShoppingListView shoppingList={shoppingList} />
        </Modal>
      )}

      {activeModal === "family-feedback" && (
        <Modal title="Família e preferências" onClose={closeModal}>
          <FamilyWorkspaceMenu
            household={selectedHousehold}
            onOpenHouseholds={() => openModal("family-households")}
            onOpenRatings={() => openModal("family-ratings")}
            onOpenScores={() => openModal("family-scores")}
          />
        </Modal>
      )}

      {activeModal === "family-households" && (
        <Modal title="Agregados e membros" onClose={closeModal}>
          <HouseholdView
            onOpenHouseholds={() => openModal("family-household-manage")}
            onOpenMembers={() => openModal("family-member-manage")}
          />
        </Modal>
      )}

      {activeModal === "family-household-manage" && (
        <Modal title="Gerir agregados" onClose={closeModal}>
          <HouseholdManageView
            households={households}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "family-member-manage" && (
        <Modal title="Gerir membros" onClose={closeModal}>
          <FamilyMemberManageView
            households={households}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "family-ratings" && (
        <Modal title="Avaliar receitas" onClose={closeModal}>
          <RecipeRatingsPanel
            household={selectedHousehold}
            recipes={recipes}
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "family-scores" && (
        <Modal title="Scores da família" onClose={closeModal}>
          <HouseholdRecipeScoresView household={selectedHousehold} />
        </Modal>
      )}

      {activeModal === "data-tools" && (
        <Modal title="Dados e importação" onClose={closeModal}>
          <DataToolsMenu
            onOpenBackup={() => openModal("data-backup")}
            onOpenRestore={() => openModal("data-restore")}
            onOpenImport={() => openModal("data-import")}
          />
        </Modal>
      )}

      {activeModal === "data-backup" && (
        <Modal title="Guardar snapshot" onClose={closeModal}>
          <SnapshotBackupPanel
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "data-restore" && (
        <Modal title="Repor snapshot" onClose={closeModal}>
          <SnapshotRestorePanel
            onSuccess={loadData}
            setFormMessage={setFormMessage}
            setFormError={setFormError}
          />
        </Modal>
      )}

      {activeModal === "data-import" && (
        <Modal title="Importação bulk JSON" onClose={closeModal}>
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