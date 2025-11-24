import json
from src.report_generator import ReportGenerator

class MockContext:
    def __init__(self, results):
        self.results = results

json_content = """
{
  "metadata": {
    "luontiaika": "2024-07-30T11:10:00Z",
    "agentti": "TUOMARI-AGENTTI",
    "vaihe": 8,
    "versio": "1.0"
  },
  "semanttinen_tarkistussumma": "Tuomari-agentti on suorittanut synteesin...",
  "konfliktin_ratkaisut": [],
  "mestaruus_poikkeama": {
    "tunnistettu": true,
    "perustelu": "Käyttäjä rikkoi tietoisesti..."
  },
  "aitous_epaily": {
    "automaattinen_lippu": false,
    "viesti_hitl:lle": ""
  },
  "pisteet": {
    "analyysi_ja_prosessi": {
      "arvosana": 4,
      "perustelu": "Käyttäjä osoitti erinomaista prosessin puhtautta ja analyyttistä syvyyttä ohjaamalla tekoälyä iteratiivisesti kohti tarkoituksenmukaisempaa lopputulosta. Varhaisen vaiheen yleisestä kysymyksestä siirryttiin tavoitehakuiseen tarkennukseen (supermegatrendit, 1-sivuinen raportti, kaupalliset vaikutukset). Metakognitiivinen tietoisuus ja input-virheen tunnistaminen korostavat prosessin laadukkuutta."
    },
    "arviointi_ja_argumentaatio": {
      "arvosana": 4,
      "perustelu": "Reflektio oli poikkeuksellisen syvällinen ja uskollinen keskusteluhistorialle. Se kuvasi tarkasti käyttäjän oivalluksia (supermegatrendit), konkreettisia muokkauspyrkimyksiä (Eurooppa-kohta, supistaminen) ja jopa lähtötiedon virheen tunnistamista. Se osoitti vahvaa metakognitiivista tietoisuutta ja rehellisyyttä prosessin kuvaamisessa, välttäen itsetehostusta."
    },
    "synteesi_ja_luovuus": {
      "arvosana": 4,
      "perustelu": "Synteesi oli erittäin omaperäinen ja strategisesti relevantti. 'Supermegatrendien' luominen yhdistelemällä alkuperäisiä megatrendejä korkeamman tason vaikutuskuvauksiksi (Ekologinen Resilienssikriisi, Geoteknologinen Valtaistelu, Epävarmuuden Sosiaalinen Polarisointi) on innovatiivista. Raportin räätälöinti 'Kaupalliselle Johtoryhmälle' kaupallisine vaikutuksineen ja strategisine toimenpiteineen osoittaa syvällistä ymmärrystä kohderyhmästä ja kykyä jalostaa tietoa strategiseksi oivallukseksi."
    }
  },
  "kriittiset_havainnot_yhteenveto": [
    "Prosessi oli iteratiivinen ja tavoitehakuinen",
    "Metakognitiivinen tietoisuus oli vahva"
  ]
}
"""

def verify_format():
    context = MockContext({"phase_8": json_content})
    generator = ReportGenerator()
    report = generator.generate_report(context)
    
    print("--- REPORT PREVIEW (OSA 2) ---")
    start_marker = "OSA 2: ANALYYTTINEN ARVIOINTI"
    if start_marker in report:
        parts = report.split(start_marker)
        if len(parts) > 1:
            osa2 = parts[1].split("OSA 3")[0]
            print(osa2)
        else:
            print("OSA 2 found but could not split.")
    else:
        print("OSA 2 NOT FOUND")

if __name__ == "__main__":
    verify_format()
