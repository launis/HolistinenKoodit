
from docx import Document
import re

doc = Document("Pääarviointikehote.docx")
full_text = '\n'.join([p.text for p in doc.paragraphs])

start_marker = "VAIHE 1:"
end_marker = "VAIHE 2:"

start_idx = full_text.find(start_marker)
end_idx = full_text.find(end_marker, start_idx + 1)

if start_idx != -1 and end_idx != -1:
    print(f"--- CONTENT BETWEEN {start_marker} AND {end_marker} ---")
    print(full_text[start_idx:end_idx])
    print("--- END CONTENT ---")
else:
    print("Markers not found.")
