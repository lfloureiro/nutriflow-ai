import { useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";

type Suggestion = {
  plan_date: string;
  meal_type: string;
  action: string;
  recipe_id: number | null;
  recipe_name: string | null;
  categoria_alimentar: string | null;
  proteina_principal: string | null;
  score: number | null;
  average_rating: number | null;
  ratings_count: number;
  reasons: string[];
};

type PreviewResponse = {
  household_id: number;
  start_date: string;
  end_date: string;
  meal_types: string[];
  skip_existing: boolean;
  suggestions: Suggestion[];
};

type ApplyResponse = {
  household_id: number;
  start_date: string;
  end_date: string;
  meal_types: string[];
  skip_existing: boolean;
  created_count: number;
  skipped_count: number;
  suggestions: Suggestion[];
};

type Props = {
  householdId: string;
  onApplied: () => Promise<void>;
};

type MealTypeOption = "almoco" | "jantar";

const mealTypeLabels: Record<MealTypeOption, string> = {
  almoco: "Almoço",
  jantar: "Jantar",
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

export function AutoPlanPanel({ householdId, onApplied }: Props) {
  const initialStartDate = useMemo(() => getTodayIsoDate(), []);
  const initialEndDate = useMemo(() => addDaysIsoDate(initialStartDate, 6), [initialStartDate]);

  const [startDate, setStartDate] = useState(initialStartDate);
  const [endDate, setEndDate] = useState(initialEndDate);
  const [selectedMealTypes, setSelectedMealTypes] = useState<MealTypeOption[]>([
    "almoco",
    "jantar",
  ]);

  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [applyingPlan, setApplyingPlan] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function toggleMealType(mealType: MealTypeOption) {
    setSelectedMealTypes((current) => {
      if (current.includes(mealType)) {
        return current.filter((item) => item !== mealType);
      }

      return [...current, mealType];
    });
  }

  async function handlePreview() {
    setMessage(null);
    setError(null);
    setPreview(null);

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
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível gerar o preview.")
        );
      }

      setPreview(data);
      setMessage("Preview gerado com sucesso.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handleApply() {
    setMessage(null);
    setError(null);

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
      setApplyingPlan(true);

      const res = await fetch(`${API_BASE_URL}/meal-plan/auto-plan/apply`, {
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
        }),
      });

      const data: ApplyResponse = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível aplicar o auto-planeamento.")
        );
      }

      setMessage(
        `Plano aplicado com sucesso. ${data.created_count} refeição(ões) criadas, ${data.skipped_count} ignorada(s).`
      );
      setPreview(null);
      await onApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setApplyingPlan(false);
    }
  }

  return (
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
          Gera um preview para almoço e jantar com base nas preferências da
          família, rotação e histórico recente.
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
            onClick={handleApply}
            disabled={
              applyingPlan ||
              loadingPreview ||
              !householdId ||
              selectedMealTypes.length === 0
            }
          >
            {applyingPlan ? "A aplicar..." : "Aplicar auto-planeamento"}
          </button>
        </div>

        {message && <p style={styles.success}>{message}</p>}
        {error && <p style={styles.error}>Erro: {error}</p>}

        {preview && (
          <div className="nf-record-list">
            {preview.suggestions.map((item, index) => (
              <div key={`${item.plan_date}-${item.meal_type}-${index}`} className="nf-record-card">
                <div className="nf-record-card-head">
                  <div className="nf-record-card-main">
                    <div className="nf-pill-row">
                      <span className="nf-score-pill">
                        {formatPlanDate(item.plan_date)}
                      </span>
                      <span className="nf-score-pill">
                        {formatMealType(item.meal_type)}
                      </span>
                      <span className="nf-score-pill">{item.action}</span>
                    </div>

                    <div className="nf-record-title">
                      {item.recipe_name ?? "Sem sugestão"}
                    </div>

                    <div className="nf-record-description">
                      {item.categoria_alimentar || "Sem categoria"} ·{" "}
                      {item.proteina_principal || "Sem proteína"} · Score{" "}
                      {item.score ?? "—"}
                    </div>

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
            ))}
          </div>
        )}
      </div>
    </section>
  );
}