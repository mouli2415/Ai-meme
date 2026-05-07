# """
# model.py
# --------
# Loads the fine-tuned (or base) distilgpt2 and generates meme captions.

# Public API:
#     generate_caption(topic: str) -> str
# """

# import os
# import re
# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM

# # ── Config ────────────────────────────────────────────────────────────────────
# FINE_TUNED_DIR = "./meme_model"
# BASE_MODEL     = "distilgpt2"
# MAX_NEW_TOKENS = 40
# TEMPERATURE    = 0.9
# TOP_K          = 50
# TOP_P          = 0.95
# # ─────────────────────────────────────────────────────────────────────────────

# # Module-level singletons — loaded once, reused on every request
# _tokenizer = None
# _model     = None


# def _load_model():
#     """Load tokenizer + model into module globals (called once)."""
#     global _tokenizer, _model

#     if _model is not None:
#         return

#     if os.path.isdir(FINE_TUNED_DIR):
#         model_path = FINE_TUNED_DIR
#         print(f"[model] Loading fine-tuned model from: {model_path}")
#     else:
#         model_path = BASE_MODEL
#         print(f"[model] Fine-tuned model not found — using base {BASE_MODEL}")
#         print(f"[model] Tip: run  python train.py  for better captions")

#     _tokenizer = AutoTokenizer.from_pretrained(model_path)
#     _tokenizer.pad_token = _tokenizer.eos_token

#     _model = AutoModelForCausalLM.from_pretrained(model_path)
#     _model.eval()
#     print("[model] Model loaded ✓")


# def _clean(raw: str) -> str:
#     """
#     Post-process raw generated text into a clean meme caption.
#       1. Remove special tokens
#       2. Collapse whitespace
#       3. Take the first complete sentence
#       4. Capitalise + ensure terminal punctuation
#       5. Hard-limit to 120 characters
#     """
#     text = raw.strip().replace("<|endoftext|>", "").strip()
#     text = re.sub(r"\s+", " ", text)

#     # Split on sentence-ending punctuation and take the first sentence
#     parts = re.split(r"(?<=[.!?])\s+", text)
#     text = parts[0].strip() if parts else text

#     # Add punctuation if missing
#     if text and text[-1] not in ".!?":
#         text += "."

#     # Capitalise first letter
#     if text:
#         text = text[0].upper() + text[1:]

#     # Hard limit
#     if len(text) > 120:
#         text = text[:117].rstrip() + "…"

#     return text


# def generate_caption(topic: str) -> str:
#     """
#     Generate a meme caption for the given topic.

#     Args:
#         topic: plain-text topic, e.g. "exam stress"

#     Returns:
#         A clean caption string, e.g. "When exam stress hits and you blank."
#     """
#     _load_model()

#     prompt = f"When {topic} happens, me:"
#     print(f"[model] Prompt: {prompt}")

#     inputs = _tokenizer(
#         prompt,
#         return_tensors="pt",
#         padding=True,
#         truncation=True,
#         max_length=32,
#     )

#     with torch.no_grad():
#         output_ids = _model.generate(
#             inputs["input_ids"],
#             attention_mask=inputs["attention_mask"],
#             max_new_tokens=MAX_NEW_TOKENS,
#             temperature=TEMPERATURE,
#             top_k=TOP_K,
#             top_p=TOP_P,
#             do_sample=True,
#             pad_token_id=_tokenizer.eos_token_id,
#         )

#     full_text = _tokenizer.decode(output_ids[0], skip_special_tokens=True)
#     print(f"[model] Raw output : {full_text}")

#     # Strip the prompt prefix
#     caption_raw = (
#         full_text[len(prompt):].strip()
#         if full_text.startswith(prompt)
#         else full_text.strip()
#     )

#     if not caption_raw or len(caption_raw) < 5:
#         caption_raw = f"When {topic} hits different."

#     caption = _clean(caption_raw)
#     print(f"[model] Caption    : {caption}")
#     return caption


import random

captions = [
    "When assignment deadline is tomorrow.",
    "Me after debugging for 5 hours.",
    "POV: Teacher says surprise test.",
    "When WiFi stops during exam.",
    "Trying to act calm during viva.",
    "When code works on first try."
]

def generate_caption(topic: str) -> str:
    related = [
        f"When {topic} happens.",
        f"Me dealing with {topic}.",
        f"POV: {topic}.",
        f"When {topic} hits differently."
    ]

    all_captions = captions + related
    return random.choice(all_captions)