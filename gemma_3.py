import contextlib
import os
import sys
import torch
import kagglehub
import json
import numpy as np
from embedding_gemma import embed_query, model1



with open("sections.json", "r", encoding="utf-8") as f:
    sections_meta = json.load(f)

embeddings = np.load("embeddings.npy")



# Point Python to the cloned repo root
sys.path.append(r"C:\Users\akshi\PycharmProjects\Gemma-4\gemma_pytorch")

from gemma.config import get_model_config
from gemma.model import GemmaForCausalLM

print("cuda" if torch.cuda.is_available() else "cpu")

# Choose variant and device
VARIANT = "1b-it"
MACHINE_TYPE = "cuda" if torch.cuda.is_available() else "cpu"
CONFIG = VARIANT.split("-")[0]   # "1b"



# Download the OFFICIAL PYTORCH checkpoint, not transformers weights
weights_dir = kagglehub.model_download(f"google/gemma-3/pyTorch/gemma-3-{VARIANT}")
print("weights_dir:", weights_dir)

# Tokenizer and checkpoint
tokenizer_path = os.path.join(weights_dir, "tokenizer.model")
assert os.path.isfile(tokenizer_path), f"Tokenizer not found: {tokenizer_path}"

ckpt_path = os.path.join(weights_dir, "model.ckpt")
assert os.path.isfile(ckpt_path), f"PyTorch checkpoint not found: {ckpt_path}"

# Build config
model_config = get_model_config(CONFIG)
model_config.dtype = "float32" if MACHINE_TYPE == "cpu" else "float16"
model_config.tokenizer = tokenizer_path

@contextlib.contextmanager
def _set_default_tensor_type(dtype: torch.dtype):
    old_dtype = torch.get_default_dtype()
    torch.set_default_dtype(dtype)
    try:
        yield
    finally:
        torch.set_default_dtype(old_dtype)

device = torch.device(MACHINE_TYPE)

with _set_default_tensor_type(model_config.get_dtype()):
    model = GemmaForCausalLM(model_config)

    # Load checkpoint
    checkpoint = torch.load(ckpt_path, map_location="cpu")
    state_dict = checkpoint["model_state_dict"]
    model.load_state_dict(state_dict, strict=False)

    model = model.to(device).eval()

print("Model loading done.")

# Gemma chat formatting
USER_CHAT_TEMPLATE = "<start_of_turn>user\n{prompt}<end_of_turn><eos>\n"
MODEL_CHAT_TEMPLATE = "<start_of_turn>model\n"


history=[]

while True:
    x=input("enter prompt, 'exit' to stop:").strip()

    if x=="exit" :
        break

    input_embedding= embed_query(x)

    embeddings_similarity = {}
    for i, emb in enumerate(embeddings):
        embeddings_similarity[i] = model1.similarity(input_embedding, emb)

    sorted_sim=dict(sorted(embeddings_similarity.items(), key=lambda p: p[1], reverse=True))
    top_3_sections=""
    for i,(idx,score) in enumerate(sorted_sim.items()):
        if i <=2:
            top_3_sections += "this section is from chapter no: "+sections_meta[str(idx)]["chapter"] + "\n"
            top_3_sections += "this section name is:  "+sections_meta[str(idx)]["section"] + "\n"
            top_3_sections +="this is the section content: "+ sections_meta[str(idx)]["text"] + "\n\n"
        else:
            break

    user_turn = USER_CHAT_TEMPLATE.format(prompt=f"""Use the context below to answer the question.

If the answer is not in the context, say you could not find it in the provided sections.

Context:
{top_3_sections}

In your answer,provide a detailed explanation to the user's query and also mention the relevant section name from the context at the end of your answer.

Question:
{x}""")


    history.append(user_turn)

    history= history[-8:]

    full_prompt= "".join(history)+ MODEL_CHAT_TEMPLATE

    print("\nGenerating...\n")

    with torch.no_grad():
        output = model.generate(
            full_prompt,
            device=device,
            output_len=1000,
            temperature=0.7,
            top_p=0.95,
            top_k=64,
        )
    output = output.split("<end_of_turn>")[0].strip() + "<end_of_turn>\n"
    history.append(MODEL_CHAT_TEMPLATE+ output)

    print(output)




