import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.auto_meal_plan_baseline_training import (
    GROUPED_EVALUATION_STRATEGY,
    train_auto_meal_plan_baseline,
)


def print_confusion_matrix(labels: list[str], matrix: list[list[int]]) -> None:
    print("Confusion matrix:")
    print("labels:", labels)
    for row in matrix:
        print(" ", row)


def print_interpretability(interpretability: dict | None) -> None:
    if not interpretability:
        return

    if interpretability["type"] == "logistic_regression_coefficients":
        if interpretability["mode"] == "binary":
            print(
                "Top features que empurram para a classe positiva "
                f"({interpretability['positive_class']}):"
            )
            for item in interpretability["top_positive_features"]:
                print(f"  + {item['feature']}: {item['value']:.4f}")

            print(
                "Top features que empurram contra a classe positiva "
                f"({interpretability['positive_class']}):"
            )
            for item in interpretability["top_negative_features"]:
                print(f"  - {item['feature']}: {item['value']:.4f}")
            return

        print("Top features por classe:")
        for class_info in interpretability["per_class"]:
            print(f"Classe: {class_info['class_name']}")
            print("  Mais positivas:")
            for item in class_info["top_positive_features"]:
                print(f"    + {item['feature']}: {item['value']:.4f}")
            print("  Mais negativas:")
            for item in class_info["top_negative_features"]:
                print(f"    - {item['feature']}: {item['value']:.4f}")
        return

    if interpretability["type"] == "random_forest_feature_importances":
        print("Top feature importances:")
        for item in interpretability["top_feature_importances"]:
            print(f"  * {item['feature']}: {item['value']:.4f}")


def print_model_results(model_results: list[dict]) -> None:
    for result in model_results:
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

        if result["fold_results"] and "test_group_count" in result["fold_results"][0]:
            print("Resumo dos folds agrupados:")
            for fold in result["fold_results"]:
                print(
                    f"  fold={fold['fold']} "
                    f"train_groups={fold['train_group_count']} "
                    f"test_groups={fold['test_group_count']}"
                )

        print_interpretability(result.get("interpretability"))
        print()


def print_feature_set_report(
    feature_set_report: dict,
    *,
    evaluation_strategy: str | None,
    cv_n_splits: int | None,
) -> None:
    print(f"Feature set: {feature_set_report['feature_set_label']}")

    if feature_set_report["excluded_features"]:
        print(
            "Features excluídas: "
            + ", ".join(feature_set_report["excluded_features"])
        )
    else:
        print("Features excluídas: nenhuma")

    print(
        f"Número de features usadas: {len(feature_set_report['feature_columns_used'])}"
    )

    if feature_set_report["dropped_numeric_features"]:
        print(
            "Features numéricas removidas por estarem vazias: "
            + ", ".join(feature_set_report["dropped_numeric_features"])
        )

    if evaluation_strategy:
        print(f"Estratégia de avaliação: {evaluation_strategy} ({cv_n_splits} folds)")

    print_model_results(feature_set_report["model_results"])

    if feature_set_report["best_model"]:
        best_model = feature_set_report["best_model"]
        print(
            "Melhor modelo deste feature set: "
            f"{best_model['model_name']} "
            f"(balanced_accuracy={best_model['balanced_accuracy']:.4f}±{best_model['balanced_accuracy_std']:.4f})"
        )
        print_confusion_matrix(
            best_model["confusion_matrix_labels"],
            best_model["confusion_matrix"],
        )
        print_interpretability(best_model.get("interpretability"))


def print_comparison_summary(comparison_summary: dict | None) -> None:
    if not comparison_summary:
        return

    print("Comparação entre variantes:")
    for item in comparison_summary["variants"]:
        print(
            f"- {item['feature_set_label']}: "
            f"melhor_modelo={item['best_model_name']} "
            f"balanced_accuracy={item['best_balanced_accuracy']:.4f}±{item['best_balanced_accuracy_std']:.4f} "
            f"f1_weighted={item['best_f1_weighted']:.4f}±{item['best_f1_weighted_std']:.4f}"
        )

    best_variant = comparison_summary["best_variant"]
    print(
        "Variante com melhor balanced_accuracy: "
        f"{best_variant['feature_set_label']} "
        f"({best_variant['best_model_name']}, "
        f"balanced_accuracy={best_variant['best_balanced_accuracy']:.4f}±{best_variant['best_balanced_accuracy_std']:.4f})"
    )


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
        help="Mantido por compatibilidade; a avaliação passa a usar validação cruzada.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Seed para reprodutibilidade. Por defeito: 42",
    )
    parser.add_argument(
        "--without-suggested-recipe-id",
        action="store_true",
        help="Treina o feature set principal sem a feature categorical suggested_recipe_id.",
    )
    parser.add_argument(
        "--compare-suggested-recipe-id",
        action="store_true",
        help="Corre a comparação lado a lado com e sem suggested_recipe_id no mesmo relatório.",
    )
    parser.add_argument(
        "--group-by-suggested-recipe-id",
        action="store_true",
        help="Usa folds agrupados por suggested_recipe_id para testar generalização para receitas não vistas.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    evaluation_strategy = (
        GROUPED_EVALUATION_STRATEGY
        if args.group_by_suggested_recipe_id
        else "stratified_kfold"
    )

    report_path, report = train_auto_meal_plan_baseline(
        dataset_path=args.dataset,
        target=args.target,
        test_size=args.test_size,
        random_state=args.random_state,
        include_suggested_recipe_id=not args.without_suggested_recipe_id,
        compare_suggested_recipe_id=args.compare_suggested_recipe_id,
        evaluation_strategy=evaluation_strategy,
    )

    print(f"Dataset: {report['dataset_path']}")
    print(f"Número de linhas: {report['row_count']}")
    print(f"Target: {report['target_column']}")
    print(f"Distribuição do target: {report['target_distribution']}")
    print(f"Estratégia global de avaliação: {report['evaluation_strategy']}")

    if report.get("grouping_feature"):
        print(
            f"Agrupamento: {report['grouping_feature']} "
            f"({report['group_count']} grupos)"
        )

    if report["status"] != "ok":
        print(f"Treino ignorado: {report['status']}")
        if report["notes"]:
            for note in report["notes"]:
                print(f"- {note}")
        print(f"Relatório gravado em: {report_path}")
        return

    feature_set_reports = report.get("feature_set_reports") or []
    if feature_set_reports:
        for index, feature_set_report in enumerate(feature_set_reports, start=1):
            if len(feature_set_reports) > 1:
                print()
                print(f"=== Variante {index}/{len(feature_set_reports)} ===")
            print_feature_set_report(
                feature_set_report,
                evaluation_strategy=report.get("evaluation_strategy"),
                cv_n_splits=report.get("cv_n_splits"),
            )

        if len(feature_set_reports) > 1:
            print()
            print_comparison_summary(report.get("comparison_summary"))
    else:
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

        print_model_results(report["model_results"])

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
            print_interpretability(report["best_model"].get("interpretability"))

    print(f"Relatório gravado em: {report_path}")


if __name__ == "__main__":
    main()