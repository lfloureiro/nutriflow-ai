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

export function FamilyMemberManageView({
  households,
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [selectedHouseholdId, setSelectedHouseholdId] = useState("");
  const [newMemberName, setNewMemberName] = useState("");
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [editMemberName, setEditMemberName] = useState("");

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

  const selectedMember = useMemo(
    () =>
      selectedHousehold?.members.find(
        (member) => String(member.id) === selectedMemberId
      ) ?? null,
    [selectedHousehold, selectedMemberId]
  );

  useEffect(() => {
    setSelectedMemberId("");
    setEditMemberName("");
  }, [selectedHouseholdId]);

  useEffect(() => {
    setEditMemberName(selectedMember?.name ?? "");
  }, [selectedMember]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();

    setLocalMessage(null);
    setLocalError(null);
    setFormMessage(null);
    setFormError(null);

    if (!selectedHousehold) {
      const message = "Seleciona primeiro um agregado.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    if (!newMemberName.trim()) {
      const message = "O nome do membro é obrigatório.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    try {
      setCreating(true);

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

      const message = "Membro criado com sucesso.";
      setNewMemberName("");
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

    if (!selectedMember) {
      const message = "Seleciona um membro.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    if (!editMemberName.trim()) {
      const message = "O nome do membro é obrigatório.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    try {
      setSaving(true);

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

      const message = "Membro atualizado com sucesso.";
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

    if (!selectedMember) {
      const message = "Seleciona um membro.";
      setLocalError(message);
      setFormError(message);
      return;
    }

    const confirmed = window.confirm(
      `Queres apagar o membro "${selectedMember.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(true);

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

      const message = "Membro apagado com sucesso.";
      setSelectedMemberId("");
      setEditMemberName("");
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
        <h2 style={styles.sectionTitle}>Gerir membros</h2>
        <p className="nf-menu-panel-text">
          Escolhe primeiro o agregado e depois cria, renomeia ou apaga membros.
        </p>
      </div>

      {localMessage && <p style={styles.success}>{localMessage}</p>}
      {localError && <p style={styles.error}>Erro: {localError}</p>}

      <div className="nf-panel-stack" style={{ marginTop: "14px" }}>
        {households.length === 0 ? (
          <p style={styles.empty}>Ainda não existem agregados.</p>
        ) : (
          <>
            <div className="nf-card-title">Selecionar agregado</div>

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
          </>
        )}

        {!selectedHousehold ? (
          <p style={styles.empty}>Seleciona um agregado para continuar.</p>
        ) : (
          <div className="nf-split-grid">
            <div className="nf-panel-stack">
              <form style={styles.form} onSubmit={handleCreate}>
                <div className="nf-card-title">Novo membro</div>

                <div className="nf-pill-row">
                  <span className="nf-context-meta-chip">
                    {selectedHousehold.name}
                  </span>
                </div>

                <input
                  style={styles.input}
                  placeholder="Nome do membro"
                  value={newMemberName}
                  onChange={(e) => setNewMemberName(e.target.value)}
                  disabled={busy}
                />

                <button style={styles.button} type="submit" disabled={busy}>
                  {creating ? "A criar..." : "Criar membro"}
                </button>
              </form>

              <div className="nf-panel-stack">
                <div className="nf-card-title">Membros existentes</div>

                {selectedHousehold.members.length === 0 ? (
                  <p style={styles.empty}>Este agregado ainda não tem membros.</p>
                ) : (
                  <div className="nf-entity-list">
                    {selectedHousehold.members.map((member) => {
                      const isActive = String(member.id) === selectedMemberId;

                      return (
                        <div
                          key={member.id}
                          className={`nf-entity-row${isActive ? " nf-entity-row--active" : ""}`}
                          role="button"
                          tabIndex={0}
                          onClick={() => setSelectedMemberId(String(member.id))}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              setSelectedMemberId(String(member.id));
                            }
                          }}
                          title={member.name}
                        >
                          <div className="nf-entity-row-main">
                            <div className="nf-entity-row-title">{member.name}</div>
                            <div className="nf-entity-row-meta">
                              ID {member.id}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            <div className="nf-panel-stack">
              <div className="nf-card-title">Editar membro selecionado</div>

              {!selectedMember ? (
                <p style={styles.empty}>
                  Seleciona um membro na lista para o editar ou apagar.
                </p>
              ) : (
                <>
                  <div className="nf-pill-row">
                    <span className="nf-context-meta-chip">
                      {selectedHousehold.name}
                    </span>
                    <span className="nf-context-meta-chip">
                      {selectedMember.name}
                    </span>
                  </div>

                  <input
                    style={styles.input}
                    value={editMemberName}
                    onChange={(e) => setEditMemberName(e.target.value)}
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
        )}
      </div>
    </section>
  );
}