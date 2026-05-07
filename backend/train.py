"""
train.py
--------
Fine-tunes distilgpt2 on dataset.txt.
Run ONCE before starting the Flask server.

    cd backend
    python train.py

Saves the fine-tuned model to ./meme_model/
"""

import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextDataset,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_MODEL   = "distilgpt2"
DATASET_FILE = "dataset.txt"
OUTPUT_DIR   = "./meme_model"
EPOCHS       = 2
BLOCK_SIZE   = 64
# ─────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 55)
    print("  AI Meme Generator — Fine-tuning distilgpt2")
    print("=" * 55)

    # 1. Tokenizer
    print("\n[1/4] Loading tokenizer …")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    print("      Tokenizer ready ✓")

    # 2. Base model
    print("\n[2/4] Loading base model …")
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    print("      Model ready ✓")

    # 3. Dataset
    print(f"\n[3/4] Loading dataset: {DATASET_FILE} …")
    train_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=DATASET_FILE,
        block_size=BLOCK_SIZE,
    )
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    print(f"      {len(train_dataset)} training blocks ready ✓")

    # 4. Train
    print(f"\n[4/4] Training for {EPOCHS} epoch(s) …")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        overwrite_output_dir=True,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=2,
        save_steps=500,
        save_total_limit=1,
        prediction_loss_only=True,
        logging_steps=10,
        no_cuda=not torch.cuda.is_available(),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )

    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"\n✅  Fine-tuned model saved to: {OUTPUT_DIR}")
    print("    You can now run:  python app.py")


if __name__ == "__main__":
    main()