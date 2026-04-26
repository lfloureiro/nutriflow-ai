import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { MealPlanItem, Recipe } from "../types";

type Props = {
  mealPlan: MealPlanItem[];
  recipes: Recipe[];
  onSuccess: () => Promise<void>;
};

type EditState = {
  plan_date: string;
  meal_type: string;
  recipe_id: string;
  notes: string;
};

const visibleMealTypes = [
  { value: "almoco", label: "Almoço" },
  { value: "jantar", label: "Jantar" },
] as const;

const MOBILE_LAYOUT_BREAKPOINT = 920;

function parseDate(value: string) {
  return new Date(`${value}T00:00:00`);
}

function toIsoDate(date: Date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(date: Date, days: number) {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

function startOfWeekSunday(date: Date) {
  const copy = new Date(date);
  copy.setDate(copy.getDate() - copy.getDay());
  return copy;
}

function endOfWeekSaturday(date: Date) {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + (6 - copy.getDay()));
  return copy;
}

function buildDateRange(startDate: string, endDate: string) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || start > end) {
    return [startDate];
  }

  const result: string[] = [];
  const current = new Date(start);

  while (current <= end) {
    result.push(toIsoDate(current));
    current.setDate(current.getDate() + 1);
  }

  return result;
}

function buildNormalizedCalendarDates(dates: string[]) {
  if (dates.length === 0) {
    return [];
  }

  const sortedDates = [...new Set(dates)].sort((a, b) => a.localeCompare(b));
  const firstDate = parseDate(sortedDates[0]);
  const lastDate = parseDate(sortedDates[sortedDates.length - 1]);

  const start = startOfWeekSunday(firstDate);
  let end = endOfWeekSaturday(lastDate);

  const currentLength =
    Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;

  if (currentLength < 14) {
    end = addDays(start, 13);
  }

  return buildDateRange(toIsoDate(start), toIsoDate(end));
}

function buildOneWeekWindowDates(startDate: string) {
  const start = parseDate(startDate);

  if (Number.isNaN(start.getTime())) {
    return [];
  }

  const anchoredStart = startOfWeekSunday(start);
  const end = addDays(anchoredStart, 6);

  return buildDateRange(toIsoDate(anchoredStart), toIsoDate(end));
}

function buildTwoWeekWindowDates(startDate: string) {
  const start = parseDate(startDate);

  if (Number.isNaN(start.getTime())) {
    return [];
  }

  const anchoredStart = startOfWeekSunday(start);
  const end = addDays(anchoredStart, 13);

  return buildDateRange(toIsoDate(anchoredStart), toIsoDate(end));
}

function formatWeekday(value: string) {
  const date = parseDate(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("pt-PT", {
    weekday: "short",
  });
}

function formatDay(value: string) {
  const date = parseDate(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("pt-PT", {
    day: "2-digit",
    month: "2-digit",
  });
}

function formatFullDate(value: string) {
  const date = parseDate(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("pt-PT", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

async function readJsonSafe(response: Response) {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
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

function truncateText(value: string, maxLength = 22) {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 1)}…`;
}

function getCompactRecipeLabel(items: MealPlanItem[]) {
  if (items.length === 0) {
    return "Sem refeição.";
  }

  if (items.length === 1) {
    return truncateText(items[0].recipe.name, 22);
  }

  return `${truncateText(items[0].recipe.name, 18)} +${items.length - 1}`;
}

function useViewportWidth() {
  const getWidth = () => {
    if (typeof window === "undefined") {
      return 1280;
    }

    return window.innerWidth;
  };

  const [viewportWidth, setViewportWidth] = useState<number>(getWidth);

  useEffect(() => {
    const handleResize = () => setViewportWidth(getWidth());

    handleResize();
    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return viewportWidth;
}

export function MealPlanList({ mealPlan, recipes, onSuccess }: Props) {
  const viewportWidth = useViewportWidth();
  const isMobileLayout = viewportWidth < MOBILE_LAYOUT_BREAKPOINT;

  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [hoveredDate, setHoveredDate] = useState<string | null>(null);
  const [windowStartDate, setWindowStartDate] = useState<string>("");

  const [editingId, setEditingId] = useState<number | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const [editState, setEditState] = useState<EditState>({
    plan_date: "",
    meal_type: "jantar",
    recipe_id: "",
    notes: "",
  });

  const visibleMealPlan = useMemo(() => {
    return mealPlan.filter((item) =>
      visibleMealTypes.some((mealType) => mealType.value === item.meal_type),
    );
  }, [mealPlan]);

  const calendarDates = useMemo(() => {
    return buildNormalizedCalendarDates(visibleMealPlan.map((item) => item.plan_date));
  }, [visibleMealPlan]);

  useEffect(() => {
    if (calendarDates.length === 0) {
      return;
    }

    if (!windowStartDate) {
      setWindowStartDate(calendarDates[0]);
    }
  }, [calendarDates, windowStartDate]);

  const visibleWindowDates = useMemo(() => {
    if (!windowStartDate) {
      return [];
    }

    return isMobileLayout
      ? buildOneWeekWindowDates(windowStartDate)
      : buildTwoWeekWindowDates(windowStartDate);
  }, [isMobileLayout, windowStartDate]);

  const mealMap = useMemo(() => {
    const nextMap = new Map<string, MealPlanItem[]>();

    visibleMealPlan.forEach((item) => {
      const key = `${item.plan_date}__${item.meal_type}`;
      const current = nextMap.get(key) ?? [];
      current.push(item);
      nextMap.set(key, current);
    });

    return nextMap;
  }, [visibleMealPlan]);

  const dateRangeLabel = useMemo(() => {
    if (visibleWindowDates.length === 0) {
      return null;
    }

    if (visibleWindowDates.length === 1) {
      return formatFullDate(visibleWindowDates[0]);
    }

    return `${formatFullDate(visibleWindowDates[0])} → ${formatFullDate(
      visibleWindowDates[visibleWindowDates.length - 1],
    )}`;
  }, [visibleWindowDates]);

  const visibleWindowItemCount = useMemo(() => {
    if (visibleWindowDates.length === 0) {
      return 0;
    }

    const dateSet = new Set(visibleWindowDates);
    return visibleMealPlan.filter((item) => dateSet.has(item.plan_date)).length;
  }, [visibleMealPlan, visibleWindowDates]);

  const selectedDayMeals = useMemo(() => {
    if (!selectedDate) {
      return {
        almoco: [] as MealPlanItem[],
        jantar: [] as MealPlanItem[],
      };
    }

    return {
      almoco: mealMap.get(`${selectedDate}__almoco`) ?? [],
      jantar: mealMap.get(`${selectedDate}__jantar`) ?? [],
    };
  }, [mealMap, selectedDate]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (editingId !== null) {
          setEditingId(null);
          return;
        }

        if (selectedDate !== null) {
          setSelectedDate(null);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [editingId, selectedDate]);

  function shiftWindowByWeeks(direction: -1 | 1) {
    if (!windowStartDate) {
      return;
    }

    const currentStart = startOfWeekSunday(parseDate(windowStartDate));
    const nextStart = addDays(currentStart, direction * 7);
    setWindowStartDate(toIsoDate(nextStart));
  }

  function handleWindowDateChange(value: string) {
    if (!value) {
      return;
    }

    const anchored = startOfWeekSunday(parseDate(value));
    setWindowStartDate(toIsoDate(anchored));
  }

  function openDay(date: string) {
    setLocalMessage(null);
    setLocalError(null);
    setSelectedDate(date);
    setEditingId(null);
  }

  function closeDay() {
    if (editingId !== null) {
      return;
    }

    setSelectedDate(null);
    setLocalMessage(null);
    setLocalError(null);
  }

  function startEditing(item: MealPlanItem) {
    setLocalMessage(null);
    setLocalError(null);
    setSelectedDate(item.plan_date);
    setEditingId(item.id);
    setEditState({
      plan_date: item.plan_date,
      meal_type: item.meal_type,
      recipe_id: String(item.recipe.id),
      notes: item.notes ?? "",
    });
  }

  function cancelEditing() {
    setEditingId(null);
    setEditState({
      plan_date: "",
      meal_type: "jantar",
      recipe_id: "",
      notes: "",
    });
  }

  async function handleSave(itemId: number) {
    setLocalMessage(null);
    setLocalError(null);

    if (!editState.plan_date) {
      setLocalError("A data é obrigatória.");
      return;
    }

    if (!editState.meal_type.trim()) {
      setLocalError("O tipo de refeição é obrigatório.");
      return;
    }

    if (!editState.recipe_id) {
      setLocalError("Tens de selecionar uma receita.");
      return;
    }

    try {
      setSavingId(itemId);

      const response = await fetch(`${API_BASE_URL}/meal-plan/${itemId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          plan_date: editState.plan_date,
          meal_type: editState.meal_type,
          recipe_id: Number(editState.recipe_id),
          notes: editState.notes.trim() ? editState.notes : null,
        }),
      });

      const data = await readJsonSafe(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível atualizar a refeição."));
      }

      setLocalMessage("Refeição atualizada com sucesso.");
      cancelEditing();
      await onSuccess();
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Erro inesperado.");
    } finally {
      setSavingId(null);
    }
  }

  async function handleDelete(item: MealPlanItem) {
    setLocalMessage(null);
    setLocalError(null);

    const confirmed = window.confirm(
      `Queres apagar a refeição "${item.recipe.name}" de ${item.plan_date}?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(item.id);

      const response = await fetch(`${API_BASE_URL}/meal-plan/${item.id}`, {
        method: "DELETE",
      });

      const data = await readJsonSafe(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível apagar a refeição."));
      }

      if (editingId === item.id) {
        cancelEditing();
      }

      setLocalMessage("Refeição apagada com sucesso.");
      await onSuccess();
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Erro inesperado.");
    } finally {
      setDeletingId(null);
    }
  }

  function renderCompactMeal(
    date: string,
    mealType: (typeof visibleMealTypes)[number],
    highlighted: boolean,
  ) {
    const items = mealMap.get(`${date}__${mealType.value}`) ?? [];
    const hasItems = items.length > 0;

    return (
      <div
        style={{
          padding: isMobileLayout ? "10px 12px" : "8px 10px",
          border: highlighted
            ? "1px solid rgba(96, 165, 250, 0.22)"
            : "1px solid rgba(148, 163, 184, 0.12)",
          borderRadius: "10px",
          background: highlighted ? "rgba(15, 23, 42, 0.42)" : "rgba(15, 23, 42, 0.28)",
          boxShadow: highlighted ? "0 0 0 1px rgba(96, 165, 250, 0.08)" : "none",
          display: "grid",
          gridTemplateRows: "auto 1fr",
          gap: "4px",
          minHeight: isMobileLayout ? "68px" : "58px",
          boxSizing: "border-box",
          transition: "border-color 160ms ease, background 160ms ease, box-shadow 160ms ease",
        }}
      >
        <div
          style={{
            fontSize: isMobileLayout ? "0.74rem" : "0.66rem",
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#93c5fd",
          }}
        >
          {mealType.label}
        </div>

        <div
          title={hasItems ? items.map((item) => item.recipe.name).join(" | ") : "Sem refeição"}
          style={{
            fontSize: hasItems ? (isMobileLayout ? "0.96rem" : "0.79rem") : isMobileLayout ? "0.86rem" : "0.73rem",
            fontWeight: hasItems ? 600 : 400,
            fontStyle: hasItems ? "normal" : "italic",
            color: hasItems ? "#e5e7eb" : "#64748b",
            lineHeight: 1.2,
            minHeight: isMobileLayout ? "34px" : "30px",
            overflow: "hidden",
            display: "-webkit-box",
            WebkitLineClamp: isMobileLayout ? 3 : 2,
            WebkitBoxOrient: "vertical",
            wordBreak: "break-word",
          }}
        >
          {getCompactRecipeLabel(items)}
        </div>
      </div>
    );
  }

  function renderMealItem(item: MealPlanItem) {
    const isBusy = savingId === item.id || deletingId === item.id;

    return (
      <div
        key={item.id}
        style={{
          padding: "14px",
          borderRadius: "14px",
          border: "1px solid rgba(148, 163, 184, 0.14)",
          background: "rgba(15, 23, 42, 0.34)",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          minWidth: 0,
        }}
      >
        <div
          style={{
            fontSize: "clamp(0.96rem, 2vw, 1rem)",
            fontWeight: 700,
            color: "#f8fafc",
            lineHeight: 1.25,
            wordBreak: "break-word",
          }}
        >
          {item.recipe.name}
        </div>

        {item.notes?.trim() ? (
          <div
            style={{
              fontSize: "0.84rem",
              color: "#94a3b8",
              lineHeight: 1.35,
              wordBreak: "break-word",
            }}
          >
            {item.notes.trim()}
          </div>
        ) : (
          <div
            style={{
              fontSize: "0.84rem",
              color: "#64748b",
              fontStyle: "italic",
              lineHeight: 1.35,
            }}
          >
            Sem notas.
          </div>
        )}

        <div
          style={{
            display: "flex",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            style={{
              ...styles.button,
              padding: "8px 12px",
              fontSize: "0.8rem",
            }}
            onClick={() => startEditing(item)}
            disabled={isBusy}
          >
            Editar
          </button>

          <button
            type="button"
            style={{
              ...styles.button,
              padding: "8px 12px",
              fontSize: "0.8rem",
              background: "#7f1d1d",
              border: "1px solid #991b1b",
            }}
            onClick={() => handleDelete(item)}
            disabled={isBusy}
          >
            {deletingId === item.id ? "A apagar..." : "Apagar"}
          </button>
        </div>
      </div>
    );
  }

  function renderMealSection(title: string, items: MealPlanItem[], highlighted = false) {
    return (
      <div
        style={{
          padding: isMobileLayout ? "14px" : "16px",
          borderRadius: "16px",
          border: highlighted
            ? "1px solid rgba(96, 165, 250, 0.24)"
            : "1px solid rgba(148, 163, 184, 0.14)",
          background: highlighted ? "rgba(15, 23, 42, 0.4)" : "rgba(15, 23, 42, 0.28)",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          minWidth: 0,
        }}
      >
        <div
          style={{
            fontSize: "0.74rem",
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#93c5fd",
          }}
        >
          {title}
        </div>

        {items.length === 0 ? (
          <div
            style={{
              fontSize: "0.9rem",
              color: "#64748b",
              fontStyle: "italic",
              lineHeight: 1.35,
            }}
          >
            Sem refeição.
          </div>
        ) : (
          items.map((item) => renderMealItem(item))
        )}
      </div>
    );
  }

  function renderMobileDayCard(date: string) {
    const almocoItems = mealMap.get(`${date}__almoco`) ?? [];
    const jantarItems = mealMap.get(`${date}__jantar`) ?? [];
    const dayItemCount = almocoItems.length + jantarItems.length;

    return (
      <button
        key={date}
        type="button"
        onClick={() => openDay(date)}
        style={{
          width: "100%",
          textAlign: "left",
          border: "1px solid rgba(148, 163, 184, 0.16)",
          borderRadius: "16px",
          background: "rgba(15, 23, 42, 0.24)",
          padding: "14px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          cursor: "pointer",
          minWidth: 0,
          boxShadow: "0 8px 24px rgba(2, 6, 23, 0.14)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "10px",
            minWidth: 0,
          }}
        >
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                fontSize: "0.72rem",
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "#93c5fd",
              }}
            >
              {formatWeekday(date)}
            </div>
            <div
              style={{
                marginTop: "3px",
                fontSize: "1.02rem",
                fontWeight: 700,
                color: "#f8fafc",
              }}
            >
              {formatDay(date)}
            </div>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              gap: "4px",
              flexShrink: 0,
            }}
          >
            <span className="nf-score-pill">{dayItemCount} refeição(ões)</span>
            <span
              style={{
                fontSize: "0.78rem",
                fontWeight: 600,
                color: "#93c5fd",
              }}
            >
              Abrir detalhe
            </span>
          </div>
        </div>

        {renderCompactMeal(date, visibleMealTypes[0], false)}
        {renderCompactMeal(date, visibleMealTypes[1], false)}
      </button>
    );
  }

  function renderEditingMeal(item: MealPlanItem) {
    const isSaving = savingId === item.id;
    const isDeleting = deletingId === item.id;
    const isBusy = isSaving || isDeleting;

    return (
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 1400,
          display: "flex",
          alignItems: isMobileLayout ? "flex-end" : "center",
          justifyContent: "center",
          padding: isMobileLayout ? "8px" : "24px",
          background: "rgba(2, 6, 23, 0.62)",
          backdropFilter: "blur(8px)",
          boxSizing: "border-box",
        }}
        onClick={cancelEditing}
      >
        <div
          onClick={(event) => event.stopPropagation()}
          style={{
            width: isMobileLayout ? "100%" : "min(760px, 92vw)",
            maxHeight: isMobileLayout ? "calc(100dvh - 8px)" : "85vh",
            overflowY: "auto",
            borderRadius: isMobileLayout ? "20px 20px 0 0" : "22px",
            border: "1px solid rgba(96, 165, 250, 0.2)",
            background: "linear-gradient(180deg, rgba(2,6,23,0.98) 0%, rgba(15,23,42,0.96) 100%)",
            boxShadow: "0 24px 80px rgba(2, 6, 23, 0.5)",
            padding: isMobileLayout ? "16px" : "22px",
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: "16px",
              marginBottom: "18px",
              flexDirection: isMobileLayout ? "column" : "row",
            }}
          >
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontSize: "0.74rem",
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "#93c5fd",
                }}
              >
                Editar refeição
              </div>

              <div
                style={{
                  marginTop: "6px",
                  fontSize: "clamp(1.05rem, 2.6vw, 1.2rem)",
                  fontWeight: 700,
                  color: "#f8fafc",
                  lineHeight: 1.25,
                }}
              >
                {item.recipe.name}
              </div>

              <div
                style={{
                  marginTop: "6px",
                  fontSize: "0.86rem",
                  color: "#94a3b8",
                }}
              >
                {formatFullDate(item.plan_date)}
              </div>
            </div>

            <button
              type="button"
              onClick={cancelEditing}
              style={{
                border: "1px solid rgba(148, 163, 184, 0.16)",
                background: "rgba(15, 23, 42, 0.42)",
                color: "#cbd5e1",
                borderRadius: "10px",
                fontSize: "0.78rem",
                padding: "8px 12px",
                cursor: "pointer",
                width: isMobileLayout ? "100%" : "auto",
              }}
            >
              Fechar
            </button>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobileLayout ? "1fr" : "1fr 1fr",
              gap: "10px",
            }}
          >
            <input
              type="date"
              style={{
                ...styles.input,
                padding: "10px 12px",
                fontSize: "0.88rem",
                minWidth: 0,
              }}
              value={editState.plan_date}
              onChange={(e) =>
                setEditState((current) => ({
                  ...current,
                  plan_date: e.target.value,
                }))
              }
              disabled={isBusy}
            />

            <select
              style={{
                ...styles.select,
                padding: "10px 12px",
                fontSize: "0.88rem",
                minWidth: 0,
              }}
              value={editState.meal_type}
              onChange={(e) =>
                setEditState((current) => ({
                  ...current,
                  meal_type: e.target.value,
                }))
              }
              disabled={isBusy}
            >
              {visibleMealTypes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <select
              style={{
                ...styles.select,
                gridColumn: "1 / -1",
                padding: "10px 12px",
                fontSize: "0.88rem",
                minWidth: 0,
              }}
              value={editState.recipe_id}
              onChange={(e) =>
                setEditState((current) => ({
                  ...current,
                  recipe_id: e.target.value,
                }))
              }
              disabled={isBusy}
            >
              <option value="">Seleciona uma receita</option>
              {recipes.map((recipe) => (
                <option key={recipe.id} value={recipe.id}>
                  {recipe.name}
                </option>
              ))}
            </select>

            <textarea
              style={{
                ...styles.textarea,
                gridColumn: "1 / -1",
                minHeight: "120px",
                padding: "10px 12px",
                fontSize: "0.88rem",
                minWidth: 0,
              }}
              value={editState.notes}
              onChange={(e) =>
                setEditState((current) => ({
                  ...current,
                  notes: e.target.value,
                }))
              }
              disabled={isBusy}
              placeholder="Notas"
            />

            <div
              style={{
                gridColumn: "1 / -1",
                display: "flex",
                gap: "10px",
                flexWrap: "wrap",
                marginTop: "4px",
                flexDirection: isMobileLayout ? "column" : "row",
              }}
            >
              <button
                type="button"
                style={{
                  ...styles.button,
                  padding: "10px 14px",
                  fontSize: "0.82rem",
                }}
                onClick={() => handleSave(item.id)}
                disabled={isBusy}
              >
                {isSaving ? "A guardar..." : "Guardar"}
              </button>

              <button
                type="button"
                style={{
                  ...styles.button,
                  padding: "10px 14px",
                  fontSize: "0.82rem",
                }}
                onClick={cancelEditing}
                disabled={isBusy}
              >
                Cancelar
              </button>

              <button
                type="button"
                style={{
                  ...styles.button,
                  padding: "10px 14px",
                  fontSize: "0.82rem",
                  background: "#7f1d1d",
                  border: "1px solid #991b1b",
                }}
                onClick={() => handleDelete(item)}
                disabled={isBusy}
              >
                {isDeleting ? "A apagar..." : "Apagar"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const editingItem =
    editingId !== null ? visibleMealPlan.find((item) => item.id === editingId) ?? null : null;

  const navControlHeight = isMobileLayout ? "44px" : "46px";

  return (
    <>
      <section
        style={{
          padding: 0,
          width: "100%",
          boxSizing: "border-box",
          minWidth: 0,
        }}
      >
        <div
          style={{
            marginBottom: "12px",
            display: "flex",
            flexWrap: "wrap",
            gap: "12px",
            alignItems: isMobileLayout ? "stretch" : "center",
            justifyContent: "space-between",
            minWidth: 0,
          }}
        >
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "10px",
              alignItems: "center",
              color: "#cbd5e1",
              fontSize: "clamp(0.78rem, 1.5vw, 0.86rem)",
              minWidth: 0,
              flex: "1 1 280px",
            }}
          >
            <span style={{ fontWeight: 700 }}>{visibleWindowItemCount} item(ns) visíveis</span>
            {dateRangeLabel ? <span>{dateRangeLabel}</span> : null}
            <span className="nf-inline-note" style={{ marginTop: 0 }}>
              {isMobileLayout ? "Modo mobile: lista semanal" : "Modo desktop: mapa de 2 semanas"}
            </span>
          </div>

          <div
            style={{
              display: "flex",
              flexWrap: isMobileLayout ? "wrap" : "nowrap",
              gap: "8px",
              alignItems: "center",
              width: isMobileLayout ? "100%" : "auto",
              minWidth: 0,
            }}
          >
            <button
              type="button"
              style={{
                ...styles.button,
                width: isMobileLayout ? "calc(50% - 4px)" : "46px",
                minWidth: isMobileLayout ? "120px" : "46px",
                height: navControlHeight,
                padding: 0,
                fontSize: "1rem",
                lineHeight: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxSizing: "border-box",
              }}
              onClick={() => shiftWindowByWeeks(-1)}
              disabled={!windowStartDate}
              title="Semana anterior"
              aria-label="Semana anterior"
            >
              ←
            </button>

            <input
              type="date"
              style={{
                ...styles.input,
                flex: isMobileLayout ? "1 1 100%" : "0 0 180px",
                width: isMobileLayout ? "100%" : "180px",
                minWidth: 0,
                height: navControlHeight,
                padding: "0 10px",
                fontSize: "0.82rem",
                boxSizing: "border-box",
              }}
              value={windowStartDate}
              onChange={(e) => handleWindowDateChange(e.target.value)}
              disabled={!windowStartDate}
            />

            <button
              type="button"
              style={{
                ...styles.button,
                width: isMobileLayout ? "calc(50% - 4px)" : "46px",
                minWidth: isMobileLayout ? "120px" : "46px",
                height: navControlHeight,
                padding: 0,
                fontSize: "1rem",
                lineHeight: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxSizing: "border-box",
              }}
              onClick={() => shiftWindowByWeeks(1)}
              disabled={!windowStartDate}
              title="Semana seguinte"
              aria-label="Semana seguinte"
            >
              →
            </button>
          </div>
        </div>

        {localMessage && <p style={styles.success}>{localMessage}</p>}
        {localError && <p style={styles.error}>Erro: {localError}</p>}

        {visibleWindowDates.length === 0 ? (
          <p style={styles.empty}>Sem almoços ou jantares no plano.</p>
        ) : isMobileLayout ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              width: "100%",
              minWidth: 0,
            }}
          >
            {visibleWindowDates.map((date) => renderMobileDayCard(date))}
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(7, minmax(0, 1fr))",
              gap: viewportWidth < 1180 ? "8px" : "10px",
              alignItems: "start",
              width: "100%",
              boxSizing: "border-box",
              minWidth: 0,
            }}
          >
            {visibleWindowDates.map((date) => {
              const isHovered = hoveredDate === date;

              return (
                <div
                  key={date}
                  title="Clique para ver o detalhe do dia"
                  onClick={() => openDay(date)}
                  onMouseEnter={() => setHoveredDate(date)}
                  onMouseLeave={() => {
                    setHoveredDate((current) => (current === date ? null : current));
                  }}
                  style={{
                    border: isHovered
                      ? "1px solid rgba(96, 165, 250, 0.28)"
                      : "1px solid rgba(148, 163, 184, 0.18)",
                    borderRadius: "12px",
                    background: isHovered ? "rgba(15, 23, 42, 0.32)" : "rgba(15, 23, 42, 0.24)",
                    boxShadow: isHovered
                      ? "0 0 0 1px rgba(96, 165, 250, 0.08), 0 10px 22px rgba(2, 6, 23, 0.22)"
                      : "0 4px 14px rgba(2, 6, 23, 0.12)",
                    overflow: "hidden",
                    minWidth: 0,
                    boxSizing: "border-box",
                    cursor: "pointer",
                    minHeight: viewportWidth < 1180 ? "162px" : "178px",
                    display: "grid",
                    gridTemplateRows: "58px auto",
                    transform: isHovered ? "translateY(-2px)" : "translateY(0)",
                    transition:
                      "border-color 160ms ease, box-shadow 160ms ease, background 160ms ease, transform 160ms ease",
                  }}
                >
                  <div
                    style={{
                      padding: viewportWidth < 1180 ? "8px" : "8px 10px",
                      borderBottom: "1px solid rgba(148, 163, 184, 0.14)",
                      background: isHovered ? "rgba(15, 23, 42, 0.42)" : "rgba(15, 23, 42, 0.34)",
                      minWidth: 0,
                      boxSizing: "border-box",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "8px",
                      transition: "background 160ms ease",
                    }}
                  >
                    <div style={{ minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: viewportWidth < 1180 ? "0.62rem" : "0.68rem",
                          fontWeight: 700,
                          letterSpacing: "0.08em",
                          textTransform: "uppercase",
                          color: "#93c5fd",
                        }}
                      >
                        {formatWeekday(date)}
                      </div>

                      <div
                        style={{
                          marginTop: "2px",
                          fontSize: viewportWidth < 1180 ? "0.88rem" : "0.96rem",
                          fontWeight: 700,
                          color: "#f8fafc",
                        }}
                      >
                        {formatDay(date)}
                      </div>
                    </div>

                    {isHovered ? (
                      <div
                        style={{
                          fontSize: "0.62rem",
                          fontWeight: 600,
                          color: "#93c5fd",
                          whiteSpace: "nowrap",
                        }}
                      >
                        Ver detalhe
                      </div>
                    ) : null}
                  </div>

                  <div
                    style={{
                      padding: viewportWidth < 1180 ? "8px 7px" : "8px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                      boxSizing: "border-box",
                    }}
                  >
                    {renderCompactMeal(date, visibleMealTypes[0], isHovered)}
                    {renderCompactMeal(date, visibleMealTypes[1], isHovered)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {selectedDate ? (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1300,
            display: "flex",
            alignItems: isMobileLayout ? "flex-end" : "center",
            justifyContent: "center",
            padding: isMobileLayout ? "8px" : "24px",
            background: "rgba(2, 6, 23, 0.54)",
            backdropFilter: "blur(7px)",
            boxSizing: "border-box",
          }}
          onClick={closeDay}
        >
          <div
            onClick={(event) => event.stopPropagation()}
            style={{
              width: isMobileLayout ? "100%" : "min(1080px, 94vw)",
              maxHeight: isMobileLayout ? "calc(100dvh - 8px)" : "86vh",
              overflowY: "auto",
              borderRadius: isMobileLayout ? "20px 20px 0 0" : "24px",
              border: "1px solid rgba(96, 165, 250, 0.18)",
              background: "linear-gradient(180deg, rgba(2,6,23,0.98) 0%, rgba(15,23,42,0.96) 100%)",
              boxShadow: "0 28px 90px rgba(2, 6, 23, 0.5)",
              boxSizing: "border-box",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: "16px",
                padding: isMobileLayout ? "18px 16px 14px 16px" : "24px 26px 18px 26px",
                borderBottom: "1px solid rgba(148, 163, 184, 0.12)",
                flexDirection: isMobileLayout ? "column" : "row",
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: "0.76rem",
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: "#93c5fd",
                  }}
                >
                  Detalhe do dia
                </div>

                <div
                  style={{
                    marginTop: "6px",
                    fontSize: "clamp(1.08rem, 2.8vw, 1.35rem)",
                    fontWeight: 700,
                    color: "#f8fafc",
                    lineHeight: 1.22,
                  }}
                >
                  {formatFullDate(selectedDate)}
                </div>
              </div>

              <button
                type="button"
                onClick={closeDay}
                style={{
                  border: "1px solid rgba(148, 163, 184, 0.16)",
                  background: "rgba(15, 23, 42, 0.42)",
                  color: "#cbd5e1",
                  borderRadius: "10px",
                  fontSize: "0.8rem",
                  padding: "10px 14px",
                  cursor: editingId === null ? "pointer" : "default",
                  width: isMobileLayout ? "100%" : "auto",
                }}
                disabled={editingId !== null}
              >
                Fechar
              </button>
            </div>

            <div
              style={{
                padding: isMobileLayout ? "16px" : "22px 26px 26px 26px",
                display: "grid",
                gridTemplateColumns: isMobileLayout ? "1fr" : "repeat(auto-fit, minmax(320px, 1fr))",
                gap: "16px",
              }}
            >
              {renderMealSection("Almoço", selectedDayMeals.almoco, true)}
              {renderMealSection("Jantar", selectedDayMeals.jantar, true)}
            </div>
          </div>
        </div>
      ) : null}

      {editingItem ? renderEditingMeal(editingItem) : null}
    </>
  );
}
