from docx import Document
import re

doc = Document('Pääarviointikehote.docx')
full_text = '\n'.join([p.text for p in doc.paragraphs])

# Etsi koko VAIHE 8 osio
vaihe8_start = full_text.find('VAIHE 8')
vaihe9_start = full_text.find('VAIHE 9', vaihe8_start)

if vaihe8_start != -1:
    if vaihe9_start != -1:
        vaihe8_text = full_text[vaihe8_start:vaihe9_start]
    else:
        vaihe8_text = full_text[vaihe8_start:vaihe8_start+10000]
    
    # Etsi interface TuomioJaPisteet
    interface_start = vaihe8_text.find('interface TuomioJaPisteet')
    if interface_start != -1:
        # Ota 2000 merkkiä interfacen jälkeen
        interface_section = vaihe8_text[interface_start:interface_start+2000]
        print("=== TuomioJaPisteet Interface ===\n")
        print(interface_section)
    else:
        print("Interface TuomioJaPisteet ei löytynyt VAIHE 8:sta")
        print("\nVAIHE 8 alkaa näin:")
        print(vaihe8_text[:1000])
else:
    print("VAIHE 8 ei löytynyt dokumentista")
