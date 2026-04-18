from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.dataset_snapshot import (
    DatasetSnapshotExportRequest,
    DatasetSnapshotExportResponse,
    DatasetSnapshotMetaRead,
    DatasetSnapshotRestoreRequest,
    DatasetSnapshotRestoreResponse,
)
from backend.app.services.dataset_snapshots import (
    export_dataset_snapshot,
    list_dataset_snapshots,
    restore_dataset_snapshot,
)

router = APIRouter(prefix="/bulk/dataset-snapshots", tags=["dataset-snapshots"])


@router.get("/", response_model=list[DatasetSnapshotMetaRead])
def list_dataset_snapshots_route():
    return list_dataset_snapshots()


@router.post("/export", response_model=DatasetSnapshotExportResponse)
def export_dataset_snapshot_route(
    data: DatasetSnapshotExportRequest,
    db: Session = Depends(get_db),
):
    try:
        snapshot = export_dataset_snapshot(
            db,
            snapshot_name=data.snapshot_name,
            description=data.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DatasetSnapshotExportResponse(
        message="Snapshot criado com sucesso.",
        snapshot=snapshot,
    )


@router.post("/restore", response_model=DatasetSnapshotRestoreResponse)
def restore_dataset_snapshot_route(
    data: DatasetSnapshotRestoreRequest,
    db: Session = Depends(get_db),
):
    try:
        snapshot, counts = restore_dataset_snapshot(
            db,
            file_name=data.file_name,
            require_schema_match=data.require_schema_match,
        )
        db.commit()
    except FileNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao restaurar snapshot: {exc}",
        ) from exc

    return DatasetSnapshotRestoreResponse(
        message="Snapshot reposto com sucesso.",
        snapshot=snapshot,
        counts=counts,
    )