import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";
import type { Household } from "../types";

type Props = {
  households: Household[];
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

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

export function HouseholdManageView({
  households,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [newHouseholdName, setNewHouseholdName] = useState("");
  const [selectedHouseholdId, setSelectedHouseholdId] = useState("");
  const [editHouseholdName, setEditHouseholdName] = useState("");

  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const selectedHousehold = useMemo(
    () =>
      households.find((household) => String(household.id) === selectedHouseholdId) ??
      null,
    [households, selectedHouseholdId]
  );

  useEffect(() => {
    setEditHouseholdName(selectedHousehold?.name ?? "");
  }, [selectedHousehold]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();

    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!newHouseholdName.trim()) {
      const message = "O nome do agregado é obrigatório.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    try {
      setCreating(true);

      const res = await fetch(`${API_BASE_URL}/households/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newHouseholdName.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível criar o agregado."));
      }

      const message = "Agregado criado com sucesso.";
      setNewHouseholdName("");
      setLocalMessage(message);
      setFormMessage(message);
      await onSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro inesperado.";
      setLocalError(message);
      setFormError(message);
    } finally {
      setCreating(false);
    }
  }

  async function handleUpdate() {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedHousehold) {
      const message = "Seleciona um agregado.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    if (!editHouseholdName.trim()) {
      const message = "O nome do agregado é obrigatório.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    try {
      setSaving(true);

      const res = await fetch(`${API_BASE_URL}/households/${selectedHousehold.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editHouseholdName.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          getErrorMessage(data, "Não foi possível atualizar o agregado.")
        );
      }

      const message = "Agregado atualizado com sucesso.";
      setLocalMessage(message);
      setFormMessage(message);
      await onSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro inesperado.";
      setLocalError(message);
      setFormError(message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedHousehold) {
      const message = "Seleciona um agregado.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    const confirmed = window.confirm(
      `Queres apagar o agregado "${selectedHousehold.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);

      const res = await fetch(`${API_BASE_URL}/households/${selectedHousehold.id}`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível apagar o agregado."));
      }

      const message = "Agregado apagado com sucesso.";
      setSelectedHouseholdId("");
      setEditHouseholdName("");
      setLocalMessage(message);
      setFormMessage(message);
      await onSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro inesperado.";
      setLocalError(message);
      setFormError(message);
    } finally {
      setDeleting(false);
    }
  }

  const busy = creating || saving || deleting;

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">Estrutura</div>
        <h2 style={styles.sectionTitle}>Gerir agregados</h2>
        <p className="nf-menu-panel-text">
          Cria novos agregados e mantém a lista atual organizada.
        </p>
      </div>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div className="nf-split-grid" style={{ marginTop: "14px" }}>
        <div className="nf-panel-stack">
          <div className="nf-card-title">Agregados existentes</div>

          {households.length === 0 ? (
            <p style={styles.empty}>Ainda não existem agregados.</p>
          ) : (
            <div className="nf-select-card-grid">
              {households.map((household) => {
                const isActive = String(household.id) === selectedHouseholdId;

                return (
                  <div
                    key={household.id}
                    className={`nf-select-card${isActive ? " nf-select-card--active" : ""}`}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedHouseholdId(String(household.id))}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedHouseholdId(String(household.id));
                      }
                    }}
                    title={household.name}
                  >
                    <div className="nf-entity-row-title">{household.name}</div>
                    <div className="nf-entity-row-meta">
                      {household.members.length} membro(s)
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="nf-panel-stack">
          <form style={styles.form} onSubmit={handleCreate}>
            <div className="nf-card-title">Novo agregado</div>

            <input
              style={styles.input}
              placeholder="Nome do agregado"
              value={newHouseholdName}
              onChange={(e) => setNewHouseholdName(e.target.value)}
              disabled={busy}
            />

            <button style={styles.button} type="submit" disabled={busy}>
              {creating ? "A criar..." : "Criar agregado"}
            </button>
          </form>

          <div className="nf-panel-stack">
            <div className="nf-card-title">Editar agregado selecionado</div>

            {!selectedHousehold ? (
              <p style={styles.empty}>
                Seleciona um agregado na lista para o editar ou apagar.
              </p>
            ) : (
              <>
                <div className="nf-pill-row">
                  <span className="nf-context-meta-chip">{selectedHousehold.name}</span>
                  <span className="nf-context-meta-chip">
                    {selectedHousehold.members.length} membro(s)
                  </span>
                </div>

                <input
                  style={styles.input}
                  value={editHouseholdName}
                  onChange={(e) => setEditHouseholdName(e.target.value)}
                  disabled={busy}
                />

                <div className="nf-actions-inline">
                  <button
                    type="button"
                    style={styles.button}
                    onClick={handleUpdate}
                    disabled={busy}
                  >
                    {saving ? "A guardar..." : "Guardar"}
                  </button>

                  <button
                    type="button"
                    style={{
                      ...styles.button,
                      background: "#7f1d1d",
                      border: "1px solid #991b1b",
                    }}
                    onClick={handleDelete}
                    disabled={busy}
                  >
                    {deleting ? "A apagar..." : "Apagar"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}