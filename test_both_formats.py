import json
from src.report_generator import ReportGenerator

class MockContext:
    def __init__(self, results):
        self.results = results

# Test 1: New format (TuomioJaPisteet interface)
new_format_json = """
{
  "metadata": {
    "luontiaika": "2024-07-30T11:10:00Z",
    "agentti": "TUOMARI-AGENTTI",
    "vaihe": 8,
    "versio": "1.0"
  },
  "semanttinen_tarkistussumma": "Tuomari-agentti on suorittanut synteesin...",
  "pisteet": {
    "analyysi_ja_prosessi": {
      "arvosana": 4,
      "perustelu": "Erinomainen prosessin puhtaus ja analyyttinen syvyys."
    },
    "arviointi_ja_argumentaatio": {
      "arvosana": 3,
      "perustelu": "Hyvä reflektio ja argumentaatio."
    },
    "synteesi_ja_luovuus": {
      "arvosana": 4,
      "perustelu": "Omaperäinen ja strategisesti relevantti synteesi."
    }
  }
}
"""

# Test 2: Old format (pisteytys with taso/kuvaus)
old_format_json = """
{
  "metadata": {
    "luontiaika": "2024-07-30T11:10:00Z",
    "agentti": "TUOMARI-AGENTTI",
    "vaihe": 8,
    "versio": "1.0"
  },
  "semanttinen_tarkistussumma": "Tuomari-agentti on suorittanut synteesin...",
  "pisteytys": {
    "kriteeri_1_analyysi": {
      "taso": 2,
      "kuvaus": "Tyydyttävä analyysi."
    },
    "kriteeri_2_reflektio": {
      "taso": 3,
      "kuvaus": "Hyvä reflektio."
    },
    "kriteeri_3_synteesi": {
      "taso": 4,
      "kuvaus": "Erinomainen synteesi."
    }
  }
}
"""

def test_format(name, json_content):
    print(f"\n{'='*60}")
    print(f"TESTING: {name}")
    print(f"{'='*60}")
    
    context = MockContext({"phase_8": json_content})
    generator = ReportGenerator()
    report = generator.generate_report(context)
    
    # Extract OSA 2
    start_marker = "OSA 2: ANALYYTTINEN ARVIOINTI"
    if start_marker in report:
        parts = report.split(start_marker)
        if len(parts) > 1:
            osa2 = parts[1].split("OSA 3")[0] if "OSA 3" in parts[1] else parts[1]
            print(osa2)
        else:
            print("OSA 2 found but could not split.")
    else:
        print("OSA 2 NOT FOUND")

if __name__ == "__main__":
    test_format("NEW FORMAT (pisteet with arvosana)", new_format_json)
    test_format("OLD FORMAT (pisteytys with taso)", old_format_json)
    print(f"\n{'='*60}")
    print("TESTS COMPLETED")
    print(f"{'='*60}")
