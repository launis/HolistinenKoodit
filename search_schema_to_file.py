from docx import Document

doc = Document('Pääarviointikehote.docx')
full_text = '\n'.join([p.text for p in doc.paragraphs])

# Etsi "pisteet:" tai "TuomioJaPisteet"
search_terms = ['pisteet:', 'TuomioJaPisteet', 'analyysi_ja_prosessi', 'arviointi_ja_argumentaatio']

output = []
for term in search_terms:
    pos = full_text.find(term)
    if pos != -1:
        output.append(f"\n=== Löytyi: '{term}' positiossa {pos} ===\n")
        # Tulosta 500 merkkiä ennen ja jälkeen
        start = max(0, pos - 200)
        end = min(len(full_text), pos + 1000)
        context = full_text[start:end]
        output.append(context)
        output.append("\n" + "="*60 + "\n")

# Tallenna tiedostoon
with open('schema_search_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("Tulokset tallennettu tiedostoon: schema_search_results.txt")
print(f"Löydettiin {len([t for t in search_terms if full_text.find(t) != -1])} hakutermiä")
