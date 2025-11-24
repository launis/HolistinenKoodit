from docx import Document
import re

doc = Document('Pääarviointikehote.docx')
full_text = '\n'.join([p.text for p in doc.paragraphs])

# Etsi TuomioJaPisteet interface
interface_match = re.search(r'interface TuomioJaPisteet.*?}[\s\n]*}', full_text, re.DOTALL)

if interface_match:
    print("=== LÖYTYI: TuomioJaPisteet Interface ===\n")
    print(interface_match.group(0))
else:
    print("EI LÖYTYNYT: TuomioJaPisteet interface")
    
# Etsi myös pisteet-rakenne
pisteet_match = re.search(r'pisteet:\s*{.*?synteesi_ja_luovuus.*?}', full_text, re.DOTALL)
if pisteet_match:
    print("\n\n=== LÖYTYI: pisteet-rakenne ===\n")
    print(pisteet_match.group(0))
