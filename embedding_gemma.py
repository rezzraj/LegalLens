import os

import sys

print("RUNNING FILE:", __file__)
print("PYTHON:", sys.executable)
import torch
os.environ["HF_HUB_OFFLINE"] = "1"
from sentence_transformers import SentenceTransformer





device = "cuda" if torch.cuda.is_available() else "cpu"

model_path = "model_emb"




model1 = SentenceTransformer(
    model_path,
    device=device,
    local_files_only=True
)





sentences=["pedophiles exits","president of america"]

embeddings=model1.encode(sentences)
similarities=model1.similarity(embeddings[0],embeddings[1])




def embedding_doc(text):
    embeddings1=model1.encode(text,prompt_name="Retrieval-document")
    return embeddings1


def embed_query(text):
    return model1.encode(text, prompt_name="Retrieval-query", normalize_embeddings=True)

if __name__=="__main__":

    print(f"Device: {model1.device}")
    print("Total number of parameters in the model:", sum([p.numel() for _, p in model1.named_parameters()]))
    print(similarities.item())
