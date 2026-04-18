import { API_BASE_URL } from "../config";

export type DatasetSnapshotMeta = {
  file_name: string;
  snapshot_name: string;
  description: string | null;
  created_at: string;
  alembic_revision: string | null;
  size_bytes: number;
};

type DatasetSnapshotExportResponse = {
  message: string;
  snapshot: DatasetSnapshotMeta;
};

type DatasetSnapshotRestoreResponse = {
  message: string;
  snapshot: DatasetSnapshotMeta;
  counts: Record<string, number>;
};

async function parseJsonResponse<T>(
  res: Response,
  fallbackMessage: string
): Promise<T> {
  const data = await res.json();

  if (!res.ok) {
    const detail =
      data &&
      typeof data === "object" &&
      "detail" in data &&
      typeof (data as { detail?: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : fallbackMessage;

    throw new Error(detail);
  }

  return data as T;
}

export async function listDatasetSnapshots(): Promise<DatasetSnapshotMeta[]> {
  const res = await fetch(`${API_BASE_URL}/bulk/dataset-snapshots/`);

  return parseJsonResponse<DatasetSnapshotMeta[]>(
    res,
    "Não foi possível listar os snapshots."
  );
}

export async function exportDatasetSnapshot(payload: {
  snapshot_name: string;
  description?: string | null;
}): Promise<DatasetSnapshotExportResponse> {
  const res = await fetch(`${API_BASE_URL}/bulk/dataset-snapshots/export`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<DatasetSnapshotExportResponse>(
    res,
    "Não foi possível criar o snapshot."
  );
}

export async function restoreDatasetSnapshot(payload: {
  file_name: string;
  require_schema_match?: boolean;
}): Promise<DatasetSnapshotRestoreResponse> {
  const res = await fetch(`${API_BASE_URL}/bulk/dataset-snapshots/restore`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<DatasetSnapshotRestoreResponse>(
    res,
    "Não foi possível repor o snapshot."
  );
}