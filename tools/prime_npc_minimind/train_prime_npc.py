#!/usr/bin/env python3
"""train_prime_npc.py — Entraînement SFT du micro-modèle PNJ Prime (Multivers LBG).

Charge les poids pré-entraînés MiniMind (full_sft_768.pth), entraîne sur les
571 dialogues multiversels des PNJ de Scrapaltai / Lost Heaven,
et sauvegarde les poids affinés prêts pour conversion GGUF.
"""

from __future__ import annotations

import os
import sys

# Compatibilité CPU Sandy Bridge / Xeon E5 (limiter MKL/OneDNN à AVX sans FMA/AVX2)
os.environ["ONEDNN_MAX_CPU_ISA"] = "AVX"
os.environ["MKL_DEBUG_CPU_TYPE"] = "4"
os.environ["MKL_ENABLE_INSTRUCTIONS"] = "AVX"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import time
from pathlib import Path

# Ajouter tools/minimind au pythonpath
MINIMIND_DIR = Path(__file__).resolve().parent.parent / "minimind"
sys.path.insert(0, str(MINIMIND_DIR))

import torch
from torch import optim
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

from model.model_minimind import MiniMindConfig, MiniMindForCausalLM
from dataset.lm_dataset import SFTDataset

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = str(BASE_DIR / "dataset" / "prime_npcs_sft.jsonl")
OUT_DIR = BASE_DIR / "out"
PRETRAIN_WEIGHT = str(MINIMIND_DIR / "out" / "full_sft_768.pth")
TOKENIZER_DIR = str(MINIMIND_DIR / "model")


def train() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Démarrage entraînement MiniMind PNJ Prime sur device: {device}")

    # 1. Config & Tokenizer
    lm_config = MiniMindConfig(hidden_size=768, num_hidden_layers=8, use_moe=False)
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_DIR)

    # 2. Modèle
    model = MiniMindForCausalLM(lm_config)
    if os.path.exists(PRETRAIN_WEIGHT):
        print(f"📦 Chargement des poids de base depuis {PRETRAIN_WEIGHT}...")
        weights = torch.load(PRETRAIN_WEIGHT, map_location=device)
        model.load_state_dict(weights, strict=False)
    else:
        print("⚠️ Aucun poids pré-entraîné trouvé, initialisation aléatoire.")

    # Convertir en float32 sur CPU pour éviter les sous-dépassements float16 (NaN)
    if device == "cpu":
        model = model.float()

    model = model.to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"🧠 Paramètres entraînables : {total_params / 1e6:.2f} M (~25M)")

    # 3. Dataset & Dataloader
    max_seq_len = 256
    batch_size = 4
    epochs = 1
    learning_rate = 5e-5

    train_ds = SFTDataset(DATASET_PATH, tokenizer, max_length=max_seq_len)
    loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    print(f"📚 Dataset chargé : {len(train_ds)} échantillons, {len(loader)} batches par époque")

    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)

    # 4. Boucle d'entraînement
    model.train()
    start_all = time.time()

    for epoch in range(epochs):
        epoch_start = time.time()
        total_loss = 0.0

        for step, (input_ids, labels) in enumerate(loader, start=1):
            input_ids = input_ids.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            res = model(input_ids, labels=labels)
            loss = res.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()

            if step % 25 == 0 or step == len(loader):
                avg_loss = total_loss / step
                print(f"  [Époque {epoch + 1}/{epochs}] Step {step}/{len(loader)} | Loss: {loss.item():.4f} (moyenne: {avg_loss:.4f})")

        print(f"✅ Époque {epoch + 1}/{epochs} terminée en {time.time() - epoch_start:.1f}s | Perte finale : {total_loss / len(loader):.4f}")

    # 5. Sauvegarde
    out_weight_path = OUT_DIR / "prime_npc_768.pth"
    torch.save(model.state_dict(), str(out_weight_path))
    print(f"🎉 Entraînement terminé en {time.time() - start_all:.1f}s !")
    print(f"💾 Poids sauvegardés dans : {out_weight_path}")


if __name__ == "__main__":
    train()
