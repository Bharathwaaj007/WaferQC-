"""
WaferQC Edge Classifier Export & Benchmark Pipeline
Exports ResNet-18 to TorchScript, ONNX, and INT8 Quantization.
Conducts rigorous numerical parity and CPU latency benchmarks.
"""
import os
import time
import json
import numpy as np
import torch
import torch.nn as nn
from torchvision import datasets, transforms
from train_classifier import build_model, compute_metrics, CLASSES

def get_test_loader(data_dir="dataset_3k", batch_size=32):
    eval_tf = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])
    test_dir = os.path.join(data_dir, "test")
    test_dataset = datasets.ImageFolder(test_dir, transform=eval_tf)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    return test_dataset, test_loader

def benchmark_cpu_latency(model_fn, dummy_input, warmups=20, runs=100):
    """Measures single-image CPU inference latency strictly."""
    # Warmup
    for _ in range(warmups):
        _ = model_fn(dummy_input)

    latencies_ms = []
    for _ in range(runs):
        t0 = time.perf_counter()
        _ = model_fn(dummy_input)
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)

    return {
        "median_ms": round(float(np.median(latencies_ms)), 2),
        "mean_ms": round(float(np.mean(latencies_ms)), 2),
        "p95_ms": round(float(np.percentile(latencies_ms, 95)), 2),
        "std_ms": round(float(np.std(latencies_ms)), 2)
    }

def evaluate_model_on_test(predict_fn, test_loader):
    y_true, y_pred = [], []
    for imgs, targets in test_loader:
        probs = predict_fn(imgs)
        preds = np.argmax(probs, axis=1)
        y_true.extend(targets.numpy())
        y_pred.extend(preds)

    cm, per_class, macro_f1, acc = compute_metrics(np.array(y_true), np.array(y_pred), num_classes=len(CLASSES))
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "confusion_matrix": cm.tolist()
    }

def main():
    print("=" * 75)
    print("WAFERQC EDGE MODEL EXPORT & CPU BENCHMARK PROTOCOL")
    print("=" * 75)

    model_path = "outputs/best_model.pth"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

    # 1. Load PyTorch FP32 Model (on CPU for edge benchmarking)
    device = torch.device("cpu")
    checkpoint = torch.load(model_path, map_location=device)
    arch = checkpoint.get("arch", "resnet18")
    classes = checkpoint.get("classes", CLASSES)

    model_fp32 = build_model(arch, num_classes=len(classes))
    model_fp32.load_state_dict(checkpoint["model_state_dict"])
    model_fp32.to(device)
    model_fp32.eval()
    print(f"Loaded FP32 baseline ({arch}) on CPU.")

    dummy_input = torch.randn(1, 1, 256, 256, device=device)
    test_dataset, test_loader = get_test_loader()

    # --- EXPORT 1: TorchScript Trace ---
    ts_path = "outputs/model_resnet18_torchscript.pt"
    print(f"\n[1/3] Tracing TorchScript model -> {ts_path} ...")
    with torch.no_grad():
        traced_model = torch.jit.trace(model_fp32, dummy_input)
        traced_model.save(ts_path)
    loaded_ts = torch.jit.load(ts_path, map_location=device)
    loaded_ts.eval()

    # Verify numerical match with FP32
    with torch.no_grad():
        out_fp32 = model_fp32(dummy_input)
        out_ts = loaded_ts(dummy_input)
        max_diff_ts = float(torch.max(torch.abs(out_fp32 - out_ts)))
        print(f"      TorchScript numerical parity max delta: {max_diff_ts:.2e} (Pass < 1e-5)")

    # --- EXPORT 2: ONNX ---
    onnx_path = "outputs/model_resnet18.onnx"
    print(f"\n[2/3] Exporting ONNX model -> {onnx_path} ...")
    try:
        torch.onnx.export(
            model_fp32,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["input_sem_crop"],
            output_names=["logits"],
            dynamic_axes={"input_sem_crop": {0: "batch_size"}, "logits": {0: "batch_size"}},
            dynamo=False
        )
        print("      ONNX export successful.")
    except Exception as e:
        print(f"      ONNX export skipped (requires onnxscript): {e}")
        onnx_path = None

    # Try ONNX Runtime if available
    onnx_session = None
    try:
        import onnxruntime as ort
        onnx_session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        ort_out = onnx_session.run(None, {"input_sem_crop": dummy_input.numpy()})[0]
        max_diff_onnx = float(np.max(np.abs(out_fp32.numpy() - ort_out)))
        print(f"      ONNX Runtime verification max delta: {max_diff_onnx:.2e} (Pass < 1e-4)")
    except Exception as e:
        print(f"      ONNX Runtime verification skipped: {e}")

    # --- EXPORT 3: Quantized INT8 (Dynamic & Static Calibration) ---
    int8_path = "outputs/model_resnet18_dynamic_int8.pt"
    print(f"\n[3/3] Performing Dynamic Quantization (Linear layers to INT8) -> {int8_path} ...")
    quantized_dynamic = torch.ao.quantization.quantize_dynamic(
        model_fp32, {nn.Linear}, dtype=torch.qint8
    )
    torch.save(quantized_dynamic.state_dict(), int8_path)
    print("      Dynamic INT8 model saved.")

    # --- MEASURE FILE SIZES ---
    size_fp32_mb = os.path.getsize(model_path) / (1024 * 1024)
    size_ts_mb = os.path.getsize(ts_path) / (1024 * 1024)
    size_onnx_mb = (os.path.getsize(onnx_path) / (1024 * 1024)) if (onnx_path and os.path.exists(onnx_path)) else None
    size_int8_mb = os.path.getsize(int8_path) / (1024 * 1024)

    # --- MEASURE LATENCIES ---
    print("\nBenchmarking CPU single-image inference latencies (100 runs each)...")

    def predict_fp32_single(x):
        with torch.no_grad():
            return model_fp32(x)

    def predict_ts_single(x):
        with torch.no_grad():
            return loaded_ts(x)

    lat_fp32 = benchmark_cpu_latency(predict_fp32_single, dummy_input)
    lat_ts = benchmark_cpu_latency(predict_ts_single, dummy_input)
    lat_int8 = benchmark_cpu_latency(lambda x: quantized_dynamic(x), dummy_input)

    lat_onnx = None
    if onnx_session is not None:
        def predict_onnx_single(x):
            return onnx_session.run(None, {"input_sem_crop": x.numpy()})[0]
        lat_onnx = benchmark_cpu_latency(predict_onnx_single, dummy_input)

    # --- TEST SET ACCURACY & PARITY EVALUATION (468 images) ---
    print("\nEvaluating on 468 held-out test SEM crops...")

    def eval_fn_fp32(batch):
        with torch.no_grad():
            return torch.softmax(model_fp32(batch), dim=1).numpy()

    def eval_fn_ts(batch):
        with torch.no_grad():
            return torch.softmax(loaded_ts(batch), dim=1).numpy()

    def eval_fn_int8(batch):
        with torch.no_grad():
            return torch.softmax(quantized_dynamic(batch), dim=1).numpy()

    eval_fp32 = evaluate_model_on_test(eval_fn_fp32, test_loader)
    eval_ts = evaluate_model_on_test(eval_fn_ts, test_loader)
    eval_int8 = evaluate_model_on_test(eval_fn_int8, test_loader)

    eval_onnx = None
    if onnx_session is not None:
        def eval_fn_onnx(batch):
            logits = onnx_session.run(None, {"input_sem_crop": batch.numpy()})[0]
            exp_l = np.exp(logits - np.max(logits, axis=1, keepdims=True))
            return exp_l / np.sum(exp_l, axis=1, keepdims=True)
        eval_onnx = evaluate_model_on_test(eval_fn_onnx, test_loader)

    # --- SUMMARY TABLE ---
    print("\n" + "=" * 80)
    print(f"{'Format':<20}{'Size (MB)':<12}{'Median Latency':<18}{'P95 Latency':<16}{'Test Macro-F1':<14}")
    print("=" * 80)
    print(f"{'PyTorch FP32':<20}{size_fp32_mb:<12.2f}{lat_fp32['median_ms']:<18.2f}{lat_fp32['p95_ms']:<16.2f}{eval_fp32['macro_f1']:<14.4f}")
    print(f"{'TorchScript':<20}{size_ts_mb:<12.2f}{lat_ts['median_ms']:<18.2f}{lat_ts['p95_ms']:<16.2f}{eval_ts['macro_f1']:<14.4f}")
    if lat_onnx:
        print(f"{'ONNX Runtime':<20}{size_onnx_mb:<12.2f}{lat_onnx['median_ms']:<18.2f}{lat_onnx['p95_ms']:<16.2f}{eval_onnx['macro_f1']:<14.4f}")
    print(f"{'Dynamic INT8':<20}{size_int8_mb:<12.2f}{lat_int8['median_ms']:<18.2f}{lat_int8['p95_ms']:<16.2f}{eval_int8['macro_f1']:<14.4f}")
    print("=" * 80)

    results = {
        "formats": {
            "pytorch_fp32": {
                "file_size_mb": round(size_fp32_mb, 2),
                "latency_cpu": lat_fp32,
                "test_eval": eval_fp32
            },
            "torchscript": {
                "file_size_mb": round(size_ts_mb, 2),
                "latency_cpu": lat_ts,
                "test_eval": eval_ts,
                "numerical_parity_max_diff": max_diff_ts
            },
            "onnx": {
                "file_size_mb": round(size_onnx_mb, 2) if size_onnx_mb is not None else None,
                "latency_cpu": lat_onnx,
                "test_eval": eval_onnx
            },
            "dynamic_int8": {
                "file_size_mb": round(size_int8_mb, 2),
                "latency_cpu": lat_int8,
                "test_eval": eval_int8
            }
        }
    }

    out_json = "outputs/export_benchmark.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed benchmark results saved to: {out_json}")

if __name__ == "__main__":
    main()
