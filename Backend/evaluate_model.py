from typing import Dict, Any
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from utils import setup_logger

logger = setup_logger(__name__)


def evaluate_predictions(y_true, y_pred, y_prob=None) -> Dict[str, Any]:
    """Calculates classification evaluation metrics."""
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }

    if y_prob is not None:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))

    cm = confusion_matrix(y_true, y_pred)
    
    logger.info("\n--- Model Performance Evaluation ---")
    logger.info(f"Accuracy  : {metrics['accuracy']:.4f}")
    logger.info(f"Precision : {metrics['precision']:.4f}")
    logger.info(f"Recall    : {metrics['recall']:.4f}")
    logger.info(f"F1 Score  : {metrics['f1']:.4f}")
    if "roc_auc" in metrics:
        logger.info(f"ROC AUC   : {metrics['roc_auc']:.4f}")
    logger.info(f"Confusion Matrix:\n{cm}")
    logger.info(f"\nDetailed Report:\n{classification_report(y_true, y_pred)}")

    return metrics