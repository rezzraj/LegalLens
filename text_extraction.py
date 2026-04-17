from embedding_gemma import embedding_doc
import pymupdf4llm
import re
import numpy as np
import json

full_text = pymupdf4llm.to_markdown(
    "it_act_2000_updated____trimmed.pdf",
    use_ocr=False,
    header=False,
    footer=False,
)


lines = full_text.split("\n")
clean_lines = []

for line in lines:
    line = line.strip()

    if not line:
        continue

    # remove page numbers
    if re.fullmatch(r"\d+", line):
        continue

    # line like * * * * * remove
    if re.fullmatch(r"(\*\s*){3,}", line):
        continue

    # remove footnote
    if re.match(r"^\d+\.\s+(Subs\.|Ins\.|The word|The words|Clause|Omitted)", line):
        continue

    clean_lines.append(line)

clean_text = "\n".join(clean_lines)

# remove inline footnote markers like 1[
clean_text = re.sub(r"\b\d+\[", "[", clean_text)

# normalize spaces/newlines
clean_text = re.sub(r"[ \t]+", " ", clean_text)
clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)
# remove fake image note
clean_text = re.sub(r"\*\*==>.*?omitted <==\*\*", "", clean_text)
# turn (_1_) style into (1)
clean_text = re.sub(r"_([^_]+)_", r"\1", clean_text)

# remove footnote lines that start with >
clean_text = re.sub(r"^>\s*\d+\..*$", "", clean_text, flags=re.MULTILINE)

# remove other blockquote markers like > [
clean_text = re.sub(r"^>\s*", "", clean_text, flags=re.MULTILINE)

# remove inline references like [1]
clean_text = re.sub(r"\[\d+\]", "", clean_text)

# normalize blank lines
clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)



chapters = re.split(
    r'(?=^##\s*CHAPTER\s*[IVXLC\d]+\b|^##\s*CHAPTER[IVXLC\d]+\b)',
    clean_text,
    flags=re.MULTILINE
)
chapters = [ch.strip() for ch in chapters if ch.strip()]

def split_sections(ch):
    parts = re.split(r'(?=^\*\*\[?\d+[A-Z]?\.\s)', ch, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip() and not p.strip().startswith("## CHAPTER")]


sections_dict = {}
sec_id = 0

for ch in chapters:
    sec_list = split_sections(ch)

    chapter_name = ch.split("\n")[0].replace("##", "").strip()

    for sec in sec_list:
        sec = sec.strip()

        m = re.match(r'^\*\*(.+?)\*\*', sec)
        section_name = m.group(1).strip() if m else None

        sections_dict[sec_id] = {
            "chapter": chapter_name,
            "section": section_name,
            "text": sec
        }
        sec_id += 1


for key, value in sections_dict.items():
    text = value["text"]
    sections_dict[key]["embedding"] = embedding_doc(text)






# save metadata without embeddings
sections_meta = {}

for key, value in sections_dict.items():
    sections_meta[key] = {
        "chapter": value["chapter"],
        "section": value["section"],
        "text": value["text"]
    }

with open("sections.json", "w", encoding="utf-8") as f:
    json.dump(sections_meta, f, ensure_ascii=False, indent=2)

# save embeddings separately
embeddings = np.array([value["embedding"] for value in sections_dict.values()])
np.save("embeddings.npy", embeddings)
