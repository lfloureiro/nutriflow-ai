import { useEffect, useMemo, useState } from "react";
import { styles } from "../styles";
import {
  exportDatasetSnapshot,
  listDatasetSnapshots,
  restoreDatasetSnapshot,
  type DatasetSnapshotMeta,
} from "../../services/datasetSnapshots";

type Props = {
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

function formatSnapshotDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("pt-PT", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

export function DatasetSnapshotsPanel({
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [snapshots, setSnapshots] = useState<DatasetSnapshotMeta[]>([]);
  const [selectedFileName, setSelectedFileName] = useState("");
  const [snapshotName, setSnapshotName] = useState("");
  const [description, setDescription] = useState("");
  const [loadingList, setLoadingList] = useState(false);
  const [savingSnapshot, setSavingSnapshot] = useState(false);
  const [restoringSnapshot, setRestoringSnapshot] = useState(false);

  const selectedSnapshot = useMemo(
    () => snapshots.find((item) => item.file_name === selectedFileName) ?? null,
    [snapshots, selectedFileName]
  );

  async function refreshSnapshots() {
    try {
      setLoadingList(true);

      const data = await listDatasetSnapshots();
      setSnapshots(data);

      if (data.length > 0) {
        setSelectedFileName((current) =>
          current && data.some((item) => item.file_name === current)
            ? current
            : data[0].file_name
        );
      } else {
        setSelectedFileName("");
      }
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Erro inesperado ao listar snapshots."
      );
    } finally {
      setLoadingList(false);
    }
  }

  useEffect(() => {
    refreshSnapshots();
  }, []);

  async function handleCreateSnapshot() {
    setFormMessage(null);
    setFormError(null);

    if (!snapshotName.trim()) {
      setFormError("Indica um nome para o snapshot.");
      return;
    }

    try {
      setSavingSnapshot(true);

      const response = await exportDatasetSnapshot({
        snapshot_name: snapshotName.trim(),
        description: description.trim() || null,
      });

      setFormMessage(response.message);
      setSnapshotName("");
      setDescription("");

      await refreshSnapshots();
      setSelectedFileName(response.snapshot.file_name);
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Erro inesperado ao criar snapshot."
      );
    } finally {
      setSavingSnapshot(false);
    }
  }

  async function handleRestoreSnapshot() {
    setFormMessage(null);
    setFormError(null);

    if (!selectedFileName) {
      setFormError("Seleciona um snapshot para repor.");
      return;
    }

    const confirmed = window.confirm(
      "Isto vai substituir os dados atuais pelos dados do snapshot selecionado. Continuar?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setRestoringSnapshot(true);

      const response = await restoreDatasetSnapshot({
        file_name: selectedFileName,
        require_schema_match: true,
      });

      setFormMessage(response.message);
      await onSuccess();
      await refreshSnapshots();
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Erro inesperado ao repor snapshot."
      );
    } finally {
      setRestoringSnapshot(false);
    }
  }

  const busy = loadingList || savingSnapshot || restoringSnapshot;

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Snapshots de dados</h2>

      <p style={styles.info}>
        Guarda o estado atual da base de dados e repõe qualquer set point já criado.
      </p>

      <div style={styles.form}>
        <input
          style={styles.input}
          type="text"
          placeholder="Nome do snapshot"
          value={snapshotName}
          onChange={(e) => setSnapshotName(e.target.value)}
          disabled={busy}
        />

        <textarea
          style={{ ...styles.textarea, minHeight: "90px" }}
          placeholder="Descrição opcional"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={busy}
        />

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            style={styles.button}
            type="button"
            onClick={handleCreateSnapshot}
            disabled={busy}
          >
            Guardar snapshot atual
          </button>

          <button
            style={styles.button}
            type="button"
            onClick={refreshSnapshots}
            disabled={busy}
          >
            Atualizar lista
          </button>
        </div>
      </div>

      <div style={{ height: "16px" }} />

      <div style={styles.form}>
        <select
          style={styles.select}
          value={selectedFileName}
          onChange={(e) => setSelectedFileName(e.target.value)}
          disabled={busy || snapshots.length === 0}
        >
          {snapshots.length === 0 ? (
            <option value="">Sem snapshots disponíveis</option>
          ) : (
            snapshots.map((snapshot) => (
              <option key={snapshot.file_name} value={snapshot.file_name}>
                {snapshot.snapshot_name} — {formatSnapshotDate(snapshot.created_at)}
              </option>
            ))
          )}
        </select>

        {selectedSnapshot && (
          <div
            style={{
              padding: "12px",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: "10px",
            }}
          >
            <div>
              <strong>Ficheiro:</strong> {selectedSnapshot.file_name}
            </div>
            <div>
              <strong>Nome:</strong> {selectedSnapshot.snapshot_name}
            </div>
            <div>
              <strong>Descrição:</strong> {selectedSnapshot.description || "-"}
            </div>
            <div>
              <strong>Criado em:</strong> {formatSnapshotDate(selectedSnapshot.created_at)}
            </div>
            <div>
              <strong>Revisão Alembic:</strong>{" "}
              {selectedSnapshot.alembic_revision || "-"}
            </div>
          </div>
        )}

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            style={styles.button}
            type="button"
            onClick={handleRestoreSnapshot}
            disabled={busy || !selectedFileName}
          >
            Repor snapshot selecionado
          </button>
        </div>
      </div>
    </section>
  );
}