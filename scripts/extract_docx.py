import zipfile
import xml.etree.ElementTree as ET
import glob
import os

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        # Word text nodes are <w:t>
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = []
        for paragraph in tree.findall('.//w:p', namespaces):
            texts = [node.text for node in paragraph.findall('.//w:t', namespaces) if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except Exception as e:
        return f"Error reading {docx_path}: {e}"

with open('c:/Projects/triage/Docu/all_docs_extracted.txt', 'w', encoding='utf-8') as out_f:
    for docx_file in glob.glob('c:/Projects/triage/Docu/*.docx'):
        out_f.write(f"\\n{'='*50}\\n")
        out_f.write(f"FILE: {os.path.basename(docx_file)}\\n")
        out_f.write(f"{'='*50}\\n")
        text = extract_text_from_docx(docx_file)
        out_f.write(text + "\\n")
