from main import questions_generator
import json
with open("sections.json", "r", encoding="utf-8") as f:
    sections_meta = json.load(f)


for key, value in sections_meta.items():
    generator = questions_generator(value.get("text") or "Could not find any text")
    sections_meta[key]["questions"]= generator
    print("done key:",key)



with open("sections_with_ques.json", "w", encoding="utf-8") as f:
    json.dump(sections_meta, f, ensure_ascii=False, indent=2)




