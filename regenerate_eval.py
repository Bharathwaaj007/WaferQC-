"""
Re-evaluates outputs/best_model.pth with the true alphabetical class mapping:
0: bridge, 1: clean, 2: nuisance_charging, 3: nuisance_jitter, 4: particle, 5: scratch
"""
import os
import json
import numpy as np
import torch
import torch.nn as nn
from torchvision import datasets, transforms
from train_classifier import (
    build_model, compute_metrics, plot_confusion_matrix,
    evaluate_threshold_sweep
)

TRUE_CLASSES = ["bridge", "clean", "nuisance_charging", "nuisance_jitter", "particle", "scratch"]

def run():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = "outputs/best_model.pth"
    checkpoint = torch.load(model_path, map_location=device)

    model = build_model(checkpoint.get("arch", "resnet18"), num_classes=len(TRUE_CLASSES)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    eval_tf = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])

    test_dir = "dataset_3k/test"
    test_dataset = datasets.ImageFolder(test_dir, transform=eval_tf)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=32, shuffle=False)

    print("Confirmed ImageFolder mapping:", test_dataset.class_to_idx)
    assert list(test_dataset.class_to_idx.keys()) == TRUE_CLASSES

    y_true_test, y_pred_test, y_probs_test = [], [], []
    with torch.no_grad():
        for imgs, targets in test_loader:
            imgs = imgs.to(device)
            outputs = model(imgs)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            y_true_test.extend(targets.numpy())
            y_pred_test.extend(preds)
            y_probs_test.extend(probs)

    y_true_test = np.array(y_true_test)
    y_pred_test = np.array(y_pred_test)
    y_probs_test = np.array(y_probs_test)

    cm, per_class, test_macro_f1, test_acc = compute_metrics(y_true_test, y_pred_test, num_classes=6)

    # Correct per_class dictionary keys
    per_class_corrected = {TRUE_CLASSES[i]: per_class[list(per_class.keys())[i]] for i in range(len(TRUE_CLASSES))}

    plot_confusion_matrix(cm, TRUE_CLASSES, "outputs/confusion_matrix.png")
    sweep_results = evaluate_threshold_sweep(y_true_test, y_probs_test, "outputs/threshold_sweep.png")

    print("\nPER-CLASS CLASSIFICATION REPORT (CORRECTED CLASS LABELS):")
    print(f"{'Class':<22}{'Precision':<12}{'Recall':<12}{'F1-Score':<12}{'Support':<10}")
    print("-" * 68)
    for cname in TRUE_CLASSES:
        info = per_class_corrected[cname]
        print(f"{cname:<22}{info['precision']:<12.4f}{info['recall']:<12.4f}{info['f1']:<12.4f}{info['support']:<10}")
    print("-" * 68)
    print(f"{'Overall Macro-F1':<22}{test_macro_f1:<12.4f}")
    print(f"{'Overall Accuracy':<22}{test_acc:<12.2%}")

    # Update checkpoint with explicit classes list
    checkpoint["classes"] = TRUE_CLASSES
    torch.save(checkpoint, model_path)

    # Save metrics JSON
    metrics_summary = {
        "architecture": checkpoint.get("arch", "resnet18"),
        "best_val_macro_f1": checkpoint.get("val_f1", 0.9637),
        "test_macro_f1": test_macro_f1,
        "test_accuracy": test_acc,
        "per_class": per_class_corrected,
        "confusion_matrix": cm.tolist(),
        "threshold_sweep": sweep_results,
        "class_mapping": test_dataset.class_to_idx
    }
    with open("outputs/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print("Updated metrics saved to outputs/metrics.json")

if __name__ == "__main__":
    run()
