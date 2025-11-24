import json
from src.report_generator import ReportGenerator

class MockContext:
    def __init__(self, results):
        self.results = results

# Test with the actual Phase 8 output structure
actual_phase8_json = """
{
  "metadata": {
    "luontiaika": "2024-05-18T15:23:00Z",
    "agentti": "TUOMARI-AGENTTI",
    "vaihe": 8,
    "versio": "1.0"
  },
  "metodologinen_loki": "RAJOITUS: Tuomari-agentti käsittelee äärimmäisen laajaa kontekstia...",
  "semanttinen_tarkistussumma": "Tämä tuomio ja pisteytys yhdistää VAIHEIDEN 1-7 havainnot...",
  "pisteytys": {
    "kriteeri1_analyysi": {
      "taso": 4,
      "perustelu": "Käyttäjä osoitti poikkeuksellisen selkeää, iteratiivista ja strategista ohjausta prompt engineeringin avulla."
    },
    "kriteeri2_reflektio": {
      "taso": 2,
      "perustelu": "Reflektio pyrki jäsentämään prosessia ja sisälsi metacognitiivisia elementtejä."
    },
    "kriteeri3_synteesi": {
      "taso": 4,
      "perustelu": "Käyttäjän ohjaus johti 'Supermegatrendien' luomiseen, jotka olivat alkuperäisten megatrendien ylittävää, innovatiivista synteesiä."
    }
  }
}
"""

def test_actual_format():
    print("="*60)
    print("TESTING ACTUAL PHASE 8 OUTPUT FORMAT")
    print("="*60)
    
    context = MockContext({"phase_8": actual_phase8_json})
    generator = ReportGenerator()
    report = generator.generate_report(context)
    
    # Extract OSA 2
    start_marker = "OSA 2: ANALYYTTINEN ARVIOINTI"
    if start_marker in report:
        parts = report.split(start_marker)
        if len(parts) > 1:
            osa2 = parts[1].split("OSA 3")[0] if "OSA 3" in parts[1] else parts[1][:500]
            print(osa2)
        else:
            print("OSA 2 found but could not split.")
    else:
        print("OSA 2 NOT FOUND")
        print("\nFull report preview:")
        print(report[:1000])

if __name__ == "__main__":
    test_actual_format()
