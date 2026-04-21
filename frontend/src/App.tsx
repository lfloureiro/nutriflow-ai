import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
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
import { FamilyWorkspaceMenu } from "./components/forms/FamilyWorkspaceMenu";
import { RecipeRatingsPanel } from "./components/forms/RecipeRatingsPanel";

import { RecipeList } from "./components/lists/RecipeList";
import { MealPlanList } from "./components/lists/MealPlanList";
import { ShoppingListView } from "./components/lists/ShoppingListView";
import { HouseholdView } from "./components/lists/HouseholdView";
import { HouseholdManageView } from "./components/lists/HouseholdManageView";
import { FamilyMemberManageView } from "./components/lists/FamilyMemberManageView";
import { HouseholdRecipeScoresView } from "./components/lists/HouseholdRecipeScoresView";

import { AutoPlanPanel } from "./components/mealplan/AutoPlanPanel";
import { Modal } from "./components/Modal";

type ActiveModal =
  | null
  | "meal-plan"
  | "auto-plan"
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

type DashboardTile = {
  id: string;
  title: string;
  description: string;
  meta?: string;
  onOpen: () => void;
  disabled?: boolean;
};

function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [mealPlan, setMealPlan] = useState<MealPlanItem[]>([]);
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [households, setHouseholds] = useState<Household[]>([]);

  const [baseLoading, setBaseLoading] = useState(true);
  const [householdLoading, setHouseholdLoading] = useState(false);
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

  const hasActiveHousehold = Boolean(selectedHouseholdId && selectedHousehold);

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

  async function loadHouseholdScopedData(
    householdId: string,
    options?: { showLoading?: boolean }
  ) {
    const requestId = ++householdScopedRequestRef.current;
    const showLoading = options?.showLoading ?? false;

    if (showLoading) {
      setHouseholdLoading(true);
    }

    try {
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
    } finally {
      if (showLoading) {
        setHouseholdLoading(false);
      }
    }
  }

  async function loadData() {
    try {
      setBaseLoading(true);
      setError(null);

      const householdId = await loadBaseData();
      await loadHouseholdScopedData(householdId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setBaseLoading(false);
      setHouseholdLoading(false);
    }
  }

  async function handleChangeHousehold(value: string) {
    try {
      setError(null);
      setFormMessage(null);
      setFormError(null);

      setSelectedHouseholdId(value);
      await loadHouseholdScopedData(value, { showLoading: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
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

  function activateTile(onOpen: () => void, disabled?: boolean) {
    if (disabled) {
      return;
    }
    onOpen();
  }

  function handleTileKeyDown(
    event: React.KeyboardEvent<HTMLDivElement>,
    onOpen: () => void,
    disabled?: boolean
  ) {
    if (disabled) {
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onOpen();
    }
  }

  const dashboardTiles: DashboardTile[] = [
    {
      id: "next-meal-manual",
      title: "Planear refeição manualmente",
      description:
        "Escolhe data, tipo de refeição e receita para adicionar manualmente ao plano.",
      meta: "Plano manual",
      onOpen: () => openModal("meal-plan"),
      disabled: !hasActiveHousehold,
    },
    {
      id: "next-meal-auto",
      title: "Gerar plano automático",
      description:
        "Cria sugestões automáticas para vários dias com base em preferências, rotação e histórico recente.",
      meta: "Plano automático",
      onOpen: () => openModal("auto-plan"),
      disabled: !hasActiveHousehold,
    },
    {
      id: "recipes",
      title: "Gerir receitas",
      description: `${recipes.length} receitas disponíveis para criar, editar e ligar a ingredientes.`,
      meta: "Receitas",
      onOpen: () => openModal("manage-recipes"),
    },
    {
      id: "family",
      title: "Família e preferências",
      description:
        "Gerir agregados, membros, avaliações e scores da família.",
      meta: "Família",
      onOpen: () => openModal("family-feedback"),
    },
  ];

  return (
    <div style={styles.page}>
      <div className="nf-shell">
        <header className="nf-header">
          <div className="nf-title-block">
            <div className="nf-kicker">NutriFlow AI</div>
            <h1 style={styles.title}>Planeamento alimentar familiar</h1>
            <p style={styles.subtitle}>
              Base estável do protótipo, centrada em agregado, plano semanal e
              preferências por receita.
            </p>
          </div>

          <div className="nf-header-right">
            <div className="nf-header-badge">
              <span className="nf-header-badge-label">Estado</span>
              <strong>
                {baseLoading
                  ? "A carregar"
                  : householdLoading
                    ? "A atualizar agregado"
                    : "Pronto"}
              </strong>
            </div>

            <div
              className="nf-utility-action"
              role="button"
              tabIndex={0}
              aria-label="Abrir administração de dados"
              title="Dados e importação"
              onClick={() => openModal("data-tools")}
              onKeyDown={(event) =>
                handleTileKeyDown(event, () => openModal("data-tools"))
              }
            >
              <span className="nf-utility-action-icon">⚙</span>
              <span className="nf-utility-action-text">Administração</span>
            </div>
          </div>
        </header>

        {(error || formMessage || formError || householdLoading) && (
          <div className="nf-status-stack">
            {householdLoading && (
              <div className="nf-status-banner nf-status-banner--info">
                A atualizar o plano e a lista de compras do agregado ativo…
              </div>
            )}

            {error && (
              <div className="nf-status-banner nf-status-banner--error">
                {error}
              </div>
            )}

            {formMessage && (
              <div className="nf-status-banner nf-status-banner--success">
                {formMessage}
              </div>
            )}

            {formError && (
              <div className="nf-status-banner nf-status-banner--error">
                {formError}
              </div>
            )}
          </div>
        )}

        {baseLoading ? (
          <section style={styles.card}>
            <div className="nf-loading-state">
              <div className="nf-kicker">Inicialização</div>
              <div className="nf-card-title">A carregar dados base</div>
              <div className="nf-card-body">
                A aplicação está a sincronizar receitas, ingredientes, agregados
                e dados do agregado ativo.
              </div>
            </div>
          </section>
        ) : !error ? (
          <>
            <section style={styles.card} className="nf-context-panel">
              <div className="nf-context-panel-head">
                <div>
                  <div className="nf-kicker">Agregado ativo</div>
                  <h2 style={styles.sectionTitle}>Contexto de trabalho</h2>
                </div>
              </div>

              {households.length === 0 ? (
                <p style={{ ...styles.empty, marginTop: "6px" }}>
                  Ainda não existem agregados. Cria um agregado em “Família e
                  preferências”.
                </p>
              ) : (
                <div className="nf-context-grid">
                  <div className="nf-context-selector-block">
                    <label htmlFor="household-selector" className="nf-field-label">
                      Agregado selecionado
                    </label>

                    <select
                      id="household-selector"
                      style={styles.select}
                      value={selectedHouseholdId}
                      onChange={(e) => handleChangeHousehold(e.target.value)}
                    >
                      <option value="">Seleciona um agregado</option>
                      {households.map((household) => (
                        <option key={household.id} value={household.id}>
                          {household.name}
                        </option>
                      ))}
                    </select>

                    {householdLoading && (
                      <p className="nf-inline-note">A atualizar plano e compras…</p>
                    )}
                  </div>

                  <div className="nf-context-summary">
                    <div className="nf-context-summary-main">
                      <div className="nf-card-title">
                        {selectedHousehold?.name ?? "Sem agregado ativo"}
                      </div>
                      <div className="nf-card-body">
                        {selectedHousehold
                          ? "O plano semanal, a lista de compras e as avaliações trabalham sobre este agregado."
                          : "Seleciona um agregado para ativar o plano semanal e a lista de compras."}
                      </div>
                    </div>

                    <div className="nf-context-meta">
                      <span className="nf-context-meta-chip">
                        {selectedHousehold?.members.length ?? 0} membros
                      </span>
                    </div>

                    <div className="nf-context-stats">
                      <div
                        className={`nf-context-stat${!hasActiveHousehold ? " nf-context-stat--disabled" : ""}`}
                        role="button"
                        tabIndex={hasActiveHousehold ? 0 : -1}
                        aria-disabled={hasActiveHousehold ? "false" : "true"}
                        title={
                          hasActiveHousehold
                            ? "Abrir plano semanal"
                            : "Seleciona primeiro um agregado"
                        }
                        onClick={() =>
                          activateTile(() => openModal("weekly-plan"), !hasActiveHousehold)
                        }
                        onKeyDown={(event) =>
                          handleTileKeyDown(
                            event,
                            () => openModal("weekly-plan"),
                            !hasActiveHousehold
                          )
                        }
                      >
                        <span className="nf-context-stat-label">Plano</span>
                        <strong className="nf-context-stat-value">{mealPlan.length}</strong>
                      </div>

                      <div
                        className={`nf-context-stat${!hasActiveHousehold ? " nf-context-stat--disabled" : ""}`}
                        role="button"
                        tabIndex={hasActiveHousehold ? 0 : -1}
                        aria-disabled={hasActiveHousehold ? "false" : "true"}
                        title={
                          hasActiveHousehold
                            ? "Abrir lista de compras"
                            : "Seleciona primeiro um agregado"
                        }
                        onClick={() =>
                          activateTile(
                            () => openModal("shopping-list"),
                            !hasActiveHousehold
                          )
                        }
                        onKeyDown={(event) =>
                          handleTileKeyDown(
                            event,
                            () => openModal("shopping-list"),
                            !hasActiveHousehold
                          )
                        }
                      >
                        <span className="nf-context-stat-label">Compras</span>
                        <strong className="nf-context-stat-value">
                          {shoppingList.length}
                        </strong>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </section>

            <section className="nf-section-block">
              <div className="nf-section-header">
                <div>
                  <div className="nf-kicker">Ações rápidas</div>
                  <h2 style={styles.sectionTitle}>O que queres fazer agora?</h2>
                </div>
              </div>

              <div className="nf-card-grid nf-card-grid--compact">
                {dashboardTiles.map((tile) => (
                  <div
                    key={tile.id}
                    className={`nf-clickable-card${tile.disabled ? " nf-clickable-card--disabled" : ""}`}
                    role="button"
                    tabIndex={tile.disabled ? -1 : 0}
                    aria-disabled={tile.disabled ? "true" : "false"}
                    onClick={() => activateTile(tile.onOpen, tile.disabled)}
                    onKeyDown={(event) =>
                      handleTileKeyDown(event, tile.onOpen, tile.disabled)
                    }
                    title={
                      tile.disabled
                        ? "Seleciona primeiro um agregado"
                        : tile.title
                    }
                  >
                    {tile.meta && <div className="nf-card-kicker">{tile.meta}</div>}
                    <div className="nf-card-title">{tile.title}</div>
                    <div className="nf-card-body">{tile.description}</div>
                  </div>
                ))}
              </div>
            </section>
          </>
        ) : null}

        {activeModal === "meal-plan" && (
          <Modal title="Planear refeição manualmente" onClose={closeModal}>
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

        {activeModal === "auto-plan" && (
          <Modal title="Gerar plano automático" onClose={closeModal}>
            <AutoPlanPanel
              householdId={selectedHouseholdId}
              onApplied={loadData}
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
            <ShoppingListView
              householdId={selectedHouseholdId}
              shoppingList={shoppingList}
              onRefresh={() => loadHouseholdScopedData(selectedHouseholdId)}
            />
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
    </div>
  );
}

export default App;