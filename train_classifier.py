"""
WaferQC PyTorch Defect Classifier Training & Evaluation Pipeline
Supports ResNet-18 and MobileNetV3-Small for 6-class SEM Defect Inspection.
"""
import os
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms, models

CLASSES = ["bridge", "clean", "nuisance_charging", "nuisance_jitter", "particle", "scratch"]

def get_transforms():
    train_transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])

    val_test_transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])

    return train_transform, val_test_transform

def build_model(arch: str = "resnet18", num_classes: int = 6):
    if arch == "resnet18":
        model = models.resnet18(weights=None)
        # Adapt conv1 for 1-channel grayscale input
        model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif arch == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(weights=None)
        # Adapt first conv for 1-channel grayscale
        orig_conv = model.features[0][0]
        model.features[0][0] = nn.Conv2d(1, orig_conv.out_channels, kernel_size=3, stride=2, padding=1, bias=False)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
    else:
        raise ValueError(f"Unsupported architecture: {arch}")
    return model

def compute_metrics(y_true, y_pred, num_classes=6):
    """Computes confusion matrix, per-class precision/recall/F1, and macro-F1."""
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1

    per_class = {}
    f1s = []
    for i in range(num_classes):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        f1s.append(f1)
        per_class[CLASSES[i]] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": int(np.sum(cm[i, :]))
        }

    macro_f1 = float(np.mean(f1s))
    accuracy = float(np.trace(cm) / np.sum(cm)) if np.sum(cm) > 0 else 0.0
    return cm, per_class, round(macro_f1, 4), round(accuracy, 4)

def plot_confusion_matrix(cm, class_names, out_path):
    plt.figure(figsize=(8, 7), dpi=150)
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Wafer Defect Classification — Test Confusion Matrix", fontsize=14, pad=15, fontweight="bold")
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=35, ha="right", fontsize=10)
    plt.yticks(tick_marks, class_names, fontsize=10)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            color = "white" if val > thresh else "black"
            plt.text(j, i, f"{val:d}", ha="center", va="center", color=color, fontweight="bold")

    plt.ylabel("True Class", fontsize=11, fontweight="bold")
    plt.xlabel("Predicted Class", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"Confusion matrix saved to: {out_path}")

def plot_training_curves(history, out_path):
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=150)

    # Loss
    ax1.plot(epochs, history["train_loss"], "b-o", label="Train Loss", linewidth=2)
    ax1.plot(epochs, history["val_loss"], "r--s", label="Val Loss", linewidth=2)
    ax1.set_title("Cross-Entropy Loss vs Epochs", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Epoch", fontsize=10)
    ax1.set_ylabel("Loss", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(fontsize=10)

    # Macro F1
    ax2.plot(epochs, history["train_f1"], "b-o", label="Train Macro-F1", linewidth=2)
    ax2.plot(epochs, history["val_f1"], "g--^", label="Val Macro-F1", linewidth=2)
    ax2.set_title("Macro-F1 Score vs Epochs", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Epoch", fontsize=10)
    ax2.set_ylabel("Macro-F1", fontsize=10)
    ax2.set_ylim([0.0, 1.05])
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(fontsize=10)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"Training curves saved to: {out_path}")

def evaluate_threshold_sweep(y_true, y_probs, out_path):
    thresholds = [0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90]
    accuracies = []
    abstain_rates = []

    print("\n--- CONFIDENCE THRESHOLD SWEEP (UNKNOWN / ABSTAIN POLICY) ---")
    print(f"{'Threshold':<12}{'Abstain Rate':<16}{'Coverage':<12}{'Abstain-Filtered Acc':<22}")
    print("-" * 62)

    for tau in thresholds:
        max_probs = np.max(y_probs, axis=1)
        preds = np.argmax(y_probs, axis=1)

        abstained_mask = max_probs < tau
        abstain_count = np.sum(abstained_mask)
        abstain_rate = abstain_count / len(y_true)

        retained_mask = ~abstained_mask
        if np.sum(retained_mask) > 0:
            retained_acc = np.mean(preds[retained_mask] == y_true[retained_mask])
        else:
            retained_acc = 1.0

        accuracies.append(retained_acc)
        abstain_rates.append(abstain_rate)
        print(f"{tau:<12.2f}{abstain_rate:<16.2%}{1.0 - abstain_rate:<12.2%}{retained_acc:<22.2%}")

    # Plot
    plt.figure(figsize=(8, 5), dpi=150)
    plt.plot(thresholds, [a * 100 for a in accuracies], "b-o", linewidth=2, label="Accuracy on Covered Images (%)")
    plt.plot(thresholds, [r * 100 for r in abstain_rates], "r--s", linewidth=2, label="Abstain Rate (UNKNOWN) (%)")
    plt.axvline(x=0.55, color="gray", linestyle=":", label="Production Operating Point (tau=0.55)")
    plt.title("Coverage vs Reliability: Confidence Threshold Sweep", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Confidence Rejection Threshold", fontsize=10)
    plt.ylabel("Percentage (%)", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"Threshold sweep plot saved to: {out_path}")

    return {
        "thresholds": thresholds,
        "accuracies": [round(float(a), 4) for a in accuracies],
        "abstain_rates": [round(float(r), 4) for r in abstain_rates]
    }

def train_and_eval(args):
    os.makedirs(args.out_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    train_tf, eval_tf = get_transforms()

    train_dir = os.path.join(args.data_dir, "train")
    val_dir = os.path.join(args.data_dir, "val")
    test_dir = os.path.join(args.data_dir, "test")

    train_dataset = datasets.ImageFolder(train_dir, transform=train_tf)
    val_dataset = datasets.ImageFolder(val_dir, transform=eval_tf)
    test_dataset = datasets.ImageFolder(test_dir, transform=eval_tf)

    print(f"Dataset loaded: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}")
    print(f"Class mapping: {train_dataset.class_to_idx}")

    # Weighted sampler to handle slight class imbalance
    class_counts = [0] * len(CLASSES)
    for _, target in train_dataset.samples:
        class_counts[target] += 1
    class_weights = [1.0 / max(1, c) for c in class_counts]
    sample_weights = [class_weights[target] for _, target in train_dataset.samples]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = build_model(args.arch, num_classes=len(CLASSES)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=3)

    best_val_f1 = -1.0
    best_model_path = os.path.join(args.out_dir, "best_model.pth")
    history = {"train_loss": [], "val_loss": [], "train_f1": [], "val_f1": []}

    print(f"\n--- COMMENCING TRAINING ({args.arch.upper()} for {args.epochs} EPOCHS) ---")
    for epoch in range(1, args.epochs + 1):
        # TRAIN
        model.train()
        train_loss = 0.0
        y_true_train, y_pred_train = [], []
        for imgs, targets in train_loader:
            imgs, targets = imgs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(targets)
            preds = torch.argmax(outputs, dim=1)
            y_true_train.extend(targets.cpu().numpy())
            y_pred_train.extend(preds.cpu().numpy())

        train_loss /= len(train_dataset)
        _, _, train_f1, train_acc = compute_metrics(np.array(y_true_train), np.array(y_pred_train))

        # VALIDATION
        model.eval()
        val_loss = 0.0
        y_true_val, y_pred_val = [], []
        with torch.no_grad():
            for imgs, targets in val_loader:
                imgs, targets = imgs.to(device), targets.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * len(targets)
                preds = torch.argmax(outputs, dim=1)
                y_true_val.extend(targets.cpu().numpy())
                y_pred_val.extend(preds.cpu().numpy())

        val_loss /= len(val_dataset)
        _, _, val_f1, val_acc = compute_metrics(np.array(y_true_val), np.array(y_pred_val))
        scheduler.step(val_f1)

        history["train_loss"].append(round(train_loss, 4))
        history["val_loss"].append(round(val_loss, 4))
        history["train_f1"].append(round(train_f1, 4))
        history["val_f1"].append(round(val_f1, 4))

        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] "
              f"Train Loss: {train_loss:.4f} | Train F1: {train_f1:.4f} | "
              f"Val Loss: {val_loss:.4f} | Val F1: {val_f1:.4f} | Val Acc: {val_acc:.2%}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save({
                "epoch": epoch,
                "arch": args.arch,
                "model_state_dict": model.state_dict(),
                "val_f1": val_f1,
                "classes": CLASSES,
                "class_to_idx": train_dataset.class_to_idx
            }, best_model_path)

    print(f"\nTraining Complete. Best Validation Macro-F1: {best_val_f1:.4f}")
    plot_training_curves(history, os.path.join(args.out_dir, "training_curves.png"))

    # TEST EVALUATION
    print("\n--- EVALUATING BEST MODEL ON HELD-OUT TEST SET (450 images) ---")
    checkpoint = torch.load(best_model_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    y_true_test, y_pred_test, y_probs_test = [], [] ,[]
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

    cm, per_class, test_macro_f1, test_acc = compute_metrics(y_true_test, y_pred_test)
    plot_confusion_matrix(cm, CLASSES, os.path.join(args.out_dir, "confusion_matrix.png"))
    sweep_results = evaluate_threshold_sweep(y_true_test, y_probs_test, os.path.join(args.out_dir, "threshold_sweep.png"))

    print("\nPER-CLASS CLASSIFICATION REPORT:")
    print(f"{'Class':<22}{'Precision':<12}{'Recall':<12}{'F1-Score':<12}{'Support':<10}")
    print("-" * 68)
    for cname in CLASSES:
        info = per_class[cname]
        print(f"{cname:<22}{info['precision']:<12.4f}{info['recall']:<12.4f}{info['f1']:<12.4f}{info['support']:<10}")
    print("-" * 68)
    print(f"{'Overall Macro-F1':<22}{test_macro_f1:<12.4f}")
    print(f"{'Overall Accuracy':<22}{test_acc:<12.2%}")

    # Save metrics JSON
    metrics_summary = {
        "architecture": args.arch,
        "epochs_trained": args.epochs,
        "best_val_macro_f1": best_val_f1,
        "test_macro_f1": test_macro_f1,
        "test_accuracy": test_acc,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "threshold_sweep": sweep_results,
        "training_history": history
    }

    metrics_path = os.path.join(args.out_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"Metrics saved to: {metrics_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default="dataset_3k")
    parser.add_argument("--arch", type=str, default="resnet18", choices=["resnet18", "mobilenet_v3_small"])
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out-dir", type=str, default="outputs")
    args = parser.parse_args()

    train_and_eval(args)
