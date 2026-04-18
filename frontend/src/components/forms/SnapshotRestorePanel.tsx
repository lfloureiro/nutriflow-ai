import { useEffect, useMemo, useState } from "react";
import { styles } from "../styles";
import {
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

export function SnapshotRestorePanel({
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [snapshots, setSnapshots] = useState<DatasetSnapshotMeta[]>([]);
  const [selectedFileName, setSelectedFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [restoring, setRestoring] = useState(false);

  const selectedSnapshot = useMemo(
    () => snapshots.find((item) => item.file_name === selectedFileName) ?? null,
    [snapshots, selectedFileName]
  );

  async function refreshSnapshots() {
    try {
      setLoading(true);

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
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshSnapshots();
  }, []);

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
      setRestoring(true);

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
      setRestoring(false);
    }
  }

  const busy = loading || restoring;

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Repor snapshot</h2>

      <p style={styles.info}>
        Seleciona o set point para o qual queres voltar.
      </p>

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
              border: "1px solid #374151",
              borderRadius: "10px",
              background: "#111827",
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
            onClick={refreshSnapshots}
            disabled={busy}
          >
            Atualizar lista
          </button>

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