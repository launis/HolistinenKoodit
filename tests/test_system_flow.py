import sys
import os
import json
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from orchestrator import Orchestrator
from context import AssessmentContext
from data_handler import DataHandler, TextUpload
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestSystemFlow(unittest.TestCase):
    def setUp(self):
        # Setup Dummy Data
        self.history_text = "Opiskelija: Miten tämä toimii? Tekoäly: Hyvin."
        self.product_text = "Tässä on lopputuote. Se on hyvä."
        self.reflection_text = "Opin paljon."
        
        self.data_handler = DataHandler()
        
        # Mock LLM Service if no API key (or for speed)
        # For this test, we want to verify ORCHESTRATION logic, not LLM intelligence.
        # So we will mock the LLM response to be valid JSON to pass parsing.
        self.mock_llm = MagicMock()
        self.mock_llm.get_available_models.return_value = ["gemini-1.5-flash"]
        
        # Default mock response
        self.default_response = json.dumps({
            "metadata": {"timestamp": "2025-01-01"},
            "data": {"analysis": "Test analysis"},
            "pisteet": {
                "analyysi_ja_prosessi": {"arvosana": 4},
                "arviointi_ja_argumentaatio": {"arvosana": 4},
                "synteesi_ja_luovuus": {"arvosana": 4}
            },
            "security_check": {"uhka_havaittu": False}
        })
        self.mock_llm.generate_response.return_value = self.default_response
        
        self.orchestrator = Orchestrator(self.mock_llm, self.data_handler)
        
        # Setup Context
        self.common_rules = "Säännöt..."
        self.prompt_phases = {
            "VAIHE 1": "Ohje 1", "VAIHE 2": "Ohje 2", "VAIHE 3": "Ohje 3",
            "VAIHE 4": "Ohje 4", "VAIHE 5": "Ohje 5", "VAIHE 6": "Ohje 6",
            "VAIHE 7": "Ohje 7", "VAIHE 8": "Ohje 8", "VAIHE 9": "Ohje 9"
        }
        self.context = AssessmentContext(self.common_rules, self.prompt_phases)
        self.context.add_file("Keskusteluhistoria.pdf", self.history_text)
        self.context.add_file("Lopputuote.pdf", self.product_text)
        self.context.add_file("Reflektiodokumentti.pdf", self.reflection_text)

    def test_mode_abc_flow(self):
        print("\n--- Testing Modes A -> B -> C Flow ---")
        
        # Mode A
        print("Running Mode A...")
        res_a = self.orchestrator.run_mode("MOODI_A", self.context, "gemini-1.5-flash", save_dataset=True)
        self.assertIn("phase_1", res_a)
        
        # Verify dataset file created
        dataset_dir = os.path.join(os.getcwd(), "dataset")
        self.assertTrue(os.path.exists(dataset_dir))
        files = os.listdir(dataset_dir)
        self.assertTrue(len(files) > 0, "Dataset directory should not be empty after run")
        
        # Mode B
        print("Running Mode B...")
        res_b = self.orchestrator.run_mode("MOODI_B", self.context, "gemini-1.5-flash", save_dataset=True)
        self.assertIn("phase_4", res_b)
        self.assertIn("phase_7", res_b)
        
        # Mode C
        print("Running Mode C...")
        # Mock Phase 9 (Report Generation) response from ReportGenerator
        # Since Orchestrator calls ReportGenerator directly for Phase 9, we need to ensure it works.
        # But ReportGenerator uses context.results.
        res_c = self.orchestrator.run_mode("MOODI_C", self.context, "gemini-1.5-flash", save_dataset=True)
        self.assertIn("phase_8", res_c)
        self.assertIn("phase_9", res_c)
        
        print("Modes A-B-C completed successfully.")

    def test_full_sequence_flow(self):
        print("\n--- Testing Full Sequence (1-9) Flow ---")
        
        # Reset context results
        self.context.results = {}
        self.orchestrator.results = {}
        
        # Run phases manually as the "Full Process" button does in app.py
        phases = self.orchestrator.get_phases()
        for step in phases:
            step_id = step["id"]
            print(f"Running {step_id}...")
            res = self.orchestrator.run_phase(step_id, self.context, "gemini-1.5-flash", save_dataset=True)
            self.assertIsNotNone(res)
            
        print("Full sequence completed successfully.")

    # Removed separate test_dataset_creation to avoid ordering issues.
    # Verification is done inside test_mode_abc_flow.

if __name__ == '__main__':
    unittest.main()
