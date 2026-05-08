import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)

# ── Config ─────────────────────────────────────────────────────────────────────

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"
OUTPUT_DIR = "adapters"
TRAIN_FILE = "train.jsonl"
VAL_FILE = "valid.jsonl"
MAX_SEQ_LENGTH = 512


# ── Load data ──────────────────────────────────────────────────────────────────

def load_jsonl(path: str) -> Dataset:
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return Dataset.from_list(records)


# ── Tokenize ───────────────────────────────────────────────────────────────────

def tokenize(examples, tokenizer):
    result = tokenizer(
        examples["text"],
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding=False,
    )
    result["labels"] = result["input_ids"].copy()
    return result


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    print("Loading model in 4-bit...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("Loading datasets...")
    train_ds = load_jsonl(TRAIN_FILE)
    val_ds = load_jsonl(VAL_FILE)

    train_ds = train_ds.map(lambda x: tokenize(x, tokenizer), batched=True, remove_columns=["text"])
    val_ds = val_ds.map(lambda x: tokenize(x, tokenizer), batched=True, remove_columns=["text"])

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=4,
        eval_strategy="steps",
        eval_steps=50,
        save_steps=100,
        logging_steps=25,
        learning_rate=2e-4,
        fp16=True,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        report_to="none",
        load_best_model_at_end=True,
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8),
    )

    print("Training...")
    trainer.train()

    print("Saving adapters...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Adapters saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()