import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import SessionLocal
from backend.app.services.auto_meal_plan_training_dataset import (
    export_auto_plan_training_dataset,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Exporta um dataset CSV para treino a partir dos eventos do auto-planeamento."
    )
    parser.add_argument(
        "--household-id",
        type=int,
        default=None,
        help="Filtra por um agregado específico.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Caminho completo do CSV de saída.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    db = SessionLocal()
    try:
        path, row_count = export_auto_plan_training_dataset(
            db,
            household_id=args.household_id,
            output_path=args.output,
        )
    finally:
        db.close()

    print(f"Dataset exportado com sucesso: {path}")
    print(f"Número de linhas: {row_count}")


if __name__ == "__main__":
    main()