# Llama 3.2 1B Instruct — ExecuTorch Export Protocol

## 1. Exporting on Laptop / Workstation (Recommended)
Exporting on an x86_64 host with ample RAM and GPU avoids out-of-memory errors on edge devices:

```bash
# In executorch repository root:
python -m examples.models.llama.export_llama \
  --checkpoint /path/to/Llama-3.2-1B-Instruct/consolidated.00.pth \
  --params /path/to/Llama-3.2-1B-Instruct/params.json \
  --output_dir ./models/ \
  -kv \
  --use_sdpa_with_kv_cache \
  -X \
  --dtype fp32 \
  -o llama3_2_1b_xnnpack_fp32.pte
```

## 2. Transferring to Raspberry Pi 5
```bash
scp llama3_2_1b_xnnpack_fp32.pte pi@<PI_IP>:~/wafer_sem/models/
scp /path/to/tokenizer.model pi@<PI_IP>:~/wafer_sem/models/
```

## 3. Benchmarking Inference on Pi 5 (Cores 2-3)
```bash
taskset -c 2,3 ~/executorch/build-xnnpack/examples/models/llama/llama_runner \
  --model_path ~/wafer_sem/models/llama3_2_1b_xnnpack_fp32.pte \
  --tokenizer_path ~/wafer_sem/models/tokenizer.model \
  --prompt "You are WaferQC Advisor. Respond with JSON: {\"analysis\": \"Bridge defect\"}" \
  --temperature 0.2 \
  --max_seq_len 256
```

Measure and record:
- **Time to First Token (TTFT)**
- **Tokens per Second (TPS)** (Design target: >= 4 tok/s on Cortex-A76)
- **Peak RSS RAM** (Design target: < 2.5 GB)
- **Cortex-A76 SoC Temperature** (`vcgencmd measure_temp`)
