from docx import Document

doc = Document('Pääarviointikehote.docx')
full_text = '\n'.join([p.text for p in doc.paragraphs])

# Etsi "pisteet:" tai "TuomioJaPisteet"
search_terms = ['pisteet:', 'TuomioJaPisteet', 'analyysi_ja_prosessi', 'arviointi_ja_argumentaatio']

for term in search_terms:
    pos = full_text.find(term)
    if pos != -1:
        print(f"\n=== Löytyi: '{term}' positiossa {pos} ===")
        # Tulosta 500 merkkiä ennen ja jälkeen
        start = max(0, pos - 200)
        end = min(len(full_text), pos + 800)
        context = full_text[start:end]
        print(context)
        print("\n" + "="*60)
