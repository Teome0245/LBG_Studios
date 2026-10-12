#!/usr/bin/env python3
"""QLoRA Compagnon — base Huihui Gemma-4 E4B abliterated → adaptateur + merge.

À lancer sur .10 (GPU), dans le venv créé par setup_venv_ft_10.sh.

Exemple :
  source .venv-ft/bin/activate
  python train_qlora_e4b.py \\
    --data dataset/compagnon_style_v1.jsonl \\
    --out runs/e4b-v2 \\
    --max-steps 120
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


DEFAULT_HF = "huihui-ai/Huihui-gemma-4-E4B-it-abliterated"
DEFAULT_DATA = Path(__file__).resolve().parent / "dataset" / "compagnon_style_v1.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if isinstance(obj, dict) and isinstance(obj.get("messages"), list):
            rows.append(obj)
    if not rows:
        raise SystemExit(f"dataset vide: {path}")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="QLoRA Compagnon E4B")
    ap.add_argument("--model", default=os.environ.get("LBG_FT_HF_MODEL", DEFAULT_HF))
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--out", type=Path, default=Path("runs/e4b-v2"))
    ap.add_argument("--max-seq", type=int, default=2048)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--max-steps", type=int, default=0, help="0 = epochs only")
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--merge", action="store_true", help="merge LoRA → full weights in out/merged")
    ap.add_argument(
        "--smoke-4g",
        action="store_true",
        help="Profil GTX 1050 Ti 4Go : seq 512, r=8, offload, max-steps défaut 20",
    )
    args = ap.parse_args()

    if args.smoke_4g:
        if args.max_seq > 512:
            args.max_seq = 512
        if args.lora_r > 8:
            args.lora_r = 8
            args.lora_alpha = 16
        if not args.max_steps:
            args.max_steps = 20
        args.batch = 1
        args.grad_accum = max(args.grad_accum, 4)
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        print("profil smoke-4g activé:", vars(args))

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("torch manquant — lancer setup_venv_ft_10.sh") from exc

    if not torch.cuda.is_available():
        raise SystemExit("CUDA indisponible — ce script est pour .10 GPU")

    print("GPU:", torch.cuda.get_device_name(0), "VRAM_GB≈", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1))
    rows = load_jsonl(args.data)
    print(f"dataset {args.data} → {len(rows)} exemples")
    args.out.mkdir(parents=True, exist_ok=True)

    # --- Unsloth path (préféré) — skip en smoke-4g (trop gourmand / fragile) ---
    model = None
    tokenizer = None
    used_unsloth = False
    if not args.smoke_4g:
        try:
            from unsloth import FastLanguageModel  # type: ignore

            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=args.model,
                max_seq_length=args.max_seq,
                load_in_4bit=True,
                dtype=None,
            )
            model = FastLanguageModel.get_peft_model(
                model,
                r=args.lora_r,
                lora_alpha=args.lora_alpha,
                lora_dropout=0.0,
                target_modules=[
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ],
                use_gradient_checkpointing="unsloth",
            )
            used_unsloth = True
            print("backend: unsloth")
        except Exception as exc:
            print(f"unsloth indispo ({exc}) — fallback transformers+peft")
    else:
        print("smoke-4g: skip unsloth → transformers+peft")

    if not used_unsloth:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        max_memory = None
        device_map = "auto"
        if args.smoke_4g:
            # 1050 Ti 4Go : majority CPU offload, thin GPU slice
            max_memory = {0: "2800MiB", "cpu": "24GiB"}
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            quantization_config=bnb,
            device_map=device_map,
            max_memory=max_memory,
            trust_remote_code=True,
            dtype=torch.float16,
            low_cpu_mem_usage=True,
            offload_buffers=True if args.smoke_4g else False,
        )
        model = prepare_model_for_kbit_training(model)
        if hasattr(model, "gradient_checkpointing_enable"):
            model.gradient_checkpointing_enable()
        model = get_peft_model(
            model,
            LoraConfig(
                r=args.lora_r,
                lora_alpha=args.lora_alpha,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=[
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ],
            ),
        )
        print("backend: transformers+peft")

    assert model is not None and tokenizer is not None

    # Chat template → text
    def to_text(example: dict) -> str:
        msgs = example["messages"]
        if hasattr(tokenizer, "apply_chat_template"):
            return tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False
            )
        parts = []
        for m in msgs:
            parts.append(f"{m.get('role','').upper()}: {m.get('content','')}")
        return "\n".join(parts)

    from datasets import Dataset

    texts = [{"text": to_text(r)} for r in rows]
    ds = Dataset.from_list(texts)

    from trl import SFTTrainer, SFTConfig

    cfg_kwargs = dict(
        output_dir=str(args.out),
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        logging_steps=5,
        save_steps=50,
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",
        warmup_ratio=0.03,
        report_to=[],
    )
    if args.max_steps and args.max_steps > 0:
        cfg_kwargs["max_steps"] = args.max_steps
    else:
        cfg_kwargs["num_train_epochs"] = args.epochs

    try:
        sft_config = SFTConfig(**cfg_kwargs, dataset_text_field="text", max_seq_length=args.max_seq)
        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=ds,
            args=sft_config,
        )
    except TypeError:
        # Compat anciennes API TRL
        from transformers import TrainingArguments

        targs = TrainingArguments(**cfg_kwargs)
        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=ds,
            dataset_text_field="text",
            max_seq_length=args.max_seq,
            args=targs,
        )

    trainer.train()
    adapter_dir = args.out / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    print("saved adapter →", adapter_dir)

    meta = {
        "base_hf": args.model,
        "ollama_base": "huihui_ai/gemma-4-abliterated:E4b-qat",
        "tag_cible": "lbg-compagnon-e4b-v2",
        "n_examples": len(rows),
        "backend": "unsloth" if used_unsloth else "transformers+peft",
    }
    (args.out / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    if args.merge:
        print("merge LoRA → full weights (VRAM)…")
        if used_unsloth:
            from unsloth import FastLanguageModel  # type: ignore

            model.save_pretrained_merged(
                str(args.out / "merged"),
                tokenizer,
                save_method="merged_16bit",
            )
        else:
            merged = model.merge_and_unload()
            merged_dir = args.out / "merged"
            merged_dir.mkdir(parents=True, exist_ok=True)
            merged.save_pretrained(str(merged_dir))
            tokenizer.save_pretrained(str(merged_dir))
        print("merged →", args.out / "merged")
        print("Ensuite : convertir en GGUF (llama.cpp) puis deploy_compagnon_e2b_ft_to_111.sh --gguf …")

    print("DONE")


if __name__ == "__main__":
    main()
