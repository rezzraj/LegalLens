import contextlib
import os
import sys
import torch
import kagglehub
import json
import numpy as np
from embedding_gemma import embed_query, model1
import re




# Point Python to the cloned repo root
sys.path.append(os.path.join(os.path.dirname(__file__), "gemma_pytorch"))

from gemma.config import get_model_config
from gemma.model import GemmaForCausalLM

#print("cuda" if torch.cuda.is_available() else "cpu")

# Choose variant and device
VARIANT = "1b-it"
MACHINE_TYPE = "cuda" if torch.cuda.is_available() else "cpu"
CONFIG = VARIANT.split("-")[0]   # "1b"



# Loading the model weights
weights_dir = "model"
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


with open("sections_with_ques.json", "r", encoding="utf-8") as f:
    sections_meta = json.load(f)

embeddings = np.load("embeddings_with_ques.npy")
for key, item in sections_meta.items():
    sec = item.get("section", "") or ""
    match = re.match(r"^\s*(\d+[A-Za-z]?)\.", sec)
    item["section_id"] = match.group(1).lower() if match else None


def extract_section_ids(query):
    return re.findall(r"section\s*(\d+[a-z]?)", query.lower())



# Gemma chat formatting
USER_CHAT_TEMPLATE = "<start_of_turn>user\n{prompt}<end_of_turn><eos>\n"
MODEL_CHAT_TEMPLATE = "<start_of_turn>model\n"


def questions_generator(query):
    user_turn = USER_CHAT_TEMPLATE.format(prompt=f"""You are generating retrieval queries for a legal RAG system.

You will be given exactly ONE section text from the Information Technology Act, 2000.

Your task:
Generate realistic user questions and short search queries that can be answered ONLY by this exact section.

Strict rules:
- Stay fully grounded in the given section text only
- Do NOT generate questions about the whole IT Act unless this exact section is about that
- Do NOT generate general, broad, textbook, summary, or explanation-style questions
- Do NOT add any introduction like "Here are some questions"
- Do NOT number the output
- Output only queries, one per line
- Do NOT invent facts, penalties, rights, procedures, or meanings not written in the section
- Make every query directly useful for retrieval
- Keep queries natural and realistic, like what a real user might type
- Include both full questions and short keyword-style searches
- Include section-identification style queries like "which section covers ..."
- If the section contains punishment, fine, imprisonment, offence, contravention, authority, power, procedure, definition, authentication, signature, or jurisdiction, generate queries about those exact things only if they are present in the section
- Avoid vague questions like "What is the purpose of this section?" or "What does this section mean?"
- Avoid repetitive paraphrases that say the same thing again and again
- Prefer concrete legal retrieval phrases

Output format:
One query per line only

Good example 1:
Section text: **66. Computer related offences.** If any person, dishonestly or fraudulently, does any act referred to in section 43, he shall be punishable with imprisonment for a term which may extend to three years or with fine which may extend to five lakh rupees or with both.

Good output:
what is the punishment for computer related offences
fine for section 66
imprisonment under section 66
which section covers computer related offences
dishonestly doing acts referred in section 43 punishment
fraudulently doing acts under section 43
section 66 penalty
computer related offences jail time
five lakh fine under section 66
offence under section 66 IT Act

Good example 2:
Section text: **3. Authentication of electronic records.** Subject to this section, any subscriber may authenticate an electronic record by affixing his digital signature. Authentication shall be effected by the use of asymmetric crypto system and hash function...

Good output:
how are electronic records authenticated
digital signature for authentication of electronic records
which section covers authentication of electronic records
what is used to authenticate an electronic record
asymmetric crypto system and hash function in authentication
public key verification of electronic record
what is section 3 of IT Act
how does a subscriber authenticate an electronic record
authentication of electronic records using digital signature
hash function in electronic record authentication

Now generate queries for this section.

Section text:
{query}

Queries: """)

    full_prompt = user_turn + MODEL_CHAT_TEMPLATE

    print("\nGenerating...\n")

    with torch.no_grad():
        output = model.generate(
            full_prompt,
            device=device,
            output_len=500,
            temperature=0.2,
            top_p=0.95,
            top_k=64,
        )
    return output.split("<end_of_turn>")[0].strip()






def query_expander(query):
    user_turn = USER_CHAT_TEMPLATE.format(prompt=f"""Convert the user’s legal question into a short keyword-only search query for finding relevant sections in the IT Act.  
  
Rules:  
  
Output ONLY keywords  
Do not write full sentences  
Do not repeat the user’s question  
Do not explain anything  
Use exactly 10 important legal keywords  
The keywords must be highly relevant to the IT Act / cyber law context  
Include broader legal terms and specific issue terms to improve search recall  
Prefer terms that would help retrieve sections, offences, penalties, liability, rights, procedures, or exceptions  
Keep the query compact, dense, and search-friendly  
Do not add filler words  
Do not use punctuation unless necessary for legal terms  
Always make the keyword set more detailed and useful than the original question  
  
Good keyword style:  
  
specific offence + legal concept + relevant IT Act terms  
nouns and legal phrases only  
no verbs unless they are essential legal terms  
no quotation marks  
no commentary  
  
Examples:  
  
User: which section applies to hacking  
Keywords: hacking unauthorized access computer system data theft cyber offence penalty section  
  
User: what happens for cyber bullying  
Keywords: cyber bullying harassment stalking intimidation abuse online communication penalty section  
  
User: is sending obscene messages illegal  
Keywords: obscene messages indecent content online communication cyber offence punishment section  
  
User: what is the punishment for identity theft  
Keywords: identity theft impersonation password misuse fraud electronic record penalty section  
  
User: can someone be punished for spreading fake news online  
Keywords: fake news misinformation online publication defamation cyber offence liability section  
  
User: what applies to phishing emails  
Keywords: phishing fraud deceptive email unauthorized access identity theft cyber offence section  
  
User: is data privacy protected under the IT Act  
Keywords: privacy confidentiality personal data information security data protection liability section  
  
User: what is the law for leaking confidential data  
Keywords: confidential data disclosure privacy breach unauthorized access security offence section  
  
User: can a website be blocked by the government  
Keywords: website blocking government powers interception monitoring content removal section  
  
User: what is the rule for electronic signatures  
Keywords: electronic signature digital signature authentication validity record recognition section  
  
Now process the user input below:  
  
User:  
{query}  
  
Keywords: """)


    full_prompt = user_turn + MODEL_CHAT_TEMPLATE

    print("\nGenerating...\n")

    with torch.no_grad():
        output = model.generate(
            full_prompt,
            device=device,
            output_len=500,
            temperature=0.1,
            top_p=0.95,
            top_k=64,
        )
    return  output.split("<end_of_turn>")[0].strip()





def model_generate(x):


    while True:


        if x == "exit":
            break

        casual_responses = {
            "thanks": "You're welcome!",
            "thank you": "You're welcome!",
            "hi": "Hello!",
            "hello": "Hello!",
            "ok": "Alright!",
            "okay": "Alright!",
            "hey": "Hi!",
            "bye": "Goodbye!",
            "goodbye": "Goodbye!",
            "your amazing": "Glad to help you!",
            "wow": "glad you liked the answer!",
            "who are you" : "I am a chat bot trained on the Information and Technology ACT, 2000. I can answer questions related to the act, I was created by Akshit Raj.",
            "what do you do"  : "I am a chat bot trained on the Information and Technology ACT, 2000. I can answer questions related to the act.",
            "how can you help me?" : "I am a chat bot trained on the Information and Technology ACT, 2000. I can answer questions related to the act.",
            "what can you do" : "I am a chat bot trained on the Information and Technology ACT, 2000. I can answer questions related to the act.",
            "what ques can you answer" : "I am a chat bot trained on the Information and Technology ACT, 2000. I can answer questions related to the act.",
            "who created you?": "i was created by Akshit Raj",
            "who created you": "i was created by Akshit Raj",
            "who built you": "i was created by Akshit Raj",
            "who is akshit raj": "he is a second year student in niit university",
            "how can you help me": "I am a chat bot trained on the Information and Technology ACT, 2000. I can answer questions related to the act.",
            "what can you help me with": "i can help you on the Information and Technology ACT, 2000. I can answer questions related to the act, or to simplify just ask me about the digital law ",
            "wassup": "Hey! 👋",
            "wasshup": "Hey! 👋",
            "sup": "Hey! 👋",
            "yo": "Hey! 👋",
            "bro": "😂 what's up bro",
            "whats up?": "All good, how can i help you?",
        }

        if x.lower().strip() in casual_responses:
            return casual_responses[x.lower().strip()]









        top_3_sections = ""
        section_name_list = []

        section_ids = extract_section_ids(x)
        found_exact_match = False

        if section_ids:
            for i in section_ids:
                for key, item in sections_meta.items():
                    if item.get("section_id") == i:
                        found_exact_match = True
                        chapter_name = sections_meta[key].get("chapter") or "Unknown Chapter"
                        section_name = sections_meta[key].get("section") or "Unknown Section"
                        section_text = sections_meta[key].get("text") or ""
                        print(section_name or "Unknown Section")
                        section_name_list.append(section_name)

                        top_3_sections += "this section is from chapter no: " + chapter_name + "\n"
                        top_3_sections += "this section name is: " + section_name + "\n"
                        top_3_sections += "this is the section content: " + section_text + "\n"
                        break
            if not found_exact_match:
                return "I could not find that section in the Information Technology Act, 2000."




        else:

            search_query = x
            print(search_query)
            input_embedding = embed_query(search_query)
            embeddings_similarity = {}
            for i, emb in enumerate(embeddings):
                embeddings_similarity[i] = model1.similarity(input_embedding, emb)

            sorted_sim = dict(sorted(embeddings_similarity.items(), key=lambda p: p[1], reverse=True))
            top_score = float(list(sorted_sim.values())[0])
            if top_score < 0.4:
                user_turn1 = USER_CHAT_TEMPLATE.format(prompt=f"""{x}""")


                full_prompt = user_turn1 + MODEL_CHAT_TEMPLATE

                print("\nGenerating...\n")

                with torch.no_grad():
                    output = model.generate(
                        full_prompt,
                        device=device,
                        output_len=100,
                        temperature=0.4,
                        top_p=0.95,
                        top_k=64,
                    )
                output = output.split("<end_of_turn>")[0].strip()

                warning_message = "Not relevant to IT act or Low confidence from model"

                return warning_message + "\n\n" + output

            for i, (idx, score) in enumerate(sorted_sim.items()):
                if i < 3:
                    chapter_name = sections_meta[str(idx)].get("chapter") or "Unknown Chapter"
                    section_name = sections_meta[str(idx)].get("section") or "Unknown Section"
                    section_questions=sections_meta[str(idx)].get("questions") or "No questions available"
                    section_text = sections_meta[str(idx)].get("text") or ""
                    print(section_name or "Unknown Section")
                    section_name_list.append(section_name)


                    top_3_sections += "this section is from chapter no: " + chapter_name + "\n"
                    top_3_sections += "this section name is: " + section_name + "\n"
                    top_3_sections += "this is the section content: " + section_text + "\n"

                else:
                    break









        user_turn = USER_CHAT_TEMPLATE.format(prompt=f""" you are answering questions related to the information and technology act 2000
Answer only from the context below.
Do not define any term unless the definition is clearly written in the context.   
Do not add examples, categories, or meanings that are not explicitly supported by the context.
if user asks you to explain any section, for example "explain section 12" then u must explain the section in summarized form based on context and is easy to read ..
Context:
{top_3_sections}

answer the question below
Question: {x}""")



        full_prompt = user_turn + MODEL_CHAT_TEMPLATE

        print("\nGenerating...\n")

        with torch.no_grad():
            output = model.generate(
                full_prompt,
                device=device,
                output_len=270,
                temperature=0.1,
                top_p=0.95,
                top_k=64,
            )
        output = output.split("<end_of_turn>")[0].strip() +"\n" +"sections from the search :"

        j=[v for v in section_name_list]

        return output + "\n\n" , j


if __name__ == "__main__":


    while True:
        x = input("enter prompt, 'exit' to stop: ").strip()
        if x == "exit":
            break

        print(model_generate(x))

