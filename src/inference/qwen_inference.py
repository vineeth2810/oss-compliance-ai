import torch

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


BASE_MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
LORA_MODEL_PATH = "models/qwen2_5_7b_oss_advanced_lora"


print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)

print("Loading base model in 4-bit...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto"
)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(
    base_model,
    LORA_MODEL_PATH
)

model.eval()

print("Qwen2.5-7B OSS compliance model loaded.")


def build_prompt(scenario):
    return f"""
You are an OSS compliance risk analysis assistant.

Classify this scanner output.

{scenario}

Return exactly in this format:
Risk: <Low|Medium|High>
Reason: <one short sentence>

Do not omit "Risk:" or "Reason:".
""".strip()


def predict_risk(scenario):
    prompt = build_prompt(scenario)

    messages = [
        {"role": "user", "content": prompt}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=80,
        do_sample=False
    )

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True
    )

    return response.strip()