import torch

from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)


BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DATASET_PATH = "data/advanced_oss_dataset.jsonl"
OUTPUT_DIR = "models/qwen2_5_7b_oss_advanced_lora"


def format_example(example):
    prompt = example["prompt"]
    response = example["response"]

    text = f"""### Instruction:
You are an OSS compliance risk analysis assistant.
Analyze the package context and return only Risk and Reason.

### Input:
{prompt}

### Response:
{response}"""

    return {"text": text}


def main():
    print("Loading dataset...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    dataset = dataset.map(format_example)

    dataset = dataset.train_test_split(test_size=0.1, seed=42)

    train_dataset = dataset["train"]
    eval_dataset = dataset["test"]

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL,
        trust_remote_code=True,
    )

    tokenizer.pad_token = tokenizer.eos_token

    print("Loading model in 4-bit...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=1024,
            padding="max_length",
        )

    print("Tokenizing...")
    train_dataset = train_dataset.map(tokenize, batched=True)
    eval_dataset = eval_dataset.map(tokenize, batched=True)

    train_dataset = train_dataset.remove_columns(
        [col for col in train_dataset.column_names if col not in ["input_ids", "attention_mask"]]
    )

    eval_dataset = eval_dataset.remove_columns(
        [col for col in eval_dataset.column_names if col not in ["input_ids", "attention_mask"]]
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=2,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        logging_steps=20,
        eval_steps=100,
        save_steps=100,
        save_total_limit=2,
        eval_strategy="steps",
        save_strategy="steps",
        fp16=True,
        bf16=False,
        optim="paged_adamw_8bit",
        report_to="none",
        gradient_checkpointing=True,
        max_grad_norm=0.3,
        warmup_ratio=0.03,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    print("Starting training...")
    trainer.train()

    print("Saving LoRA adapter...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"Saved advanced adapter to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
