import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { Modal } from "../Modal";
import { styles } from "../styles";
import type { Recipe } from "../types";

type Suggestion = {
  plan_date: string;
  meal_type: string;
  action: string;
  recipe_id: number | null;
  recipe_name: string | null;
  categoria_alimentar: string | null;
  proteina_principal: string | null;
  score: number | null;
  heuristic_score: number | null;
  ml_score: number | null;
  final_score: number | null;
  average_rating: number | null;
  ratings_count: number;
  reasons: string[];
  engine_version: string | null;
};

type PreviewResponse = {
  household_id: number;
  start_date: string;
  end_date: string;
  meal_types: string[];
  skip_existing: boolean;
  suggestions: Suggestion[];
};

type ApplyAdjustedResponse = {
  household_id: number;
  start_date: string;
  end_date: string;
  meal_types: string[];
  skip_existing: boolean;
  created_count: number;
  skipped_count: number;
  ignored_count: number;
  replaced_count: number;
  suggestions: Suggestion[];
};

type Props = {
  householdId: string;
  onApplied: () => Promise<void>;
};

type MealTypeOption = "almoco" | "jantar";
type ApplyDecision = "keep" | "replace" | "ignore" | "skip_existing";
type ProteinBalanceMode = "free" | "ratio_1_1" | "ratio_2_1" | "ratio_3_1";

type EditableSuggestion = Suggestion & {
  apply_decision: ApplyDecision;
  adjusted_recipe_id: number | null;
};

const mealTypeLabels: Record<MealTypeOption, string> = {
  almoco: "Almoço",
  jantar: "Jantar",
};

const proteinBalanceModeLabels: Record<ProteinBalanceMode, string> = {
  free: "Livre",
  ratio_1_1: "1 carne : 1 peixe",
  ratio_2_1: "2 carnes : 1 peixe",
  ratio_3_1: "3 carnes : 1 peixe",
};

function getTodayIsoDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = `${now.getMonth() + 1}`.padStart(2, "0");
  const day = `${now.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDaysIsoDate(startIso: string, days: number) {
  const start = new Date(`${startIso}T00:00:00`);
  start.setDate(start.getDate() + days);

  const year = start.getFullYear();
  const month = `${start.getMonth() + 1}`.padStart(2, "0");
  const day = `${start.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatMealType(value: string) {
  return mealTypeLabels[value as MealTypeOption] ?? value;
}

function formatPlanDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("pt-PT", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
  });
}

function formatScore(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(2);
}

function formatSignedScore(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}`;
}

function formatMlScore(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "—";
  }

  return `${Math.round(value * 100)}%`;
}

function getMlInsight(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "Sem score ML";
  }

  if (value >= 0.7) {
    return "ML: aceitação alta";
  }

  if (value <= 0.35) {
    return "ML: risco de troca";
  }

  return "ML: aceitação intermédia";
}

function formatEngineVersion(value: string | null | undefined) {
  if (!value) {
    return "Motor desconhecido";
  }

  if (value === "hybrid_ml_v1") {
    return "Heurística + ML";
  }

  if (value === "heuristic_v1") {
    return "Heurística";
  }

  return value;
}

function getEffectiveFinalScore(item: Suggestion | EditableSuggestion) {
  return item.final_score ?? item.score;
}

function getMlImpactValue(item: Suggestion | EditableSuggestion) {
  const finalScore = getEffectiveFinalScore(item);
  const heuristicScore = item.heuristic_score;

  if (
    finalScore == null ||
    heuristicScore == null ||
    Number.isNaN(finalScore) ||
    Number.isNaN(heuristicScore)
  ) {
    return null;
  }

  return finalScore - heuristicScore;
}

function getMlImpactLabel(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return "Impacto ML indisponível";
  }

  if (value >= 2) {
    return "ML reforçou";
  }

  if (value <= -2) {
    return "ML penalizou";
  }

  return "ML quase neutro";
}

function getErrorMessage(data: unknown, fallback: string) {
  if (
    data &&
    typeof data === "object" &&
    "detail" in data &&
    typeof (data as { detail?: unknown }).detail === "string"
  ) {
    return (data as { detail: string }).detail;
  }

  return fallback;
}

function recipeFitsMealType(recipe: Recipe, mealType: string) {
  if (!recipe.adequado_refeicao || recipe.adequado_refeicao === "ambos") {
    return true;
  }

  return recipe.adequado_refeicao === mealType;
}

function sortRecipesByName(recipes: Recipe[]) {
  return [...recipes].sort((a, b) => a.name.localeCompare(b.name, "pt-PT"));
}

function getDecisionLabel(value: ApplyDecision) {
  switch (value) {
    case "keep":
      return "Manter";
    case "replace":
      return "Trocar";
    case "ignore":
      return "Ignorar";
    case "skip_existing":
      return "Já existe";
    default:
      return value;
  }
}

export function AutoPlanPanel({ householdId, onApplied }: Props) {
  const initialStartDate = useMemo(() => getTodayIsoDate(), []);
  const initialEndDate = useMemo(() => addDaysIsoDate(initialStartDate, 6), [initialStartDate]);

  const [startDate, setStartDate] = useState(initialStartDate);
  const [endDate, setEndDate] = useState(initialEndDate);
  const [selectedMealTypes, setSelectedMealTypes] = useState<MealTypeOption[]>([
    "almoco",
    "jantar",
  ]);
  const [proteinBalanceMode, setProteinBalanceMode] =
    useState<ProteinBalanceMode>("free");
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loadingRecipes, setLoadingRecipes] = useState(false);

  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [editableSuggestions, setEditableSuggestions] = useState<EditableSuggestion[]>([]);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [applyingPlan, setApplyingPlan] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadRecipes() {
      try {
        setLoadingRecipes(true);

        const res = await fetch(`${API_BASE_URL}/recipes/`);
        const data = await res.json();

        if (!res.ok) {
          throw new Error(getErrorMessage(data, "Não foi possível carregar as receitas."));
        }

        if (isMounted) {
          setRecipes(sortRecipesByName(data));
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Erro inesperado.");
        }
      } finally {
        if (isMounted) {
          setLoadingRecipes(false);
        }
      }
    }

    loadRecipes();

    return () => {
      isMounted = false;
    };
  }, []);

  function toggleMealType(mealType: MealTypeOption) {
    setSelectedMealTypes((current) => {
      if (current.includes(mealType)) {
        return current.filter((item) => item !== mealType);
      }

      return [...current, mealType];
    });
  }

  function suggestionToEditable(item: Suggestion): EditableSuggestion {
    return {
      ...item,
      apply_decision: item.action === "suggest" ? "keep" : "skip_existing",
      adjusted_recipe_id: item.recipe_id,
    };
  }

  function compatibleRecipesForMealType(mealType: string) {
    return recipes.filter((recipe) => recipeFitsMealType(recipe, mealType));
  }

  function getSelectedRecipe(item: EditableSuggestion) {
    if (item.apply_decision === "ignore") {
      return null;
    }

    const recipeId = item.adjusted_recipe_id ?? item.recipe_id;
    if (recipeId == null) {
      return null;
    }

    return recipes.find((recipe) => recipe.id === recipeId) ?? null;
  }

  function updateSuggestion(
    index: number,
    updater: (current: EditableSuggestion) => EditableSuggestion,
  ) {
    setEditableSuggestions((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? updater(item) : item)),
    );
  }

  function setDecision(index: number, decision: ApplyDecision) {
    updateSuggestion(index, (current) => {
      if (current.action !== "suggest") {
        return current;
      }

      if (decision === "keep") {
        return {
          ...current,
          apply_decision: "keep",
          adjusted_recipe_id: current.recipe_id,
        };
      }

      if (decision === "ignore") {
        return {
          ...current,
          apply_decision: "ignore",
        };
      }

      const compatible = compatibleRecipesForMealType(current.meal_type);
      const fallbackRecipeId =
        current.adjusted_recipe_id ??
        current.recipe_id ??
        compatible[0]?.id ??
        null;

      return {
        ...current,
        apply_decision: "replace",
        adjusted_recipe_id: fallbackRecipeId,
      };
    });
  }

  function setAdjustedRecipe(index: number, recipeId: string) {
    const parsedRecipeId = recipeId ? Number(recipeId) : null;

    updateSuggestion(index, (current) => {
      const shouldKeep = parsedRecipeId !== null && parsedRecipeId === current.recipe_id;

      return {
        ...current,
        adjusted_recipe_id: parsedRecipeId,
        apply_decision: shouldKeep ? "keep" : "replace",
      };
    });
  }

  async function handlePreview() {
    setMessage(null);
    setError(null);
    setPreview(null);
    setEditableSuggestions([]);

    if (!householdId) {
      setError("Seleciona primeiro um agregado.");
      return;
    }

    if (!startDate || !endDate) {
      setError("Seleciona a data inicial e final.");
      return;
    }

    if (selectedMealTypes.length === 0) {
      setError("Seleciona pelo menos um tipo de refeição.");
      return;
    }

    try {
      setLoadingPreview(true);

      const res = await fetch(`${API_BASE_URL}/meal-plan/auto-plan/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          household_id: Number(householdId),
          start_date: startDate,
          end_date: endDate,
          meal_types: selectedMealTypes,
          skip_existing: true,
          protein_balance_mode: proteinBalanceMode,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível gerar o preview."));
      }

      setPreview(data);
      setEditableSuggestions(data.suggestions.map(suggestionToEditable));
      setMessage("Preview gerado com sucesso. Revê as sugestões antes de aplicar.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handleApplyAdjusted() {
    setMessage(null);
    setError(null);

    if (!householdId) {
      setError("Seleciona primeiro um agregado.");
      return;
    }

    if (!preview || editableSuggestions.length === 0) {
      setError("Gera primeiro um preview.");
      return;
    }

    try {
      setApplyingPlan(true);

      const res = await fetch(`${API_BASE_URL}/meal-plan/auto-plan/apply-adjusted`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          household_id: Number(householdId),
          start_date: preview.start_date,
          end_date: preview.end_date,
          meal_types: preview.meal_types,
          skip_existing: preview.skip_existing,
          suggestions: editableSuggestions.map((item) => ({
            plan_date: item.plan_date,
            meal_type: item.meal_type,
            original_action: item.action,
            original_recipe_id: item.recipe_id,
            adjusted_recipe_id: item.adjusted_recipe_id,
            apply_decision: item.apply_decision,
            score: item.score,
            heuristic_score: item.heuristic_score,
            ml_score: item.ml_score,
            final_score: item.final_score,
            average_rating: item.average_rating,
            ratings_count: item.ratings_count,
            reasons: item.reasons,
            engine_version: item.engine_version,
          })),
        }),
      });

      const data: ApplyAdjustedResponse = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível aplicar o plano ajustado."),
        );
      }

      setMessage(
        `Plano aplicado com sucesso. ${data.created_count} criada(s), ` +
          `${data.replaced_count} trocada(s) antes de aplicar, ` +
          `${data.ignored_count} ignorada(s) e ${data.skipped_count} não aplicada(s).`,
      );
      setPreview(null);
      setEditableSuggestions([]);
      await onApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setApplyingPlan(false);
    }
  }

  const previewStats = useMemo(() => {
    const stats = {
      keep: 0,
      replace: 0,
      ignore: 0,
      skip_existing: 0,
    };

    editableSuggestions.forEach((item) => {
      stats[item.apply_decision] += 1;
    });

    return stats;
  }, [editableSuggestions]);

  return (
    <>
      <section
      style={{
        ...styles.card,
        marginTop: "16px",
        background: "rgba(15, 23, 42, 0.55)",
      }}
    >
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Auto-planeamento</div>
        <h3 style={styles.sectionTitle}>Sugestão automática de refeições</h3>
        <p className="nf-menu-panel-text">
          Gera um preview, revê cada slot e só depois aplica o plano final ao agregado.
        </p>
      </div>

      <div className="nf-panel-stack" style={{ marginTop: "14px" }}>
        <div className="nf-actions-inline">
          <div style={{ flex: 1 }}>
            <label htmlFor="auto-plan-start-date" className="nf-field-label">
              Data inicial
            </label>
            <input
              id="auto-plan-start-date"
              type="date"
              style={styles.input}
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div style={{ flex: 1 }}>
            <label htmlFor="auto-plan-end-date" className="nf-field-label">
              Data final
            </label>
            <input
              id="auto-plan-end-date"
              type="date"
              style={styles.input}
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        <div>
          <div className="nf-field-label">Tipos de refeição</div>
          <div className="nf-filter-row">
            {(["almoco", "jantar"] as MealTypeOption[]).map((mealType) => {
              const active = selectedMealTypes.includes(mealType);

              return (
                <button
                  key={mealType}
                  type="button"
                  className={`nf-filter-chip${active ? " nf-filter-chip--active" : ""}`}
                  onClick={() => toggleMealType(mealType)}
                >
                  {mealTypeLabels[mealType]}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <div className="nf-field-label">Regras ativas</div>
          <div className="nf-pill-row" style={{ alignItems: "center" }}>
            <span className="nf-score-pill">
              Carne/peixe: {proteinBalanceModeLabels[proteinBalanceMode]}
            </span>
            <button
              type="button"
              className="nf-utility-action"
              onClick={() => setAdvancedOpen(true)}
            >
              <span className="nf-utility-action-icon">⚙</span>
              <span className="nf-utility-action-text">Regras avançadas</span>
            </button>
          </div>
        </div>

        <div className="nf-actions-inline">
          <button
            type="button"
            style={styles.button}
            onClick={handlePreview}
            disabled={loadingPreview || applyingPlan || !householdId}
          >
            {loadingPreview ? "A gerar preview..." : "Gerar preview"}
          </button>

          <button
            type="button"
            style={styles.button}
            onClick={handleApplyAdjusted}
            disabled={
              applyingPlan ||
              loadingPreview ||
              !householdId ||
              !preview ||
              editableSuggestions.length === 0
            }
          >
            {applyingPlan ? "A aplicar..." : "Aplicar plano ajustado"}
          </button>
        </div>

        {loadingRecipes && <p className="nf-inline-note">A carregar receitas…</p>}
        {message && <p style={styles.success}>{message}</p>}
        {error && <p style={styles.error}>Erro: {error}</p>}

        {preview && (
          <>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "8px",
                marginTop: "8px",
              }}
            >
              <span className="nf-score-pill">
                Regra carne/peixe: {proteinBalanceModeLabels[proteinBalanceMode]}
              </span>
              <span className="nf-score-pill">Manter: {previewStats.keep}</span>
              <span className="nf-score-pill">Trocar: {previewStats.replace}</span>
              <span className="nf-score-pill">Ignorar: {previewStats.ignore}</span>
              <span className="nf-score-pill">Já existe: {previewStats.skip_existing}</span>
            </div>

            <div className="nf-record-list">
              {editableSuggestions.map((item, index) => {
                const compatibleRecipes = compatibleRecipesForMealType(item.meal_type);
                const selectedRecipe = getSelectedRecipe(item);
                const effectiveFinalScore = getEffectiveFinalScore(item);
                const mlImpactValue = getMlImpactValue(item);

                return (
                  <div
                    key={`${item.plan_date}-${item.meal_type}-${index}`}
                    className="nf-record-card"
                  >
                    <div className="nf-record-card-head">
                      <div className="nf-record-card-main">
                        <div className="nf-pill-row">
                          <span className="nf-score-pill">{formatPlanDate(item.plan_date)}</span>
                          <span className="nf-score-pill">{formatMealType(item.meal_type)}</span>
                          <span className="nf-score-pill">
                            {getDecisionLabel(item.apply_decision)}
                          </span>
                          <span className="nf-score-pill">
                            {formatEngineVersion(item.engine_version)}
                          </span>
                          <span className="nf-score-pill">{getMlInsight(item.ml_score)}</span>
                        </div>

                        <div className="nf-record-title">
                          {selectedRecipe?.name ?? item.recipe_name ?? "Sem sugestão"}
                        </div>

                        <div className="nf-record-description">
                          {(selectedRecipe?.categoria_alimentar ??
                            item.categoria_alimentar ??
                            "Sem categoria")}{" "}
                          ·{" "}
                          {(selectedRecipe?.proteina_principal ??
                            item.proteina_principal ??
                            "Sem proteína")}
                        </div>

                        <div
                          className="nf-pill-row"
                          style={{ marginTop: "10px", marginBottom: "6px" }}
                        >
                          <span className="nf-score-pill">
                            Heurística: {formatScore(item.heuristic_score)}
                          </span>
                          <span className="nf-score-pill">
                            ML: {formatMlScore(item.ml_score)}
                          </span>
                          <span className="nf-score-pill">
                            Final: {formatScore(effectiveFinalScore)}
                          </span>
                          <span className="nf-score-pill">
                            Impacto ML: {formatSignedScore(mlImpactValue)}
                          </span>
                          <span className="nf-score-pill">{getMlImpactLabel(mlImpactValue)}</span>
                        </div>

                        {item.action === "suggest" ? (
                          <>
                            <div
                              className="nf-filter-row"
                              style={{ marginTop: "12px", marginBottom: "10px" }}
                            >
                              <button
                                type="button"
                                className={`nf-filter-chip${item.apply_decision === "keep" ? " nf-filter-chip--active" : ""}`}
                                onClick={() => setDecision(index, "keep")}
                              >
                                Manter
                              </button>

                              <button
                                type="button"
                                className={`nf-filter-chip${item.apply_decision === "replace" ? " nf-filter-chip--active" : ""}`}
                                onClick={() => setDecision(index, "replace")}
                              >
                                Trocar
                              </button>

                              <button
                                type="button"
                                className={`nf-filter-chip${item.apply_decision === "ignore" ? " nf-filter-chip--active" : ""}`}
                                onClick={() => setDecision(index, "ignore")}
                              >
                                Ignorar
                              </button>
                            </div>

                            {item.apply_decision === "replace" && (
                              <div style={{ marginTop: "10px" }}>
                                <label
                                  htmlFor={`replacement-${index}`}
                                  className="nf-field-label"
                                >
                                  Receita a aplicar
                                </label>
                                <select
                                  id={`replacement-${index}`}
                                  style={styles.select}
                                  value={item.adjusted_recipe_id ?? ""}
                                  onChange={(e) => setAdjustedRecipe(index, e.target.value)}
                                >
                                  {compatibleRecipes.map((recipe) => (
                                    <option key={recipe.id} value={recipe.id}>
                                      {recipe.name}
                                    </option>
                                  ))}
                                </select>

                                {item.recipe_name && item.recipe_id !== item.adjusted_recipe_id && (
                                  <p className="nf-inline-note" style={{ marginTop: "8px" }}>
                                    Sugestão original: {item.recipe_name}
                                  </p>
                                )}
                              </div>
                            )}
                          </>
                        ) : (
                          <p className="nf-inline-note" style={{ marginTop: "12px" }}>
                            Este slot já estava ocupado no plano e será apenas mantido como
                            referência.
                          </p>
                        )}

                        {item.reasons.length > 0 && (
                          <div className="nf-pill-row" style={{ marginTop: "10px" }}>
                            {item.reasons.map((reason, reasonIndex) => (
                              <span
                                key={`${item.plan_date}-${item.meal_type}-reason-${reasonIndex}`}
                                className="nf-score-pill"
                              >
                                {reason}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
      </section>

      {advancedOpen && (
        <Modal title="Regras avançadas de geração" onClose={() => setAdvancedOpen(false)}>
          <div className="nf-panel-stack">
            <div>
              <label htmlFor="protein-balance-mode" className="nf-field-label">
                Padrão carne / peixe
              </label>
              <select
                id="protein-balance-mode"
                style={styles.select}
                value={proteinBalanceMode}
                onChange={(e) => setProteinBalanceMode(e.target.value as ProteinBalanceMode)}
              >
                <option value="free">Livre</option>
                <option value="ratio_1_1">1 carne : 1 peixe</option>
                <option value="ratio_2_1">2 carnes : 1 peixe</option>
                <option value="ratio_3_1">3 carnes : 1 peixe</option>
              </select>
            </div>

            <div className="nf-pill-row">
              <span className="nf-score-pill">
                Seleção atual: {proteinBalanceModeLabels[proteinBalanceMode]}
              </span>
            </div>

            <p className="nf-inline-note" style={{ lineHeight: 1.6, margin: 0 }}>
              Estas regras influenciam o próximo preview. A lógica tenta respeitar o
              padrão carne/peixe escolhido e continua a rodar os tipos de carne para
              evitar repetições do mesmo tipo de proteína.
            </p>

            <div className="nf-actions-inline" style={{ marginTop: "4px" }}>
              <button
                type="button"
                style={styles.button}
                onClick={() => setAdvancedOpen(false)}
              >
                Fechar
              </button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}