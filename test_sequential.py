import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))
from orchestrator import Orchestrator
from config import EXECUTION_MODES

# Mock dependencies
class MockLLM:
    def generate_response(self, prompt, model):
        return "Mock response"

class MockData:
    pass

class MockContext:
    def __init__(self):
        self.prompt_modules = {"VAIHE 1": "Instructions", "VAIHE 2": "Instructions"}
    def build_prompt(self, key):
        return "Prompt"
    def add_result(self, key, res):
        pass

orchestrator = Orchestrator(MockLLM(), MockData())
context = MockContext()

print("Testing MOODI_A execution...")
# MOODI_A has phase_1, phase_2, phase_3
# But my mock context only has VAIHE 1 and VAIHE 2.
# Orchestrator checks if phase_key is in prompt_modules.
# So phase_3 will return a warning or error string, but it should run phase 1 and 2.

results = orchestrator.run_mode("MOODI_A", context, "model")
print(f"Results keys: {list(results.keys())}")
if "phase_1" in results and "phase_2" in results:
    print("SUCCESS: Phases executed sequentially.")
else:
    print("FAILURE: Phases missing.")
