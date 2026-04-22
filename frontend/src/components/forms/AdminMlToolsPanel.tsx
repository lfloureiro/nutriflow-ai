import { useState } from "react";
import { API_BASE_URL } from "../../config";
import { styles } from "../styles";

type Props = {
  onSuccess: () => Promise<void>;
  setFormMessage: (value: string | null) => void;
  setFormError: (value: string | null) => void;
};

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

export function AdminMlToolsPanel({
  onSuccess,
  setFormMessage,
  setFormError,
}: Props) {
  const [busyAction, setBusyAction] = useState<string | null>(null);

  async function handleExportDataset() {
    setFormMessage(null);
    setFormError(null);

    try {
      setBusyAction("export");

      const response = await fetch(
        `${API_BASE_URL}/admin-tools/ml/export-auto-plan-dataset`,
        {
          method: "POST",
        },
      );

      const data = await readJsonSafe(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível exportar o dataset."));
      }

      setFormMessage(
        `Dataset exportado com sucesso (${data.row_count} linhas).`,
      );
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Erro inesperado.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleTrainBaseline() {
    setFormMessage(null);
    setFormError(null);

    try {
      setBusyAction("train");

      const response = await fetch(
        `${API_BASE_URL}/admin-tools/ml/train-auto-plan-baseline`,
        {
          method: "POST",
        },
      );

      const data = await readJsonSafe(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível treinar o baseline."));
      }

      if (data.status === "ok" && data.best_model) {
        setFormMessage(
          `Treino concluído. Melhor modelo: ${data.best_model.model_name} ` +
            `(balanced_accuracy ${Number(data.best_model.balanced_accuracy).toFixed(4)}).`,
        );
      } else {
        const notes =
          Array.isArray(data.notes) && data.notes.length > 0
            ? ` ${data.notes.join(" ")}`
            : "";

        setFormMessage(`Treino processado com estado "${data.status}".${notes}`);
      }
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Erro inesperado.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleResetTestingState() {
    const confirmed = window.confirm(
      "Isto vai apagar o plano, eventos de auto-planeamento, feedback ligado às refeições, estados da lista de compras e todos os datasets/resultados ML gerados para testes. Queres continuar?",
    );

    if (!confirmed) {
      return;
    }

    setFormMessage(null);
    setFormError(null);

    try {
      setBusyAction("reset");

      const response = await fetch(
        `${API_BASE_URL}/admin-tools/testing/reset-meal-plan-ml-state`,
        {
          method: "POST",
        },
      );

      const data = await readJsonSafe(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Não foi possível limpar o estado de teste."));
      }

      await onSuccess();

      setFormMessage(
        `Limpeza concluída: ${data.deleted_meal_plan_count} refeições, ` +
          `${data.deleted_auto_event_count} eventos, ` +
          `${data.deleted_dataset_file_count} datasets e ` +
          `${data.deleted_result_file_count} relatórios removidos.`,
      );
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Erro inesperado.");
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <section style={styles.card}>
      <div className="nf-menu-panel-head">
        <div className="nf-kicker">AI e ML</div>
        <h2 style={styles.sectionTitle}>Ferramentas de teste e treino</h2>
        <p className="nf-menu-panel-text">
          Exporta o dataset supervisionado, corre o baseline ML e limpa o plano e
          os artefactos gerados durante os testes.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gap: "12px",
          marginTop: "14px",
        }}
      >
        <button
          type="button"
          style={styles.button}
          onClick={handleExportDataset}
          disabled={busyAction !== null}
        >
          {busyAction === "export" ? "A exportar dataset..." : "Exportar dataset ML"}
        </button>

        <button
          type="button"
          style={styles.button}
          onClick={handleTrainBaseline}
          disabled={busyAction !== null}
        >
          {busyAction === "train" ? "A treinar baseline..." : "Treinar baseline ML"}
        </button>

        <button
          type="button"
          style={{
            ...styles.button,
            background: "#7f1d1d",
            border: "1px solid #991b1b",
          }}
          onClick={handleResetTestingState}
          disabled={busyAction !== null}
        >
          {busyAction === "reset"
            ? "A limpar plano e artefactos..."
            : "Limpar plano + datasets/resultados de teste"}
        </button>
      </div>
    </section>
  );
}