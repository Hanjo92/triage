import os
import glob

doc_dir = r"c:\Projects\triage\docs"
extract_path = os.path.join(doc_dir, "all_docs_extracted.txt")

if not os.path.exists(extract_path):
    print("No extract found.")
    exit()

with open(extract_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('\\n', '\n')
parts = text.split("==================================================")

current_file = None
saved_files = 0

for part in parts:
    part = part.strip()
    if not part:
        continue
    if part.startswith("FILE:"):
        current_file = part.split("FILE:")[1].strip()
    elif current_file:
        md_name = current_file.replace('.docx', '.md')
        out_path = os.path.join(doc_dir, md_name)
        with open(out_path, 'w', encoding='utf-8') as out_f:
            title = md_name.replace('.md', '').replace('_', ' ').title()
            out_f.write(f"# {title}\n\n")
            out_f.write(part.strip() + "\n")
        saved_files += 1
        current_file = None

print(f"Saved {saved_files} md files.")

if saved_files > 5:
    for f in glob.glob(os.path.join(doc_dir, "*.docx")):
        try: os.remove(f)
        except: pass
    try: os.remove(extract_path)
    except: pass
