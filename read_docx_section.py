import docx
import re

def extract_section(filename, section_header_pattern):
    try:
        doc = docx.Document(filename)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        
        text = "\n".join(full_text)
        
        # Etsi kohta 2.6
        # Oletetaan että otsikko on "2.6 Tekninen Toteutuskehys..."
        match = re.search(section_header_pattern, text, re.IGNORECASE)
        if not match:
            print("Section not found via regex. Dumping first 2000 chars to check content:")
            print(text[:2000])
            return

        start_index = match.start()
        # Etsi seuraava pääotsikko (esim. 2.7 tai 3.)
        next_section = re.search(r'\n\d+\.\d+\s', text[start_index + 10:])
        
        if next_section:
            end_index = start_index + 10 + next_section.start()
            content = text[start_index:end_index]
        else:
            content = text[start_index:]
            
        with open("section_2_6.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("Wrote content to section_2_6.txt")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_section("temp_doc.docx", r"2\.6\s+Tekninen")
