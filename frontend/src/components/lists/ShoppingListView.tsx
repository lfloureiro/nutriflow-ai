import { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { ShoppingListItem } from "../types";

type Props = {
  householdId: string;
  shoppingList: ShoppingListItem[];
  onRefresh: () => Promise<void>;
};

type FilterMode = "all" | "pending" | "cart";

const POLLING_INTERVAL_MS = 10000;

function formatMealType(mealType: string) {
  return mealType
    .replaceAll("-", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
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

function formatSyncTime(value: Date | null) {
  if (!value) {
    return "Ainda não sincronizada";
  }

  return value.toLocaleTimeString("pt-PT", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function ShoppingListView({
  householdId,
  shoppingList,
  onRefresh,
}: Props) {
  const [filter, setFilter] = useState<FilterMode>("all");
  const [showSources, setShowSources] = useState(false);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastSyncedAt, setLastSyncedAt] = useState<Date | null>(new Date());

  const filteredItems = useMemo(() => {
    if (filter === "pending") {
      return shoppingList.filter((item) => !item.in_cart);
    }

    if (filter === "cart") {
      return shoppingList.filter((item) => item.in_cart);
    }

    return shoppingList;
  }, [shoppingList, filter]);

  useEffect(() => {
    setLastSyncedAt(new Date());
  }, [shoppingList]);

  const refreshList = useCallback(
    async (options?: { silent?: boolean }) => {
      if (!householdId) {
        return;
      }

      const silent = options?.silent ?? false;

      if (!silent) {
        setLocalMessage(null);
        setLocalError(null);
        setIsRefreshing(true);
      }

      try {
        await onRefresh();
        setLastSyncedAt(new Date());

        if (!silent) {
          setLocalMessage("Lista sincronizada.");
        }
      } catch (err) {
        if (!silent) {
          setLocalError(
            err instanceof Error
              ? err.message
              : "Erro inesperado ao sincronizar a lista."
          );
        }
      } finally {
        if (!silent) {
          setIsRefreshing(false);
        }
      }
    },
    [householdId, onRefresh]
  );

  useEffect(() => {
    if (!householdId) {
      return;
    }

    const intervalId = window.setInterval(() => {
      if (document.hidden || savingKey !== null) {
        return;
      }

      void refreshList({ silent: true });
    }, POLLING_INTERVAL_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [householdId, refreshList, savingKey]);

  async function toggleInCart(item: ShoppingListItem) {
    setLocalMessage(null);
    setLocalError(null);

    if (!householdId) {
      setLocalError("Seleciona primeiro um agregado.");
      return;
    }

    const key = `${item.ingredient_id}-${item.unit ?? ""}`;

    try {
      setSavingKey(key);

      const res = await fetch(`${API_BASE_URL}/shopping-list/item-state`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          household_id: Number(householdId),
          ingredient_id: item.ingredient_id,
          unit: item.unit,
          in_cart: !item.in_cart,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível atualizar o estado do item.")
        );
      }

      setLocalMessage(
        !item.in_cart
          ? "Item marcado como já no cesto."
          : "Item retirado do estado já no cesto."
      );

      await refreshList({ silent: true });
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingKey(null);
    }
  }

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Compras</div>
        <h2 style={styles.sectionTitle}>Lista de compras</h2>
        <p className="nf-menu-panel-text">
          Vista partilhada dos itens a comprar, com estado persistido do cesto e
          sincronização automática.
        </p>
      </div>

      <div className="nf-pill-row" style={{ marginTop: "12px" }}>
        <span className="nf-context-meta-chip">
          {shoppingList.length} item(ns) no total
        </span>
        <span className="nf-context-meta-chip">
          {shoppingList.filter((item) => !item.in_cart).length} por comprar
        </span>
        <span className="nf-context-meta-chip">
          {shoppingList.filter((item) => item.in_cart).length} já no cesto
        </span>
      </div>

      <div
        className="nf-actions-inline"
        style={{ marginTop: "12px", alignItems: "center" }}
      >
        <span className="nf-context-meta-chip">
          Última sincronização: {formatSyncTime(lastSyncedAt)}
        </span>

        <button
          type="button"
          className={`nf-filter-chip${isRefreshing ? " nf-filter-chip--active" : ""}`}
          onClick={() => void refreshList()}
          disabled={isRefreshing || !householdId}
        >
          {isRefreshing ? "A sincronizar..." : "Atualizar agora"}
        </button>
      </div>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div className="nf-filter-row" style={{ marginTop: "14px" }}>
        <button
          type="button"
          className={`nf-filter-chip${filter === "all" ? " nf-filter-chip--active" : ""}`}
          onClick={() => setFilter("all")}
        >
          Todos
        </button>

        <button
          type="button"
          className={`nf-filter-chip${filter === "pending" ? " nf-filter-chip--active" : ""}`}
          onClick={() => setFilter("pending")}
        >
          Por comprar
        </button>

        <button
          type="button"
          className={`nf-filter-chip${filter === "cart" ? " nf-filter-chip--active" : ""}`}
          onClick={() => setFilter("cart")}
        >
          Já no cesto
        </button>

        <button
          type="button"
          className={`nf-filter-chip${showSources ? " nf-filter-chip--active" : ""}`}
          onClick={() => setShowSources((current) => !current)}
        >
          {showSources ? "Ocultar refeições" : "Mostrar refeições"}
        </button>
      </div>

      {filteredItems.length === 0 ? (
        <p style={{ ...styles.empty, marginTop: "14px" }}>
          {shoppingList.length === 0
            ? "Sem itens na lista."
            : "Nenhum item corresponde ao filtro atual."}
        </p>
      ) : (
        <div className="nf-shopping-grid" style={{ marginTop: "14px" }}>
          {filteredItems.map((item) => {
            const key = `${item.ingredient_id}-${item.unit ?? ""}`;
            const isSaving = savingKey === key;

            return (
              <div
                key={key}
                className={`nf-shopping-card${item.in_cart ? " nf-shopping-card--in-cart" : ""}`}
              >
                <div className="nf-shopping-card-head">
                  <div>
                    <div className="nf-record-title">{item.ingredient_name}</div>
                    <div className="nf-card-body">
                      {showSources
                        ? `${item.sources.length} origem(ns) no plano`
                        : "Origens ocultas"}
                    </div>
                  </div>

                  <div className="nf-shopping-quantity">
                    {item.quantity ? item.quantity : "—"}
                    {item.unit ? ` ${item.unit}` : ""}
                  </div>
                </div>

                {showSources ? (
                  <div className="nf-pill-row" style={{ marginTop: "10px" }}>
                    {item.sources.map((source, index) => (
                      <span
                        key={`${source.recipe_id}-${index}`}
                        className="nf-score-pill"
                        title={`${source.plan_date} · ${source.meal_type} · ${source.recipe_name}`}
                      >
                        {source.plan_date} · {formatMealType(source.meal_type)} ·{" "}
                        {source.recipe_name}
                      </span>
                    ))}
                  </div>
                ) : null}

                <div className="nf-shopping-actions">
                  <span
                    className={`nf-shopping-state${item.in_cart ? " nf-shopping-state--done" : ""}`}
                  >
                    {item.in_cart ? "Já no cesto" : "Por comprar"}
                  </span>

                  <button
                    type="button"
                    className={`nf-filter-chip${item.in_cart ? " nf-filter-chip--active" : ""}`}
                    onClick={() => toggleInCart(item)}
                    disabled={isSaving}
                  >
                    {isSaving
                      ? "A guardar..."
                      : item.in_cart
                        ? "Marcar como por comprar"
                        : "Marcar como já no cesto"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}