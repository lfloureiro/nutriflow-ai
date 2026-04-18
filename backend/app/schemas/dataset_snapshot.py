from pydantic import BaseModel, Field


class DatasetSnapshotMetaRead(BaseModel):
    file_name: str
    snapshot_name: str
    description: str | None = None
    created_at: str
    alembic_revision: str | None = None
    size_bytes: int


class DatasetSnapshotExportRequest(BaseModel):
    snapshot_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class DatasetSnapshotExportResponse(BaseModel):
    message: str
    snapshot: DatasetSnapshotMetaRead


class DatasetSnapshotRestoreRequest(BaseModel):
    file_name: str = Field(..., min_length=1)
    require_schema_match: bool = True


class DatasetSnapshotRestoreResponse(BaseModel):
    message: str
    snapshot: DatasetSnapshotMetaRead
    counts: dict[str, int]