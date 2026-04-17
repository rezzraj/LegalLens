from embedding_gemma import embedding_doc
import json
import numpy as np

with open("sections_with_ques.json", "r", encoding="utf-8") as f:
    sections_meta = json.load(f)
embeddings_with_ques=[]
for i, values in sections_meta.items():
    embed_text=""
    embed_text+="chapter: "+(values.get("chapter") or "")+ "\n"
    embed_text+="section: "+(values.get("section") or "")+ "\n"
    embed_text+="text: "+(values.get("text") or "")+ "\n"
    embed_text+="questions: " +(values.get("questions") or "") + "\n"
    embeddings_with_ques.append(embedding_doc(embed_text))

    print(f"done key: {i}")


embeddings_with_ques=np.array(embeddings_with_ques)
np.save("embeddings_with_ques.npy", embeddings_with_ques)
