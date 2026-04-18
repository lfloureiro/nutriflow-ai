import { useState } from "react";
import { styles } from "../styles";
import { exportDatasetSnapshot } from "../../services/datasetSnapshots";

type Props = {
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

export function SnapshotBackupPanel({
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [snapshotName, setSnapshotName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCreateSnapshot() {
    setFormMessage(null);
    setFormError(null);

    if (!snapshotName.trim()) {
      setFormError("Indica um nome para o snapshot.");
      return;
    }

    try {
      setLoading(true);

      const response = await exportDatasetSnapshot({
        snapshot_name: snapshotName.trim(),
        description: description.trim() || null,
      });

      setFormMessage(response.message);
      setSnapshotName("");
      setDescription("");

      await onSuccess();
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Erro inesperado ao criar snapshot."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={styles.card}>
      <h2 style={styles.sectionTitle}>Guardar snapshot</h2>

      <p style={styles.info}>
        Guarda o estado atual da base de dados como um novo set point.
      </p>

      <div style={styles.form}>
        <input
          style={styles.input}
          type="text"
          placeholder="Nome do snapshot"
          value={snapshotName}
          onChange={(e) => setSnapshotName(e.target.value)}
          disabled={loading}
        />

        <textarea
          style={{ ...styles.textarea, minHeight: "100px" }}
          placeholder="Descrição opcional"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={loading}
        />

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            style={styles.button}
            type="button"
            onClick={handleCreateSnapshot}
            disabled={loading}
          >
            Guardar snapshot
          </button>
        </div>
      </div>
    </section>
  );
}