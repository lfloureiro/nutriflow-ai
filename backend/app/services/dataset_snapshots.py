import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.models.family_member import FamilyMember
from backend.app.models.household import Household
from backend.app.models.ingredient import Ingredient
from backend.app.models.meal_feedback import MealFeedback
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient
from backend.app.models.recipe_preference import RecipePreference
from backend.app.schemas.dataset_snapshot import DatasetSnapshotMetaRead

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "dataset_snapshots"

REQUIRED_DATA_KEYS = [
    "households",
    "family_members",
    "ingredients",
    "recipes",
    "recipe_ingredients",
    "meal_plan",
]

OPTIONAL_DATA_KEYS = [
    "feedback",
    "recipe_preferences",
]


def ensure_snapshot_dir() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_snapshot_name(name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_-]+", "-", name.strip())
    clean = clean.strip("-_")

    if not clean:
        raise ValueError("O nome do snapshot é inválido.")

    return clean


def validate_file_name(file_name: str) -> str:
    if Path(file_name).name != file_name:
        raise ValueError("Nome de ficheiro inválido.")

    if not file_name.endswith(".json"):
        raise ValueError("O snapshot tem de ser um ficheiro .json.")

    return file_name


def get_current_alembic_revision(db: Session) -> str | None:
    try:
        return db.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar_one_or_none()
    except Exception:
        return None


def build_snapshot_metadata(
    document: dict[str, Any],
    path: Path,
) -> DatasetSnapshotMetaRead:
    meta = document.get("meta", {})

    created_at = meta.get("created_at")
    if not created_at:
        created_at = datetime.fromtimestamp(
            path.stat().st_mtime,
            tz=timezone.utc,
        ).isoformat()

    return DatasetSnapshotMetaRead(
        file_name=path.name,
        snapshot_name=str(meta.get("snapshot_name") or path.stem),
        description=meta.get("description"),
        created_at=str(created_at),
        alembic_revision=meta.get("alembic_revision"),
        size_bytes=path.stat().st_size,
    )


def parse_datetime_value(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def serialize_dataset(db: Session) -> dict[str, list[dict[str, Any]]]:
    households = db.query(Household).order_by(Household.id.asc()).all()
    family_members = db.query(FamilyMember).order_by(FamilyMember.id.asc()).all()
    ingredients = db.query(Ingredient).order_by(Ingredient.id.asc()).all()
    recipes = db.query(Recipe).order_by(Recipe.id.asc()).all()
    recipe_ingredients = (
        db.query(RecipeIngredient).order_by(RecipeIngredient.id.asc()).all()
    )
    meal_plan_items = db.query(MealPlanItem).order_by(MealPlanItem.id.asc()).all()
    feedback_items = db.query(MealFeedback).order_by(MealFeedback.id.asc()).all()
    preference_items = (
        db.query(RecipePreference).order_by(RecipePreference.id.asc()).all()
    )

    return {
        "households": [
            {
                "id": item.id,
                "name": item.name,
            }
            for item in households
        ],
        "family_members": [
            {
                "id": item.id,
                "name": item.name,
                "household_id": item.household_id,
            }
            for item in family_members
        ],
        "ingredients": [
            {
                "id": item.id,
                "name": item.name,
            }
            for item in ingredients
        ],
        "recipes": [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
            }
            for item in recipes
        ],
        "recipe_ingredients": [
            {
                "id": item.id,
                "recipe_id": item.recipe_id,
                "ingredient_id": item.ingredient_id,
                "quantity": item.quantity,
                "unit": item.unit,
            }
            for item in recipe_ingredients
        ],
        "meal_plan": [
            {
                "id": item.id,
                "household_id": item.household_id,
                "plan_date": item.plan_date.isoformat(),
                "meal_type": item.meal_type,
                "notes": item.notes,
                "recipe_id": item.recipe_id,
            }
            for item in meal_plan_items
        ],
        "feedback": [
            {
                "id": item.id,
                "meal_plan_item_id": item.meal_plan_item_id,
                "family_member_id": item.family_member_id,
                "reaction": item.reaction,
                "note": item.note,
            }
            for item in feedback_items
        ],
        "recipe_preferences": [
            {
                "id": item.id,
                "household_id": item.household_id,
                "family_member_id": item.family_member_id,
                "recipe_id": item.recipe_id,
                "rating": item.rating,
                "note": item.note,
                "updated_at": item.updated_at.isoformat(),
            }
            for item in preference_items
        ],
    }


def count_dataset(dataset: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    result = {
        "households": len(dataset["households"]),
        "family_members": len(dataset["family_members"]),
        "ingredients": len(dataset["ingredients"]),
        "recipes": len(dataset["recipes"]),
        "recipe_ingredients": len(dataset["recipe_ingredients"]),
        "meal_plan": len(dataset["meal_plan"]),
    }

    if "feedback" in dataset:
        result["feedback"] = len(dataset["feedback"])

    if "recipe_preferences" in dataset:
        result["recipe_preferences"] = len(dataset["recipe_preferences"])

    return result


def export_dataset_snapshot(
    db: Session,
    snapshot_name: str,
    description: str | None = None,
) -> DatasetSnapshotMetaRead:
    ensure_snapshot_dir()

    safe_name = sanitize_snapshot_name(snapshot_name)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    file_name = f"{timestamp}_{safe_name}.json"
    file_path = SNAPSHOT_DIR / file_name

    document = {
        "meta": {
            "snapshot_name": snapshot_name.strip(),
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "alembic_revision": get_current_alembic_revision(db),
        },
        "data": serialize_dataset(db),
    }

    file_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return build_snapshot_metadata(document, file_path)


def list_dataset_snapshots() -> list[DatasetSnapshotMetaRead]:
    ensure_snapshot_dir()

    snapshots: list[DatasetSnapshotMetaRead] = []

    for path in sorted(
        SNAPSHOT_DIR.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            snapshots.append(build_snapshot_metadata(document, path))
        except Exception:
            continue

    return snapshots


def load_snapshot_document(file_name: str) -> tuple[Path, dict[str, Any]]:
    ensure_snapshot_dir()

    valid_name = validate_file_name(file_name)
    file_path = SNAPSHOT_DIR / valid_name

    if not file_path.exists():
        raise FileNotFoundError("Snapshot não encontrado.")

    try:
        document = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("O ficheiro de snapshot não contém JSON válido.") from exc

    if not isinstance(document, dict):
        raise ValueError("Formato de snapshot inválido.")

    if "data" not in document or not isinstance(document["data"], dict):
        raise ValueError("O snapshot não contém a secção 'data' válida.")

    return file_path, document


def validate_snapshot_dataset(dataset: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_DATA_KEYS if key not in dataset]
    if missing:
        raise ValueError(
            f"O snapshot não contém as secções obrigatórias: {missing}"
        )

    for key in REQUIRED_DATA_KEYS:
        if not isinstance(dataset[key], list):
            raise ValueError(f"A secção '{key}' do snapshot é inválida.")

    for key in OPTIONAL_DATA_KEYS:
        if key in dataset and not isinstance(dataset[key], list):
            raise ValueError(f"A secção '{key}' do snapshot é inválida.")


def clear_all_data(db: Session) -> None:
    db.query(MealFeedback).delete(synchronize_session=False)
    db.query(RecipePreference).delete(synchronize_session=False)
    db.query(MealPlanItem).delete(synchronize_session=False)
    db.query(RecipeIngredient).delete(synchronize_session=False)
    db.query(FamilyMember).delete(synchronize_session=False)
    db.query(Household).delete(synchronize_session=False)
    db.query(Recipe).delete(synchronize_session=False)
    db.query(Ingredient).delete(synchronize_session=False)


def resolve_legacy_household_id(dataset: dict[str, list[dict[str, Any]]]) -> int | None:
    meal_plan_rows = dataset["meal_plan"]

    if all("household_id" in row for row in meal_plan_rows):
        return None

    household_rows = dataset["households"]
    if len(household_rows) == 1:
        return int(household_rows[0]["id"])

    raise ValueError(
        "O snapshot usa meal_plan antigo sem household_id. Com vários agregados isso é ambíguo e não pode ser restaurado automaticamente."
    )


def restore_dataset_rows(db: Session, dataset: dict[str, list[dict[str, Any]]]) -> None:
    legacy_household_id = resolve_legacy_household_id(dataset)

    for row in dataset["households"]:
        db.add(
            Household(
                id=row["id"],
                name=row["name"],
            )
        )
    db.flush()

    for row in dataset["family_members"]:
        db.add(
            FamilyMember(
                id=row["id"],
                name=row["name"],
                household_id=row["household_id"],
            )
        )
    db.flush()

    for row in dataset["ingredients"]:
        db.add(
            Ingredient(
                id=row["id"],
                name=row["name"],
            )
        )
    db.flush()

    for row in dataset["recipes"]:
        db.add(
            Recipe(
                id=row["id"],
                name=row["name"],
                description=row.get("description"),
            )
        )
    db.flush()

    for row in dataset["recipe_ingredients"]:
        db.add(
            RecipeIngredient(
                id=row["id"],
                recipe_id=row["recipe_id"],
                ingredient_id=row["ingredient_id"],
                quantity=row.get("quantity"),
                unit=row.get("unit"),
            )
        )
    db.flush()

    for row in dataset["meal_plan"]:
        db.add(
            MealPlanItem(
                id=row["id"],
                household_id=row.get("household_id", legacy_household_id),
                plan_date=date.fromisoformat(row["plan_date"]),
                meal_type=row["meal_type"],
                notes=row.get("notes"),
                recipe_id=row["recipe_id"],
            )
        )
    db.flush()

    for row in dataset.get("feedback", []):
        db.add(
            MealFeedback(
                id=row["id"],
                meal_plan_item_id=row["meal_plan_item_id"],
                family_member_id=row["family_member_id"],
                reaction=row["reaction"],
                note=row.get("note"),
            )
        )
    db.flush()

    for row in dataset.get("recipe_preferences", []):
        db.add(
            RecipePreference(
                id=row["id"],
                household_id=row["household_id"],
                family_member_id=row["family_member_id"],
                recipe_id=row["recipe_id"],
                rating=row["rating"],
                note=row.get("note"),
                updated_at=parse_datetime_value(row.get("updated_at")),
            )
        )
    db.flush()


def restore_dataset_snapshot(
    db: Session,
    file_name: str,
    require_schema_match: bool = True,
) -> tuple[DatasetSnapshotMetaRead, dict[str, int]]:
    file_path, document = load_snapshot_document(file_name)

    meta = document.get("meta", {})
    dataset = document["data"]

    validate_snapshot_dataset(dataset)

    snapshot_revision = meta.get("alembic_revision")
    current_revision = get_current_alembic_revision(db)

    if require_schema_match and snapshot_revision != current_revision:
        raise ValueError(
            "A revisão Alembic do snapshot não coincide com a revisão atual da base de dados."
        )

    clear_all_data(db)
    restore_dataset_rows(db, dataset)

    return build_snapshot_metadata(document, file_path), count_dataset(dataset)