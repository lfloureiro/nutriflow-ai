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
      setLocalError("O nome do agregado é obrigatório.");
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

      setNewHouseholdName("");
      setSelectedHouseholdId(String(data.id));
      setLocalMessage("Agregado criado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
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
      setLocalError("Seleciona um agregado.");
      return;
    }

    if (!editHouseholdName.trim()) {
      setLocalError("O nome do agregado é obrigatório.");
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
        throw new Error(getErrorMessage(data, "Não foi possível atualizar o agregado."));
      }

      setLocalMessage("Agregado atualizado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
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
      setLocalError("Seleciona um agregado.");
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

      setSelectedHouseholdId("");
      setEditHouseholdName("");
      setLocalMessage("Agregado apagado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeleting(false);
    }
  }

  const busy = creating || saving || deleting;

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Gerir agregados</h2>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div style={{ display: "grid", gap: "24px" }}>
        <form style={styles.form} onSubmit={handleCreate}>
          <h3 style={styles.formTitle}>Novo agregado</h3>

          <input
            style={styles.input}
            placeholder="Nome do agregado"
            value={newHouseholdName}
            onChange={(e) => setNewHouseholdName(e.target.value)}
            disabled={busy}
          />

          <button style={styles.button} type="submit" disabled={busy}>
            Criar agregado
          </button>
        </form>

        <div style={styles.form}>
          <h3 style={styles.formTitle}>Editar ou apagar agregado</h3>

          {households.length === 0 ? (
            <p style={styles.empty}>Sem agregados.</p>
          ) : (
            <>
              <select
                style={styles.select}
                value={selectedHouseholdId}
                onChange={(e) => setSelectedHouseholdId(e.target.value)}
                disabled={busy}
              >
                <option value="">Seleciona um agregado</option>
                {households.map((household) => (
                  <option key={household.id} value={household.id}>
                    {household.name}
                  </option>
                ))}
              </select>

              {selectedHousehold && (
                <>
                  <input
                    style={styles.input}
                    value={editHouseholdName}
                    onChange={(e) => setEditHouseholdName(e.target.value)}
                    disabled={busy}
                  />

                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      style={styles.button}
                      onClick={handleUpdate}
                      disabled={busy}
                    >
                      Guardar
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
                      Apagar
                    </button>
                  </div>

                  <div
                    style={{
                      padding: "12px",
                      border: "1px solid #374151",
                      borderRadius: "10px",
                      background: "#111827",
                    }}
                  >
                    <strong>Membros neste agregado:</strong>{" "}
                    {selectedHousehold.members.length}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}