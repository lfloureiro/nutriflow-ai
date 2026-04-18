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

export function HouseholdView({
  households,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [newHouseholdName, setNewHouseholdName] = useState("");
  const [selectedHouseholdId, setSelectedHouseholdId] = useState("");
  const [editHouseholdName, setEditHouseholdName] = useState("");

  const [newMemberName, setNewMemberName] = useState("");
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [editMemberName, setEditMemberName] = useState("");

  const [creatingHousehold, setCreatingHousehold] = useState(false);
  const [savingHousehold, setSavingHousehold] = useState(false);
  const [deletingHousehold, setDeletingHousehold] = useState(false);

  const [creatingMember, setCreatingMember] = useState(false);
  const [savingMember, setSavingMember] = useState(false);
  const [deletingMember, setDeletingMember] = useState(false);

  const [localMessage, setLocalMessage] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const selectedHousehold = useMemo(
    () =>
      households.find((household) => String(household.id) === selectedHouseholdId) ??
      null,
    [households, selectedHouseholdId]
  );

  const selectedMember = useMemo(
    () =>
      selectedHousehold?.members.find(
        (member) => String(member.id) === selectedMemberId
      ) ?? null,
    [selectedHousehold, selectedMemberId]
  );

  useEffect(() => {
    setEditHouseholdName(selectedHousehold?.name ?? "");
    setSelectedMemberId("");
    setEditMemberName("");
  }, [selectedHouseholdId, selectedHousehold]);

  useEffect(() => {
    setEditMemberName(selectedMember?.name ?? "");
  }, [selectedMember]);

  async function handleCreateHousehold(e: React.FormEvent) {
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
      setCreatingHousehold(true);

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
      setCreatingHousehold(false);
    }
  }

  async function handleUpdateHousehold() {
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
      setSavingHousehold(true);

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

      setLocalMessage("Agregado atualizado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingHousehold(false);
    }
  }

  async function handleDeleteHousehold() {
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
      setDeletingHousehold(true);

      const res = await fetch(`${API_BASE_URL}/households/${selectedHousehold.id}`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível apagar o agregado."));
      }

      setSelectedHouseholdId("");
      setSelectedMemberId("");
      setEditHouseholdName("");
      setEditMemberName("");
      setLocalMessage("Agregado apagado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeletingHousehold(false);
    }
  }

  async function handleCreateMember(e: React.FormEvent) {
    e.preventDefault();

    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedHousehold) {
      setLocalError("Seleciona primeiro um agregado.");
      return;
    }

    if (!newMemberName.trim()) {
      setLocalError("O nome do membro é obrigatório.");
      return;
    }

    try {
      setCreatingMember(true);

      const res = await fetch(
        `${API_BASE_URL}/households/${selectedHousehold.id}/members`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: newMemberName.trim(),
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível criar o membro."));
      }

      setNewMemberName("");
      setSelectedMemberId(String(data.id));
      setLocalMessage("Membro criado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setCreatingMember(false);
    }
  }

  async function handleUpdateMember() {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedHousehold) {
      setLocalError("Seleciona um agregado.");
      return;
    }

    if (!selectedMember) {
      setLocalError("Seleciona um membro.");
      return;
    }

    if (!editMemberName.trim()) {
      setLocalError("O nome do membro é obrigatório.");
      return;
    }

    try {
      setSavingMember(true);

      const res = await fetch(
        `${API_BASE_URL}/households/${selectedHousehold.id}/members/${selectedMember.id}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: editMemberName.trim(),
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível atualizar o membro."));
      }

      setLocalMessage("Membro atualizado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSavingMember(false);
    }
  }

  async function handleDeleteMember() {
    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedHousehold) {
      setLocalError("Seleciona um agregado.");
      return;
    }

    if (!selectedMember) {
      setLocalError("Seleciona um membro.");
      return;
    }

    const confirmed = window.confirm(
      `Queres apagar o membro "${selectedMember.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingMember(true);

      const res = await fetch(
        `${API_BASE_URL}/households/${selectedHousehold.id}/members/${selectedMember.id}`,
        {
          method: "DELETE",
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível apagar o membro."));
      }

      setSelectedMemberId("");
      setEditMemberName("");
      setLocalMessage("Membro apagado com sucesso.");
      await onSuccess();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setDeletingMember(false);
    }
  }

  const busy =
    creatingHousehold ||
    savingHousehold ||
    deletingHousehold ||
    creatingMember ||
    savingMember ||
    deletingMember;

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Agregados e membros</h2>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div style={{ display: "grid", gap: "24px" }}>
        <form style={styles.form} onSubmit={handleCreateHousehold}>
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
                      onClick={handleUpdateHousehold}
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
                      onClick={handleDeleteHousehold}
                      disabled={busy}
                    >
                      Apagar
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </div>

        <form style={styles.form} onSubmit={handleCreateMember}>
          <h3 style={styles.formTitle}>Novo membro</h3>

          <select
            style={styles.select}
            value={selectedHouseholdId}
            onChange={(e) => setSelectedHouseholdId(e.target.value)}
            disabled={busy}
          >
            <option value="">Seleciona o agregado</option>
            {households.map((household) => (
              <option key={household.id} value={household.id}>
                {household.name}
              </option>
            ))}
          </select>

          <input
            style={styles.input}
            placeholder="Nome do membro"
            value={newMemberName}
            onChange={(e) => setNewMemberName(e.target.value)}
            disabled={busy || !selectedHousehold}
          />

          <button style={styles.button} type="submit" disabled={busy || !selectedHousehold}>
            Criar membro
          </button>
        </form>

        <div style={styles.form}>
          <h3 style={styles.formTitle}>Editar ou apagar membro</h3>

          {!selectedHousehold ? (
            <p style={styles.empty}>Seleciona um agregado para gerir os membros.</p>
          ) : selectedHousehold.members.length === 0 ? (
            <p style={styles.empty}>Este agregado ainda não tem membros.</p>
          ) : (
            <>
              <select
                style={styles.select}
                value={selectedMemberId}
                onChange={(e) => setSelectedMemberId(e.target.value)}
                disabled={busy}
              >
                <option value="">Seleciona um membro</option>
                {selectedHousehold.members.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.name}
                  </option>
                ))}
              </select>

              {selectedMember && (
                <>
                  <input
                    style={styles.input}
                    value={editMemberName}
                    onChange={(e) => setEditMemberName(e.target.value)}
                    disabled={busy}
                  />

                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      style={styles.button}
                      onClick={handleUpdateMember}
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
                      onClick={handleDeleteMember}
                      disabled={busy}
                    >
                      Apagar
                    </button>
                  </div>
                </>
              )}

              <div
                style={{
                  padding: "12px",
                  border: "1px solid #374151",
                  borderRadius: "10px",
                  background: "#111827",
                }}
              >
                <strong>Membros atuais:</strong>
                <ul style={{ margin: "8px 0 0 18px" }}>
                  {selectedHousehold.members.map((member) => (
                    <li key={member.id}>{member.name}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}