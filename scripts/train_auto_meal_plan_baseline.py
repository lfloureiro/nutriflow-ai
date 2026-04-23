import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.auto_meal_plan_baseline_training import (
    train_auto_meal_plan_baseline,
)


def print_confusion_matrix(labels: list[str], matrix: list[list[int]]) -> None:
    print("Confusion matrix:")
    print("labels:", labels)
    for row in matrix:
        print(" ", row)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Treina baselines de ML a partir do dataset exportado do auto-planeamento."
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
        default="accepted_as_suggested",
        help="Coluna alvo a usar. Por defeito: accepted_as_suggested",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.3,
        help="Mantido por compatibilidade; a avaliação passa a usar validação cruzada estratificada.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Seed para reprodutibilidade. Por defeito: 42",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    report_path, report = train_auto_meal_plan_baseline(
        dataset_path=args.dataset,
        target=args.target,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    print(f"Dataset: {report['dataset_path']}")
    print(f"Número de linhas: {report['row_count']}")
    print(f"Target: {report['target_column']}")
    print(f"Distribuição do target: {report['target_distribution']}")

    if report["dropped_numeric_features"]:
        print(
            "Features numéricas removidas por estarem vazias: "
            + ", ".join(report["dropped_numeric_features"])
        )

    if report["evaluation_strategy"]:
        print(
            f"Estratégia de avaliação: {report['evaluation_strategy']} "
            f"({report['cv_n_splits']} folds)"
        )

    if report["status"] != "ok":
        print(f"Treino ignorado: {report['status']}")
        if report["notes"]:
            for note in report["notes"]:
                print(f"- {note}")
        print(f"Relatório gravado em: {report_path}")
        return

    for result in report["model_results"]:
        print(
            f"[{result['model_name']}] "
            f"accuracy={result['accuracy']:.4f}±{result['accuracy_std']:.4f} "
            f"balanced_accuracy={result['balanced_accuracy']:.4f}±{result['balanced_accuracy_std']:.4f} "
            f"f1_weighted={result['f1_weighted']:.4f}±{result['f1_weighted_std']:.4f}"
        )
        print_confusion_matrix(
            result["confusion_matrix_labels"],
            result["confusion_matrix"],
        )

    if report["best_model"]:
        print(
            "Melhor modelo: "
            f"{report['best_model']['model_name']} "
            f"(balanced_accuracy={report['best_model']['balanced_accuracy']:.4f}±{report['best_model']['balanced_accuracy_std']:.4f})"
        )
        print_confusion_matrix(
            report["best_model"]["confusion_matrix_labels"],
            report["best_model"]["confusion_matrix"],
        )

    print(f"Relatório gravado em: {report_path}")


if __name__ == "__main__":
    main()