import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.auto_meal_plan_model_publishing import (
    DEFAULT_PUBLISH_EVALUATION_STRATEGY,
    DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID,
    DEFAULT_PUBLISH_TARGET,
    publish_auto_meal_plan_model,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Treina e publica um modelo online para o auto-planeamento."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Caminho explícito para o CSV. Se não for dado, usa o mais recente em data/ml_datasets/.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=DEFAULT_PUBLISH_TARGET,
        help=f"Target a publicar. Por defeito: {DEFAULT_PUBLISH_TARGET}",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.3,
        help="Mantido por compatibilidade.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Seed para reprodutibilidade. Por defeito: 42",
    )
    parser.add_argument(
        "--include-suggested-recipe-id",
        action="store_true",
        default=DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID,
        help="Publica um modelo que também usa suggested_recipe_id como feature.",
    )
    parser.add_argument(
        "--evaluation-strategy",
        type=str,
        default=DEFAULT_PUBLISH_EVALUATION_STRATEGY,
        help=f"Estratégia de avaliação para escolher o modelo a publicar. Por defeito: {DEFAULT_PUBLISH_EVALUATION_STRATEGY}",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    model_path, report_path, metadata = publish_auto_meal_plan_model(
        dataset_path=args.dataset,
        target=args.target,
        test_size=args.test_size,
        random_state=args.random_state,
        include_suggested_recipe_id=args.include_suggested_recipe_id,
        evaluation_strategy=args.evaluation_strategy,
    )

    print(f"Modelo publicado em: {model_path}")
    print(f"Relatório base: {report_path}")
    print(f"Engine version: {metadata.get('engine_version')}")
    print(f"Model name: {metadata.get('model_name')}")
    print(f"Target: {metadata.get('target_column')}")
    print(f"Feature set: {metadata.get('feature_set_label')}")
    print(f"Evaluation strategy: {metadata.get('evaluation_strategy')}")
    print(f"Feature count: {metadata.get('feature_count')}")
    print(f"Published at: {metadata.get('published_at_utc')}")


if __name__ == "__main__":
    main()
